import hashlib
import importlib.util
import json
import io
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock
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

    def test_nested_state_inside_another_skill_is_refused(self):
        other = self.base / "host" / "skills" / "another-skill"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("# Other installed skill\n")
        for destination in (other, other / "references" / "private"):
            with self.subTest(destination=destination.name):
                with self.assertRaisesRegex(ValueError, "outside the installed skill"):
                    state.private_path(destination)
                self.assertFalse((destination / "profile.json").exists())

    def test_nonobject_profiles_fail_cleanly_without_mutation(self):
        for raw in (b"[]", b"null", b'"profile"', b"7", b"true"):
            with self.subTest(raw=raw):
                (self.data / "profile.json").write_bytes(raw)
                for operation in (state.validate, state.migrate):
                    with self.assertRaisesRegex(ValueError, "expected object"):
                        operation(self.data)
                stderr = io.StringIO()
                with mock.patch.object(sys, "argv", ["state.py", "validate", "--data-dir", str(self.data)]), \
                        mock.patch.object(state, "private_path", return_value=self.data), \
                        mock.patch.object(sys, "stderr", stderr):
                    with self.assertRaises(SystemExit) as error:
                        state.main()
                self.assertEqual(error.exception.code, 1)
                self.assertIn("State error: profile: expected object", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())
                self.assertEqual((self.data / "profile.json").read_bytes(), raw)
                self.assertFalse((self.data / "backups").exists())
                self.assertFalse((self.data / ".state-mutation.lock").exists())

    def test_migration_refuses_edit_after_validation(self):
        self.legacy()
        newer = state.encode({"schema_version": 1, "goals": ["Newer user edit"]})
        real_validate = state.validate

        def edit_after_validation(data):
            result = real_validate(data)
            (data / "profile.json").write_bytes(newer)
            return result

        with mock.patch.object(state, "validate", side_effect=edit_after_validation):
            with self.assertRaisesRegex(ValueError, "profile changed"):
                state.migrate(self.data)
        self.assertEqual((self.data / "profile.json").read_bytes(), newer)
        self.assertFalse((self.data / "backups").exists())
        self.assertFalse((self.data / ".state-mutation.lock").exists())

    def test_migration_rechecks_after_writing_backup_receipt(self):
        _, before, history = self.legacy()
        newer = state.encode({"schema_version": 1, "goals": ["Edit during backup"]})
        real_write = state.atomic_write

        def edit_after_receipt(path, raw, **kwargs):
            result = real_write(path, raw, **kwargs)
            if path.name.endswith(".receipt.json"):
                (self.data / "profile.json").write_bytes(newer)
            return result

        with mock.patch.object(state, "atomic_write", side_effect=edit_after_receipt):
            with self.assertRaisesRegex(ValueError, "profile changed"):
                state.migrate(self.data)
        self.assertEqual((self.data / "profile.json").read_bytes(), newer)
        self.assertEqual((self.data / "practice.jsonl").read_bytes(), history)
        backups = [p for p in (self.data / "backups").glob("*.json") if ".receipt." not in p.name]
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), before)
        self.assertFalse(list(self.data.glob(".state-*")))

    def test_rollback_refuses_edit_during_validation(self):
        self.legacy()
        backup = state.migrate(self.data)
        newer = state.encode({"schema_version": 2, "goals": ["Edit during rollback"], "preferences": {}})
        real_validate = state.validate

        def edit_during_validation(data):
            result = real_validate(data)
            (data / "profile.json").write_bytes(newer)
            return result

        with mock.patch.object(state, "validate", side_effect=edit_during_validation):
            with self.assertRaisesRegex(ValueError, "profile changed"):
                state.rollback(self.data, backup)
        self.assertEqual((self.data / "profile.json").read_bytes(), newer)
        self.assertFalse(list(self.data.glob(".state-*")))

    def test_exclusive_lock_refuses_all_mutations_and_another_process(self):
        _, before, history = self.legacy()
        with state.mutation_lock(self.data):
            for operation in (lambda: state.initialise(self.data), lambda: state.migrate(self.data),
                              lambda: state.rollback(self.data, self.data / "backups" / "unused.json")):
                with self.assertRaisesRegex(ValueError, "already locked"):
                    operation()
            code = ("import importlib.util, pathlib, sys; "
                    "s=importlib.util.spec_from_file_location('state',sys.argv[1]); "
                    "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                    "m.migrate(pathlib.Path(sys.argv[2]))")
            result = subprocess.run([sys.executable, "-c", code, str(PACKAGE / "scripts/state.py"), str(self.data)],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already locked", result.stderr)
            self.assertEqual((self.data / "profile.json").read_bytes(), before)
            self.assertEqual((self.data / "practice.jsonl").read_bytes(), history)
        self.assertFalse((self.data / ".state-mutation.lock").exists())
        self.assertIsNotNone(state.migrate(self.data))

    def test_preexisting_lock_is_never_stolen(self):
        _, before, _ = self.legacy()
        lock = self.data / ".state-mutation.lock"
        lock.write_bytes(b"other or interrupted writer\n")
        with self.assertRaisesRegex(ValueError, "already locked"):
            state.migrate(self.data)
        self.assertEqual(lock.read_bytes(), b"other or interrupted writer\n")
        self.assertEqual((self.data / "profile.json").read_bytes(), before)

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
        catalog = json.loads((PACKAGE / "references/catalog.json").read_text(encoding="utf-8"))
        self.assertGreater(files, 30)
        self.assertEqual(methods, len(catalog["methods"]))
        self.assertEqual(methods, catalog["method_count"])
        self.assertEqual(catalog["package_version"], "0.2.1")
    def catalog_fixture(self):
        catalog = json.loads((PACKAGE / "references/catalog.json").read_text(encoding="utf-8"))
        dimensions = json.loads((PACKAGE / "references/dimensions.json").read_text(encoding="utf-8"))
        files = {path.relative_to(PACKAGE).as_posix(): path.read_text(encoding="utf-8") for path in PACKAGE.rglob("*.md")}
        return catalog, dimensions, files

    def test_catalog_accepts_an_additional_stable_method(self):
        catalog, dimensions, files = self.catalog_fixture()
        method = json.loads(json.dumps(catalog["methods"][0]))
        previous_id, previous_file = method["id"], method["file"]
        method["id"] = f"L{max(int(item['id'][1:]) for item in catalog['methods']) + 1:02}"
        method["file"] = f"references/methods/{method['id']}-fixture.md"
        method["guide_url"] = "https://github.com/haitaowu12/leadership-toolbox/blob/main/skills/leadership-toolbox/" + method["file"] + "#try-it"
        files[method["file"]] = files[previous_file].replace(f"# {previous_id} · ", f"# {method['id']} · ", 1)
        files["references/catalog.md"] += f"\n[Fixture](methods/{method['id']}-fixture.md)\n"
        catalog["methods"].append(method)
        catalog["method_count"] = len(catalog["methods"])
        self.assertEqual(validator.validate_catalog(catalog, dimensions, files), [])

    def test_catalog_rejects_mismatched_count_duplicate_and_unordered_ids(self):
        for change in ("count", "duplicate", "order"):
            with self.subTest(change=change):
                catalog, dimensions, files = self.catalog_fixture()
                if change == "count":
                    catalog["method_count"] += 1
                elif change == "duplicate":
                    catalog["methods"][1]["id"] = catalog["methods"][0]["id"]
                else:
                    catalog["methods"].reverse()
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_catalog_rejects_missing_and_orphan_cards(self):
        for change in ("missing", "orphan"):
            with self.subTest(change=change):
                catalog, dimensions, files = self.catalog_fixture()
                if change == "missing":
                    del files[catalog["methods"][0]["file"]]
                else:
                    files["references/methods/L999-orphan.md"] = "# Uncatalogued fixture\n"
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_catalog_rejects_card_version_and_licence_drift(self):
        for change in ("version", "licence"):
            with self.subTest(change=change):
                catalog, dimensions, files = self.catalog_fixture()
                method = next(item for item in catalog["methods"] if item["id"] == "L05")
                if change == "version":
                    method["version"] = "0.0.0"
                else:
                    method["license"] = "MIT"
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_catalog_rejects_invalid_alternative_ids(self):
        for alternatives in (["L999999"], [], ["L01"], ["L02", "L02"]):
            with self.subTest(alternatives=alternatives):
                catalog, dimensions, files = self.catalog_fixture()
                catalog["methods"][0]["profile"]["alternative_ids"] = alternatives
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_catalog_rejects_invalid_time_ranges(self):
        for minutes in ([20, 10], [-1, 10], [0, 0], [True, 10], [5], "10 minutes"):
            with self.subTest(minutes=minutes):
                catalog, dimensions, files = self.catalog_fixture()
                catalog["methods"][0]["profile"]["time_minutes"] = minutes
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_catalog_rejects_invalid_matching_descriptors(self):
        for change in ("unknown_dimension", "duration_dimension", "unknown_label", "overlap", "empty", "reason", "sparse"):
            with self.subTest(change=change):
                catalog, dimensions, files = self.catalog_fixture()
                descriptors = catalog["methods"][0]["profile"]["dimensions"]
                dimension_id = next(iter(descriptors))
                descriptor = descriptors[dimension_id]
                if change == "unknown_dimension":
                    descriptors["not_a_dimension"] = descriptors.pop(dimension_id)
                elif change == "duration_dimension":
                    descriptors["time_runway"] = descriptors.pop(dimension_id)
                elif change == "unknown_label":
                    descriptor["fit"] = ["not_a_label"]
                elif change == "overlap":
                    label = (descriptor["fit"] + descriptor["caution"])[0]
                    descriptor["fit"], descriptor["caution"] = [label], [label]
                elif change == "empty":
                    descriptor["fit"], descriptor["caution"] = [], []
                elif change == "reason":
                    descriptor["reason"] = ""
                else:
                    catalog["methods"][0]["profile"]["dimensions"] = {dimension_id: descriptor}
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_catalog_rejects_missing_profile_fields(self):
        for field in ("jobs", "preconditions", "avoid", "output", "outcome", "guardrail", "metric_contract"):
            with self.subTest(field=field):
                catalog, dimensions, files = self.catalog_fixture()
                del catalog["methods"][0]["profile"][field]
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_dimension_definitions_need_unique_ids_and_anchors(self):
        for change in ("duplicate_dimension", "duplicate_value", "anchor"):
            with self.subTest(change=change):
                catalog, dimensions, files = self.catalog_fixture()
                definition = next(item for item in dimensions["dimensions"] if item["values"])
                if change == "duplicate_dimension":
                    dimensions["dimensions"].append(definition)
                elif change == "duplicate_value":
                    definition["values"].append(definition["values"][0])
                else:
                    del definition["values"][0]["anchor"]
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_generic_privacy_markers_without_source_specific_terms(self):
        markers = ("/" + "home/fictional/notes", "gh" + "p_" + "a" * 36, "github" + "_pat_" + "b" * 40, "-----BEGIN " + "PRIVATE KEY-----")
        for marker in markers:
            with self.subTest(marker_type=marker.split("/")[0]):
                self.assertIsNotNone(validator.DENIED.search(marker))
        self.assertIsNone(validator.DENIED.search((ROOT / "scripts/validate.py").read_text(encoding="utf-8")))

    def test_public_file_refuses_traversal_and_symlink_ancestors(self):
        public = self.base / "public"
        public.mkdir()
        (public / "safe.txt").write_text("public")
        (self.data / "fixture.txt").write_text("private fixture")
        (public / "linked").symlink_to(self.data, target_is_directory=True)
        for name in ("../private/fixture.txt", "linked/fixture.txt", "safe/../safe.txt", "/absolute.txt", "C:/drive.txt", "nested\\file.txt"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validator.public_file(public, name)
        self.assertEqual(validator.public_file(public, "safe.txt").read_text(), "public")

    def test_install_staging_and_backups_stay_outside_discovery(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        (dest / "old-version-marker.txt").write_text("old")
        real_replace = installer.os.replace
        observed = []

        def record_replace(source, target):
            source, target = Path(source), Path(target)
            observed.append((source, target))
            if source != dest:
                self.assertNotIn(dest.parent, source.parents)
            return real_replace(source, target)

        with mock.patch.object(installer.os, "replace", side_effect=record_replace):
            backup = installer.install(dest)
        self.assertNotIn(dest.parent, backup.parents)
        self.assertEqual(backup.parent, dest.parent.parent / ".leadership-toolbox-backups")
        self.assertTrue(observed)
        self.assertEqual(list(dest.parent.iterdir()), [dest])
        installer.install(dest, backup)
        self.assertTrue((dest / "old-version-marker.txt").exists())
        self.assertTrue((backup / "old-version-marker.txt").exists())

    def test_custom_backup_directory_is_used_for_staging_and_restore(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        backups = self.base / "package-backups"
        installer.install(dest, backup_dir=backups)
        (dest / "old-version-marker.txt").write_text("old")
        backup = installer.install(dest, backup_dir=backups)
        self.assertEqual(backup.parent, backups)
        installer.install(dest, backup, backup_dir=backups)
        self.assertTrue((dest / "old-version-marker.txt").is_file())
        self.assertTrue(backup.is_dir())
        self.assertFalse(list(backups.glob(".leadership-stage-*")))

    def test_backup_locations_overlapping_discovery_are_refused(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        for backups in (dest.parent, dest.parent / "backups", dest.parent.parent):
            with self.subTest(backups=backups), self.assertRaises(ValueError):
                installer.install(dest, backup_dir=backups)
        self.assertFalse(dest.exists())

    def test_failed_replacement_restores_original_skill(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        (dest / "old-version-marker.txt").write_text("keep me")
        original = (dest / "SKILL.md").read_bytes()
        real_replace = installer.os.replace

        def fail_incoming(source, target):
            if Path(source) != dest and Path(target) == dest and Path(source).parent.name.startswith(".leadership-stage-"):
                raise OSError("simulated replacement failure")
            return real_replace(source, target)

        with mock.patch.object(installer.os, "replace", side_effect=fail_incoming):
            with self.assertRaises(OSError):
                installer.install(dest)
        self.assertEqual((dest / "SKILL.md").read_bytes(), original)
        self.assertEqual((dest / "old-version-marker.txt").read_text(), "keep me")
        self.assertFalse(list(installer.backup_directory(dest).glob(".leadership-stage-*")))

    def test_failed_backup_move_leaves_original_skill(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        installer.install(dest)
        original = (dest / "SKILL.md").read_bytes()
        with mock.patch.object(installer.os, "replace", side_effect=OSError("simulated cross-device rename")):
            with self.assertRaises(OSError):
                installer.install(dest)
        self.assertEqual((dest / "SKILL.md").read_bytes(), original)

    def test_symlink_backup_directory_is_refused(self):
        dest = self.base / "host" / "skills" / "leadership-toolbox"
        target = self.base / "backup-target"
        target.mkdir()
        linked = self.base / "backup-link"
        linked.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            installer.install(dest, backup_dir=linked)
        self.assertFalse(dest.exists())

    def test_situation_schema_retains_unknown_and_evidence_guards(self):
        schema = json.loads((PACKAGE / "schemas/situation-v1.schema.json").read_text(encoding="utf-8"))
        dimensions = schema["properties"]["dimensions"]["properties"]
        for name, entry in dimensions.items():
            with self.subTest(dimension=name):
                guards = entry["allOf"]
                unknown = next(guard for guard in guards if guard["if"]["properties"]["status"]["enum"] == ["unknown", "not_applicable"])
                grounded = next(guard for guard in guards if guard["if"]["properties"]["status"]["enum"] == ["grounded", "provisional"])
                self.assertEqual(unknown["then"]["properties"]["value"], {"type": "null"})
                self.assertEqual(grounded["then"]["properties"]["value"], {"not": {"type": "null"}})
                self.assertEqual(grounded["then"]["properties"]["basis"]["minItems"], 1)
        support = dimensions["support_gaps"]["properties"]["value"]["anyOf"][1]
        self.assertIn({"if": {"contains": {"const": "none"}}, "then": {"maxItems": 1}}, support["allOf"])
        self.assertEqual(dimensions["time_runway"]["properties"]["value"]["anyOf"][1]["minProperties"], 1)

    def test_situation_schema_labels_match_dimension_definitions(self):
        schema = json.loads((PACKAGE / "schemas/situation-v1.schema.json").read_text(encoding="utf-8"))
        definitions = json.loads((PACKAGE / "references/dimensions.json").read_text(encoding="utf-8"))["dimensions"]
        properties = schema["properties"]["dimensions"]["properties"]
        self.assertEqual(set(properties), {item["id"] for item in definitions})
        for definition in definitions:
            if definition["id"] == "time_runway":
                continue
            value = properties[definition["id"]]["properties"]["value"]
            declared = value["anyOf"][1]["items"]["enum"] if definition["type"] == "multi_select" else [item for item in value["enum"] if item is not None]
            self.assertEqual(declared, [item["id"] for item in definition["values"]])

    def test_metric_contract_rejects_missing_or_empty_observations(self):
        for change in ("missing", "empty", "unknown_key"):
            with self.subTest(change=change):
                catalog, dimensions, files = self.catalog_fixture()
                contract = catalog["methods"][0]["profile"]["metric_contract"]
                if change == "missing":
                    del contract["balancing_indicator"]
                elif change == "empty":
                    contract["review_timing"] = ""
                else:
                    contract["success_probability"] = "invented"
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

if __name__ == "__main__":
    unittest.main()
