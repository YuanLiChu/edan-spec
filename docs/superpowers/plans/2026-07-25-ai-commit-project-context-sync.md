# AI Commit Project Context Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every AI-authored code commit entering the target branch detect and update affected Project Context documents, with equivalent behavior in Claude Code, OpenCode, and Kilo Code, and deliver CodeGraph 1.5.0 for offline Linux upgrade.

**Architecture:** Claude Code remains the only hand-maintained source. A deterministic Python gate reports the staged change scope, while the AI protocol performs CodeGraph `sync/status/impact/explore`, updates only affected context documents, and validates them before commit. The existing offline builder adapts the canonical protocol and Skills into OpenCode and Kilo packages; a separate builder verifies and packages the official CodeGraph Linux release for intranet installation.

**Tech Stack:** Markdown Skills and Agent instructions, Python 3 standard library, `unittest`, Git CLI, CodeGraph 1.5.0 CLI, deterministic ZIP/tar verification.

**Confirmed Intranet Target:** Ubuntu 22.04 on `x86_64`; download only the official `codegraph-linux-x64.tar.gz` asset. Reject ARM64 assets.

---

## File Map

| File | Responsibility |
|------|----------------|
| `claudecode/.claude/docs/project-context-commit-protocol.md` | Canonical AI commit protocol shared by all Claude workflows and adapted into other platforms |
| `claudecode/.claude/CLAUDE.md` | Requires the gate for every AI code commit entering a target branch |
| `claudecode/.claude/skills/project-context/SKILL.md` | Defines Commit mode and CodeGraph-driven incremental update behavior |
| `claudecode/.claude/skills/project-context/scripts/context_gate.py` | Deterministically reads the staged change scope and emits JSON |
| `claudecode/.claude/skills/project-context/scripts/validate_context.py` | Optionally verifies evidence source paths against the project root |
| `claudecode/.claude/skills/task-implement/SKILL.md` | Inserts the gate between code verification and commit |
| `claudecode/.claude/skills/task-implement/references/parallel-execution.md` | Treats worktree commits as transport-only and runs one aggregate target-branch gate |
| `scripts/build_offline_bundles.py` | Adapts the canonical protocol and changed Skills into OpenCode/Kilo bundles |
| `scripts/derive_project_context.py` | Includes the canonical gate reference in project-context-only derived packages |
| `scripts/build_codegraph_offline.py` | Builds a verified Linux CodeGraph 1.5.0 offline bundle from official release assets |
| `packaging/codegraph-linux-INSTALL.md` | Intranet migration, installation, verification, and rollback guide |
| `packaging/install-codegraph-offline.sh` | Offline installer that preserves the old executable and installs into a versioned directory |
| `tests/test_project_context_commit_gate.py` | Gate parsing and decision tests |
| `tests/test_project_context_commit_protocol.py` | Claude protocol/Skill integration contract tests |
| `tests/test_validate_project_context.py` | Evidence source-path validation tests |
| `tests/test_offline_bundle_builder.py` | Three-platform protocol equivalence tests |
| `tests/test_project_context_derivation.py` | Project-context-only derived package tests |
| `tests/test_codegraph_offline_bundle.py` | Official asset checksum and offline bundle tests |

## Task 1: Add the Deterministic Staged-Change Gate

**Files:**
- Create: `tests/test_project_context_commit_gate.py`
- Create: `claudecode/.claude/skills/project-context/scripts/context_gate.py`

- [ ] **Step 1: Write the failing parser and decision tests**

```python
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "claudecode"
    / ".claude"
    / "skills"
    / "project-context"
    / "scripts"
    / "context_gate.py"
)
SPEC = importlib.util.spec_from_file_location("context_gate", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT}")
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


class ContextGateTests(unittest.TestCase):
    def test_parses_rename_from_zero_delimited_name_status(self) -> None:
        changes = gate.parse_name_status_z(b"R100\0src/old.cpp\0src/new.cpp\0")
        self.assertEqual("R100", changes[0].status)
        self.assertEqual("src/old.cpp", changes[0].old_path)
        self.assertEqual("src/new.cpp", changes[0].path)

    def test_skips_when_project_context_is_absent(self) -> None:
        report = gate.build_report(
            [gate.Change("M", "src/alarm.cpp")], context_exists=False
        )
        self.assertEqual("skip", report["decision"])
        self.assertEqual("context-absent", report["reason"])

    def test_requests_semantic_analysis_for_source_change(self) -> None:
        report = gate.build_report(
            [gate.Change("M", "src/alarm.cpp")], context_exists=True
        )
        self.assertEqual("analyze", report["decision"])
        self.assertEqual(["src/alarm.cpp"], report["candidatePaths"])

    def test_skips_context_only_change_to_prevent_recursion(self) -> None:
        report = gate.build_report(
            [gate.Change("M", "EdanSpec/context/project.md")],
            context_exists=True,
        )
        self.assertEqual("skip", report["decision"])
        self.assertEqual("context-only", report["reason"])
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
python -m unittest tests.test_project_context_commit_gate -v
```

