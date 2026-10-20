#!/usr/bin/env python3
"""Install a complete skill; keep staging/backups outside host skill discovery."""
import argparse
import os
import json
import re
from urllib.parse import unquote, urlsplit
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "leadership-toolbox"
PRIVATE_NAMES = {"profile.json", "practice.jsonl", ".user-data", "backups", ".git"}
BACKUP_PREFIX = ".leadership-toolbox.backup-"
CORE_FILES = {
    "SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "references/catalog.json", "references/catalog.md",
    "references/workflow.md", "references/user-data.md",
    "scripts/state.py", "schemas/profile-v1.schema.json",
    "schemas/profile-v2.schema.json", "schemas/practice-v1.schema.json",
    "templates/conversation.md", "templates/practice-record.md",
    "templates/role-review.md",
}


def real_path(value, label):
    path = Path(value).expanduser().absolute()
    if any(part.is_symlink() for part in [path, *path.parents]):
        raise ValueError(f"{label} must not contain symlinks")
    return path.resolve()


def overlaps(first, second):
    return first == second or first in second.parents or second in first.parents


def backup_directory(dest, value=None):
    directory = real_path(value if value is not None else dest.parent.parent / ".leadership-toolbox-backups", "backup directory")
    if overlaps(directory, dest.parent):
        raise ValueError("backup directory must be outside and separate from the host skill discovery directory")
    return directory


