# EdanSpec Three-Platform Offline Skill Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three independently installable, checksum-verified offline ZIP bundles from the current EdanSpec worktree for Claude Code, OpenCode, and Kilo Code.

**Architecture:** A standard-library Python builder copies each platform into an isolated staging directory, overlays the current Claude-only Skill changes onto OpenCode with explicit frontmatter/path adaptation, then derives Kilo resources from the adapted OpenCode staging tree. The builder writes per-package manifests, creates deterministic ZIPs, re-extracts them for verification, and writes an outer `SHA256SUMS.txt`.

**Tech Stack:** Python 3.13 standard library (`argparse`, `hashlib`, `pathlib`, `re`, `shutil`, `zipfile`), `pytest`, `pytest-cov`, Claude Code CLI 2.1.156, Kilo CLI 7.4.11.

---

## File Map

- Create `.coveragerc` — branch/line coverage configuration for the new builder.
- Create `scripts/build_offline_bundles.py` — platform adaptation, staging, manifest, ZIP, and verification logic.
- Create `tests/test_offline_bundle_builder.py` — behavioral tests for adaptation, exclusion, package structure, manifests, and Kilo naming.
- Create `packaging/claudecode-INSTALL.md` — Claude Code offline installation and discovery instructions.
- Create `packaging/opencode-INSTALL.md` — OpenCode offline installation and discovery instructions.
- Create `packaging/kilocode-INSTALL.md` — Kilo Code offline installation and discovery instructions.
- Modify `docs/superpowers/specs/2026-07-24-three-platform-offline-skill-packaging-design.md` — already updated to include Kilo agents, docs, and rules.
- Generate `dist/edan-spec-offline-20260724/*.zip` and `SHA256SUMS.txt` — deliverables, not committed.

### Task 1: Configure Coverage Before Writing Builder Tests

**Files:**
- Create: `.coveragerc`

- [ ] **Step 1: Create branch-aware coverage configuration**

```ini
[run]
branch = True
source =
    scripts/build_offline_bundles.py

[report]
show_missing = True
skip_covered = False
fail_under = 80
```

- [ ] **Step 2: Create an isolated development environment**

Run:

```powershell
$venv = Join-Path $env:TEMP "edan-spec-packaging-venv"
uv venv $venv
uv pip install --python "$venv\Scripts\python.exe" pytest pytest-cov
```

Expected: the temporary Python environment contains `pytest` and `pytest-cov`; no package is installed into the offline bundles.

- [ ] **Step 3: Verify coverage tooling**

Run:

```powershell
& "$venv\Scripts\python.exe" -m pytest --help | Select-String -- '--cov'
```

Expected: output contains `--cov`.

- [ ] **Step 4: Commit coverage configuration**

```powershell
git add .coveragerc
git commit -m "test(packaging): configure bundle builder coverage" -m "Co-Authored-By: Claude"
```

### Task 2: Define Builder Behavior With Failing Tests

**Files:**
- Create: `tests/test_offline_bundle_builder.py`
- Test: `tests/test_offline_bundle_builder.py`

- [ ] **Step 1: Add tests for Skill and Agent adaptation**

```python
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts" / "build_offline_bundles.py"
SPEC = importlib.util.spec_from_file_location("build_offline_bundles", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules["build_offline_bundles"] = builder
SPEC.loader.exec_module(builder)


def test_adapt_skill_text_rewrites_name_and_platform_paths() -> None:
    source = """---
name: edanspec:project-context
description: demo
---
Read .claude/skills/project-context/references/project-template.md.
"""
    adapted = builder.adapt_skill_text(
        source,
        target_name="project-context",
        source_prefix=".claude",
        target_prefix=".opencode",
    )
    assert "name: project-context" in adapted
    assert ".opencode/skills/project-context" in adapted
    assert "edanspec:" not in adapted


def test_adapt_agent_text_creates_subagent_permissions() -> None:
    source = """---
name: module-explorer
description: Module explorer
tools: ["Read", "Glob", "Grep", "Bash", "Write"]
---
Agent body.
"""
    adapted = builder.adapt_agent_text(source)
    assert "mode: subagent" in adapted
    assert "read: allow" in adapted
    assert "edit: allow" in adapted
    assert "tools:" not in adapted
    assert "Agent body." in adapted
```

