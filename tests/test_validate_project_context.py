from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT_DIR
    / "claudecode"
    / ".claude"
    / "skills"
    / "project-context"
    / "scripts"
    / "validate_context.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_context", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALID_PROJECT = """# Project: Demo

## L0 系统地图

```mermaid
flowchart LR
    A[入口] -->|调用 P-001| B[核心]
    B -->|调用 P-001| C[构件 C]
    C -->|调用 P-001| D[构件 D]
    D -->|调用 P-001| E[构件 E]
    E -->|调用 P-001| F[构件 F]
    F -->|调用 P-001| G[构件 G]
    G -->|调用 P-001| H[构件 H]
    H -->|调用 P-001| I[构件 I]
    I -->|调用 P-001| J[构件 J]
```

### 图例

- 实线：Verified

## 模块索引

| 模块 | 文档 |
|------|------|
| core | [module.md](modules/core/module.md) |

## 证据

| Evidence ID | 事实/关系 | 来源 | 定位 | 证据状态 | 置信度 | 备注 |
|-------------|-----------|------|------|----------|--------|------|
| P-001 | A 调用 B | CodeGraph | `a.cpp:1` | Verified | High | caller→callee |

## 已知盲区

| 盲区 | 影响 | 状态 | 补证 |
|------|------|------|------|
| QML | UI 入口 | Unknown | 定向读取 |
"""

VALID_MODULE = """# Module: Core

## L1 核心构件图

```mermaid
flowchart LR
    A[入口] -->|调用 M-001| B[编排]
```

### 图例

- 实线：Verified

## 证据

| Evidence ID | 事实/关系 | 来源 | 定位 | 证据状态 | 置信度 | 备注 |
|-------------|-----------|------|------|----------|--------|------|
| M-001 | A 调用 B | Source | `core.cpp:2` | Verified | High | caller→callee |

## 已知盲区

None.
"""


class ValidateProjectContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = load_validator()

    def test_valid_context_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = Path(temp_dir)
            module_dir = context / "modules" / "core"
            module_dir.mkdir(parents=True)
            (context / "project.md").write_text(VALID_PROJECT, encoding="utf-8")
            (module_dir / "module.md").write_text(VALID_MODULE, encoding="utf-8")

            report = self.validator.validate_context(context)

            self.assertEqual([], report["errors"])
            self.assertEqual(2, report["documents"])

    def test_missing_link_target_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = Path(temp_dir)
            context.mkdir(exist_ok=True)
            (context / "project.md").write_text(VALID_PROJECT, encoding="utf-8")

            report = self.validator.validate_context(context)

            self.assertTrue(any("链接目标不存在" in error for error in report["errors"]))

    def test_undefined_evidence_reference_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = Path(temp_dir)
            context.mkdir(exist_ok=True)
            broken = VALID_PROJECT.replace("P-001 | A 调用 B", "P-002 | A 调用 B")
            (context / "project.md").write_text(broken, encoding="utf-8")

            report = self.validator.validate_context(context)

            self.assertTrue(any("未定义 Evidence ID: P-001" in error for error in report["errors"]))

    def test_disallowed_evidence_state_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = Path(temp_dir)
            context.mkdir(exist_ok=True)
            broken = VALID_PROJECT.replace("| Verified | High |", "| Certain | High |")
            (context / "project.md").write_text(broken, encoding="utf-8")

            report = self.validator.validate_context(context)

            self.assertTrue(any("非法证据状态: Certain" in error for error in report["errors"]))

    def test_project_mermaid_over_30_nodes_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = Path(temp_dir)
            context.mkdir(exist_ok=True)
            nodes = "\n".join(f"    N{i}[Node {i}]" for i in range(31))
            oversized = VALID_PROJECT.replace(
                "    A[入口] -->|调用 P-001| B[核心]",
                nodes + "\n    N0 -->|调用 P-001| N1",
            ).replace("[module.md](modules/core/module.md)", "`not-generated`")
            (context / "project.md").write_text(oversized, encoding="utf-8")

            report = self.validator.validate_context(context)

            self.assertTrue(
                any(
                    "Mermaid 节点数" in error and "超过上限 30" in error
                    for error in report["errors"]
                )
            )

    def test_project_mermaid_under_10_nodes_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = Path(temp_dir)
            context.mkdir(exist_ok=True)
            first_edge = "    A[入口] -->|调用 P-001| B[核心]"
            graph_lines = VALID_PROJECT.splitlines()
            kept: list[str] = []
            in_graph = False
            for line in graph_lines:
                if line == "```mermaid":
                    in_graph = True
                if not in_graph or line in {"```mermaid", "flowchart LR", first_edge, "```"}:
                    kept.append(line)
                if in_graph and line == "```":
                    in_graph = False
            undersized = "\n".join(kept).replace(
                "[module.md](modules/core/module.md)", "`not-generated`"
            )
            (context / "project.md").write_text(undersized, encoding="utf-8")

            report = self.validator.validate_context(context)

            self.assertTrue(any("Mermaid 节点数 2 低于下限 10" in error for error in report["errors"]))

    def test_mermaid_edge_without_evidence_id_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = Path(temp_dir)
            context.mkdir(exist_ok=True)
            broken = VALID_PROJECT.replace(
                "A[入口] -->|调用 P-001| B[核心]",
                "A[入口] -->|调用| B[核心]",
            ).replace("[module.md](modules/core/module.md)", "`not-generated`")
            (context / "project.md").write_text(broken, encoding="utf-8")

            report = self.validator.validate_context(context)

            self.assertTrue(any("Mermaid 边缺少有效 Evidence ID" in error for error in report["errors"]))

    def test_sequence_messages_are_not_counted_as_nodes(self) -> None:
        block = """sequenceDiagram
    participant A as Caller
    participant B as Service
    A->>B: method_one(value) (F-001)
    B-->>A: method_two(result) (F-002)
"""
        self.assertEqual(2, self.validator.mermaid_node_count(block))


if __name__ == "__main__":
    unittest.main()