def required_file(tree, name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("invalid skill file path")
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
        raise ValueError(f"unsafe skill file path: {name}")
    path = tree / name
    if (any(part.is_symlink() for part in [path, *path.parents])
            or not path.is_file() or tree.resolve() not in path.resolve().parents):
        raise ValueError(f"missing or unsafe required skill file: {name}")
    return path


def frontmatter_string(value):
    """Read the single-line string subset used by this package's YAML header.

    This is deliberately not a general YAML parser. Block/flow collections,
    aliases, tags, multiline strings and inline comments are rejected rather
    than guessed at; quoted strings and plain text cover the shipped layouts.
    """
    value = value.strip()
    if not value:
        raise ValueError("SKILL.md frontmatter requires nonempty strings")
    if value.startswith('"'):
        try:
            result = json.loads(value)
        except ValueError as error:
            raise ValueError("invalid quoted SKILL.md frontmatter string") from error
    elif value.startswith("'"):
        if not re.fullmatch(r"'(?:[^']|'')*'", value):
            raise ValueError("invalid quoted SKILL.md frontmatter string")
        result = value[1:-1].replace("''", "'")
    else:
        # Some hosts use YAML 1.1 implicit dates and sexagesimal numbers.
        # Require quotes for those forms so every accepted value is a string.
        if (value[0] in "!&*{}[],#|>@`%\"'"
                or re.search(r"(?:^[-?:]|:)(?:\s|$)|\s#", value)
                or value.lower() in {"null", "~", "true", "false", "yes", "no", "on", "off"}
                or re.fullmatch(
                    r"[0-9]{4}-[0-9]{2}-[0-9]{2}|"
                    r"[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:t| +)"
                    r"[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?"
                    r"(?: *(?:z|[-+][0-9]{1,2}(?::[0-9]{2})?))?", value, re.I)
                or re.fullmatch(
                    r"[-+]?(?:0x[0-9a-f_]+|0o[0-7_]+|0b[01_]+|"
                    r"[0-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?|"
                    r"(?:[0-9][0-9_]*(?:\.[0-9_]*)?|\.[0-9_]+)"
                    r"(?:e[-+]?[0-9]+)?|\.(?:inf|nan))", value, re.I)):
            raise ValueError("unsupported SKILL.md frontmatter string syntax")
        result = value
    if (not isinstance(result, str) or not result.strip()
            or any(ord(char) < 32 or ord(char) == 127 for char in result)):
        raise ValueError("SKILL.md frontmatter requires nonempty single-line strings")
    return result


def check_entrypoint(tree, catalog):
    """Validate the shipped header shape without pinning a release version."""
    skill = (tree / "SKILL.md").read_text(encoding="utf-8")
    front = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", skill, re.S)
    if not front:
        raise ValueError("SKILL.md must begin with complete YAML frontmatter")
    fields = {}
    metadata = None
    section = None
    for line in front[1].split("\n"):
        if any(ord(char) < 32 or ord(char) == 127 for char in line):
            raise ValueError("invalid control character in SKILL.md frontmatter")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        field = re.fullmatch(r"( {2})?([a-z][a-z0-9_-]*):(?: +(.*))?", line)
        if not field:
            raise ValueError("unsupported or malformed SKILL.md frontmatter")
        indent, key, value = field.groups()
        if indent:
            if section != "metadata" or metadata is None:
                raise ValueError("SKILL.md frontmatter has unexpected indentation")
            target = metadata
        else:
            section = key
            target = fields
        if key in target:
            raise ValueError(f"duplicate SKILL.md frontmatter field: {key}")
        if not indent and key == "metadata":
            if value and value.strip():
                raise ValueError("SKILL.md metadata must be an indented mapping")
            metadata = {}
            fields[key] = metadata
        else:
            target[key] = frontmatter_string(value or "")
    if fields.get("name") != "leadership-toolbox":
        raise ValueError("SKILL.md name must match leadership-toolbox")
    description = fields.get("description")
    if not isinstance(description, str) or not 1 <= len(description) <= 200:
        raise ValueError("SKILL.md requires a description of 1 to 200 characters")
    version = catalog.get("package_version")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("skill catalog must contain a valid package_version")
    if metadata is None or metadata.get("version") != version:
        raise ValueError("SKILL.md metadata.version must match the skill catalog")


def check_tree(tree, *, complete=True):
    if tree.is_symlink() or not tree.is_dir():
        raise ValueError("source must be a real complete skill directory")
    for path in tree.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink in skill tree")
        if path.name in PRIVATE_NAMES or path.name == ".env" or path.name.startswith(".env."):
            raise ValueError("private data or repository history inside skill; move it out before updating")
        if not path.is_dir() and not path.is_file():
            raise ValueError("unsupported entry in skill tree")

    if not complete:
        return
    for name in CORE_FILES:
        required_file(tree, name)
    catalog = json.loads((tree / "references/catalog.json").read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("methods"), list) or not catalog["methods"]:
        raise ValueError("skill catalog must contain method entries")
    check_entrypoint(tree, catalog)
    for method in catalog["methods"]:
        if not isinstance(method, dict):
            raise ValueError("invalid method entry in skill catalog")
        required_file(tree, method.get("file"))
        if "knowledge_file" in method:
            required_file(tree, method["knowledge_file"])

    # Follow this version's actual dependencies, including older complete layouts.
    for document in tree.rglob("*.md"):
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            parts = urlsplit(link.strip("<>"))
            if parts.scheme or parts.netloc:
                continue
            target = (document.parent / unquote(parts.path)).resolve() if parts.path else document.resolve()
            if tree.resolve() not in target.parents or not target.is_file():
                raise ValueError(f"missing or outside skill dependency: {document.name}: {link}")


def install(dest, source=SOURCE, backup_dir=None):
    dest = real_path(dest, "destination")
    source = real_path(source, "source")
    if dest.name != "leadership-toolbox":
        raise ValueError("destination folder must be named leadership-toolbox")
    if overlaps(dest, source):
        raise ValueError("destination must be separate from source")
    backup_root = backup_directory(dest, backup_dir)
    if backup_root == source or source in backup_root.parents:
        raise ValueError("backup directory must not be inside the source skill")
    check_tree(source)
    if dest.exists():
        check_tree(dest, complete=False)
    dest.parent.mkdir(parents=True, exist_ok=True)
    backup_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".leadership-stage-", dir=backup_root))
    incoming = staging / "leadership-toolbox"
    backup = None
    try:
        shutil.copytree(source, incoming, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        check_tree(incoming)
        try:
            if dest.exists():
                backup = backup_root / f"{BACKUP_PREFIX}{uuid.uuid4().hex}"
                if backup.exists():
                    raise ValueError("backup path already exists; refusing overwrite")
                os.replace(dest, backup)
            os.replace(incoming, dest)
        except BaseException:
            if backup is not None and backup.exists() and not dest.exists():
                os.replace(backup, dest)
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True, help="explicit host skill path ending in leadership-toolbox")
    parser.add_argument("--backup-dir", help="directory outside the host skill discovery root, on the same filesystem; default: sibling .leadership-toolbox-backups")
    parser.add_argument("--restore", help="previous package backup; preserves the package it replaces")
    args = parser.parse_args()
    try:
        dest = real_path(args.dest, "destination")
        backup_root = backup_directory(dest, args.backup_dir)
        source = SOURCE
        if args.restore:
            source = real_path(args.restore, "restore source")
            # Read legacy adjacent backups, but never create another there.
            if not source.name.startswith(BACKUP_PREFIX) or source.parent not in {backup_root, dest.parent}:
                raise ValueError("restore requires a named backup in the configured backup directory or a legacy adjacent backup")
        backup = install(dest, source, backup_root)
        print("Installed complete skill; external user data unchanged")
        if backup:
            print(f"Previous skill backup: {backup}")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Install error: {error}\n")


if __name__ == "__main__":
    main()
