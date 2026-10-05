#!/usr/bin/env python3
"""Install a complete skill; keep staging/backups outside host skill discovery."""
import argparse
import os
from pathlib import Path
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "leadership-toolbox"
PRIVATE_NAMES = {"profile.json", "practice.jsonl", ".user-data", "backups", ".git"}
BACKUP_PREFIX = ".leadership-toolbox.backup-"


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


def check_tree(tree):
    if tree.is_symlink() or not tree.is_dir() or not (tree / "SKILL.md").is_file():
        raise ValueError("source must be a real complete skill directory")
    for path in tree.rglob("*"):
        if path.is_symlink():
            raise ValueError("symlink in skill tree")
        if path.name in PRIVATE_NAMES:
            raise ValueError("private data or repository history inside skill; move it out before updating")
        if not path.is_dir() and not path.is_file():
            raise ValueError("unsupported entry in skill tree")


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
        check_tree(dest)
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