- [ ] **Step 2: Add tests for staging and package verification**

```python
def test_build_all_creates_directly_extractable_platform_layouts(tmp_path: Path) -> None:
    output = builder.build_all(ROOT, tmp_path / "dist", date_tag="20260724")
    extracted = {}
    for platform, archive in output.archives.items():
        root = tmp_path / "extracted" / platform
        builder.extract_archive(archive, root)
        builder.verify_manifest(root)
        extracted[platform] = root
    assert (extracted["claudecode"] / ".claude" / "skills").is_dir()
    assert (extracted["opencode"] / ".opencode" / "skills").is_dir()
    assert (extracted["opencode"] / "opencode.json").is_file()
    assert (extracted["kilocode"] / ".kilo" / "skills").is_dir()
    assert (extracted["kilocode"] / ".kilo" / "agents" / "module-explorer.md").is_file()
    assert (extracted["kilocode"] / ".kilo" / "docs").is_dir()
    assert (extracted["kilocode"] / ".kilo" / "rules").is_dir()
    assert (extracted["kilocode"] / "AGENTS.md").is_file()


def test_kilo_skill_names_match_directory_names(tmp_path: Path) -> None:
    output = builder.build_all(ROOT, tmp_path / "dist", date_tag="20260724")
    root = tmp_path / "extracted-kilocode"
    builder.extract_archive(output.archives["kilocode"], root)
    skills = root / ".kilo" / "skills"
    for skill_dir in sorted(path for path in skills.iterdir() if path.is_dir()):
        name = builder.read_frontmatter_name(skill_dir / "SKILL.md")
        assert name == skill_dir.name


def test_packages_exclude_junk_and_verify_manifests(tmp_path: Path) -> None:
    output = builder.build_all(ROOT, tmp_path / "dist", date_tag="20260724")
    forbidden = {".DS_Store", "__pycache__", ".git"}
    for platform, archive in output.archives.items():
        root = tmp_path / "verified" / platform
        builder.extract_archive(archive, root)
        assert not any(path.name in forbidden for path in root.rglob("*"))
        assert not any(path.suffix in {".pyc", ".pyo", ".log"} for path in root.rglob("*"))
        builder.verify_manifest(root)
    assert output.sha256sums.is_file()
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```powershell
& "$venv\Scripts\python.exe" -m pytest tests/test_offline_bundle_builder.py -q
```

Expected: collection fails because `scripts/build_offline_bundles.py` does not exist.

- [ ] **Step 4: Commit failing tests**

```powershell
git add tests/test_offline_bundle_builder.py
git commit -m "test(packaging): specify offline bundle behavior" -m "Co-Authored-By: Claude"
```

### Task 3: Implement Platform Adaptation and Staging

**Files:**
- Create: `scripts/build_offline_bundles.py`
- Test: `tests/test_offline_bundle_builder.py`

- [ ] **Step 1: Implement frontmatter and text adaptation**

Implement these exact public functions:

```python
def read_frontmatter_name(skill_file: Path) -> str:
    text = skill_file.read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text)
    if match is None:
        raise BundleError(f"missing valid skill name: {skill_file}")
    return match.group(1)


def adapt_skill_text(
    text: str,
    *,
    target_name: str,
    source_prefix: str,
    target_prefix: str,
) -> str:
    text = re.sub(
        r"(?m)^name:\s*[^\r\n]+$",
        f"name: {target_name}",
        text,
        count=1,
    )
    text = text.replace(source_prefix + "/", target_prefix + "/")
    text = text.replace("edanspec:", "edanspec-")
    text = text.replace("`AGENT.md`", "`AGENTS.md`")
    return text


def adapt_agent_text(text: str) -> str:
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise BundleError("agent file is missing YAML frontmatter")
    description_match = re.search(r"(?m)^description:\s*(.+)$", parts[1])
    if description_match is None:
        raise BundleError("agent file is missing description")
    description = description_match.group(1).strip()
    body = parts[2].lstrip("\r\n")
    return (
        "---\n"
        f"description: {description}\n"
        "mode: subagent\n"
        "permission:\n"
        "  read: allow\n"
        "  glob: allow\n"
        "  grep: allow\n"
        "  bash: allow\n"
        "  edit: allow\n"
        "---\n\n"
        f"{body}"
    )
