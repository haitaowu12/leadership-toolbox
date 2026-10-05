#!/usr/bin/env python3
"""Build only reviewed explicit paths, plus file hashes. Never archives Git history."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"

def paths():
    return [line.strip() for line in (ROOT / "RELEASE_FILES.txt").read_text().splitlines() if line.strip() and not line.startswith("#")]

def build(output=None):
    names = paths()
    if len(names) != len(set(names)):
        raise ValueError("duplicate release path")
    payload = {}
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe release path")
        path = ROOT / relative
        if any(part.is_symlink() for part in [path, *path.parents]) or not path.is_file():
            raise ValueError(f"unsafe/non-file release entry: {name}")
        payload[name] = path.read_bytes()
    manifest = {"version": VERSION, "files": {name: hashlib.sha256(raw).hexdigest() for name, raw in payload.items()}}
    output = Path(output) if output else ROOT / "dist" / f"leadership-toolbox-{VERSION}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(payload.items()):
            archive.writestr(f"leadership-toolbox-{VERSION}/{name}", raw)
        archive.writestr(f"leadership-toolbox-{VERSION}/RELEASE_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    return output, len(payload)

if __name__ == "__main__":
    from validate import validate
    validate()
    result, count = build()
    print(f"Built {result.name}: {count} allowlisted files plus checksum manifest")
