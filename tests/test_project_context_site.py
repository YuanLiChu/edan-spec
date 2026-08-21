from __future__ import annotations

import json
import importlib.util
import tempfile
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BUILD_SITE_PATH = ROOT_DIR / "skills" / "project-context" / "scripts" / "build_site.py"
SPEC = importlib.util.spec_from_file_location("build_site", BUILD_SITE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {BUILD_SITE_PATH}")
build_site = importlib.util.module_from_spec(SPEC)
sys.modules["build_site"] = build_site
SPEC.loader.exec_module(build_site)


class ProjectContextSiteTests(unittest.TestCase):
    def test_builds_single_file_site_with_project_module_and_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context_dir = Path(temp_dir) / "context"
            output_dir = Path(temp_dir) / "site"
            write_context_fixture(context_dir)

            result = build_site.build_site(context_dir, output_dir)

            index_html = output_dir / "index.html"
            self.assertEqual(index_html.resolve(), result.resolve())
            html = index_html.read_text(encoding="utf-8")
            payload = extract_payload(html)

            self.assertEqual("Demo Platform", payload["projectTitle"])
            self.assertEqual(["project", "module", "flow"], [doc["kind"] for doc in payload["documents"]])
            self.assertIn("Patient Admission", html)
            self.assertIn('href="#flow:admission:patient-admission"', payload["documents"][1]["html"])
            self.assertIn("admission flow", payload["documents"][2]["searchText"])
            self.assertIn("Hybrid explorer", html)

    def test_builds_when_module_has_no_flows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context_dir = Path(temp_dir) / "context"
            output_dir = Path(temp_dir) / "site"
            (context_dir / "modules" / "shared-kernel").mkdir(parents=True)
            (context_dir / "project.md").write_text("# Utility Project\n", encoding="utf-8")
            (context_dir / "modules" / "shared-kernel" / "module.md").write_text(
                "# Module: Shared Kernel\n\nNo standalone flows.\n",
                encoding="utf-8",
            )

            build_site.build_site(context_dir, output_dir)

            payload = extract_payload((output_dir / "index.html").read_text(encoding="utf-8"))
            self.assertEqual(["project", "module"], [doc["kind"] for doc in payload["documents"]])
            module_doc = payload["documents"][1]
            self.assertEqual([], module_doc["children"])
            self.assertEqual("shared-kernel", module_doc["module"])

    def test_handles_utf8_bom_markdown_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context_dir = Path(temp_dir) / "context"
            output_dir = Path(temp_dir) / "site"
            context_dir.mkdir()
            (context_dir / "project.md").write_text(
                "\ufeff# BOM Project\n\nWindows-authored Markdown.\n",
                encoding="utf-8",
            )

            build_site.build_site(context_dir, output_dir)

            payload = extract_payload((output_dir / "index.html").read_text(encoding="utf-8"))
            self.assertEqual("BOM Project", payload["projectTitle"])
            self.assertIn("<h1", payload["documents"][0]["html"])

    def test_unreadable_markdown_becomes_error_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context_dir = Path(temp_dir) / "context"
            output_dir = Path(temp_dir) / "site"
            module_dir = context_dir / "modules" / "broken"
            module_dir.mkdir(parents=True)
            (context_dir / "project.md").write_text("# Broken Project\n", encoding="utf-8")
            (module_dir / "module.md").write_bytes(b"\xff\xfe\x00\x00")

            build_site.build_site(context_dir, output_dir)

            payload = extract_payload((output_dir / "index.html").read_text(encoding="utf-8"))
            self.assertEqual(["project", "module"], [doc["kind"] for doc in payload["documents"]])
            self.assertIn("Unable to read Markdown", payload["documents"][1]["html"])


def write_context_fixture(context_dir: Path) -> None:
    flow_dir = context_dir / "modules" / "admission" / "flows"
    flow_dir.mkdir(parents=True)
    (context_dir / "project.md").write_text(
        "# Demo Platform\n\n## Module Index\n\n- [Admission](modules/admission/module.md)\n",
        encoding="utf-8",
    )
    (context_dir / "modules" / "admission" / "module.md").write_text(
        "# Module: Admission\n\nHandles patient admission.\n\n"
        "## Business Flows\n\n"
        "| Flow | Design |\n|------|--------|\n| Patient Admission | [flow](flows/patient-admission.md) |\n",
        encoding="utf-8",
    )
    (flow_dir / "patient-admission.md").write_text(
        "# Patient Admission\n\nThis admission flow registers a patient.\n\n"
        "```mermaid\nsequenceDiagram\nA->>B: register\n```\n",
        encoding="utf-8",
    )


def extract_payload(html: str) -> dict:
    marker = '<script id="context-data" type="application/json">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    return json.loads(html[start:end])


if __name__ == "__main__":
    unittest.main()
