from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT_DIR = Path(__file__).resolve().parents[1]
SCAN_PROJECT_PATH = (
    ROOT_DIR
    / "claudecode"
    / ".claude"
    / "skills"
    / "project-context"
    / "scripts"
    / "scan-project.py"
)
SPEC = importlib.util.spec_from_file_location("scan_project", SCAN_PROJECT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCAN_PROJECT_PATH}")
scan_project = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scan_project)


class ScanProjectTests(unittest.TestCase):
    def test_detects_default_codegraph_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / ".codegraph" / "codegraph.db"
            index_path.parent.mkdir()
            index_path.write_bytes(b"sqlite")

            self.assertTrue(scan_project.has_codegraph_index(root))
            self.assertEqual(index_path, scan_project.codegraph_index_path(root))

    def test_respects_codegraph_dir_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index_path = root / ".codegraph-internal" / "codegraph.db"
            index_path.parent.mkdir()
            index_path.write_bytes(b"sqlite")

            with mock.patch.dict(os.environ, {"CODEGRAPH_DIR": ".codegraph-internal"}):
                self.assertTrue(scan_project.has_codegraph_index(root))
                self.assertEqual(index_path, scan_project.codegraph_index_path(root))

    def test_fast_scan_counts_files_without_reading_line_totals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "main.cpp").write_text("int main() {\n  return 0;\n}\n", encoding="utf-8")
            (root / "src" / "helper.h").write_text("#pragma once\n", encoding="utf-8")

            result = scan_project.scan(root, count_lines=False)

            self.assertEqual("fast", result["scanMode"])
            self.assertEqual(2, result["sourceFileCount"])
            self.assertEqual(
                [
                    {"lang": "c", "files": 1, "lines": None},
                    {"lang": "cpp", "files": 1, "lines": None},
                ],
                result["languages"],
            )

    def test_full_scan_preserves_language_line_totals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('a')\nprint('b')\n", encoding="utf-8")

            result = scan_project.scan(root, count_lines=True)

            self.assertEqual("full", result["scanMode"])
            self.assertEqual([{"lang": "python", "files": 1, "lines": 2}], result["languages"])

    def test_project_under_parent_named_build_is_not_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "build" / "project"
            (root / "src").mkdir(parents=True)
            (root / "src" / "main.cpp").write_text(
                "int main() { return 0; }\n", encoding="utf-8"
            )

            result = scan_project.scan(root, count_lines=False)

            self.assertEqual(1, result["sourceFileCount"])

    def test_walk_prunes_ignored_subtrees_before_descent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            visited: list[str] = []

            def fake_walk(_root: Path):
                dirs = ["src", "node_modules"]
                yield str(root), dirs, []
                for directory in dirs:
                    visited.append(directory)
                    yield str(root / directory), [], []

            with mock.patch.object(scan_project.os, "walk", fake_walk):
                scan_project.scan(root, count_lines=False)

            self.assertEqual(["src"], visited)


if __name__ == "__main__":
    unittest.main()