```

- [ ] **Step 2: Implement safe copy helpers**

Use a single exclusion predicate:

```python
FORBIDDEN_NAMES = {".DS_Store", "__pycache__", ".git"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".log"}


def should_exclude(path: Path) -> bool:
    return (
        any(part in FORBIDDEN_NAMES for part in path.parts)
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
    )
```

`copy_tree_filtered(source, destination)` must iterate files in sorted relative-path order, reject missing sources with `BundleError`, create parent directories, and copy with `shutil.copy2`.

- [ ] **Step 3: Implement Claude and OpenCode staging**

Claude staging:

```python
copy_tree_filtered(repo_root / "claudecode" / ".claude", stage / ".claude")
```

OpenCode staging begins with the current OpenCode tree and config:

```python
copy_tree_filtered(repo_root / "opencode" / ".opencode", stage / ".opencode")
shutil.copy2(repo_root / "opencode" / "opencode.json", stage / "opencode.json")
```

Then overlay the full current Claude directories:

```python
SKILL_OVERLAYS = {
    "design-review": "edanspec-design-review",
    "project-context": "project-context",
}
AGENT_OVERLAYS = ("flow-explorer.md", "module-explorer.md")
DOC_OVERLAYS = ("image-prompt.md", "project-context-skill-guide.md")
```

For each Skill overlay, copy every file, adapt UTF-8 Markdown/Python text from `.claude/` to `.opencode/`, and force the target `SKILL.md` frontmatter name to the target directory name. For each Agent overlay, call `adapt_agent_text`; for each documentation overlay, replace `.claude/` with `.opencode/` and `edanspec:` with `edanspec-`.

- [ ] **Step 4: Implement Kilo staging**

Copy the adapted OpenCode staging resources:

```python
copy_tree_filtered(opencode_stage / ".opencode" / "skills", kilo_stage / ".kilo" / "skills")
copy_tree_filtered(opencode_stage / ".opencode" / "agents", kilo_stage / ".kilo" / "agents")
copy_tree_filtered(opencode_stage / ".opencode" / "docs", kilo_stage / ".kilo" / "docs")
copy_tree_filtered(opencode_stage / ".opencode" / "rules", kilo_stage / ".kilo" / "rules")
```

Copy `.opencode/AGENTS.md` to root `AGENTS.md`, then adapt all UTF-8 text beneath Kilo staging:

```python
text = text.replace(".opencode/", ".kilo/")
text = text.replace("`docs/", "`.kilo/docs/")
text = text.replace("`rules/", "`.kilo/rules/")
text = text.replace("`AGENT.md`", "`AGENTS.md`")
```

Validate every `.kilo/skills/<name>/SKILL.md` with `read_frontmatter_name` and raise `BundleError` when the directory name differs.

- [ ] **Step 5: Run focused tests**

Run:

```powershell
& "$venv\Scripts\python.exe" -m pytest tests/test_offline_bundle_builder.py -q
```

Expected: adaptation tests pass; package tests may still fail because install templates and ZIP functions are not implemented.

### Task 4: Add Offline Installation Documents

**Files:**
- Create: `packaging/claudecode-INSTALL.md`
- Create: `packaging/opencode-INSTALL.md`
- Create: `packaging/kilocode-INSTALL.md`
- Test: `tests/test_offline_bundle_builder.py`

- [ ] **Step 1: Write Claude Code installation instructions**

The document must instruct users to back up an existing `.claude/`, extract the ZIP into the project root, verify `.claude/CLAUDE.md` and `.claude/skills/`, then start a new Claude session and run `/skills`. It must state that the archive does not include Claude Code or model credentials.

- [ ] **Step 2: Write OpenCode installation instructions**

The document must instruct users to back up `.opencode/` and `opencode.json`, extract into the project root, verify both paths, start OpenCode, and confirm that `edanspec-*` skills and configured agents are visible. It must state that OpenCode CLI and internal model routing are prerequisites.

- [ ] **Step 3: Write Kilo Code installation instructions**

The document must include:

```powershell
kilo debug skill
kilo debug agent module-explorer
kilo debug agent flow-explorer
```

It must explain that `.kilo/skills/`, `.kilo/agents/`, `.kilo/docs/`, `.kilo/rules/`, and root `AGENTS.md` are extracted into the target project and that a new session or `/reload` is required.

- [ ] **Step 4: Extend tests for installation documents**

```python
def test_each_package_contains_platform_installation_document(tmp_path: Path) -> None:
    output = builder.build_all(ROOT, tmp_path / "dist", date_tag="20260724")
    for platform, archive in output.archives.items():
        root = tmp_path / "install-docs" / platform
        builder.extract_archive(archive, root)
        install = (root / "INSTALL.md").read_text(encoding="utf-8")
        assert "内网" in install
        assert "SHA-256" in install
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
& "$venv\Scripts\python.exe" -m pytest tests/test_offline_bundle_builder.py -q
```

Expected: tests progress to the manifest/ZIP implementation boundary.

### Task 5: Implement Manifests, ZIP Creation, and Re-Extraction Verification

**Files:**
- Modify: `scripts/build_offline_bundles.py`
- Test: `tests/test_offline_bundle_builder.py`

- [ ] **Step 1: Implement manifest generation and verification**

Use SHA-256 over file bytes. `MANIFEST.sha256` contains sorted lines in this format:

```text
<64 lowercase hex characters>  <forward-slash relative path>
```

Exclude `MANIFEST.sha256` itself from its own listing. `verify_manifest(root)` must reject a missing file, unexpected file, or hash mismatch.

- [ ] **Step 2: Implement deterministic ZIP creation**

Write entries in sorted relative-path order with `/` separators. Use `zipfile.ZIP_DEFLATED`, set each `ZipInfo.date_time` to `(2026, 7, 24, 0, 0, 0)`, and preserve executable bits for `.sh` files via `external_attr`.

- [ ] **Step 3: Implement `build_all` and CLI**

Expose:

```python
@dataclass(frozen=True)
class BuildOutput:
    archives: dict[str, Path]
    sha256sums: Path


