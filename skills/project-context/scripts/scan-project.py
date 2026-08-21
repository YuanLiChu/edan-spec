#!/usr/bin/env python3
# scan-project.py — 确定性采集项目结构事实，输出 JSON 供 project-context skill 使用
# 跨平台：macOS / Windows / Linux
# 用法:
#   python scan-project.py                    # 完整扫描当前工作目录
#   python scan-project.py --fast /path/to/dir # 大仓库快速扫描（不逐文件计行）
# 输出 JSON 到 stdout。
#
# 本脚本只做"事实采集"，不做语义判定：
#   ✓ 目录树、构建文件、源码文件清单、语言分布、行数
#   ✓ codegraph 索引是否存在（供主 Agent 决定是否走 codegraph 路径）
#   ✗ 模块边界判定（交给子 Agent + 可选 codegraph query）
#   ✗ 核心类提取（交给子 Agent + codegraph query）
#   ✗ 基础设施识别（交给主 Agent 读配置文件）

import argparse
import json
import os
import sys
from pathlib import Path

# 支持的源码扩展名 → 语言
SOURCE_EXTS = {
    ".kt": "kotlin", ".java": "java", ".go": "go",
    ".ts": "typescript", ".tsx": "typescript", ".js": "javascript",
    ".jsx": "javascript", ".py": "python", ".rs": "rust", ".cs": "csharp",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".c": "c", ".h": "c",
    ".hpp": "cpp", ".m": "objc", ".swift": "swift", ".rb": "ruby",
    ".php": "php", ".scala": "scala",
}

# 构建文件 → 构建工具
BUILD_FILES = {
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "settings.gradle": "gradle",
    "settings.gradle.kts": "gradle",
    "pom.xml": "maven",
    "package.json": "npm",
    "go.mod": "go",
    "Cargo.toml": "cargo",
    "CMakeLists.txt": "cmake",
    "Makefile": "make",
}

# 应忽略的目录（构建产物、依赖、IDE）
IGNORE_DIRS = {
    "node_modules", ".git", ".gradle", "build", "target", "dist",
    "out", ".idea", ".vscode", "__pycache__", ".venv", "venv",
    ".next", ".nuxt", "vendor", "Pods", ".cxx", ".codegraph",
}


def is_ignored_relative(path: Path) -> bool:
    """相对项目根的路径是否落在忽略目录内。"""
    return any(part in IGNORE_DIRS for part in path.parts)


def detect_build_files(root: Path) -> list[str]:
    """识别项目根目录下存在的构建文件名。"""
    found = []
    for name in BUILD_FILES:
        if (root / name).exists():
            found.append(name)
    return sorted(found)


def walk_project(
    root: Path, count_lines: bool = True, max_depth: int = 3
) -> tuple[list[dict], list[str]]:
    """单次遍历项目，原地裁剪忽略目录并收集源码与有限目录树。"""
    files = []
    tree = []
    for current, dirs, names in os.walk(root):
        current_path = Path(current)
        relative_dir = current_path.relative_to(root)
        dirs[:] = sorted(name for name in dirs if name not in IGNORE_DIRS)

        depth = len(relative_dir.parts)
        if relative_dir != Path(".") and depth <= max_depth:
            tree.append(str(relative_dir))

        for name in sorted(names):
            path = current_path / name
            relative = path.relative_to(root)
            if is_ignored_relative(relative):
                continue
            lang = SOURCE_EXTS.get(path.suffix.lower())
            if not lang:
                continue
            lines = None
            if count_lines:
                try:
                    with path.open(encoding="utf-8", errors="ignore") as source_file:
                        lines = sum(1 for _ in source_file)
                except Exception:
                    lines = 0
            files.append(
                {
                    "path": str(relative),
                    "lang": lang,
                    "lines": lines,
                }
            )
    return sorted(files, key=lambda item: item["path"]), sorted(tree)


def scan_source_files(root: Path, count_lines: bool = True) -> list[dict]:
    """兼容入口：扫描源码文件。新代码应通过 scan() 复用单次遍历。"""
    files, _ = walk_project(root, count_lines=count_lines)
    return files


def scan_dir_tree(root: Path, max_depth: int = 3) -> list[str]:
    """兼容入口：收集有限目录树。新代码应通过 scan() 复用单次遍历。"""
    _, tree = walk_project(root, count_lines=False, max_depth=max_depth)
    return tree


def codegraph_dir_name() -> str:
    """返回 CodeGraph 索引目录名；无效覆盖值按官方默认值降级。"""
    name = os.environ.get("CODEGRAPH_DIR", ".codegraph").strip()
    if (
        not name
        or name in {".", ".."}
        or Path(name).is_absolute()
        or "/" in name
        or "\\" in name
    ):
        return ".codegraph"
    return name


def codegraph_index_path(root: Path) -> Path:
    """返回当前环境配置对应的 CodeGraph SQLite 路径。"""
    return root / codegraph_dir_name() / "codegraph.db"


def has_codegraph_index(root: Path) -> bool:
    """项目是否已建立 codegraph 索引。"""
    return codegraph_index_path(root).is_file()


def scan(root: Path, count_lines: bool = True) -> dict:
    """主入口：采集项目结构事实，返回 JSON。"""
    files, tree = walk_project(root, count_lines=count_lines)
    lang_counts: dict[str, int] = {}
    lang_lines: dict[str, int] = {}
    for f in files:
        lang_counts[f["lang"]] = lang_counts.get(f["lang"], 0) + 1
        if count_lines:
            lang_lines[f["lang"]] = lang_lines.get(f["lang"], 0) + f["lines"]
    index_path = codegraph_index_path(root)
    return {
        "projectRoot": str(root),
        "projectName": root.name,
        "scanMode": "full" if count_lines else "fast",
        "buildFiles": detect_build_files(root),
        "dirTree": tree,
        "sourceFileCount": len(files),
        "languages": [
            {
                "lang": lg,
                "files": lang_counts[lg],
                "lines": lang_lines[lg] if count_lines else None,
            }
            for lg in sorted(lang_counts)
        ],
        "codegraphIndexed": has_codegraph_index(root),
        "codegraphIndexPath": str(index_path),
    }


if __name__ == "__main__":
    # 默认扫描当前工作目录（Claude Code 运行 skill 时 cwd 通常是项目根）。
    # 不从脚本位置向上推导——skill 部署到 .claude/skills/ 下时层级不固定，
    # 猜根会指错。需要扫别的目录时显式传参。
    parser = argparse.ArgumentParser(description="采集 project-context 所需的结构事实")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="跳过逐文件行数统计；适合大仓库或已有 CodeGraph 索引的项目",
    )
    parser.add_argument("root", nargs="?", default=str(Path.cwd()), help="项目根目录")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_absolute():
        root = Path.cwd() / root
    if not root.is_dir():
        print(json.dumps({"error": f"目录不存在: {root}"}, ensure_ascii=False))
        sys.exit(1)
    try:
        result = scan(root, count_lines=not args.fast)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)
