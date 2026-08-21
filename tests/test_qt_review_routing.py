from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, name: str):
    path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


classifier = load_module(
    "skills/edanspec-code-review/scripts/classify_qt_scope.py",
    "classify_qt_scope",
)
aggregator = load_module(
    "skills/edanspec-code-review/scripts/aggregate_reports.py",
    "aggregate_reports",
)


class QtReviewRoutingTests(unittest.TestCase):
    def test_bundled_qt_skills_have_authoritative_assets(self) -> None:
        expected = {
            "qt-cpp-review": (
                "references/qt-deprecated-classes.md",
                "references/qt-framework-checklist.md",
                "references/qt-review-checklist.md",
                "references/lint-scripts/qt_review_lint.py",
            ),
            "qt-qml-review": (
                "references/qt-qml-review-checklist.md",
                "references/lint-scripts/qt_qml_lint.py",
            ),
        }
        for skill_name, references in expected.items():
            skill = ROOT_DIR / "skills" / skill_name
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "README.md").is_file())
            self.assertIn("BSD 3-Clause License", (skill / "LICENSE.txt").read_text(encoding="utf-8"))
            for reference in references:
                self.assertTrue((skill / reference).is_file(), reference)

    def test_bundled_linters_execute_on_minimal_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cpp = root / "main.cpp"
            qml = root / "Main.qml"
            cpp.write_text("#include <QObject>\nclass Main : public QObject { Q_OBJECT };\n", encoding="utf-8")
            qml.write_text("import QtQuick\nItem {}\n", encoding="utf-8")
            for skill_name, script_name, source in (
                ("qt-cpp-review", "qt_review_lint.py", cpp),
                ("qt-qml-review", "qt_qml_lint.py", qml),
            ):
                script = ROOT_DIR / "skills" / skill_name / "references" / "lint-scripts" / script_name
                result = subprocess.run(
                    [sys.executable, str(script), str(source)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertIn(result.returncode, (0, 1), result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_routes_qml_qmltypes_and_only_explicit_qt_cpp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            java = root / "Main.java"
            plain_cpp = root / "math.cpp"
            qt_cpp = root / "model.cpp"
            qml = root / "Main.qml"
            qmltypes = root / "module.qmltypes"
            java.write_text("class Main {}\n", encoding="utf-8")
            plain_cpp.write_text("int add(int a, int b) { return a + b; }\n", encoding="utf-8")
            qt_cpp.write_text(
                "#include <QObject>\nclass Model : public QObject { Q_OBJECT };\n",
                encoding="utf-8",
            )
            qml.write_text("import QtQuick\nItem {}\n", encoding="utf-8")
            qmltypes.write_text("Module { Component { name: \"Model\" } }\n", encoding="utf-8")

            result = classifier.classify_scope(
                [java, plain_cpp, qt_cpp, qml, qmltypes]
            )

            self.assertEqual(result["allFiles"], [str(path) for path in [java, plain_cpp, qt_cpp, qml, qmltypes]])
            self.assertEqual(result["qtCppFiles"], [str(qt_cpp)])
            self.assertEqual(result["qmlFiles"], [str(qml), str(qmltypes)])
            self.assertIn("Qt include", " ".join(result["evidence"][str(qt_cpp)]))

    def test_routes_cpp_referenced_by_qt_build_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "controller.cpp"
            build = root / "CMakeLists.txt"
            source.write_text("int controller() { return 0; }\n", encoding="utf-8")
            build.write_text(
                "find_package(Qt6 REQUIRED COMPONENTS Quick)\n"
                "qt_add_executable(app controller.cpp)\n",
                encoding="utf-8",
            )

            result = classifier.classify_scope([source, build])

            self.assertEqual(result["qtCppFiles"], [str(source)])
            self.assertTrue(any("Qt build declaration" in item for item in result["evidence"][str(source)]))

    def test_deduplicates_same_location_and_semantics_but_preserves_sources(self) -> None:
        findings = [
            {
                "file": "src/model.cpp",
                "line": 42,
                "semantic": "missing dataChanged roles",
                "source": "generic review",
            },
            {
                "file": "src/model.cpp",
                "line": 42,
                "finding": "Missing dataChanged roles",
                "source": "qt-cpp-review",
                "id": "D-001",
                "rule": "MDL",
                "confidence": 92,
            },
        ]

        merged = aggregator.deduplicate_findings(findings)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["sources"], ["generic review", "qt-cpp-review"])
        self.assertEqual(merged[0]["qtReferences"], [{"id": "D-001", "rule": "MDL", "confidence": 92}])

    def test_conclusion_matrix_keeps_incomplete_separate_from_approve(self) -> None:
        self.assertEqual(
            aggregator.compute_conclusion("complete", "not-applicable", "not-applicable", False),
            "APPROVE",
        )
        self.assertEqual(
            aggregator.compute_conclusion("complete", "complete", "complete", False),
            "APPROVE",
        )
        self.assertEqual(
            aggregator.compute_conclusion("complete", "partial", "not-applicable", False),
            "INCOMPLETE",
        )
        self.assertEqual(
            aggregator.compute_conclusion("complete", "failed", "complete", True),
            "REQUEST_CHANGES",
        )


if __name__ == "__main__":
    unittest.main()
