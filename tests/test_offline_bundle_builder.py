from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT_DIR / "scripts" / "build_offline_bundles.py"
SPEC = importlib.util.spec_from_file_location("build_offline_bundles", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {BUILDER_PATH}")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class OfflineBundleBuilderTests(unittest.TestCase):
    def test_cli_can_run_directly_from_repo_root(self) -> None:
        result = subprocess.run(
            [sys.executable, str(BUILDER_PATH), "--help"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--output-dir", result.stdout)

    def test_builds_three_verified_platform_archives(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = builder.build_all(
                ROOT_DIR, Path(temp_dir) / "dist", date_tag="20260724"
            )

            self.assertEqual(
                {"claudecode", "opencode", "kilocode"}, set(output.archives)
            )
            self.assertTrue(output.sha256sums.is_file())

            prefixes = {
                "claudecode": ".claude",
                "opencode": ".opencode",
                "kilocode": ".kilo",
            }
            for platform, archive in output.archives.items():
                extracted = Path(temp_dir) / f"extract-{platform}"
                builder.extract_archive(archive, extracted)
                builder.verify_manifest(extracted)
                skill = (
                    extracted
                    / prefixes[platform]
                    / "skills"
                    / ("project-context" if platform != "claudecode" else "project-context")
                    / "SKILL.md"
                )
                self.assertIn(
                    "codegraph_explore", skill.read_text(encoding="utf-8")
                )
                for qt_skill_name, lint_script in (
                    ("qt-cpp-review", "references/lint-scripts/qt_review_lint.py"),
                    ("qt-qml-review", "references/lint-scripts/qt_qml_lint.py"),
                ):
                    qt_skill = (
                        extracted
                        / prefixes[platform]
                        / "skills"
                        / qt_skill_name
                    )
                    self.assertEqual(
                        qt_skill_name,
                        builder.common.read_frontmatter_name(qt_skill / "SKILL.md"),
                    )
                    self.assertTrue((qt_skill / "LICENSE.txt").is_file())
                    self.assertTrue((qt_skill / lint_script).is_file())
                install = (extracted / "INSTALL.md").read_text(encoding="utf-8")
                self.assertIn("\u5185\u7f51\u5b89\u88c5", install)
                self.assertIn("SHA-256", install)

    def test_open_and_kilo_packages_do_not_leak_claude_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = builder.build_all(
                ROOT_DIR, Path(temp_dir) / "dist", date_tag="20260724"
            )
            for platform in ("opencode", "kilocode"):
                extracted = Path(temp_dir) / f"extract-{platform}"
                builder.extract_archive(output.archives[platform], extracted)
                for path in extracted.rglob("*"):
                    if path.is_file() and path.suffix.lower() in {
                        ".md",
                        ".py",
                        ".txt",
                        ".json",
                    }:
                        self.assertNotIn(
                            ".claude/",
                            path.read_text(encoding="utf-8"),
                            str(path),
                        )


if __name__ == "__main__":
    unittest.main()
