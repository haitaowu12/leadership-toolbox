"""Distribution and CLI lifecycle checks; these do not activate an assistant host."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "leadership-toolbox"
IMPLICIT_YAML_SCALARS = (
    "2026-10-06", "2026-10-06T17:59:00Z", "2026-10-06t17:59:00+05:30",
    "2026-10-6 7:59:00.5 -5", "2026-10-06 17:59:00",
    "1:20", "-1:20", "+1:20", "1:20:30", "1:20.5", "-1:20:30.5",
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load("distribution_release", ROOT / "scripts/build_release.py")
installer = load("distribution_installer", ROOT / "scripts/install.py")


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()
            and "__pycache__" not in path.parts and path.suffix != ".pyc"}


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    def copy_source(self):
        return Path(shutil.copytree(
            PACKAGE, self.base / "source",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc")))

    def test_skill_zip_has_one_root_complete_resources_and_verified_hashes(self):
        output, count = release.build_skill(self.base / "skill.zip")
        prefix = "leadership-toolbox/"
        expected = {name.removeprefix(release.SKILL_PREFIX)
                    for name in release.paths() if name.startswith(release.SKILL_PREFIX)}
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(set(names),
                             {prefix + name for name in expected}
                             | {prefix + "RELEASE_MANIFEST.json"})
            manifest = json.loads(archive.read(prefix + "RELEASE_MANIFEST.json"))
            self.assertEqual(manifest["version"], release.VERSION)
            self.assertEqual(set(manifest["files"]), expected)
            self.assertEqual(count, len(expected))
            for name, digest in manifest["files"].items():
                raw = archive.read(prefix + name)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                self.assertEqual(raw, (PACKAGE / name).read_bytes())
            for name in ("SKILL.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
                         "references/methods/L32-accountable-repair.md",
                         "references/knowledge/teams-feedback.md",
                         "schemas/situation-v1.schema.json", "scripts/state.py"):
                self.assertIn(prefix + name, names)
            archive.extractall(self.base / "extracted-skill")
        installer.check_tree(self.base / "extracted-skill" / "leadership-toolbox")

    def test_build_all_creates_reproducible_archives_and_outer_checksums(self):
        first = release.build_all(self.base / "first")
        second = release.build_all(self.base / "second")
        for left, right in zip(first[:3], second[:3]):
            self.assertEqual(left.read_bytes(), right.read_bytes())
        checksums = {}
        for line in first[2].read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            checksums[name] = digest
        self.assertEqual(set(checksums), {path.name for path in first[:2]})
        for path in first[:2]:
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             checksums[path.name])

    def test_skill_upload_metadata_and_notices_are_required(self):
        original = release.payload()
        skill_key = release.SKILL_PREFIX + "SKILL.md"
        for failure in ("name", "description", "license", "notices"):
            with self.subTest(failure=failure):
                files = dict(original)
                if failure == "name":
                    files[skill_key] = files[skill_key].replace(
                        b"name: leadership-toolbox", b"name: mismatched-name", 1)
                elif failure == "description":
                    text = files[skill_key].decode("utf-8")
                    text = re.sub(r"^description: .+$",
                                  "description: " + "x" * 201, text, count=1, flags=re.M)
                    files[skill_key] = text.encode("utf-8")
                else:
                    missing = "LICENSE" if failure == "license" else "THIRD_PARTY_NOTICES.md"
                    del files[release.SKILL_PREFIX + missing]
                with self.assertRaises(ValueError):
                    release.skill_payload(files)

    def test_builder_refuses_noncanonical_cross_platform_and_duplicate_paths(self):
        for names in (["../escape"], ["/absolute"], ["C:/drive"], ["nested\\file"],
                      ["safe/../file"], ["./file"], ["file", "file"]):
            with self.subTest(names=names):
                with mock.patch.object(release, "paths", return_value=names):
                    with self.assertRaises(ValueError):
                        release.payload()

    def test_repository_archive_cli_install_update_restore_in_fresh_directories(self):
        output, _ = release.build(self.base / "repository.zip")
        with zipfile.ZipFile(output) as archive:
            archive.extractall(self.base / "source-archive")
        source = self.base / "source-archive" / f"leadership-toolbox-{release.VERSION}"
        script = source / "scripts/install.py"
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        backup_root = self.base / "package-backups"
        private = self.base / "private"
        private.mkdir()
        (private / "profile.json").write_bytes(b'{"fictional":true}\n')
        (private / "practice.jsonl").write_bytes(b'{"fixture":"unchanged"}\n')
        original_private = snapshot(private)
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

        def command(*extra, expect_success=True):
            result = subprocess.run(
                [sys.executable, str(script), "--dest", str(dest),
                 "--backup-dir", str(backup_root), *map(str, extra)],
                cwd=self.base, env=environment, text=True,
                capture_output=True, timeout=30)
            if expect_success:
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            else:
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            return result

        validation = subprocess.run(
            [sys.executable, str(source / "scripts/validate.py")],
            cwd=self.base, env=environment, text=True,
            capture_output=True, timeout=30)
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
        first = command()
        self.assertNotIn("Previous skill backup:", first.stdout)
        self.assertEqual(snapshot(dest), snapshot(source / "skills/leadership-toolbox"))
        (dest / "old-package-only.txt").write_bytes(b"restore this old package\n")
        old_package = snapshot(dest)
        updated = command()
        match = re.search(r"^Previous skill backup: (.+)$", updated.stdout, re.M)
        self.assertIsNotNone(match, updated.stdout)
        old_backup = Path(match[1])
        self.assertEqual(old_backup.parent, backup_root)
        self.assertEqual(snapshot(old_backup), old_package)
        new_package = snapshot(dest)
        self.assertNotIn("old-package-only.txt", new_package)
        self.assertEqual(list(dest.parent.iterdir()), [dest])
        restored = command("--restore", old_backup)
        self.assertEqual(snapshot(dest), old_package)
        self.assertEqual(snapshot(old_backup), old_package)
        replaced = re.search(r"^Previous skill backup: (.+)$", restored.stdout, re.M)
        self.assertIsNotNone(replaced, restored.stdout)
        self.assertEqual(snapshot(Path(replaced[1])), new_package)
        self.assertEqual(snapshot(private), original_private)
        self.assertFalse(list(backup_root.glob(".leadership-stage-*")))
        command("--restore", source / "skills/leadership-toolbox", expect_success=False)
        self.assertEqual(snapshot(dest), old_package)

    def test_incomplete_source_preserves_existing_install(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        previous = snapshot(dest)
        partial = self.base / "partial"
        partial.mkdir()
        (partial / "SKILL.md").write_text("# Incomplete fixture\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            installer.install(dest, partial)
        self.assertEqual(snapshot(dest), previous)

    def test_invalid_skill_entrypoint_preserves_existing_install(self):
        source = self.copy_source()
        skill = source / "SKILL.md"
        original = skill.read_text(encoding="utf-8")
        front, body = original.split("\n---\n", 1)
        description = re.search(r"^description: .+$", front, re.M)[0]
        version_line = re.search(r"^  version: .+$", front, re.M)[0]
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        previous = snapshot(dest)
        backup_root = installer.backup_directory(dest)
        backups = snapshot(backup_root)
        invalid = {
            "empty file": "",
            "plain Markdown": "# Leadership Toolbox\nNo frontmatter.\n",
            "missing opening delimiter": original.removeprefix("---\n"),
            "missing closing delimiter": front + "\n" + body,
            "malformed closing delimiter": front + "\n--\n" + body,
            "missing name": original.replace("name: leadership-toolbox\n", "", 1),
            "wrong name": original.replace("name: leadership-toolbox", "name: wrong-skill", 1),
            "missing description": original.replace(description + "\n", "", 1),
            "blank description": original.replace(description, "description:   ", 1),
            "empty quoted description": original.replace(description, 'description: ""', 1),
            "whitespace quoted description": original.replace(description, 'description: "   "', 1),
            "boolean description": original.replace(description, "description: true", 1),
            "numeric description": original.replace(description, "description: 123", 1),
            "list description": original.replace(description, "description: [leadership]", 1),
            "long description": original.replace(description, "description: " + "x" * 201, 1),
            "missing version": original.replace(version_line + "\n", "", 1),
            "wrong version": original.replace(version_line, '  version: "9.9.9"', 1),
            "unclosed quote": original.replace(version_line, '  version: "0.2.1', 1),
            "mismatched quotes": original.replace(version_line, "  version: \"0.2.1'", 1),
            "duplicate name": original.replace("metadata:", "name: leadership-toolbox\nmetadata:", 1),
            "duplicate description": original.replace("metadata:", description + "\nmetadata:", 1),
            "duplicate version": original.replace(version_line, version_line + "\n" + version_line, 1),
            "duplicate metadata": original.replace("\n---\n", "\nmetadata:\n" + version_line + "\n---\n", 1),
            "wrong parent": original.replace("metadata:", "other:", 1),
            "unindented version": original.replace("  version:", "version:", 1),
            "wrong indentation": original.replace("  version:", "    version:", 1),
            "tab indentation": original.replace("  version:", "\tversion:", 1),
            "metadata scalar": original.replace("metadata:", "metadata: text", 1),
            "malformed field": original.replace("metadata:", "invalid syntax\nmetadata:", 1),
            "unquoted mapping": original.replace(description, "description: nested: value", 1),
            "unsupported alias": original.replace(description, "description: *alias", 1),
            "unsupported multiline": original.replace(description, "description: >\n  Some text", 1),
            "control character": original.replace(description, "description: text\x00", 1),
        }
        invalid.update({
            "implicit YAML scalar " + value:
                original.replace(description, "description: " + value, 1)
            for value in IMPLICIT_YAML_SCALARS
        })
        for label, contents in invalid.items():
            with self.subTest(label=label):
                skill.write_text(contents, encoding="utf-8")
                with mock.patch.object(installer.os, "replace") as replace:
                    with self.assertRaises(ValueError):
                        installer.install(dest, source)
                    replace.assert_not_called()
                self.assertEqual(snapshot(dest), previous)
                self.assertEqual(snapshot(backup_root), backups)
                self.assertEqual(list(dest.parent.iterdir()), [dest])
                self.assertFalse(list(backup_root.glob(".leadership-stage-*")))

    def test_invalid_catalog_version_preserves_existing_install(self):
        source = self.copy_source()
        path = source / "references/catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        previous = snapshot(dest)
        for version in (None, "", 0.2, [], {}, True, "v0.2.1", "9.9.9"):
            with self.subTest(version=version):
                catalog["package_version"] = version
                path.write_text(json.dumps(catalog), encoding="utf-8")
                with self.assertRaises(ValueError):
                    installer.install(dest, source)
                self.assertEqual(snapshot(dest), previous)
        del catalog["package_version"]
        path.write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaises(ValueError):
            installer.install(dest, source)
        self.assertEqual(snapshot(dest), previous)

    def test_supported_entrypoint_strings_and_older_package_versions(self):
        source = self.copy_source()
        skill = source / "SKILL.md"
        original = skill.read_text(encoding="utf-8")
        catalog_path = source / "references/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        current_version = catalog["package_version"]
        version_line = re.search(r"^  version: .+$", original, re.M)[0]
        for version in ("0.1.0", "0.2.0", current_version):
            catalog["package_version"] = version
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            for quote in ("", "'", '"'):
                with self.subTest(version=version, quote=quote):
                    contents = original.replace(version_line, f"  version: {quote}{version}{quote}", 1)
                    skill.write_text(contents, encoding="utf-8")
                    installer.check_tree(source)
        header = ('---\n# Supported single-line scalar forms\n'
                  'name: "leadership-toolbox"\n'
                  "description: 'Help with a leader''s decisions: practical support.'\n"
                  f'\nmetadata:\n  version: "{current_version}"\n---\n')
        skill.write_bytes((header + original.split("\n---\n", 1)[1]).replace("\n", "\r\n").encode("utf-8"))
        installer.check_tree(source)

    def test_quoted_dates_timestamps_and_sexagesimal_values_are_strings(self):
        for value in IMPLICIT_YAML_SCALARS:
            for quote in ("'", '"'):
                with self.subTest(value=value, quote=quote):
                    self.assertEqual(installer.frontmatter_string(quote + value + quote), value)

    def test_staged_entrypoint_is_checked_before_destination_replacement(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        previous = snapshot(dest)
        copytree = shutil.copytree

        def damaged_copy(source, target, *args, **kwargs):
            result = copytree(source, target, *args, **kwargs)
            if Path(target).name == "leadership-toolbox":
                (Path(target) / "SKILL.md").write_text("# Damaged staged skill\n", encoding="utf-8")
            return result

        with mock.patch.object(installer.shutil, "copytree", side_effect=damaged_copy):
            with mock.patch.object(installer.os, "replace") as replace:
                with self.assertRaises(ValueError):
                    installer.install(dest)
                replace.assert_not_called()
        self.assertEqual(snapshot(dest), previous)
        self.assertFalse(list(installer.backup_directory(dest).iterdir()))

    def test_malformed_existing_entrypoint_can_be_repaired_but_not_restored(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        original = snapshot(dest)
        (dest / "SKILL.md").write_bytes(b"malformed old package\n")
        damaged = snapshot(dest)
        backup = installer.install(dest)
        self.assertEqual(snapshot(dest), original)
        self.assertEqual(snapshot(backup), damaged)
        with self.assertRaises(ValueError):
            installer.install(dest, backup)
        self.assertEqual(snapshot(dest), original)
        self.assertEqual(snapshot(backup), damaged)

    def test_missing_core_or_catalog_card_is_rejected_before_replacement(self):
        source = self.copy_source()
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        previous = snapshot(dest)
        catalog = json.loads((source / "references/catalog.json").read_text(encoding="utf-8"))
        missing_names = [
            "LICENSE", "scripts/state.py", "schemas/practice-v1.schema.json",
            catalog["methods"][0]["file"], catalog["methods"][0]["knowledge_file"]]
        for name in missing_names:
            with self.subTest(name=name):
                path = source / name
                raw = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaises(ValueError):
                        installer.install(dest, source)
                    self.assertEqual(snapshot(dest), previous)
                finally:
                    path.write_bytes(raw)

    def test_environment_files_are_rejected_in_source_and_destination(self):
        source = self.copy_source()
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        for location in (source, dest):
            for name in (".env", ".env.local", ".env.production"):
                with self.subTest(location=location.name, name=name):
                    path = location / name
                    path.write_text("FICTIONAL_SETTING=fixture\n", encoding="utf-8")
                    previous = snapshot(dest)
                    try:
                        with self.assertRaises(ValueError):
                            installer.install(dest, source)
                        self.assertEqual(snapshot(dest), previous)
                        self.assertTrue(path.is_file())
                    finally:
                        path.unlink()

    def test_catalog_paths_cannot_escape_or_follow_symlinks(self):
        source = self.copy_source()
        catalog_path = source / "references/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        original = catalog["methods"][0]["file"]
        for name in ("../outside.md", "/absolute.md", "C:/drive.md",
                     "references\\method.md", "./SKILL.md", "references/../SKILL.md"):
            with self.subTest(name=name):
                catalog["methods"][0]["file"] = name
                catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
                with self.assertRaises(ValueError):
                    installer.check_tree(source)
        catalog["methods"][0]["file"] = original
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        card = source / original
        raw = card.read_bytes()
        external = self.base / "outside.md"
        external.write_bytes(raw)
        card.unlink()
        card.symlink_to(external)
        with self.assertRaises(ValueError):
            installer.check_tree(source)


    def test_missing_runtime_dependencies_preserve_existing_install(self):
        source = self.copy_source()
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        previous = snapshot(dest)
        for name in ("dimensions.json", "matching.md", "interview.md",
                     "measurement.md", "evidence-map.md", "sources.json"):
            with self.subTest(name=name):
                path = source / "references" / name
                raw = path.read_bytes()
                path.unlink()
                try:
                    with self.assertRaises(ValueError):
                        installer.install(dest, source)
                    self.assertEqual(snapshot(dest), previous)
                finally:
                    path.write_bytes(raw)

    def test_missing_or_escaping_markdown_dependency_is_rejected(self):
        source = self.copy_source()
        skill = source / "SKILL.md"
        original = skill.read_text(encoding="utf-8")
        (self.base / "outside.md").write_text("fixture", encoding="utf-8")
        for target in ("references/missing.md", "../outside.md"):
            with self.subTest(target=target):
                skill.write_text(original + "\n[Fixture](" + target + ")\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    installer.check_tree(source)
        skill.write_text(original, encoding="utf-8")
        installer.check_tree(source)

    def test_damaged_destination_can_be_reinstalled_and_restored(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        original = snapshot(dest)
        complete_backup = installer.install(dest)
        (dest / "SKILL.md").unlink()
        (dest / "references/methods/L01-delegation.md").unlink()
        damaged = snapshot(dest)
        damaged_backup = installer.install(dest)
        self.assertEqual(snapshot(dest), original)
        self.assertEqual(snapshot(damaged_backup), damaged)
        with self.assertRaises(ValueError):
            installer.install(dest, damaged_backup)
        self.assertEqual(snapshot(dest), original)
        (dest / "references/measurement.md").unlink()
        damaged_again = snapshot(dest)
        preserved = installer.install(dest, complete_backup)
        self.assertEqual(snapshot(dest), original)
        self.assertEqual(snapshot(preserved), damaged_again)


if __name__ == "__main__":
    unittest.main()
