import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/leadership-toolbox"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

state = load("state", PACKAGE / "scripts/state.py")
installer = load("installer", ROOT / "scripts/install.py")
release = load("release", ROOT / "scripts/build_release.py")
validator = load("validator", ROOT / "scripts/validate.py")

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.data = self.base / "private"
        self.data.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def legacy(self, extra=None):
        profile = {"schema_version": 1, "goals": ["Develop a specific task skill"], "preferred_name": "", "custom": {"retain": [1, 2]}}
        if extra:
            profile.update(extra)
        raw = json.dumps(profile, ensure_ascii=False).encode()
        (self.data / "profile.json").write_bytes(raw)
        entry = {"schema_version": 1, "id": "fictional-01", "date": "2026-10-05", "package_version": "0.0.1", "method_id": "L02", "method_version": "0.0.1", "prediction": "A chosen step", "outcome_signal": "Attempt discussed", "guardrail": "No added overload", "review_date": "2026-10-12", "status": "declined", "custom": "preserve"}
        history = (json.dumps(entry, ensure_ascii=False) + "\n\n").encode()
        (self.data / "practice.jsonl").write_bytes(history)
        return profile, raw, history

    def test_blank_profile_is_valid_and_init_is_non_overwriting(self):
        self.data.rmdir()
        state.initialise(self.data)
        profile, raw = state.validate(self.data)
        self.assertEqual(profile["goals"], [])
        with self.assertRaises(ValueError):
            state.initialise(self.data)
        self.assertEqual((self.data / "profile.json").read_bytes(), raw)

    def test_migration_preserves_extensions_and_history_and_rollback_bytes(self):
        profile, raw, history = self.legacy()
        backup = state.migrate(self.data)
        migrated, _ = state.validate(self.data)
        self.assertEqual(migrated["custom"], profile["custom"])
        self.assertEqual(migrated["goals"], profile["goals"])
        self.assertEqual((self.data / "practice.jsonl").read_bytes(), history)
        self.assertEqual(backup.read_bytes(), raw)
        state.rollback(self.data, backup)
        self.assertEqual((self.data / "profile.json").read_bytes(), raw)
        self.assertEqual((self.data / "practice.jsonl").read_bytes(), history)

    def test_rollback_refuses_newer_profile_edits(self):
        self.legacy()
        backup = state.migrate(self.data)
        current = json.loads((self.data / "profile.json").read_text())
        current["goals"].append("Newer goal")
        newer = state.encode(current)
        (self.data / "profile.json").write_bytes(newer)
        with self.assertRaises(ValueError):
            state.rollback(self.data, backup)
        self.assertEqual((self.data / "profile.json").read_bytes(), newer)

    def test_profile_rollback_preserves_newer_practice_entries(self):
        _, raw, history = self.legacy()
        backup = state.migrate(self.data)
        newer = json.loads(history.splitlines()[0])
        newer["id"] = "fictional-02"
        newer["status"] = "mixed"
        newer["observations"] = ["Newer situated observation"]
        extended = history + (json.dumps(newer) + "\n").encode()
        (self.data / "practice.jsonl").write_bytes(extended)
        state.rollback(self.data, backup)
        self.assertEqual((self.data / "profile.json").read_bytes(), raw)
        self.assertEqual((self.data / "practice.jsonl").read_bytes(), extended)

    def test_unsupported_profile_refuses_without_mutation(self):
        _, _, history = self.legacy({"schema_version": 99})
        raw = (self.data / "profile.json").read_bytes()
        with self.assertRaises(ValueError):
            state.migrate(self.data)
        self.assertEqual((self.data / "profile.json").read_bytes(), raw)
        self.assertEqual((self.data / "practice.jsonl").read_bytes(), history)
        self.assertFalse((self.data / "backups").exists())

    def test_preferences_conflict_refuses_without_mutation(self):
        _, raw, _ = self.legacy({"preferences": "cannot overwrite"})
        with self.assertRaises(ValueError):
            state.migrate(self.data)
        self.assertEqual((self.data / "profile.json").read_bytes(), raw)
        self.assertFalse((self.data / "backups").exists())

    def test_invalid_history_prevents_profile_migration(self):
        _, raw, _ = self.legacy()
        (self.data / "practice.jsonl").write_text('{"schema_version": 99}\n')
        with self.assertRaises(ValueError):
            state.migrate(self.data)
        self.assertEqual((self.data / "profile.json").read_bytes(), raw)

    def test_duplicate_history_id_is_rejected(self):
        _, _, history = self.legacy()
        (self.data / "practice.jsonl").write_bytes(history + history)
        with self.assertRaises(ValueError):
            state.validate(self.data)

    def test_symlink_state_and_shared_repo_locations_refused(self):
        link = self.base / "linked"
        link.symlink_to(self.data, target_is_directory=True)
        with self.assertRaises(ValueError):
            state.private_path(link)
        shared = self.base / "shared"
        (shared / ".git").mkdir(parents=True)
        with self.assertRaises(ValueError):
            state.private_path(shared / "private")
        with self.assertRaises(ValueError):
            state.private_path(PACKAGE / "private")

    def test_fresh_install_is_complete_and_external_state_survives_updates(self):
        _, raw, history = self.legacy()
        dest = self.base / "host" / "leadership-toolbox"
        self.assertIsNone(installer.install(dest))
        self.assertTrue((dest / "LICENSE").is_file())
        self.assertTrue((dest / "references/methods/L14-handoff.md").is_file())
        self.assertTrue((dest / "scripts/state.py").is_file())
        (dest / "old-version-marker.txt").write_text("old package only")
        backup = installer.install(dest)
        self.assertFalse((dest / "old-version-marker.txt").exists())
        self.assertTrue((backup / "old-version-marker.txt").exists())
        installer.install(dest, backup)
        self.assertTrue((dest / "old-version-marker.txt").exists())
        self.assertEqual((self.data / "profile.json").read_bytes(), raw)
        self.assertEqual((self.data / "practice.jsonl").read_bytes(), history)

    def test_update_refuses_misplaced_private_data_preserving_old_skill(self):
        dest = self.base / "host" / "leadership-toolbox"
        installer.install(dest)
        (dest / "profile.json").write_text("private fixture")
        before = (dest / "SKILL.md").read_bytes()
        with self.assertRaises(ValueError):
            installer.install(dest)
        self.assertEqual((dest / "SKILL.md").read_bytes(), before)
        self.assertEqual((dest / "profile.json").read_text(), "private fixture")

    def test_destination_symlink_refused(self):
        target = self.base / "target"
        target.mkdir()
        dest = self.base / "leadership-toolbox"
        dest.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            installer.install(dest)
        self.assertFalse((target / "SKILL.md").exists())

    def test_archive_has_only_allowlist_and_hashes_and_is_independent(self):
        output, count = release.build(self.base / "release.zip")
        prefix = f"leadership-toolbox-{release.VERSION}/"
        with zipfile.ZipFile(output) as archive:
            manifest = json.loads(archive.read(prefix + "RELEASE_MANIFEST.json"))
            names = set(archive.namelist())
            self.assertEqual(names, {prefix + name for name in release.paths()} | {prefix + "RELEASE_MANIFEST.json"})
            self.assertEqual(count, len(manifest["files"]))
            for name, expected in manifest["files"].items():
                self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), expected)
            archive.extractall(self.base / "extracted")
        extracted = self.base / "extracted" / f"leadership-toolbox-{release.VERSION}"
        validator.validate(extracted)
        fresh_installer = load("fresh_installer", extracted / "scripts/install.py")
        dest = self.base / "fresh-host" / "leadership-toolbox"
        fresh_installer.install(dest)
        installed_state = load("installed_state", dest / "scripts/state.py")
        data = self.base / "fresh-private"
        installed_state.initialise(data)
        installed_state.validate(data)
        card = extracted / "skills/leadership-toolbox/references/methods/L02-grow.md"
        card.write_text(card.read_text() + "\nUnexpected mutation\n")
        with self.assertRaises(ValueError):
            validator.validate(extracted)

    def test_package_validation(self):
        files, methods = validator.validate()
        self.assertGreater(files, 30)
        self.assertEqual(methods, 14)

if __name__ == "__main__":
    unittest.main()
