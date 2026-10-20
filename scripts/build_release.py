#!/usr/bin/env python3
"""Build reviewed repository and single-skill ZIPs without Git history or user data."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.1"
SKILL_PREFIX = "skills/leadership-toolbox/"


def paths():
    lines = (ROOT / "RELEASE_FILES.txt").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def payload():
    names = paths()
    if len(names) != len(set(names)):
        raise ValueError("duplicate release path")
    result = {}
    for name in names:
        relative = PurePosixPath(name)
        if (not name or "\\" in name or ":" in name or relative.is_absolute()
                or ".." in relative.parts or relative.as_posix() != name):
            raise ValueError(f"unsafe release path: {name}")
        path = ROOT / name
        if any(part.is_symlink() for part in [path, *path.parents]) or not path.is_file():
            raise ValueError(f"unsafe/non-file release entry: {name}")
        result[name] = path.read_bytes()
    return result


def skill_payload(reviewed):
    result = {name.removeprefix(SKILL_PREFIX): raw
              for name, raw in reviewed.items() if name.startswith(SKILL_PREFIX)}
    required = {"SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md"}
    if not required <= set(result):
        raise ValueError("skill archive is missing its entrypoint or notices")
    skill = result["SKILL.md"].decode("utf-8")
    front = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", skill, re.S)
    if not front or not re.search(r"^name: leadership-toolbox$", front[1], re.M):
        raise ValueError("skill archive name must match its leadership-toolbox folder")
    description = re.search(r"^description: (.+)$", front[1], re.M)
    if not description or not 1 <= len(description[1]) <= 200:
        raise ValueError("web upload requires a nonempty description of at most 200 characters")
    return result


def write_archive(output, prefix, files):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"version": VERSION, "files": {
        name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(files.items())}}
    members = dict(files)
    if "RELEASE_MANIFEST.json" in members:
        raise ValueError("reserved generated manifest name in payload")
    members["RELEASE_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(members.items()):
            entry = zipfile.ZipInfo(f"{prefix}/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, raw)
    return output, len(files)


def build(output=None):
    output = Path(output) if output else ROOT / "dist" / f"leadership-toolbox-{VERSION}.zip"
    return write_archive(output, f"leadership-toolbox-{VERSION}", payload())


def build_skill(output=None):
    output = Path(output) if output else ROOT / "dist" / f"leadership-toolbox-skill-{VERSION}.zip"
    return write_archive(output, "leadership-toolbox", skill_payload(payload()))


def build_all(output_dir=None):
    output_dir = Path(output_dir) if output_dir else ROOT / "dist"
    reviewed = payload()
    skill = skill_payload(reviewed)
    source, source_count = write_archive(
        output_dir / f"leadership-toolbox-{VERSION}.zip",
        f"leadership-toolbox-{VERSION}", reviewed)
    upload, skill_count = write_archive(
        output_dir / f"leadership-toolbox-skill-{VERSION}.zip", "leadership-toolbox", skill)
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in (source, upload)), encoding="utf-8")
    return source, upload, checksums, source_count, skill_count


if __name__ == "__main__":
    from validate import validate
    validate()
    source, upload, checksums, source_count, skill_count = build_all()
    print(f"Built {source.name}: {source_count} reviewed files plus manifest")
    print(f"Built {upload.name}: {skill_count} skill files plus manifest")
    print(f"Wrote {checksums.name}; archive creation does not verify host activation")