def build_all(repo_root: Path, output_dir: Path, *, date_tag: str) -> BuildOutput:
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    if not re.fullmatch(r"\d{8}", date_tag):
        raise BundleError(f"date tag must use YYYYMMDD: {date_tag}")
    output_dir.mkdir(parents=True, exist_ok=True)
    archives: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix="edan-spec-offline-") as temp_dir:
        temp_root = Path(temp_dir)
        stages = {
            "claudecode": temp_root / "stage-claudecode",
            "opencode": temp_root / "stage-opencode",
            "kilocode": temp_root / "stage-kilocode",
        }
        stage_claudecode(repo_root, stages["claudecode"])
        stage_opencode(repo_root, stages["opencode"])
        stage_kilocode(stages["opencode"], stages["kilocode"])
        for platform, stage in stages.items():
            install_source = repo_root / "packaging" / f"{platform}-INSTALL.md"
            shutil.copy2(install_source, stage / "INSTALL.md")
            write_manifest(stage)
            archive = output_dir / f"edan-spec-{platform}-{date_tag}.zip"
            create_archive(stage, archive)
            verification_root = temp_root / f"verify-{platform}"
            extract_archive(archive, verification_root)
            verify_manifest(verification_root)
            archives[platform] = archive
    sha256sums = output_dir / "SHA256SUMS.txt"
    write_archive_checksums(archives, sha256sums)
    return BuildOutput(archives=archives, sha256sums=sha256sums)
```

CLI:

```powershell
python scripts/build_offline_bundles.py --repo-root . --output-dir dist/edan-spec-offline-20260724 --date-tag 20260724
```

The command must build in a temporary directory, copy only final ZIPs and `SHA256SUMS.txt` into the output directory, re-extract each ZIP into a second temporary directory, run `verify_manifest`, and print archive paths, file counts, and hashes.

- [ ] **Step 4: Run focused tests with coverage**

Run:

```powershell
& "$venv\Scripts\python.exe" -m pytest tests/test_offline_bundle_builder.py `
  --cov=scripts.build_offline_bundles --cov-branch --cov-report=term-missing --cov-report=json:coverage.json -q
```

