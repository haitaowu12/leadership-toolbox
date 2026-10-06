#!/usr/bin/env python3
"""Optional private state management. Standard library only; never uploads data."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"

def check(value, schema, where="root"):
    # Validator for the deliberately small subset used by the bundled schemas.
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        raise ValueError(f"{where}: unsupported version/constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{where}: invalid value")
    expected = {"object": dict, "array": list, "string": str}.get(schema.get("type"))
    if expected and not isinstance(value, expected):
        raise ValueError(f"{where}: expected {schema['type']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"{where}: missing {key}")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                check(value[key], sub, f"{where}.{key}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            check(item, schema["items"], f"{where}[{i}]")

def schema(name):
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text())

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def private_path(path):
    path = Path(path).expanduser()
    # Refuse symlinks at every existing component, before resolving.
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise ValueError("private path must not contain symlinks")
    path = path.resolve()
    package = Path(__file__).resolve().parents[1]
    if (path == package or package in path.parents
            or any((part / "SKILL.md").exists() for part in [path, *path.parents])):
        raise ValueError("user data must be outside the installed skill")
    # Also reject any shared Git checkout, including its nested directories.
    if any((part / ".git").exists() for part in [path, *path.parents]):
        raise ValueError("user data must be outside a shared Git repository")
    return path

def safe_file(path):
    if path.is_symlink():
        raise ValueError("state file must not be a symlink")
    return path

@contextmanager
def mutation_lock(data):
    """Fail closed for concurrent helper mutations; never steal a stale lock."""
    lock = data / ".state-mutation.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError("state mutation already locked; stop other writers before retrying") from None
    try:
        with os.fdopen(fd, "w") as out:
            out.write(f"{os.getpid()}\n")
        yield
    finally:
        lock.unlink()

def atomic_write(path, raw, *, expected=None):
    safe_file(path)
    fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        # Catch intervening edits before replacement. External editors must also
        # be stopped: ordinary filesystems do not offer compare-and-swap here.
        if expected is not None and safe_file(path).read_bytes() != expected:
            raise ValueError("profile changed during operation; mutation refused")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()

def validate(data):
    raw = safe_file(data / "profile.json").read_bytes()
    profile = json.loads(raw)
    if not isinstance(profile, dict):
        raise ValueError("profile: expected object; no mutation")
    version = profile.get("schema_version")
    if type(version) is not int or version not in (1, 2):
        raise ValueError("unsupported profile version; no mutation")
    check(profile, schema(f"profile-v{version}"))
    history = safe_file(data / "practice.jsonl")
    seen = set()
    if history.exists():
        for i, line in enumerate(history.read_text().splitlines(), 1):
            if not line.strip():
                continue
            entry = json.loads(line)
            check(entry, schema("practice-v1"), f"practice line {i}")
            if entry["id"] in seen:
                raise ValueError("duplicate practice record id")
            seen.add(entry["id"])
    return profile, raw

def initialise(data):
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    with mutation_lock(data):
        _initialise(data)

def _initialise(data):
    if (data / "profile.json").exists() or (data / "practice.jsonl").exists():
        raise ValueError("existing state; init does not overwrite")
    # Exclusive creation, private permissions; no mandatory profile contents.
    for name, raw in [("profile.json", encode({"schema_version": 2, "goals": [], "preferences": {}})), ("practice.jsonl", b"")]:
        fd = os.open(data / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as out:
            out.write(raw)

def migrate(data):
    with mutation_lock(data):
        return _migrate(data)

def _migrate(data):
    profile, before = validate(data)
    if profile["schema_version"] == 2:
        return None
    after = dict(profile)
    after["schema_version"] = 2
    # Preserve even forward/custom fields; refuse conflicts rather than overwrite.
    if "preferences" in after and not isinstance(after["preferences"], dict):
        raise ValueError("preferences conflict; migration refused without mutation")
    after.setdefault("preferences", {})
    check(after, schema("profile-v2"))
    new_raw = encode(after)
    if safe_file(data / "profile.json").read_bytes() != before:
        raise ValueError("profile changed during operation; mutation refused")
    backups = safe_file(data / "backups")
    backups.mkdir(mode=0o700, exist_ok=True)
    backup = backups / f"profile-v1-{uuid.uuid4().hex}.json"
    atomic_write(backup, before)
    # Receipt stores hashes only. Practice remains byte-for-byte unchanged.
    receipt = {"before_sha256": digest(before), "after_sha256": digest(new_raw), "from": 1, "to": 2}
    atomic_write(backup.with_suffix(".receipt.json"), encode(receipt))
    atomic_write(data / "profile.json", new_raw, expected=before)
    return backup

def rollback(data, backup):
    with mutation_lock(data):
        _rollback(data, backup)

def _rollback(data, backup):
    backup = Path(backup).expanduser()
    if backup.is_symlink() or backup.parent.is_symlink():
        raise ValueError("backup must not contain symlinks")
    backup = backup.resolve()
    if backup.parent != data / "backups":
        raise ValueError("backup must belong to this data directory")
    old = safe_file(backup).read_bytes()
    receipt = json.loads(safe_file(backup.with_suffix(".receipt.json")).read_bytes())
    current = safe_file(data / "profile.json").read_bytes()
    if digest(old) != receipt["before_sha256"] or digest(current) != receipt["after_sha256"]:
        raise ValueError("backup changed or profile has newer edits; rollback refused")
    check(json.loads(old), schema("profile-v1"))
    validate(data)
    atomic_write(data / "profile.json", old, expected=current)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "validate", "migrate", "rollback"])
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--backup")
    args = parser.parse_args()
    try:
        data = private_path(args.data_dir)
        if args.command == "init":
            initialise(data)
        elif args.command == "validate":
            validate(data)
        elif args.command == "migrate":
            backup = migrate(data)
            print(f"Backup: {backup}" if backup else "Already at schema v2; unchanged")
        elif args.command == "rollback":
            if not args.backup:
                raise ValueError("rollback requires --backup")
            rollback(data, args.backup)
        print(f"{args.command}: OK")
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f"State error: {error}\n")

if __name__ == "__main__":
    main()