Expected: import fails because `context_gate.py` does not exist.

- [ ] **Step 3: Implement the minimal gate**

Create `context_gate.py` with this public contract:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath


CONTEXT_PREFIX = PurePosixPath("EdanSpec/context")
RELEVANT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx",
    ".qml", ".proto", ".json", ".jsonc", ".xml", ".yaml", ".yml",
    ".cmake", ".gradle", ".java", ".kt", ".py", ".go", ".rs",
    ".ts", ".tsx", ".js", ".jsx", ".cs", ".swift",
}
RELEVANT_NAMES = {
    "CMakeLists.txt", "Makefile", "meson.build", "package.json",
    "pom.xml", "settings.gradle", "build.gradle",
}


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None = None


def parse_name_status_z(payload: bytes) -> list[Change]:
    tokens = payload.decode("utf-8", errors="surrogateescape").split("\0")
    tokens = [token for token in tokens if token]
    changes: list[Change] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if status.startswith(("R", "C")):
            old_path, path = tokens[index], tokens[index + 1]
            index += 2
            changes.append(Change(status=status, path=path, old_path=old_path))
        else:
            path = tokens[index]
            index += 1
            changes.append(Change(status=status, path=path))
    return changes


def is_context_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return parts[:2] == CONTEXT_PREFIX.parts


def is_candidate(path: str) -> bool:
    item = PurePosixPath(path)
    return item.name in RELEVANT_NAMES or item.suffix.lower() in RELEVANT_SUFFIXES


def build_report(changes: list[Change], *, context_exists: bool) -> dict:
    if not context_exists:
        return {
            "decision": "skip",
            "reason": "context-absent",
            "changes": [asdict(change) for change in changes],
            "candidatePaths": [],
        }
    non_context = [change for change in changes if not is_context_path(change.path)]
    if not non_context:
        return {
            "decision": "skip",
            "reason": "context-only",
            "changes": [asdict(change) for change in changes],
            "candidatePaths": [],
        }
    candidates = sorted(
        {
            path
            for change in non_context
            for path in (change.old_path, change.path)
            if path is not None and is_candidate(path)
        }
    )
    return {
        "decision": "analyze" if candidates else "skip",
        "reason": "relevant-staged-change" if candidates else "no-relevant-change",
        "changes": [asdict(change) for change in changes],
        "candidatePaths": candidates,
    }


