#!/usr/bin/env python3
"""Derive OpenCode and Kilo project-context bundles from Claude Code source."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {".md", ".py", ".txt", ".json", ".jsonc", ".yaml", ".yml"}
EXCLUDED_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}
MANIFEST_NAME = "MANIFEST.sha256"


class DerivationError(RuntimeError):
    """Raised when a derived package cannot satisfy its contract."""


def read_frontmatter_name(skill_file: Path) -> str:
    text = skill_file.read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*([a-z0-9-]+)\s*$", text)
    if match is None:
        raise DerivationError(f"missing portable skill name: {skill_file}")
    return match.group(1)


def adapt_skill_text(
    text: str, *, target_prefix: str, target_name: str = "project-context"
) -> str:
    adapted, count = re.subn(
        r"(?m)^name:\s*[^\r\n]+$",
        f"name: {target_name}",
        text,
        count=1,
    )
    if count != 1:
        raise DerivationError("SKILL.md is missing name frontmatter")
    adapted = adapted.replace(".claude/", target_prefix + "/")
    return adapted.replace("edanspec:", "edanspec-")


def adapt_agent_text(text: str, *, target_prefix: str) -> str:
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise DerivationError("agent file is missing YAML frontmatter")
    description_match = re.search(r"(?m)^description:\s*(.+)$", parts[1])
    if description_match is None:
        raise DerivationError("agent file is missing description")
    description = description_match.group(1).strip()
    body = parts[2].lstrip("\r\n")
    body = body.replace(".claude/", target_prefix + "/")
    body = body.replace("edanspec:", "edanspec-")
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


def should_exclude(path: Path) -> bool:
    return (
        any(part in EXCLUDED_NAMES for part in path.parts)
        or path.suffix.lower() in EXCLUDED_SUFFIXES
    )


def copy_adapted_tree(
    source: Path,
    destination: Path,
    *,
    source_prefix: str,
    target_prefix: str,
    adapt_skill: bool = False,
) -> None:
    if not source.is_dir():
        raise DerivationError(f"source directory does not exist: {source}")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if not path.is_file() or should_exclude(relative):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            text = text.replace(source_prefix + "/", target_prefix + "/")
            text = text.replace("edanspec:", "edanspec-")
            if adapt_skill and relative.as_posix() == "SKILL.md":
                text = adapt_skill_text(
                    text,
                    target_prefix=target_prefix,
                    target_name="project-context",
                )
            target.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(path, target)


def stage_opencode(repo_root: Path, stage: Path) -> None:
    claude = repo_root / "claudecode" / ".claude"
    copy_adapted_tree(
        claude / "skills" / "project-context",
        stage / ".opencode" / "skills" / "project-context",
        source_prefix=".claude",
        target_prefix=".opencode",
        adapt_skill=True,
    )

    agents = stage / ".opencode" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    for name in ("module-explorer.md", "flow-explorer.md"):
        source = claude / "agents" / name
        adapted = adapt_agent_text(
            source.read_text(encoding="utf-8"), target_prefix=".opencode"
        )
        (agents / name).write_text(adapted, encoding="utf-8", newline="\n")

    docs = stage / ".opencode" / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    guide = (claude / "docs" / "project-context-skill-guide.md").read_text(
        encoding="utf-8"
    )
    guide = guide.replace(".claude/", ".opencode/").replace(
        "edanspec:", "edanspec-"
    )
    (docs / "project-context-skill-guide.md").write_text(
        guide, encoding="utf-8", newline="\n"
    )
    write_install(stage, platform="OpenCode", prefix=".opencode")


def stage_kilocode(opencode_stage: Path, stage: Path) -> None:
    source = opencode_stage / ".opencode"
    copy_adapted_tree(
        source,
        stage / ".kilo",
        source_prefix=".opencode",
        target_prefix=".kilo",
    )
    write_install(stage, platform="Kilo Code", prefix=".kilo")


def write_install(stage: Path, *, platform: str, prefix: str) -> None:
    text = f"""# project-context for {platform}

