from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REGISTRY = ROOT_DIR / "MedSpec" / "review-stack.yaml"
GENERIC_SKILL = ROOT_DIR / "skills" / "code-review" / "SKILL.md"
GENERIC_REVIEWER = ROOT_DIR / "agents" / "code-reviewer.md"


def stack_block(text: str, stack_id: str) -> str:
    match = re.search(
        rf"(?ms)^\s*- id: {re.escape(stack_id)}\s*$"
        rf"(?P<body>.*?)(?=^\s*- id: |\Z)",
        text,
    )
    if match is None:
        raise AssertionError(f"missing stack: {stack_id}")
    return match.group("body")


class ReviewStackContractTests(unittest.TestCase):
    def test_registry_defines_qt_cpp_and_qml_without_embedding_checklists(self) -> None:
        text = REGISTRY.read_text(encoding="utf-8")
        self.assertIn("version: 1", text)
        cpp = stack_block(text, "qt-cpp")
        qml = stack_block(text, "qt-qml")

        self.assertIn("enabled: true", cpp)
        self.assertIn("skill: qt-cpp-review", cpp)
        self.assertIn("extensions:", cpp)
        self.assertIn("content_any:", cpp)
        self.assertIn("build_any:", cpp)
        self.assertIn("guidance:", cpp)
        self.assertIn("skill: qt-qml-review", qml)
        self.assertIn("extensions:", qml)
        self.assertIn("guidance:", qml)
        self.assertLess(len(text), 5000)
        self.assertNotIn("QAbstractItemModel contract", text)

    def test_generic_review_is_stack_neutral(self) -> None:
        skill = GENERIC_SKILL.read_text(encoding="utf-8")
        reviewer = GENERIC_REVIEWER.read_text(encoding="utf-8")

        for required in (
            "MedSpec/review-stack.yaml",
            ".meddev/review-stack.yaml",
            "allFiles",
            "matchedFiles",
            "guidance",
            "specialists",
            "genericReview",
            "INCOMPLETE",
        ):
            self.assertIn(required, skill)
        self.assertNotIn("qtCppFiles", skill)
        self.assertNotIn("qmlFiles", skill)
        self.assertNotIn("qtCppReview", skill)
        self.assertNotIn("qmlReview", skill)
        self.assertIn("specialist", reviewer.lower())

    def test_specialist_skills_own_their_workflow_and_notes(self) -> None:
        expected = {
            "qt-cpp-review": (
                "Qt C++",
                "framework",
                "lessons-learned.md",
                "review-workflow.md",
            ),
            "qt-qml-review": (
                "QML",
                "qmllint",
                "lessons-learned.md",
                "review-workflow.md",
            ),
        }
        for name, markers in expected.items():
            skill_dir = ROOT_DIR / "skills" / name
            skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            for marker in markers:
                self.assertIn(marker, skill, name)
            self.assertTrue((skill_dir / "references" / "review-workflow.md").is_file())
            self.assertTrue((skill_dir / "references" / "lessons-learned.md").is_file())

    def test_project_guidance_paths_are_explicit_and_local(self) -> None:
        registry = REGISTRY.read_text(encoding="utf-8")
        for relative in (
            "MedSpec/review-notes/qt-cpp.md",
            "MedSpec/review-notes/qt-qml.md",
        ):
            self.assertIn(relative, registry)
            self.assertTrue((ROOT_DIR / relative).is_file())

    def test_qt_skills_are_invoked_from_generic_code_review(self) -> None:
        cpp = (ROOT_DIR / "skills" / "qt-cpp-review" / "SKILL.md").read_text(encoding="utf-8")
        qml = (ROOT_DIR / "skills" / "qt-qml-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("meddev:code-review", cpp)
        self.assertIn("meddev:code-review", qml)
        self.assertNotIn("edanspec:", cpp)
        self.assertNotIn("edanspec:", qml)
        self.assertNotIn("EdanSpec", cpp)
        self.assertNotIn("EdanSpec", qml)


if __name__ == "__main__":
    unittest.main()
