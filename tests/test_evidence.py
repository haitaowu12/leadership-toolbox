"""Structural research-library checks; these do not verify source findings."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/leadership-toolbox"
spec = importlib.util.spec_from_file_location("evidence_validator", ROOT / "scripts/validate.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class EvidenceLibraryTests(unittest.TestCase):
    def fixture(self):
        library = json.loads((PACKAGE / "references/sources.json").read_text())
        mapping = json.loads((PACKAGE / "references/evidence-map.json").read_text())
        catalog = json.loads((PACKAGE / "references/catalog.json").read_text())
        files = {path.relative_to(PACKAGE).as_posix(): path.read_text() for path in PACKAGE.rglob("*.md")}
        return library, mapping, catalog, files

    def test_complete_library_and_method_links(self):
        data = self.fixture()
        self.assertEqual(validator.validate_evidence(*data), [])
        self.assertEqual({row["method_id"] for row in data[1]["methods"]}, {row["id"] for row in data[2]["methods"]})

    def test_rejects_duplicate_or_missing_method_mapping(self):
        for change in ("duplicate", "missing", "invalid"):
            with self.subTest(change=change):
                library, mapping, catalog, files = self.fixture()
                if change == "duplicate":
                    mapping["methods"].append(copy.deepcopy(mapping["methods"][0]))
                elif change == "missing":
                    mapping["methods"].pop()
                else:
                    mapping["methods"][0]["method_id"] = []
                self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_duplicate_source_or_unknown_reference(self):
        for change in ("duplicate", "unknown", "wrong_role"):
            with self.subTest(change=change):
                library, mapping, catalog, files = self.fixture()
                if change == "duplicate":
                    library["sources"].append(copy.deepcopy(library["sources"][0]))
                elif change == "unknown":
                    mapping["methods"][0]["provenance_ids"] = ["P999999"]
                else:
                    mapping["methods"][0]["book_ids"] = mapping["methods"][0]["provenance_ids"]
                self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_missing_scope_limits_and_rights(self):
        for field in ("inspected_scope", "claim_limit", "reuse", "access", "topics", "methods"):
            with self.subTest(field=field):
                library, mapping, catalog, files = self.fixture()
                del library["sources"][0][field]
                self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_metadata_as_empirical_support(self):
        library, mapping, catalog, files = self.fixture()
        sid = next(row["research_ids"][0] for row in mapping["methods"] if row["research_ids"])
        next(source for source in library["sources"] if source["id"] == sid)["access"] = "metadata_only"
        self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_invalid_urls_doi_year_and_access(self):
        for field, value in (("url", "http://example.org"), ("doi", "not-a-doi"), ("year", True), ("access", "entire_book_assumed")):
            with self.subTest(field=field):
                library, mapping, catalog, files = self.fixture()
                library["sources"][0][field] = value
                self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_missing_source_note_or_stable_heading(self):
        for change in ("file", "heading"):
            with self.subTest(change=change):
                library, mapping, catalog, files = self.fixture()
                source = library["sources"][0]
                if change == "file":
                    source["notes_file"] = "references/missing.md"
                else:
                    files[source["notes_file"]] = files[source["notes_file"]].replace("## " + source["id"], "## REMOVED")
                self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_missing_card_link_knowledge_route_and_open_question(self):
        for change in ("card", "knowledge", "question", "readable_map"):
            with self.subTest(change=change):
                library, mapping, catalog, files = self.fixture()
                entry = mapping["methods"][0]
                if change == "card":
                    method = next(item for item in catalog["methods"] if item["id"] == entry["method_id"])
                    files[method["file"]] = files[method["file"]].replace("(../evidence-map.md#" + entry["method_id"].lower() + ")", "(../evidence-map.md)")
                elif change == "knowledge":
                    entry["knowledge_file"] = "references/missing.md"
                elif change == "question":
                    entry["open_question"] = ""
                else:
                    files["references/evidence-map.md"] = files["references/evidence-map.md"].replace("## " + entry["method_id"], "## REMOVED")
                self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_asymmetric_method_source_mapping(self):
        library, mapping, catalog, files = self.fixture()
        entry = mapping["methods"][0]
        source = next(item for item in library["sources"] if item["id"] == entry["provenance_ids"][0])
        source["methods"] = [mid for mid in source["methods"] if mid != entry["method_id"]]
        self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_catalog_source_and_route_drift(self):
        for field, value in (("source_ids", ["E99999"]), ("knowledge_file", "missing.md"), ("evidence_map", "references/evidence-map.md#wrong")):
            with self.subTest(field=field):
                library, mapping, catalog, files = self.fixture()
                catalog["methods"][0][field] = value
                self.assertTrue(validator.validate_evidence(library, mapping, catalog, files))

    def test_rejects_practical_guide_url_drift(self):
        for value in (None, "https://example.org/wiki/leadership", "https://github.com/haitaowu12/leadership-toolbox/wiki/GROW"):
            with self.subTest(value=value):
                _, _, catalog, files = self.fixture()
                dimensions = json.loads((PACKAGE / "references/dimensions.json").read_text())
                catalog["methods"][0]["guide_url"] = value
                self.assertTrue(validator.validate_catalog(catalog, dimensions, files))

    def test_practical_link_is_separate_from_original_evidence(self):
        _, _, catalog, files = self.fixture()
        for method in catalog["methods"]:
            with self.subTest(method=method["id"]):
                self.assertNotEqual(method["guide_url"], method["source"])
                self.assertIn(method["source"], files[method["file"]])
                self.assertTrue(method["source_ids"])
                if method["id"] in ("L05", "L27"):
                    self.assertEqual(method["license"], "CC-BY-SA-4.0")
                    self.assertIn("creativecommons.org/licenses/by-sa/4.0", files[method["file"]])

    def test_malformed_top_level_is_reported(self):
        library, mapping, catalog, files = self.fixture()
        self.assertTrue(validator.validate_evidence([], mapping, catalog, files))
        self.assertTrue(validator.validate_evidence(library, {}, catalog, files))


if __name__ == "__main__":
    unittest.main()
