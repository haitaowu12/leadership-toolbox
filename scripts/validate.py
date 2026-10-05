#!/usr/bin/env python3
"""Structural, local-link, metadata and reviewed-public-file validation."""
import json
import hashlib
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "leadership-toolbox"
DENIED = re.compile(r"(?:/Users/|/home/|sediment://|gh[pousr]_[A-Za-z0-9]{15,}|github_pat_|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|tonys-second-brain|personal-private|authorized-private-noncommercial)", re.I)


def validate(root=ROOT):
    errors = []
    allowed = [line.strip() for line in (root / "RELEASE_FILES.txt").read_text().splitlines() if line.strip() and not line.startswith("#")]
    if len(allowed) != len(set(allowed)):
        errors.append("duplicate allowlist paths")
    skip = {".git", "__pycache__", "dist", ".venv"}
    actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file() and not any(part in skip for part in path.relative_to(root).parts) and path.suffix != ".pyc"}
    if "RELEASE_MANIFEST.json" in actual:
        actual.remove("RELEASE_MANIFEST.json")
        manifest = json.loads((root / "RELEASE_MANIFEST.json").read_text())
        if set(manifest.get("files", {})) != set(allowed):
            errors.append("checksum manifest file list mismatch")
        for name, expected in manifest.get("files", {}).items():
            if name not in allowed or not (root / name).is_file() or hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
                errors.append(f"checksum mismatch: {name}")
    if actual != set(allowed):
        errors.append(f"allowlist mismatch: unreviewed={sorted(actual-set(allowed))}; missing={sorted(set(allowed)-actual)}")
    for name in allowed:
        path = root / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink() or not path.is_file():
            errors.append(f"unsafe/missing file: {name}")
            continue
        text = path.read_text()
        # Only the scanner's own pattern definition is a deliberate marker.
        scanned = "\n".join(line for line in text.splitlines() if not (name == "scripts/validate.py" and line.startswith("DENIED = re.compile(")))
        if DENIED.search(scanned):
            errors.append(f"private path/source/credential marker: {name}")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError:
                errors.append(f"invalid JSON: {name}")
        if path.suffix == ".md":
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                link = link.strip("<>")
                parts = urlsplit(link)
                if parts.scheme:
                    if parts.scheme != "https":
                        errors.append(f"unexpected link scheme: {name}")
                    continue
                target = (path.parent / unquote(parts.path)).resolve() if parts.path else path.resolve()
                if root.resolve() not in [target, *target.parents] or not target.is_file():
                    errors.append(f"broken/outside link: {name}: {link}")
    package = root / "skills" / "leadership-toolbox"
    skill = (package / "SKILL.md").read_text()
    if not skill.startswith("---\n") or skill.count("---") < 2:
        errors.append("missing frontmatter")
    front = skill.split("---", 2)[1]
    if not re.search(r"^name: leadership-toolbox$", front, re.M) or not re.search(r"^description: .+", front, re.M):
        errors.append("invalid skill metadata")
    metadata = (package / "agents/openai.yaml").read_text()
    if "$leadership-toolbox" not in metadata:
        errors.append("missing invocation prompt")
    catalog = json.loads((package / "references/catalog.json").read_text())
    ids = [method["id"] for method in catalog["methods"]]
    if len(ids) != len(set(ids)) or ids != [f"L{i:02}" for i in range(1, 15)]:
        errors.append("method IDs duplicate, missing or unstable")
    for method in catalog["methods"]:
        path = package / method["file"]
        if not path.is_file() or method["version"] != catalog["package_version"]:
            errors.append(f"invalid catalog path/version: {method['id']}")
        if method["id"] == "L05" and method["license"] != "CC-BY-SA-4.0":
            errors.append("L05 licence boundary lost")
    if errors:
        raise ValueError("\n".join(errors))
    return len(allowed), len(ids)

if __name__ == "__main__":
    try:
        files, methods = validate()
        print(f"PASS: {files} reviewed files; {methods} methods; local links, JSON, metadata and public-file boundary")
        print("External links/source claims require source review; structural checks do not prove human outcomes.")
    except (ValueError, OSError) as error:
        sys.exit(str(error))
