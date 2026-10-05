#!/usr/bin/env python3
"""Copy a complete skill with replace/restore backups; never touches external state."""
import argparse
import os
from pathlib import Path
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "leadership-toolbox"
PRIVATE_NAMES = {"profile.json", "practice.jsonl", ".user-data", "backups", ".git"}

def check_tree(tree):
    if tree.is_symlink() or not tree.is_dir() or not (tree / "SKILL.md").is_file():
        raise ValueError("source must be a real complete skill directory")
    for path in tree.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink in skill tree")
        if path.name in PRIVATE_NAMES:
            raise ValueError("private data or repository history inside skill; move it out before updating")


def install(dest, source=SOURCE):
    dest = Path(dest).expanduser()
    for part in [dest, *dest.parents]:
        if part.is_symlink():
            raise ValueError("destination must not contain symlinks")
    dest = dest.resolve()
    source = Path(source)
    for part in [source, *source.parents]:
        if part.is_symlink():
            raise ValueError("source must not contain symlinks")
    source = source.resolve()
    if dest.name != "leadership-toolbox":
        raise ValueError("destination folder must be named leadership-toolbox")
    if dest == source or source in dest.parents or dest in source.parents:
        raise ValueError("destination must be separate from source")
    check_tree(source)
    if dest.exists():
        check_tree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".leadership-stage-", dir=dest.parent))
    incoming = staging / "leadership-toolbox"
    backup = None
    try:
        shutil.copytree(source, incoming, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        check_tree(incoming)
        if dest.exists():
            backup = dest.parent / f".leadership-toolbox.backup-{uuid.uuid4().hex}"
            os.replace(dest, backup)
        try:
            os.replace(incoming, dest)
        except BaseException:
            if backup:
                os.replace(backup, dest)
            raise
    finally:
        shutil.rmtree(staging)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True, help="explicit host skill path ending in leadership-toolbox")
    parser.add_argument("--restore", help="previous backup from this destination's parent")
    args = parser.parse_args()
    try:
        source = SOURCE
        if args.restore:
            source = Path(args.restore).expanduser()
            if source.is_symlink() or not source.name.startswith(".leadership-toolbox.backup-") or source.resolve().parent != Path(args.dest).expanduser().resolve().parent:
                raise ValueError("restore requires a backup next to the destination")
        backup = install(args.dest, source)
        print("Installed complete skill; external user data unchanged")
        if backup:
            print(f"Previous skill backup: {backup}")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Install error: {error}\n")

if __name__ == "__main__":
    main()
