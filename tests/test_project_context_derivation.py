from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT_DIR / "scripts" / "derive_project_context.py"
SPEC = importlib.util.spec_from_file_location("derive_project_context", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {BUILDER_PATH}")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class ProjectContextDerivationTests(unittest.TestCase):
    def test_adapts_skill_name_and_platform_paths(self) -> None:
        source = """---
name: edanspec:project-context
description: demo
---
Read .claude/skills/project-context/references/codegraph.md.
"""

        adapted = builder.adapt_skill_text(
            source, target_prefix=".opencode", target_name="project-context"
        )

        self.assertIn("name: project-context", adapted)
        self.assertIn(".opencode/skills/project-context", adapted)
        self.assertNotIn(".claude/", adapted)
        self.assertNotIn("edanspec:", adapted)

    def test_builds_open_and_kilo_archives_from_claude_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = builder.build_all(
                ROOT_DIR, Path(temp_dir) / "dist", date_tag="20260724"
            )

            for platform, archive in output.items():
                extracted = Path(temp_dir) / f"extract-{platform}"
                builder.extract_archive(archive, extracted)
                builder.verify_manifest(extracted)
                prefix = ".opencode" if platform == "opencode" else ".kilo"
                skill = extracted / prefix / "skills" / "project-context"
                skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertEqual(
                    "project-context", builder.read_frontmatter_name(skill / "SKILL.md")
                )
                self.assertIn("codegraph_explore", skill_text)
                self.assertIn("Graph-Heuristic", skill_text)
                self.assertTrue((skill / "references" / "codegraph.md").is_file())
                self.assertTrue((skill / "references" / "evidence-contract.md").is_file())
                self.assertTrue((skill / "references" / "review-checklist.md").is_file())
                self.assertTrue((skill / "references" / "impact-template.md").is_file())
                self.assertTrue((skill / "scripts" / "validate_context.py").is_file())
                self.assertTrue(
                    (extracted / prefix / "agents" / "module-explorer.md").is_file()
                )
                self.assertTrue(
                    (extracted / prefix / "agents" / "flow-explorer.md").is_file()
                )

                for path in extracted.rglob("*"):
                    if path.is_file() and path.suffix.lower() in {".md", ".py", ".txt"}:
                        text = path.read_text(encoding="utf-8")
                        self.assertNotIn(".claude/", text, str(path))

    def test_derived_skill_contains_every_canonical_skill_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = builder.build_all(
                ROOT_DIR, Path(temp_dir) / "dist", date_tag="20260724"
            )
            extracted = Path(temp_dir) / "extract"
            builder.extract_archive(output["opencode"], extracted)

            source = (
                ROOT_DIR
                / "skills"
                / "project-context"
            )
            derived = extracted / ".opencode" / "skills" / "project-context"
            source_files = {
                path.relative_to(source).as_posix()
                for path in source.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            }
            derived_files = {
                path.relative_to(derived).as_posix()
                for path in derived.rglob("*")
                if path.is_file()
            }

            self.assertEqual(source_files, derived_files)


if __name__ == "__main__":
    unittest.main()
