#!/usr/bin/env python3
"""Validate project-context Markdown structure, evidence, links, and graph limits."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


ALLOWED_EVIDENCE_STATES = {"Verified", "Graph-Heuristic", "Inferred", "Unknown"}
EVIDENCE_ID_RE = re.compile(r"\b[PMFI]-\d{3}\b")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)#]+\.md)(?:#[^)]*)?\)")
MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
FLOW_NODE_RE = re.compile(r"(?<![\w])([A-Za-z][A-Za-z0-9_]*)\s*(?=\[|\(|\{)")
SEQUENCE_PARTICIPANT_RE = re.compile(r"^\s*participant\s+([A-Za-z][A-Za-z0-9_]*)", re.MULTILINE)
MERMAID_EDGE_RE = re.compile(r"(?:-+\.?-*>|=+>|-+>>)")
PLACEHOLDER_RE = re.compile(r"\{(?:project|module|flow|target|source|absolute|codegraph)[^{}\n]{0,60}\}", re.IGNORECASE)


def document_kind(relative_path: Path) -> str:
    parts = relative_path.parts
    if relative_path.as_posix() == "project.md":
        return "project"
    if "impacts" in parts:
        return "impact"
    if "flows" in parts:
        return "flow"
    if relative_path.name == "module.md":
        return "module"
    return "other"


def graph_bounds(kind: str, block: str) -> tuple[int | None, int | None]:
    if block.lstrip().lower().startswith("sequencediagram"):
        return None, {
            "project": 30,
            "module": 25,
            "flow": 20,
            "impact": 30,
        }.get(kind)
    return {
        "project": (10, 30),
        "module": (None, 25),
        "flow": (8, 20),
        "impact": (None, 30),
    }.get(kind, (None, None))


def evidence_definitions(markdown: str) -> tuple[list[str], list[tuple[str, str]]]:
    ids: list[str] = []
    states: list[tuple[str, str]] = []
    for line in markdown.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not re.fullmatch(r"[PMFI]-\d{3}", cells[0]):
            continue
        ids.append(cells[0])
        if len(cells) >= 5:
            states.append((cells[0], cells[4]))
    return ids, states


def mermaid_node_count(block: str) -> int:
    if block.lstrip().lower().startswith("sequencediagram"):
        return len(set(SEQUENCE_PARTICIPANT_RE.findall(block)))
    return len(set(FLOW_NODE_RE.findall(block)))


def expected_evidence_prefix(kind: str) -> str | None:
    return {
        "project": "P",
        "module": "M",
        "flow": "F",
        "impact": "I",
    }.get(kind)


def mermaid_edge_errors(
    block: str,
    *,
    label: str,
    graph_index: int,
    expected_prefix: str,
    definitions: set[str],
) -> list[str]:
    errors: list[str] = []
    expected_re = re.compile(rf"\b{re.escape(expected_prefix)}-\d{{3}}\b")
    for line_number, line in enumerate(block.splitlines(), start=1):
        if not MERMAID_EDGE_RE.search(line):
            continue
        ids = expected_re.findall(line)
        if not ids or not any(evidence_id in definitions for evidence_id in ids):
            errors.append(
                f"{label}: Mermaid 边缺少有效 Evidence ID "
                f"(图 #{graph_index}, 行 {line_number}, 期望 {expected_prefix}-nnn)"
            )
    return errors


def validate_document(path: Path, context_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    relative = path.relative_to(context_dir)
    label = relative.as_posix()
    kind = document_kind(relative)
    markdown = path.read_text(encoding="utf-8").lstrip("\ufeff")

    if kind in {"project", "module", "flow", "impact"}:
        if "证据" not in markdown:
            errors.append(f"{label}: 缺少证据章节")
        if "已知盲区" not in markdown:
            errors.append(f"{label}: 缺少已知盲区章节")

    for target in MARKDOWN_LINK_RE.findall(markdown):
        resolved = (path.parent / target).resolve()
        if not resolved.is_file():
            errors.append(f"{label}: 链接目标不存在: {target}")

    placeholders = sorted(set(PLACEHOLDER_RE.findall(markdown)))
    for placeholder in placeholders:
        errors.append(f"{label}: 未替换模板占位符: {placeholder}")

    definitions, states = evidence_definitions(markdown)
    counts = Counter(definitions)
    for evidence_id, count in sorted(counts.items()):
        if count > 1:
            errors.append(f"{label}: Evidence ID 重复定义: {evidence_id}")

    references = set(EVIDENCE_ID_RE.findall(markdown))
    undefined = sorted(references - set(definitions))
    for evidence_id in undefined:
        errors.append(f"{label}: 未定义 Evidence ID: {evidence_id}")

    for evidence_id, state in states:
        if state not in ALLOWED_EVIDENCE_STATES:
            errors.append(f"{label}: 非法证据状态: {state} ({evidence_id})")

    blocks = MERMAID_BLOCK_RE.findall(markdown)
    if blocks and "图例" not in markdown:
        errors.append(f"{label}: Mermaid 图缺少图例")

    prefix = expected_evidence_prefix(kind)
    if prefix is not None:
        for evidence_id in definitions:
            if not evidence_id.startswith(prefix + "-"):
                errors.append(
                    f"{label}: Evidence ID 前缀错误: {evidence_id}，期望 {prefix}-nnn"
                )

    for index, block in enumerate(blocks, start=1):
        minimum, maximum = graph_bounds(kind, block)
        count = mermaid_node_count(block)
        if minimum is not None and count < minimum:
            errors.append(
                f"{label}: Mermaid 节点数 {count} 低于下限 {minimum} (图 #{index})"
            )
        if maximum is not None and count > maximum:
            errors.append(
                f"{label}: Mermaid 节点数 {count} 超过上限 {maximum} (图 #{index})"
            )
        if prefix is not None:
            errors.extend(
                mermaid_edge_errors(
                    block,
                    label=label,
                    graph_index=index,
                    expected_prefix=prefix,
                    definitions=set(definitions),
                )
            )

    if kind == "other":
        warnings.append(f"{label}: 未识别文档类型，跳过层级专属检查")
    return errors, warnings


def validate_context(context_dir: Path) -> dict:
    context_dir = context_dir.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not context_dir.is_dir():
        return {
            "contextPath": str(context_dir),
            "documents": 0,
            "errors": [f"目录不存在: {context_dir}"],
            "warnings": [],
        }

    project_path = context_dir / "project.md"
    if not project_path.is_file():
        errors.append("缺少 project.md")

    documents = sorted(context_dir.rglob("*.md"))
    for path in documents:
        document_errors, document_warnings = validate_document(path, context_dir)
        errors.extend(document_errors)
        warnings.extend(document_warnings)

    return {
        "contextPath": str(context_dir),
        "documents": len(documents),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 project-context 知识地图")
    parser.add_argument("context_dir", type=Path, help="EdanSpec/context 目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    report = validate_context(args.context_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Documents: {report['documents']}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
