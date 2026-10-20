"""Static example/packaging checks, not model behavior or host-rendering tests."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/leadership-toolbox"


class VisualContractTests(unittest.TestCase):
    def setUp(self):
        self.example = (PACKAGE / "references/visual-examples.md").read_text()
        self.mermaid = re.search(r"```mermaid\n(.*?)\n```", self.example, re.S)[1]

    def test_visual_resources_are_in_reviewed_payload_and_routing(self):
        paths = (ROOT / "RELEASE_FILES.txt").read_text().splitlines()
        skill = (PACKAGE / "SKILL.md").read_text()
        for name in ("references/visual-modelling.md", "references/visual-examples.md",
                     "templates/situation-model.md"):
            with self.subTest(name=name):
                self.assertIn("skills/leadership-toolbox/" + name, paths)
                self.assertIn("(" + name + ")", skill)
                self.assertTrue((PACKAGE / name).is_file())

    def test_optional_diagram_has_only_declared_nodes_and_stable_edges(self):
        nodes = re.findall(r'^  (N\d+)\["', self.mermaid, re.M)
        self.assertEqual(len(nodes), len(set(nodes)))
        self.assertEqual(set(nodes), {"N1", "N2", "N3", "N4"})
        edges = re.findall(r"^  (N\d+) -->\|(R\d+) ([^|]+)\| (N\d+)$",
                           self.mermaid, re.M)
        self.assertEqual({(source, rid, target) for source, rid, _, target in edges},
                         {("N1", "R3", "N4"), ("N4", "R4", "N3")})
        for source, _, label, target in edges:
            self.assertIn(source, nodes)
            self.assertIn(target, nodes)
            self.assertIn("reported E2", label)
        self.assertNotRegex(self.mermaid, r"\bR[12]\b")
        self.assertNotRegex(self.mermaid, r"click|<|%%\{")

    def test_text_fallback_and_corrected_current_view_match_optional_diagram(self):
        current = self.example.split("Current relationships:", 1)[1].split("```", 1)[0]
        fallback = self.example.split("Accessible equivalent:", 1)[1].split("## 4.", 1)[0]
        for rid, source, target in (("R3", "N1", "N4"), ("R4", "N4", "N3")):
            self.assertIn(f"{rid}: {source} → {target}", current)
            self.assertIn(f"{rid}: {source} → {target}", fallback)
        self.assertNotRegex(current, r"R[12]:")
        self.assertIn("retires R1 and R2", self.example)
        self.assertIn("L01 delegation is not eligible", self.example)

    def test_example_keeps_hypotheses_and_options_out_of_current_diagram(self):
        self.assertNotRegex(self.mermaid, r"\b[HOPK]\d+\b")
        for rid in ("R5", "R6"):
            self.assertRegex(self.example, rf"{rid}: [^\n]+\[hypothesis\]")
        for rid in ("R7", "R8", "R9"):
            self.assertRegex(self.example, rf"{rid}: [^\n]+\[proposed")
        self.assertIn("O4: coordinator delegates finance's approval [excluded", self.example)


if __name__ == "__main__":
    unittest.main()
