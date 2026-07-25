from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_CONTEXT_DIR = ROOT_DIR / "claudecode" / ".claude" / "skills" / "project-context"
SKILL_PATH = PROJECT_CONTEXT_DIR / "SKILL.md"
MODULE_AGENT_PATH = ROOT_DIR / "claudecode" / ".claude" / "agents" / "module-explorer.md"
FLOW_AGENT_PATH = ROOT_DIR / "claudecode" / ".claude" / "agents" / "flow-explorer.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ProjectContextCodeGraphContractTests(unittest.TestCase):
    def test_skill_uses_current_default_codegraph_contract(self) -> None:
        skill = read(SKILL_PATH)

        for required in (
            "codegraph_explore",
            "projectPath",
            "maxFiles",
            "codegraph status",
            "--json",
            "codegraph init",
            ".codegraph/codegraph.db",
        ):
            self.assertIn(required, skill)

        for obsolete in (
            "codegraph stats <",
            "codegraph languages <",
            "向量相似度",
            "--db .codegraph/codegraph.db",
            "codegraph index <dir>",
        ):
            self.assertNotIn(obsolete, skill)

    def test_skill_defines_layer_limits_and_evidence_levels(self) -> None:
        skill = read(SKILL_PATH)

        for layer in ("L0", "L1", "L2", "L3", "L4"):
            self.assertIn(layer, skill)
        for evidence in ("Verified", "Inferred", "Unknown"):
            self.assertIn(evidence, skill)
        for limit in ("10-30", "≤25", "8-20", "最多 3 层"):
            self.assertIn(limit, skill)

    def test_skill_stays_within_progressive_disclosure_budget(self) -> None:
        self.assertLessEqual(len(read(SKILL_PATH).splitlines()), 500)
        self.assertTrue((PROJECT_CONTEXT_DIR / "references" / "codegraph.md").is_file())

    def test_explorers_use_explore_instead_of_query_or_impact_as_the_default(self) -> None:
        for path in (MODULE_AGENT_PATH, FLOW_AGENT_PATH):
            agent = read(path)
            self.assertIn("codegraph explore", agent)
            self.assertIn("--path", agent)
            self.assertIn("Verified", agent)
            self.assertNotIn("codegraph query \"", agent)
            self.assertNotIn("codegraph impact \"", agent)

    def test_templates_include_evidence_and_blind_spots(self) -> None:
        for name in ("project-template.md", "module-template.md", "flow-template.md", "impact-template.md"):
            template_path = PROJECT_CONTEXT_DIR / "references" / name
            self.assertTrue(template_path.is_file(), name)
            template = read(template_path)
            self.assertIn("证据", template, name)
            self.assertIn("已知盲区", template, name)

    def test_flow_core_nodes_are_not_forced_to_equal_the_module_class_diagram(self) -> None:
        skill = read(SKILL_PATH)
        flow_agent = read(FLOW_AGENT_PATH)
        forbidden = "所有类必须是 module.md 类图的子集"

        self.assertNotIn(forbidden, skill)
        self.assertNotIn(forbidden, flow_agent)


if __name__ == "__main__":
    unittest.main()
