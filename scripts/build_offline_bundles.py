#!/usr/bin/env python3
"""Build verified EdanSpec offline bundles for three agent platforms."""

from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

try:
    from scripts import derive_project_context as common
except (ImportError, ModuleNotFoundError):  # Direct execution from scripts/.
    _common_spec = importlib.util.spec_from_file_location(
        "derive_project_context", Path(__file__).with_name("derive_project_context.py")
    )
    if _common_spec is None or _common_spec.loader is None:
        raise ImportError("unable to load derive_project_context.py")
    common = importlib.util.module_from_spec(_common_spec)
    sys.modules[_common_spec.name] = common
    _common_spec.loader.exec_module(common)


class BuildOutput(NamedTuple):
    archives: dict[str, Path]
    sha256sums: Path


QT_SKILL_FILES = {
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


def copy_platform_tree(
    source: Path,
    destination: Path,
    *,
    source_prefix: str,
    target_prefix: str,
) -> None:
    common.copy_adapted_tree(
        source,
        destination,
        source_prefix=source_prefix,
        target_prefix=target_prefix,
    )


def stage_claudecode(repo_root: Path, stage: Path) -> None:
    copy_root_assets(repo_root, stage, prefix=".claude", rename_agents=True)


def overlay_project_context(repo_root: Path, stage: Path) -> None:
    target = stage / ".opencode"
    # Root assets already contain the canonical project-context skill and guide;
    # only the Claude-specific explorer agents need platform adaptation here.
    agents_source = repo_root / "claudecode" / ".claude" / "agents"
    agents = target / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    for name in ("module-explorer.md", "flow-explorer.md"):
        text = common.adapt_agent_text(
            (agents_source / name).read_text(encoding="utf-8"),
            target_prefix=".opencode",
        )
        (agents / name).write_text(text, encoding="utf-8", newline="\n")


def copy_root_assets(
    repo_root: Path, stage: Path, *, prefix: str, rename_agents: bool = False
) -> None:
    """Deploy the repository's single root asset set into a platform prefix."""
    destination = stage / prefix
    destination.mkdir(parents=True, exist_ok=True)
    agents_name = "CLAUDE.md" if prefix == ".claude" else "AGENTS.md"
    agents_text = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    agents_text = agents_text.replace(".claude/", prefix + "/")
    (destination / agents_name).write_text(
        agents_text, encoding="utf-8", newline="\n"
    )
    for name in ("docs", "rules", "skills"):
        common.copy_adapted_tree(
            repo_root / name,
            destination / name,
            source_prefix=".claude",
            target_prefix=prefix,
        )
    if rename_agents:
        source = repo_root / "claudecode" / ".claude" / "agents"
        target = destination / "agents"
        target.mkdir(parents=True, exist_ok=True)
        for name in ("module-explorer.md", "flow-explorer.md"):
            text = common.adapt_agent_text(
                (source / name).read_text(encoding="utf-8"),
                target_prefix=prefix,
            )
            (target / name).write_text(text, encoding="utf-8", newline="\n")


def stage_opencode(repo_root: Path, stage: Path) -> None:
    copy_root_assets(repo_root, stage, prefix=".opencode")
    shutil.copy2(repo_root / "opencode.json", stage / "opencode.json")
    overlay_project_context(repo_root, stage)


def stage_kilocode(opencode_stage: Path, stage: Path) -> None:
    source = opencode_stage / ".opencode"
    for name in ("agents", "docs", "rules", "skills"):
        copy_platform_tree(
            source / name,
            stage / ".kilo" / name,
            source_prefix=".opencode",
            target_prefix=".kilo",
        )
    agents_text = (source / "AGENTS.md").read_text(encoding="utf-8")
    agents_text = agents_text.replace(".opencode/", ".kilo/")
    (stage / "AGENTS.md").write_text(
        agents_text, encoding="utf-8", newline="\n"
    )


def install_text(platform: str, prefix: str, date_tag: str) -> str:
    archive = f"edan-spec-{platform}-{date_tag}.zip"
    display = {
        "claudecode": "Claude Code",
        "opencode": "OpenCode",
        "kilocode": "Kilo Code",
    }[platform]
    verify = {
        "claudecode": "claude --version",
        "opencode": "opencode --version",
        "kilocode": "kilo debug skill",
    }[platform]
    return (
        f"# EdanSpec for {display} - \u5185\u7f51\u5b89\u88c5\n\n"
        "This archive contains EdanSpec rules, agents, skills, templates, and "
        "local scripts. It does not contain the agent CLI, model service, "
        "credentials, or CodeGraph runtime.\n\n"
        "## Install\n\n"
        f"1. Verify the ZIP SHA-256 against `SHA256SUMS.txt`.\n"
        f"2. Back up the existing `{prefix}/` directory in the target project.\n"
        f"3. Extract `{archive}` directly into the target project root.\n"
        f"4. Confirm `{prefix}/skills/project-context/SKILL.md` exists.\n"
        f"   Qt projects also require `{prefix}/skills/qt-cpp-review/` and "
        f"`{prefix}/skills/qt-qml-review/`.\n"
        f"5. Restart {display} and run `{verify}`.\n\n"
        "PowerShell:\n\n"
        "```powershell\n"
        f"Expand-Archive .\\{archive} -DestinationPath . -Force\n"
        f"Test-Path {prefix}/skills/project-context/SKILL.md\n"
        "```\n\n"
        "Linux:\n\n"
        "```bash\n"
        f"unzip -o {archive} -d .\n"
        f"test -f {prefix}/skills/project-context/SKILL.md\n"
        "```\n\n"
        "Use `MANIFEST.sha256` to verify every extracted file. Install and "
        "initialize CodeGraph separately on the intranet machine before using "
        "the graph-first project-context workflow.\n"
    )


def validate_stage(stage: Path, *, platform: str, prefix: str) -> None:
    skill = stage / prefix / "skills" / "project-context" / "SKILL.md"
    if not skill.is_file():
        raise common.DerivationError(f"missing project-context skill: {skill}")
    if "codegraph_explore" not in skill.read_text(encoding="utf-8"):
        raise common.DerivationError(f"stale project-context skill: {skill}")
    for skill_name, references in QT_SKILL_FILES.items():
        qt_skill = stage / prefix / "skills" / skill_name
        entry = qt_skill / "SKILL.md"
        license_file = qt_skill / "LICENSE.txt"
        if not entry.is_file():
            raise common.DerivationError(f"missing Qt skill entry: {entry}")
        if common.read_frontmatter_name(entry) != skill_name:
            raise common.DerivationError(
                f"Qt skill name does not match directory: {entry}"
            )
        if not license_file.is_file() or "BSD 3-Clause License" not in license_file.read_text(
            encoding="utf-8"
        ):
            raise common.DerivationError(f"missing Qt skill license: {license_file}")
        for relative in references:
            required = qt_skill / relative
            if not required.is_file():
                raise common.DerivationError(
                    f"Qt skill {skill_name} is missing {relative}"
                )
    if platform == "claudecode":
        return
    for skill_file in (stage / prefix / "skills").glob("*/SKILL.md"):
        if common.read_frontmatter_name(skill_file) != skill_file.parent.name:
            raise common.DerivationError(
                f"skill name does not match directory: {skill_file}"
            )
    for path in stage.rglob("*"):
        if path.is_file() and path.suffix.lower() in common.TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            if ".claude/" in text:
                raise common.DerivationError(
                    f"Claude path leaked into {platform} package: {path}"
                )


def write_archive_checksums(archives: dict[str, Path], destination: Path) -> None:
    lines = [
        f"{common.file_sha256(path)}  {path.name}"
        for _, path in sorted(archives.items())
    ]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def build_all(repo_root: Path, output_dir: Path, *, date_tag: str) -> BuildOutput:
    if not re.fullmatch(r"\d{8}", date_tag):
        raise common.DerivationError(f"date tag must use YYYYMMDD: {date_tag}")
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archives: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix="edan-spec-offline-") as temp_dir:
        temp = Path(temp_dir)
        stages = {
            "claudecode": temp / "stage-claudecode",
            "opencode": temp / "stage-opencode",
            "kilocode": temp / "stage-kilocode",
        }
        stage_claudecode(repo_root, stages["claudecode"])
        stage_opencode(repo_root, stages["opencode"])
        stage_kilocode(stages["opencode"], stages["kilocode"])
        prefixes = {
            "claudecode": ".claude",
            "opencode": ".opencode",
            "kilocode": ".kilo",
        }
        for platform, stage in stages.items():
            (stage / "INSTALL.md").write_text(
                install_text(platform, prefixes[platform], date_tag),
                encoding="utf-8",
                newline="\n",
            )
            validate_stage(
                stage, platform=platform, prefix=prefixes[platform]
            )
            common.write_manifest(stage)
            archive = output_dir / f"edan-spec-{platform}-{date_tag}.zip"
            common.create_archive(stage, archive, date_tag=date_tag)
            verification = temp / f"verify-{platform}"
            common.extract_archive(archive, verification)
            common.verify_manifest(verification)
            archives[platform] = archive
    sha256sums = output_dir / "SHA256SUMS.txt"
    write_archive_checksums(archives, sha256sums)
    return BuildOutput(archives=archives, sha256sums=sha256sums)


extract_archive = common.extract_archive
verify_manifest = common.verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build verified EdanSpec offline bundles."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-tag", required=True, help="YYYYMMDD")
    args = parser.parse_args()
    output = build_all(args.repo_root, args.output_dir, date_tag=args.date_tag)
    for platform, archive in sorted(output.archives.items()):
        print(
            f"{platform}: {archive} "
            f"sha256={common.file_sha256(archive)}"
        )
    print(f"checksums: {output.sha256sums}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