本包由仓库中的 Claude Code 唯一源码确定性派生，适合复制到内网项目。

1. 校验 ZIP 的 SHA-256。
2. 备份目标项目中已有的 `{prefix}/`。
3. 将 ZIP 直接解压到项目根目录。
4. 确认 `{prefix}/skills/project-context/SKILL.md`、两个 explorer 和 references/scripts 均存在。
5. 重启 {platform}，再执行 project-context。

包内不包含 Agent CLI、模型、凭证或 CodeGraph。目标机需预装这些运行时。
`MANIFEST.sha256` 用于校验解压后的每个文件。
"""
    (stage / "INSTALL.md").write_text(text, encoding="utf-8", newline="\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(root: Path) -> Path:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != MANIFEST_NAME:
            entries.append(f"{file_sha256(path)}  {path.relative_to(root).as_posix()}")
    manifest = root / MANIFEST_NAME
    manifest.write_text("\n".join(entries) + "\n", encoding="utf-8", newline="\n")
    return manifest


def verify_manifest(root: Path) -> None:
    manifest = root / MANIFEST_NAME
    if not manifest.is_file():
        raise DerivationError(f"missing {MANIFEST_NAME}: {root}")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, separator, relative = line.partition("  ")
        if separator != "  " or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise DerivationError(f"invalid manifest line: {line}")
        expected[relative] = digest
    actual = {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != MANIFEST_NAME
    }
    if actual != expected:
        raise DerivationError("manifest does not match extracted package contents")


def create_archive(root: Path, archive: Path, *, date_tag: str) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    timestamp = (
        int(date_tag[0:4]),
        int(date_tag[4:6]),
        int(date_tag[6:8]),
        0,
        0,
        0,
    )
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_resolved = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if destination_resolved not in target.parents and target != destination_resolved:
                raise DerivationError(f"unsafe archive path: {member.filename}")
        bundle.extractall(destination)


def validate_stage(stage: Path, *, prefix: str) -> None:
    skill = stage / prefix / "skills" / "project-context" / "SKILL.md"
    if read_frontmatter_name(skill) != "project-context":
        raise DerivationError(f"skill name does not match directory: {skill}")
    for required in (
        "references/codegraph.md",
        "references/evidence-contract.md",
        "references/review-checklist.md",
        "references/impact-template.md",
        "scripts/validate_context.py",
    ):
        if not (skill.parent / required).is_file():
            raise DerivationError(f"derived skill is missing {required}")
    for path in stage.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            if ".claude/" in path.read_text(encoding="utf-8"):
                raise DerivationError(f"Claude path leaked into derived package: {path}")


def build_all(
    repo_root: Path, output_dir: Path, *, date_tag: str
) -> dict[str, Path]:
    if not re.fullmatch(r"\d{8}", date_tag):
        raise DerivationError(f"date tag must use YYYYMMDD: {date_tag}")
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archives: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix="project-context-derived-") as temp_dir:
        temp = Path(temp_dir)
        opencode = temp / "opencode"
        kilocode = temp / "kilocode"
        stage_opencode(repo_root, opencode)
        stage_kilocode(opencode, kilocode)
        for platform, stage, prefix in (
            ("opencode", opencode, ".opencode"),
            ("kilocode", kilocode, ".kilo"),
        ):
            validate_stage(stage, prefix=prefix)
            write_manifest(stage)
            archive = output_dir / f"project-context-{platform}-{date_tag}.zip"
            create_archive(stage, archive, date_tag=date_tag)
            verification = temp / f"verify-{platform}"
            extract_archive(archive, verification)
            verify_manifest(verification)
            archives[platform] = archive
    return archives


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从 Claude Code 唯一源码派生 project-context OpenCode/Kilo 包"
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-tag", required=True, help="YYYYMMDD")
    args = parser.parse_args()
    archives = build_all(args.repo_root, args.output_dir, date_tag=args.date_tag)
    for platform, archive in sorted(archives.items()):
        print(f"{platform}: {archive} sha256={file_sha256(archive)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
