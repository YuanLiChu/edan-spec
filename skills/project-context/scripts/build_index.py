#!/usr/bin/env python3
"""Build a legacy compact source index for offline fallback only.

The default project-context workflow uses the official CodeGraph index. Keep
this script only for environments where CodeGraph cannot be installed; do not
merge its heuristic relationships with CodeGraph evidence as if they had the
same confidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".java",
    ".kt",
    ".kts",
    ".go",
    ".py",
    ".rs",
    ".cs",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".qml",
}

CONFIG_NAMES = {
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "go.mod",
    "Cargo.toml",
    "CMakeLists.txt",
    "pyproject.toml",
    "requirements.txt",
}

EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "out",
    "bin",
    "obj",
    "target",
    "vendor",
    "third_party",
    "3rdparty",
    "cmake-build-debug",
    "cmake-build-release",
}

CLASS_PATTERN = re.compile(
    r"\b(class|interface|struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)"
)
FUNC_PATTERN = re.compile(
    r"\b(?:function|def|fun)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)
CPP_FUNC_PATTERN = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_:<>~]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)\s*(?:const\s*)?(?:override\s*)?[{;]"
)
QML_COMPONENT_PATTERN = re.compile(r"^\s*([A-Z][A-Za-z0-9_]*)\s*\{", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build EdanSpec project context indexes.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--edanspec-dir",
        default="EdanSpec",
        help="Directory where context/.index should be written.",
    )
    parser.add_argument(
        "--module-depth",
        type=int,
        default=1,
        help="Top-level path depth used for automatic module grouping.",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Explicit module mapping. Can be passed multiple times.",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=80,
        help="Maximum symbols stored per module index.",
    )
    return parser.parse_args()


def is_excluded(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDE_DIRS or part.startswith("cmake-build-") for part in rel_parts)


def iter_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [
            d
            for d in dirs
            if d not in EXCLUDE_DIRS
            and not d.startswith("cmake-build-")
            and not is_excluded(current_path / d, root)
        ]
        for filename in files:
            path = current_path / filename
            if not is_excluded(path, root):
                yield path


def read_text_sample(path: Path, limit: int = 256_000) -> str:
    try:
        data = path.read_bytes()[:limit]
    except OSError:
        return ""
    return data.decode("utf-8", errors="ignore")


def line_count(path: Path) -> int:
    try:
        with path.open("rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def file_hash(path: Path) -> str:
    digest = hashlib.sha1()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def parse_module_args(module_args: list[str], root: Path) -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for item in module_args:
        if "=" not in item:
            raise SystemExit(f"--module must use NAME=PATH format: {item}")
        name, raw_path = item.split("=", 1)
        modules[name.strip()] = (root / raw_path.strip()).resolve()
    return modules


def infer_module(path: Path, root: Path, explicit: dict[str, Path], depth: int) -> str:
    for name, module_path in explicit.items():
        try:
            path.relative_to(module_path)
            return name
        except ValueError:
            continue
    rel = path.relative_to(root)
    parts = rel.parts[: max(depth, 1)]
    if not parts:
        return root.name
    return "-".join(p.lower().replace("_", "-") for p in parts if p)


def symbol_kind(name: str) -> str:
    lowered = name.lower()
    if "controller" in lowered or lowered.endswith("api"):
        return "entry"
    if any(x in lowered for x in ("consumer", "handler", "command", "scheduler", "job")):
        return "entry"
    if any(x in lowered for x in ("service", "manager", "usecase", "processor")):
        return "service"
    if any(x in lowered for x in ("repository", "dao", "mapper", "store")):
        return "repository"
    if any(x in lowered for x in ("client", "gateway", "adapter")):
        return "external-client"
    if any(x in lowered for x in ("model", "entity", "record", "dto", "vo")):
        return "model"
    return "other"


def extract_symbols(path: Path, root: Path) -> list[dict[str, str]]:
    text = read_text_sample(path)
    if not text:
        return []
    rel = str(path.relative_to(root)).replace("\\", "/")
    symbols: list[dict[str, str]] = []
    for match in CLASS_PATTERN.finditer(text):
        name = match.group(2)
        symbols.append({"name": name, "kind": symbol_kind(name), "file": rel})
    for match in FUNC_PATTERN.finditer(text):
        name = match.group(1)
        symbols.append({"name": name, "kind": symbol_kind(name), "file": rel})
    if path.suffix.lower() in {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}:
        for match in CPP_FUNC_PATTERN.finditer(text):
            name = match.group(2)
            if name not in {"if", "for", "while", "switch", "return"}:
                symbols.append({"name": name, "kind": symbol_kind(name), "file": rel})
    if path.suffix.lower() == ".qml":
        stem = path.stem
        symbols.append({"name": stem, "kind": "entry" if stem[0:1].isupper() else "other", "file": rel})
        for match in QML_COMPONENT_PATTERN.finditer(text):
            name = match.group(1)
            symbols.append({"name": name, "kind": symbol_kind(name), "file": rel})
    return symbols


def classify_file(path: Path) -> str:
    name = path.name
    suffix = path.suffix.lower()
    if name in CONFIG_NAMES or suffix in {".yaml", ".yml", ".json", ".toml", ".ini", ".conf", ".xml"}:
        return "config"
    if suffix in SOURCE_EXTENSIONS:
        return "source"
    if suffix in {".md", ".rst", ".txt"}:
        return "doc"
    return "other"


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    edanspec_dir = Path(args.edanspec_dir)
    if not edanspec_dir.is_absolute():
        edanspec_dir = root / edanspec_dir
    index_dir = edanspec_dir / "context" / ".index"
    modules_dir = index_dir / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    explicit_modules = parse_module_args(args.module, root)
    modules: dict[str, dict] = defaultdict(
        lambda: {
            "files": [],
            "language_counts": Counter(),
            "line_count": 0,
            "symbols": [],
            "entry_candidates": [],
            "core_class_candidates": [],
            "data_model_candidates": [],
            "config_files": [],
            "flow_candidates": [],
        }
    )
    project_files = []
    build_files = []
    language_counts = Counter()

    for path in iter_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        kind = classify_file(path)
        suffix = path.suffix.lower()
        module_name = infer_module(path, root, explicit_modules, args.module_depth)
        stat = path.stat()
        record = {
            "path": rel,
            "kind": kind,
            "extension": suffix,
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
        }
        project_files.append(record)
        module = modules[module_name]
        module["files"].append(record)
        if suffix in SOURCE_EXTENSIONS:
            lines = line_count(path)
            module["line_count"] += lines
            module["language_counts"][suffix] += 1
            language_counts[suffix] += 1
            for symbol in extract_symbols(path, root):
                module["symbols"].append(symbol)
        if path.name in CONFIG_NAMES:
            build_files.append(rel)
        if kind == "config":
            module["config_files"].append(rel)

    for module_name, module in modules.items():
        symbols = module["symbols"]
        seen = set()
        compact_symbols = []
        for symbol in symbols:
            key = (symbol["name"], symbol["file"])
            if key in seen:
                continue
            seen.add(key)
            compact_symbols.append(symbol)
        compact_symbols = compact_symbols[: args.max_symbols]
        module["symbols"] = compact_symbols
        module["entry_candidates"] = [s for s in compact_symbols if s["kind"] == "entry"][:20]
        module["core_class_candidates"] = [
            s
            for s in compact_symbols
            if s["kind"] in {"entry", "service", "repository", "external-client"}
        ][:30]
        module["data_model_candidates"] = [s for s in compact_symbols if s["kind"] == "model"][:30]
        module["flow_candidates"] = [
            {
                "name": s["name"],
                "entry": f'{s["name"]}',
                "evidence_file": s["file"],
                "status": "candidate",
            }
            for s in module["entry_candidates"][:20]
        ]
        module["language_counts"] = dict(module["language_counts"])
        module["file_count"] = len(module["files"])
        module["hash"] = hashlib.sha1(
            json.dumps(module["files"], sort_keys=True).encode("utf-8")
        ).hexdigest()
        module_path = modules_dir / f"{module_name}.json"
        module_path.write_text(
            json.dumps({"module": module_name, **module}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    project_index = {
        "root": str(root),
        "file_count": len(project_files),
        "source_file_count": sum(1 for f in project_files if f["kind"] == "source"),
        "language_counts": dict(language_counts),
        "build_files": build_files,
        "modules": [
            {
                "name": name,
                "file_count": module["file_count"],
                "line_count": module["line_count"],
                "language_counts": module["language_counts"],
                "index": f"modules/{name}.json",
                "hash": module["hash"],
            }
            for name, module in sorted(modules.items())
        ],
    }
    (index_dir / "project-index.json").write_text(
        json.dumps(project_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (index_dir / "scan-state.json").write_text(
        json.dumps(
            {
                "root": str(root),
                "module_count": len(modules),
                "file_count": len(project_files),
                "module_hashes": {name: module["hash"] for name, module in modules.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {index_dir / 'project-index.json'}")
    print(f"Wrote {len(modules)} module indexes to {modules_dir}")


if __name__ == "__main__":
    main()