Expected: all tests pass and total line coverage is at least 80%.

- [ ] **Step 5: Enforce branch coverage**

Run:

```powershell
& "$venv\Scripts\python.exe" -c "import json; d=json.load(open('coverage.json', encoding='utf-8'))['totals']; line=100*d['covered_lines']/d['num_statements']; branch=100*d['covered_branches']/d['num_branches']; print(f'line={line:.2f}% branch={branch:.2f}%'); assert line >= 80 and branch >= 70"
```

Expected: line coverage ≥80% and branch coverage ≥70%.

- [ ] **Step 6: Commit builder, templates, and tests**

```powershell
git add scripts/build_offline_bundles.py tests/test_offline_bundle_builder.py packaging/claudecode-INSTALL.md packaging/opencode-INSTALL.md packaging/kilocode-INSTALL.md
git commit -m "feat(packaging): build three-platform offline bundles" -m "Co-Authored-By: Claude"
```

### Task 6: Build and Validate the Real Deliverables

**Files:**
- Generate: `dist/edan-spec-offline-20260724/edan-spec-claudecode-20260724.zip`
- Generate: `dist/edan-spec-offline-20260724/edan-spec-opencode-20260724.zip`
- Generate: `dist/edan-spec-offline-20260724/edan-spec-kilocode-20260724.zip`
- Generate: `dist/edan-spec-offline-20260724/SHA256SUMS.txt`

- [ ] **Step 1: Run all existing repository tests**

```powershell
python -m pytest -q
node --test tests/context_browser_app.test.mjs
```

Expected: all Python and Node tests pass.

- [ ] **Step 2: Build final archives from the current worktree**

```powershell
python scripts/build_offline_bundles.py `
  --repo-root . `
  --output-dir dist/edan-spec-offline-20260724 `
  --date-tag 20260724
```

Expected: three ZIPs and `SHA256SUMS.txt` are printed with successful manifest verification.

- [ ] **Step 3: Verify Claude Code package statically**

Extract to a new temporary directory and confirm:

```powershell
Test-Path .claude/CLAUDE.md
Test-Path .claude/skills/design-review/SKILL.md
claude --version
```

Expected: both paths are true and Claude Code reports its installed version. No model call is made.

- [ ] **Step 4: Record OpenCode verification boundary**

Run:

```powershell
Get-Command opencode -ErrorAction SilentlyContinue
```

Expected on this machine: no command found. Verify the OpenCode archive statically and state in `INSTALL.md`/handoff that live CLI discovery was not run locally.

- [ ] **Step 5: Verify Kilo Skill and Agent discovery**

Extract the Kilo ZIP into a fresh temporary project and run from that directory:

```powershell
kilo debug skill
kilo debug agent module-explorer
kilo debug agent flow-explorer
```

Expected: all packaged Skill names are listed, and both project-context subagents resolve without configuration errors.

- [ ] **Step 6: Verify final hashes independently**

```powershell
Get-FileHash dist/edan-spec-offline-20260724/*.zip -Algorithm SHA256
Get-Content dist/edan-spec-offline-20260724/SHA256SUMS.txt
```

Expected: all three computed hashes match the corresponding lines in `SHA256SUMS.txt`.

- [ ] **Step 7: Check Git scope**

```powershell
git diff --check
git status --short
```

Expected: no new whitespace errors; user-owned pre-existing Skill changes remain present and are not accidentally committed. The generated `dist/` directory remains an uncommitted deliverable.

### Task 7: Final Handoff

**Files:**
- Deliver: `dist/edan-spec-offline-20260724/*.zip`
- Deliver: `dist/edan-spec-offline-20260724/SHA256SUMS.txt`

- [ ] **Step 1: Report exact archive paths and sizes**

Use `Get-Item` to report each absolute path and byte size.

- [ ] **Step 2: Report verification evidence**

Include Python/Node test counts, line/branch coverage, Kilo discovery results, checksum match, and the explicit OpenCode CLI limitation.

- [ ] **Step 3: Report installation entry point**

Tell the user to copy the selected ZIP into the intranet, verify its SHA-256 against `SHA256SUMS.txt`, and extract it directly into the target project root.
