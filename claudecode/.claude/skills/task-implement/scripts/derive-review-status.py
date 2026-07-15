#!/usr/bin/env python3
# derive-review-status.py — 从审查报告文件推导审查状态
# 跨平台：macOS / Windows / Linux
# 用法:
#   python derive-review-status.py                                    # 扫描 EdanSpec/feature/ 下所有活跃 feature
#   python derive-review-status.py EdanSpec/feature/20260518-login    # 指定具体 feature 目录
# 输出: JSON 格式的审查状态到 stdout

import json
import os
import re
import sys
from pathlib import Path

REVIEW_FILES = {
    "codeReview":     "code-review-report.md",
    "securityReview": "security-review-report.md",
    "verify":         "verify-report.md",
}


def parse_report(file_path: Path) -> dict | None:
    """解析审查报告文件，提取状态和 findings。

    返回: { "status": "passed"|"failed", "hasCritical": bool,
            "findings": { "critical": N, "important": N, "suggestion": N },
            "lastRun": "..." }
    如果文件不存在或无法解析，返回 None。
    """
    if not file_path.is_file():
        return None

    content = file_path.read_text(encoding="utf-8")

    # 提取各严重度数量：匹配表格中的 CRITICAL/IMPORTANT/SUGGESTION 行
    # 格式: | CRITICAL | N | ...
    critical_match = re.search(r"\|\s*CRITICAL\s*\|\s*(\d+)\s*\|", content)
    important_match = re.search(r"\|\s*IMPORTANT\s*\|\s*(\d+)\s*\|", content)
    suggestion_match = re.search(r"\|\s*SUGGESTION\s*\|\s*(\d+)\s*\|", content)

    critical = int(critical_match.group(1)) if critical_match else 0
    important = int(important_match.group(1)) if important_match else 0
    suggestion = int(suggestion_match.group(1)) if suggestion_match else 0

    # 也尝试从报告表格中提取状态
    # 匹配结论行: | **结论** | APPROVE / REQUEST_CHANGES |
    conclusion_match = re.search(r"\|\s*\*\*结论\*\*\s*\|\s*(\S+)", content)
    if conclusion_match:
        conclusion = conclusion_match.group(1).strip()
        status = "passed" if conclusion == "APPROVE" else "failed"
    else:
        status = "passed" if critical == 0 else "failed"

    # 提取最后运行时间（如果有）
    last_run_match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", content)
    last_run = last_run_match.group(1) if last_run_match else None

    return {
        "status": status,
        "lastRun": last_run,
        "hasCritical": critical > 0,
        "findings": {
            "critical": critical,
            "important": important,
            "suggestion": suggestion,
        },
    }


def derive(feature_dir: Path) -> dict:
    """从 feature 目录下的审查报告文件推导审查状态。"""
    review_status = {}

    for gate_name, filename in REVIEW_FILES.items():
        result = parse_report(feature_dir / filename)
        if result is not None:
            review_status[gate_name] = result
        else:
            review_status[gate_name] = {
                "status": "pending",
                "lastRun": None,
                "hasCritical": False,
                "findings": {"critical": 0, "important": 0, "suggestion": 0},
            }

    return review_status


def all_completed(review_status: dict) -> bool:
    """判断是否全部关卡通过。"""
    for gate in review_status.values():
        if gate["status"] != "passed" or gate["hasCritical"]:
            return False
    return True


if __name__ == "__main__":
    # 定位项目根目录：从脚本位置 (skills/task-implement/scripts/) 向上 3 级
    SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent

    if len(sys.argv) > 1:
        arg = Path(sys.argv[1])
        if not arg.is_absolute():
            arg = PROJECT_ROOT / arg
        feature_dir = arg
        if not feature_dir.is_dir():
            print(json.dumps({"error": f"目录不存在: {feature_dir}"}, ensure_ascii=False))
            sys.exit(1)
        result = derive(feature_dir)
        output = {"feature": feature_dir.name, "reviewStatus": result, "allPassed": all_completed(result)}
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        root = PROJECT_ROOT / "EdanSpec" / "feature"
        if not root.is_dir():
            print(json.dumps({"error": "EdanSpec/feature/ 目录不存在"}, ensure_ascii=False))
            sys.exit(1)

        features = [d for d in root.iterdir() if d.is_dir()]
        output = {}
        for feature_dir in sorted(features):
            review_status = derive(feature_dir)
            output[feature_dir.name] = {
                "reviewStatus": review_status,
                "allPassed": all_completed(review_status),
            }
        print(json.dumps(output, indent=2, ensure_ascii=False))