def collect_staged_changes(project_root: Path) -> list[Change]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "-z",
         "--diff-filter=ACMRDTUXB"],
        cwd=project_root,
        capture_output=True,
        check=True,
    )
    return parse_name_status_z(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect staged Project Context impact")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    report = build_report(
        collect_staged_changes(root),
        context_exists=(root / "EdanSpec" / "context" / "project.md").is_file(),
    )
    print(
        json.dumps(report, ensure_ascii=False, indent=2)
        if args.json
        else f"{report['decision']}: {report['reason']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run:

```powershell
python -m unittest tests.test_project_context_commit_gate -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit the gate increment**

```powershell
git add -- tests/test_project_context_commit_gate.py claudecode/.claude/skills/project-context/scripts/context_gate.py
git commit -m "feat(project-context): add staged change gate"
```

## Task 2: Add the Canonical AI Commit Protocol

**Files:**
- Create: `tests/test_project_context_commit_protocol.py`
- Create: `claudecode/.claude/docs/project-context-commit-protocol.md`
- Modify: `claudecode/.claude/CLAUDE.md`
- Modify: `claudecode/.claude/skills/project-context/SKILL.md`
- Modify: `claudecode/.claude/skills/task-implement/SKILL.md`

- [ ] **Step 1: Write failing protocol contract tests**

```python
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "claudecode" / ".claude"


class ProjectContextCommitProtocolTests(unittest.TestCase):
    def test_canonical_protocol_has_complete_gate(self) -> None:
        text = (CLAUDE / "docs/project-context-commit-protocol.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "context_gate.py",
            "git diff --cached",
            "codegraph sync",
            "codegraph status",
            "codegraph impact",
            "codegraph explore",
            "validate_context.py",
            "阻止提交",
        ):
            self.assertIn(required, text)

    def test_all_claude_commit_surfaces_require_protocol(self) -> None:
        paths = (
            CLAUDE / "CLAUDE.md",
            CLAUDE / "skills/project-context/SKILL.md",
            CLAUDE / "skills/task-implement/SKILL.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("project-context-commit-protocol.md", text, str(path))

    def test_task_implement_runs_gate_before_git_commit(self) -> None:
        text = (CLAUDE / "skills/task-implement/SKILL.md").read_text(encoding="utf-8")
        commit_step = text.split("## 步骤五：提交与状态更新", 1)[1]
        self.assertLess(
            commit_step.index("Project Context Gate"),
            commit_step.index("git commit"),
        )
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```powershell
python -m unittest tests.test_project_context_commit_protocol -v
```

Expected: fail because the canonical protocol file and references are absent.

- [ ] **Step 3: Write the canonical protocol**

The document must define this exact order:

```markdown
## Required order

1. Stage only the current increment's code, tests, task state, and already-known documentation.
2. Run `context_gate.py --project-root "<projectPath>" --json`.
3. If the result is `skip`, record its reason in the commit summary.
4. If the result is `analyze`, run `codegraph sync "<projectPath>"`.
5. Run `codegraph status "<projectPath>" --json`; an unavailable, incomplete, or pending index blocks the commit.
6. Use `codegraph impact <symbol> --path "<projectPath>" --depth 2 --json` and bounded `codegraph explore`.
7. Update only affected L0/L1/L2/L3 documents using Project Context Update mode.
8. Run `validate_context.py "<contextPath>" --project-root "<projectPath>" --json`.
9. Stage only the affected context documents and re-check `git diff --cached`.
10. Commit only after all errors are zero.
```

Also state:

- Context absent and context-only changes are valid skip cases.
- Dynamic evidence uses `Graph-Heuristic` or `Unknown`.
- CodeGraph or validation failure blocks the commit.
- The AI must not install CodeGraph or rebuild/delete context without explicit authority.

- [ ] **Step 4: Link the protocol from all Claude commit surfaces**

Add a required Git rule to `CLAUDE.md`:

```markdown
### Project Context 提交门禁

AI 准备把代码提交到目标分支前，必须完整读取
[`docs/project-context-commit-protocol.md`](docs/project-context-commit-protocol.md)
并按其顺序执行。该门禁适用于直接提交、`task-implement` 和并行结果聚合。
```

Add `Commit` mode to `project-context/SKILL.md` and make it reference the canonical protocol. In Commit mode, the staged diff is authoritative, CodeGraph is synchronized explicitly, only affected documents are updated, and the validator receives `--project-root`.

Insert this stage into `task-implement/SKILL.md`:

```text
TDD → 代码验证 → Project Context Gate → 原子提交 → 更新任务状态
```

The Skill must require the canonical protocol immediately before its existing `git add`/`git commit` instructions.

- [ ] **Step 5: Run focused protocol tests**

Run:

```powershell
python -m unittest tests.test_project_context_commit_protocol tests.test_project_context_codegraph -v
```

Expected: all protocol and existing CodeGraph contract tests pass.

- [ ] **Step 6: Commit the protocol increment**

```powershell
git add -- tests/test_project_context_commit_protocol.py claudecode/.claude/CLAUDE.md claudecode/.claude/docs/project-context-commit-protocol.md claudecode/.claude/skills/project-context/SKILL.md claudecode/.claude/skills/task-implement/SKILL.md
git commit -m "feat(project-context): enforce AI commit sync protocol"
```

## Task 3: Validate Evidence Source Paths

**Files:**
- Modify: `tests/test_validate_project_context.py`
- Modify: `claudecode/.claude/skills/project-context/scripts/validate_context.py`
- Modify: `claudecode/.claude/docs/project-context-commit-protocol.md`

- [ ] **Step 1: Add failing source-path tests**

Add two tests using the existing `VALID_PROJECT` and `VALID_MODULE` constants:

```python
def test_existing_evidence_source_path_passes(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        context = project_root / "EdanSpec" / "context"
        module_dir = context / "modules" / "core"
        module_dir.mkdir(parents=True)
        source = project_root / "src" / "alarm.cpp"
        source.parent.mkdir(parents=True)
        source.write_text("void alarm() {}\n", encoding="utf-8")
        project = VALID_PROJECT.replace("`a.cpp:1`", "`src/alarm.cpp:1`")
        module = VALID_MODULE.replace("`core.cpp:2`", "`src/alarm.cpp:1`")
        (context / "project.md").write_text(project, encoding="utf-8")
        (module_dir / "module.md").write_text(module, encoding="utf-8")

        report = self.validator.validate_context(
            context, project_root=project_root
        )

        self.assertEqual([], report["errors"])


def test_missing_evidence_source_path_is_an_error(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        context = project_root / "EdanSpec" / "context"
        context.mkdir(parents=True)
        project = VALID_PROJECT.replace(
            "[module.md](modules/core/module.md)", "`not-generated`"
        ).replace("`a.cpp:1`", "`src/missing.cpp:12`")
        (context / "project.md").write_text(project, encoding="utf-8")

        report = self.validator.validate_context(
            context, project_root=project_root
        )

        self.assertTrue(
            any("证据源码路径不存在" in error for error in report["errors"])
        )
```

- [ ] **Step 2: Run the two tests and verify RED**

Run:

```powershell
python -m unittest tests.test_validate_project_context.ValidateProjectContextTests.test_existing_evidence_source_path_passes tests.test_validate_project_context.ValidateProjectContextTests.test_missing_evidence_source_path_is_an_error -v
```

Expected: fail because `validate_context` does not accept `project_root`.

- [ ] **Step 3: Implement optional path verification**

Add:

```python
EVIDENCE_LOCATION_RE = re.compile(
    r"`([^`]+\.(?:c|cc|cpp|cxx|h|hh|hpp|hxx|qml|proto|py|go|rs|java|kt|ts|tsx|js|jsx|cs|swift|json|xml|ya?ml|cmake))(?::\d+)?`",
    re.IGNORECASE,
)


def evidence_source_paths(markdown: str) -> set[str]:
    return {match.replace("\\", "/") for match in EVIDENCE_LOCATION_RE.findall(markdown)}
```

Extend `validate_document` and `validate_context` with `project_root: Path | None`. When a parsed relative source path is present and `project_root / source` is not a file, append:

```text
<document>: 证据源码路径不存在: <source>
```

Add CLI option:

```python
parser.add_argument("--project-root", type=Path)
```

Symbols such as `Class::method` and absolute paths remain outside this deterministic check; the AI verifies them through CodeGraph.

- [ ] **Step 4: Update the protocol command and run validator tests**

Ensure the protocol uses:

```bash
python .claude/skills/project-context/scripts/validate_context.py \
  "<projectPath>/EdanSpec/context" \
  --project-root "<projectPath>" \
  --json
```

Run:

```powershell
python -m unittest tests.test_validate_project_context -v
```

Expected: all validator tests pass.

- [ ] **Step 5: Commit the evidence validation increment**

```powershell
git add -- tests/test_validate_project_context.py claudecode/.claude/skills/project-context/scripts/validate_context.py claudecode/.claude/docs/project-context-commit-protocol.md
git commit -m "feat(project-context): validate evidence source paths"
```

## Task 4: Close the Parallel Worktree Path

**Files:**
- Modify: `tests/test_project_context_commit_protocol.py`
- Modify: `claudecode/.claude/skills/task-implement/references/parallel-execution.md`
- Modify: `claudecode/.claude/skills/task-implement/SKILL.md`

- [ ] **Step 1: Add a failing parallel-path contract**

```python
def test_parallel_results_are_aggregated_before_context_gate(self) -> None:
    text = (
        CLAUDE
        / "skills/task-implement/references/parallel-execution.md"
    ).read_text(encoding="utf-8")
    self.assertIn("临时传输提交", text)
    self.assertIn("cherry-pick --no-commit", text)
    self.assertLess(text.index("cherry-pick --no-commit"), text.index("Project Context Gate"))
    self.assertLess(text.index("Project Context Gate"), text.index("目标分支原子提交"))
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```powershell
python -m unittest tests.test_project_context_commit_protocol.ProjectContextCommitProtocolTests.test_parallel_results_are_aggregated_before_context_gate -v
```

Expected: fail because the current reference directly cherry-picks worktree commits.

- [ ] **Step 3: Replace the parallel integration sequence**

Use this sequence:

```text
子 Agent TDD + 临时传输提交
  → 主 Agent收集每个提交和影响摘要
  → git cherry-pick --no-commit <commit>（依次聚合）
  → 统一测试/构建/Lint/覆盖率
  → Project Context Gate
  → 目标分支原子提交
```

The subagent prompt must state:

- Do not modify `EdanSpec/context/`.
- Report changed files, core symbols, and possible context impact.
- The worktree commit is transport-only and must not be pushed or merged directly.

The main Skill must prohibit target-branch completion when aggregate context validation has not passed.

- [ ] **Step 4: Run focused tests**

```powershell
python -m unittest tests.test_project_context_commit_protocol -v
```

Expected: all protocol tests pass.

- [ ] **Step 5: Commit the parallel increment**

```powershell
git add -- tests/test_project_context_commit_protocol.py claudecode/.claude/skills/task-implement/references/parallel-execution.md claudecode/.claude/skills/task-implement/SKILL.md
git commit -m "feat(task-implement): aggregate context updates for parallel work"
```

## Task 5: Derive the Protocol into OpenCode and Kilo Code

**Files:**
- Modify: `tests/test_offline_bundle_builder.py`
- Modify: `tests/test_project_context_derivation.py`
- Modify: `scripts/build_offline_bundles.py`
- Modify: `scripts/derive_project_context.py`

- [ ] **Step 1: Add failing three-platform equivalence tests**

After extracting each full package, assert:

```python
platform_paths = {
    "claudecode": (
        ".claude/docs/project-context-commit-protocol.md",
        ".claude/skills/task-implement/SKILL.md",
    ),
    "opencode": (
        ".opencode/docs/project-context-commit-protocol.md",
        ".opencode/skills/edanspec-task-implement/SKILL.md",
    ),
    "kilocode": (
        ".kilo/docs/project-context-commit-protocol.md",
        ".kilo/skills/edanspec-task-implement/SKILL.md",
    ),
}
for platform, (protocol_path, task_path) in platform_paths.items():
    protocol = (extracted / protocol_path).read_text(encoding="utf-8")
    task = (extracted / task_path).read_text(encoding="utf-8")
    self.assertIn("codegraph sync", protocol)
    self.assertIn("Project Context Gate", task)
```

Also assert:

- OpenCode/Kilo text contains neither `.claude/` nor `edanspec:`.
- Kilo text contains no `.opencode/`.
- OpenCode `.opencode/AGENTS.md` and Kilo root `AGENTS.md` require the platform-local protocol.
- The project-context-only packages include the platform-local protocol document and global Agent instruction.

- [ ] **Step 2: Run derivation tests and verify RED**

```powershell
python -m unittest tests.test_offline_bundle_builder tests.test_project_context_derivation -v
```

Expected: fail because only project-context resources are currently overlaid.

- [ ] **Step 3: Implement canonical overlays**

In `build_offline_bundles.py`:

1. Copy and adapt `project-context-commit-protocol.md`.
2. Copy and adapt the entire canonical `task-implement` tree into `edanspec-task-implement`.
3. Keep the existing canonical project-context overlay.
4. Insert or replace this marked block in OpenCode `.opencode/AGENTS.md`:

```markdown
<!-- PROJECT_CONTEXT_COMMIT_GATE_START -->
## Project Context Commit Gate

Before any AI-authored code commit enters the target branch, read and follow
`.opencode/docs/project-context-commit-protocol.md`.
<!-- PROJECT_CONTEXT_COMMIT_GATE_END -->
```

5. Derive Kilo from the adapted OpenCode staging tree so the block points to `.kilo/docs/...`.

Implement a pure helper:

```python
def replace_marked_block(
    text: str, *, start: str, end: str, block: str
) -> str:
    pattern = re.compile(
        rf"{re.escape(start)}.*?{re.escape(end)}",
        re.DOTALL,
    )
    if pattern.search(text):
        return pattern.sub(block, text)
    return text.rstrip() + "\n\n" + block + "\n"
```

Apply the same protocol-document and Agent-block overlay in `derive_project_context.py`.

- [ ] **Step 4: Verify derived packages**

```powershell
python -m unittest tests.test_offline_bundle_builder tests.test_project_context_derivation -v
```

Expected: all package tests pass, including manifest re-extraction.

- [ ] **Step 5: Commit the derivation increment**

```powershell
git add -- tests/test_offline_bundle_builder.py tests/test_project_context_derivation.py scripts/build_offline_bundles.py scripts/derive_project_context.py
git commit -m "feat(packaging): derive commit protocol across agents"
```

## Task 6: Build the CodeGraph 1.5.0 Linux Offline Package

**Files:**
- Create: `tests/test_codegraph_offline_bundle.py`
- Create: `scripts/build_codegraph_offline.py`
- Create: `packaging/codegraph-linux-INSTALL.md`
- Create: `packaging/install-codegraph-offline.sh`

- [ ] **Step 1: Write failing offline bundle tests**

Use a temporary fake official release directory containing:

```text
codegraph-linux-x64.tar.gz
SHA256SUMS
```

The tests must verify:

```python
def test_rejects_asset_when_official_checksum_mismatches(self) -> None:
    with self.assertRaises(builder.OfflineBundleError):
        builder.build_bundle(
            source_dir=self.release_dir,
            output_dir=self.output_dir,
            version="1.5.0",
            target="linux-x64",
            repo_root=ROOT,
        )


def test_builds_verified_offline_archive(self) -> None:
    archive = builder.build_bundle(
        source_dir=self.release_dir,
        output_dir=self.output_dir,
        version="1.5.0",
        target="linux-x64",
        repo_root=ROOT,
    )
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
    self.assertIn("codegraph-linux-x64.tar.gz", names)
    self.assertIn("SHA256SUMS", names)
    self.assertIn("INSTALL.md", names)
    self.assertIn("install-codegraph-offline.sh", names)
```

- [ ] **Step 2: Run tests and verify RED**

```powershell
python -m unittest tests.test_codegraph_offline_bundle -v
```

Expected: import fails because the builder does not exist.

- [ ] **Step 3: Implement checksum-verified packaging**

`build_codegraph_offline.py` must:

- Accept `--version 1.5.0`, `--target linux-x64|linux-arm64`, and `--output-dir`.
- Build this delivery with `--target linux-x64`; the confirmed intranet target is Ubuntu 22.04 `x86_64`.
- Reject an asset whose filename is not exactly `codegraph-linux-x64.tar.gz` for this delivery.
- Default release URLs to:

```text
https://github.com/colbymchenry/codegraph/releases/download/v1.5.0/codegraph-linux-x64.tar.gz
https://github.com/colbymchenry/codegraph/releases/download/v1.5.0/SHA256SUMS
```

- Support `--source-dir` for deterministic tests and air-gapped rebuilds.
- Parse the official `SHA256SUMS`.
- Hash the downloaded asset and fail closed on mismatch.
- Create `codegraph-1.5.0-linux-x64-offline.zip` with deterministic entry order and timestamps.
- Write a package-local `MANIFEST.sha256` covering the asset, installer, and guide.
- Re-extract the ZIP and verify its manifest before returning success.

- [ ] **Step 4: Write the offline installer and migration guide**

The installer must:

```sh
set -eu
version="v1.5.0"
archive="codegraph-linux-x64.tar.gz"
install_root="${CODEGRAPH_INSTALL_DIR:-$HOME/.codegraph}"
bin_dir="${CODEGRAPH_BIN_DIR:-$HOME/.local/bin}"
dest="$install_root/versions/$version"

case "$(uname -m)" in
  x86_64|amd64) ;;
  *) echo "Expected x86_64/amd64; use the matching offline package." >&2; exit 1 ;;
esac

sha256sum -c SHA256SUMS
mkdir -p "$dest" "$bin_dir"
tar -xzf "$archive" -C "$dest" --strip-components=1
ln -sfn "$dest" "$install_root/current"
ln -sfn "$dest/bin/codegraph" "$bin_dir/codegraph"
"$bin_dir/codegraph" --version
```

The guide must require:

1. `uname -m` verification.
2. Recording `command -v codegraph` and `codegraph --version`.
3. Backing up the old `.codegraph*` project index before migration.
4. Running the package installer without deleting the old 0.2.5 executable.
5. Putting `~/.local/bin` before the old executable on `PATH`.
6. Re-running `codegraph init` in the project.
7. Checking `codegraph status --json`.
8. Restarting the AI client after MCP configuration.
9. Running one known-symbol `explore` and `impact` smoke test.
10. Rolling back by restoring the previous `PATH` order and index backup.

- [ ] **Step 5: Run offline bundle tests**

```powershell
python -m unittest tests.test_codegraph_offline_bundle -v
```

Expected: all checksum, target, manifest, and archive tests pass.

- [ ] **Step 6: Commit the offline packaging increment**

```powershell
git add -- tests/test_codegraph_offline_bundle.py scripts/build_codegraph_offline.py packaging/codegraph-linux-INSTALL.md packaging/install-codegraph-offline.sh
git commit -m "feat(packaging): add CodeGraph Linux offline upgrade"
```

## Task 7: Run End-to-End Verification and Repackage

**Files:**
- Modify only if verification exposes defects in files from Tasks 1–6.
- Generate: `dist/edan-spec-offline-20260725/edan-spec-claudecode-20260725.zip`
- Generate: `dist/edan-spec-offline-20260725/edan-spec-opencode-20260725.zip`
- Generate: `dist/edan-spec-offline-20260725/edan-spec-kilocode-20260725.zip`
- Generate: `dist/edan-spec-offline-20260725/SHA256SUMS.txt`
- Generate: `dist/edan-spec-offline-20260725.zip`
- Generate: `dist/codegraph-offline-20260725/codegraph-1.5.0-linux-x64-offline.zip`

- [ ] **Step 1: Compile all Python scripts**

```powershell
python -m py_compile scripts/build_offline_bundles.py scripts/derive_project_context.py scripts/build_codegraph_offline.py claudecode/.claude/skills/project-context/scripts/context_gate.py claudecode/.claude/skills/project-context/scripts/validate_context.py
```

Expected: exit code 0 and no output.

- [ ] **Step 2: Run the complete Python suite**

```powershell
python -m unittest discover -s tests -v
```

Expected: 0 failures and 0 errors.

- [ ] **Step 3: Run browser tests and patch validation**

```powershell
node --test tests/context_browser_app.test.mjs
git diff --check
```

Expected: all Node tests pass; `git diff --check` exits 0.

- [ ] **Step 4: Exercise the gate in a temporary Git repository**

Create a temporary repository containing a minimal valid `EdanSpec/context/project.md`, stage a C++ source change, and run:

```powershell
$tempRepo = Join-Path $env:TEMP "project-context-gate-smoke"
python claudecode/.claude/skills/project-context/scripts/context_gate.py --project-root $tempRepo --json
```

Expected JSON:

```json
{
  "decision": "analyze",
  "reason": "relevant-staged-change",
  "candidatePaths": ["src/alarm.cpp"]
}
```

Then stage only `EdanSpec/context/project.md`; expected decision is `skip` with reason `context-only`.

- [ ] **Step 5: Build the three EdanSpec platform packages**

```powershell
python scripts/build_offline_bundles.py --repo-root . --output-dir dist/edan-spec-offline-20260725 --date-tag 20260725
```

Expected: three ZIP paths and SHA-256 values are printed; every archive is re-extracted and manifest-verified.

- [ ] **Step 6: Create the single-file EdanSpec transfer archive**

```powershell
Compress-Archive -LiteralPath dist/edan-spec-offline-20260725 -DestinationPath dist/edan-spec-offline-20260725.zip -CompressionLevel Optimal -Force
Get-FileHash dist/edan-spec-offline-20260725.zip -Algorithm SHA256
```

Expected: one outer ZIP containing exactly the three platform ZIPs and `SHA256SUMS.txt`; its SHA-256 is recorded for handoff.

- [ ] **Step 7: Build the official CodeGraph Linux x64 offline package**

```powershell
python scripts/build_codegraph_offline.py --version 1.5.0 --target linux-x64 --output-dir dist/codegraph-offline-20260725
```

Expected: the official asset matches the v1.5.0 `SHA256SUMS`, and the final offline ZIP is re-extracted and verified.

- [ ] **Step 8: Inspect the final package contracts**

For every EdanSpec platform package, verify:

- platform-local global Agent instructions require the commit protocol;
- platform-local `task-implement` and `project-context` reference the protocol;
- `context_gate.py` and the updated validator are present;
- no source-platform path or Skill-name leaks remain.

For the CodeGraph package, verify:

- only the official archive plus local guide/installer/manifests are present;
- `SHA256SUMS` matches the official v1.5.0 release;
- the final ZIP SHA-256 is recorded for handoff.

- [ ] **Step 9: Perform code review and fix all CRITICAL/IMPORTANT findings**

Review correctness, failure behavior, path safety, archive traversal safety, deterministic output, and three-platform semantic equivalence. Re-run Steps 1–8 after any fix.

- [ ] **Step 10: Commit verification-only fixes**

If verification changed source files:

```powershell
git add -- claudecode/.claude/CLAUDE.md claudecode/.claude/docs/project-context-commit-protocol.md claudecode/.claude/skills/project-context/SKILL.md claudecode/.claude/skills/project-context/scripts/context_gate.py claudecode/.claude/skills/project-context/scripts/validate_context.py claudecode/.claude/skills/task-implement/SKILL.md claudecode/.claude/skills/task-implement/references/parallel-execution.md scripts/build_offline_bundles.py scripts/derive_project_context.py scripts/build_codegraph_offline.py packaging/codegraph-linux-INSTALL.md packaging/install-codegraph-offline.sh tests/test_project_context_commit_gate.py tests/test_project_context_commit_protocol.py tests/test_validate_project_context.py tests/test_offline_bundle_builder.py tests/test_project_context_derivation.py tests/test_codegraph_offline_bundle.py
git commit -m "fix(project-context): close commit sync verification findings"
```

Do not commit generated `dist/` artifacts unless the repository policy explicitly requires it.

## Task 8: Intranet Migration Handoff

**Files:**
- No repository source changes unless the installation guide is corrected from observed evidence.

- [ ] **Step 1: Record target architecture before transfer**

On the intranet machine:

```bash
uname -m
command -v codegraph
codegraph --version
```

Expected for the planned package: `x86_64` or `amd64`, and current CodeGraph `0.2.5`.

- [ ] **Step 2: Copy and verify both offline deliverables**

Copy:

```text
edan-spec-offline-20260725.zip
codegraph-1.5.0-linux-x64-offline.zip
```

Verify their communicated SHA-256 values before extraction.

- [ ] **Step 3: Back up the old index and install CodeGraph 1.5.0**

Follow `INSTALL.md`. The backup target must be an explicit project-local path such as:

```bash
mv .codegraph .codegraph.v0.2.5.backup
```

or, if 0.2.5 uses a single database:

```bash
mv .codegraph.db .codegraph.db.v0.2.5.backup
```

Run only the command matching the path that actually exists. Do not remove either backup.

- [ ] **Step 4: Re-index and verify the nxapp project**

```bash
export PATH="$HOME/.local/bin:$PATH"
codegraph --version
codegraph init "$HOME/work/NX3.0-II-feature/nxapp"
codegraph status "$HOME/work/NX3.0-II-feature/nxapp" --json
```

Expected: version `1.5.0`, initialized index, nonzero files/nodes/edges, complete index state, and no pending changes.

- [ ] **Step 5: Install the matching EdanSpec platform package**

Extract the selected Claude Code/OpenCode/Kilo ZIP directly into the nxapp project root, preserving hidden directories. Restart the agent and confirm the platform-local commit protocol file is readable.

- [ ] **Step 6: Run smoke tests**

Use a known alarm-limit symbol:

```bash
codegraph explore "confirm_recommend alarm limit recommendation flow" --path "$HOME/work/NX3.0-II-feature/nxapp" --max-files 12
codegraph impact confirm_recommend --path "$HOME/work/NX3.0-II-feature/nxapp" --depth 2 --json
```

Then stage a harmless source change without committing and run the platform-local `context_gate.py`. Confirm the AI reports whether Project Context is affected; revert the harmless test edit after the smoke test.

- [ ] **Step 7: Record migration result**

Record:

- CodeGraph version and index status.
- Selected EdanSpec platform.
- `explore` and `impact` smoke-test result.
- Context Gate result.
- Old executable path and index-backup path for rollback.
