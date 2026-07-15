#!/usr/bin/env python3
# derive-artifact-status.py — 从文件系统事实推导 artifactGraph 状态
# 跨平台：macOS / Windows / Linux
# 用法:
#   python derive-artifact-status.py                                    # 扫描 EdanSpec/feature/ 下所有活跃 feature
#   python derive-artifact-status.py EdanSpec/feature/20260518-login    # 指定具体 feature 目录
# 输出: JSON 格式的 artifactGraph 数组到 stdout

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def normalize_capability(name: str) -> str:
    """归一化 capability 名称：去连字符/下划线、转小写。
    'user-auth' → 'userauth', 'Authentication' → 'authentication'
    """
    return name.replace("-", "").replace("_", "").lower()


def is_prefix_of(a: str, b: str) -> bool:
    """a 是否是 b 的前缀（且 a != b）"""
    return a != b and (b.startswith(a) or a.startswith(b))


def detect_spec_conflicts(feature_root: Path) -> list[dict]:
    """扫描所有活跃 feature 的 specs/，检测文件名冲突。
    冲突判定：
    1. 归一化后完全相同（auth-spec vs auth-spec）
    2. 归一化后互为前缀（auth-spec vs authentication-spec）
    返回冲突列表，每项包含两个 feature 名和各自的 spec 名。
    """
    if not feature_root.is_dir():
        return []

    # 收集所有 feature 的 spec 名称
    feature_specs: dict[str, list[tuple[str, str]]] = {}  # feature_name -> [(raw_name, normalized_name)]
    for feature_dir in sorted(feature_root.iterdir()):
        if not feature_dir.is_dir():
            continue
        specs_dir = feature_dir / "specs"
        if not specs_dir.is_dir():
            continue
        items = []
        for f in specs_dir.glob("*-spec.md"):
            raw = f.name.removesuffix("-spec.md")
            items.append((raw, normalize_capability(raw)))
        if items:
            feature_specs[feature_dir.name] = items

    conflicts: list[dict] = []
    seen: set[tuple] = set()
    feature_names = sorted(feature_specs.keys())

    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            f1, f2 = feature_names[i], feature_names[j]
            for raw1, norm1 in feature_specs[f1]:
                for raw2, norm2 in feature_specs[f2]:
                    if norm1 == norm2 or is_prefix_of(norm1, norm2):
                        key = tuple(sorted([f1, f2, raw1, raw2]))
                        if key not in seen:
                            seen.add(key)
                            conflicts.append({
                                "feature_a": f1,
                                "spec_a": raw1,
                                "feature_b": f2,
                                "spec_b": raw2,
                                "reason": "identical" if norm1 == norm2 else "prefix_match",
                            })

    return conflicts


def file_has_content(path: Path) -> bool:
    """文件存在且非空"""
    return path.is_file() and path.stat().st_size > 0


def dir_has_pattern(dir_path: Path, pattern: str) -> bool:
    """目录下是否有匹配模式（glob）的文件"""
    return dir_path.is_dir() and list(dir_path.glob(pattern))


def get_spec_items(feature_dir: Path) -> list[str]:
    """列出 specs/ 下的 capability 名称"""
    specs_dir = feature_dir / "specs"
    if not specs_dir.is_dir():
        return []
    return [f.name.removesuffix("-spec.md") for f in specs_dir.glob("*-spec.md") if f.is_file()]


def file_mtime_iso(path: Path) -> str | None:
    """返回文件修改时间的 ISO 8601 字符串"""
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "")


def _artifact_specs(feature_dir: Path) -> list[dict]:
    """生成各 artifact 的元数据，不含状态"""
    proposal_mtime = file_mtime_iso(feature_dir / "proposal.md")
    design_mtime = file_mtime_iso(feature_dir / "design.md")

    return [
        {
            "id": "proposal",
            "file": "proposal.md",
            "dependsOn": [],
            "done": file_has_content(feature_dir / "proposal.md"),
            "lastModified": proposal_mtime,
        },
        {
            "id": "specs",
            "file": "specs/",
            "dependsOn": ["proposal"],
            "done": dir_has_pattern(feature_dir / "specs", "*-spec.md"),
            "items": get_spec_items(feature_dir),
            "lastModified": None,
        },
        {
            "id": "design",
            "file": "design.md",
            "dependsOn": ["proposal"],
            "done": file_has_content(feature_dir / "design.md"),
            "lastModified": design_mtime,
        },
    ]


def derive(feature_dir: str) -> list[dict]:
    base = Path(feature_dir)
    raw = _artifact_specs(base)

    # 按依赖顺序计算状态：先算的 artifact 状态是后算 artifact 的判断依据
    done_ids: set[str] = set()
    for item in raw:
        deps_met = all(d in done_ids for d in item["dependsOn"])
        if item["done"]:
            item["status"] = "done"
            done_ids.add(item["id"])
        elif deps_met:
            item["status"] = "ready"
        else:
            item["status"] = "pending"
        del item["done"]  # 内部字段，不输出

    return raw


if __name__ == "__main__":
    # 定位项目根目录：从脚本位置 (skills/create-spec/scripts/) 向上 3 级
    SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent

    # --detect-conflicts 模式：只输出冲突
    if "--detect-conflicts" in sys.argv:
        feature_root = PROJECT_ROOT / "EdanSpec" / "feature"
        conflicts = detect_spec_conflicts(feature_root)
        print(json.dumps(conflicts, indent=2, ensure_ascii=False))
        sys.exit(0)

    if len(sys.argv) > 1:
        arg = Path(sys.argv[1])
        if not arg.is_absolute():
            arg = PROJECT_ROOT / arg
        result = derive(str(arg))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        root = PROJECT_ROOT / "EdanSpec" / "feature"
        if not root.is_dir():
            print(json.dumps({"error": "EdanSpec/feature/ 目录不存在"}, ensure_ascii=False))
            sys.exit(1)

        features = [d for d in root.iterdir() if d.is_dir()]
        output = {}
        for feature_dir in sorted(features):
            output[feature_dir.name] = derive(str(feature_dir))
        print(json.dumps(output, indent=2, ensure_ascii=False))
