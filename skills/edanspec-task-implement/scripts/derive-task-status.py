#!/usr/bin/env python3
from __future__ import annotations

# derive-task-status.py — 从文件系统事实推导 taskGraph 状态
# 跨平台：macOS / Windows / Linux
# 用法:
#   python derive-task-status.py                                    # 扫描 EdanSpec/feature/ 下所有活跃 feature
#   python derive-task-status.py EdanSpec/feature/20260518-login    # 指定具体 feature 目录
# 输出: JSON 格式的 taskGraph 数组到 stdout

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def read_tasks_file(feature_dir: Path) -> str | None:
    tasks_path = feature_dir / "tasks.md"
    if not tasks_path.is_file():
        return None
    return tasks_path.read_text(encoding="utf-8")


def parse_tasks_from_markdown(content: str) -> list[dict]:
    """解析 tasks.md 中的任务节点。

    提取: id, title, dependsOn, files, increments[]
    """
    tasks = []
    # 匹配 Task-XXX 标题: ### Task-001：xxx 或 ### Task-001: xxx
    task_pattern = re.compile(
        r"^###\s+(Task-\d+)\s*[:：]\s*(.+)$", re.MULTILINE
    )

    # 匹配前置依赖: **前置依赖**：Task-001，Task-002 或 **前置依赖**：无
    dep_pattern = re.compile(r"\*\*前置依赖\*\*[:：]\s*(.+)$", re.MULTILINE)

    # 匹配涉及文件: **涉及文件**： 后面的列表项
    files_pattern = re.compile(
        r"\*\*涉及文件\*\*[:：]\s*\n((?:- .+\n?)+)", re.MULTILINE
    )

    # 匹配增量 checkbox: - [ ] / - [x] **增量 N**：...
    increment_pattern = re.compile(
        r"- \[([ x])\]\s+\*\*增量\s+(\d+)\*\*[:：]\s*(.*)", re.MULTILINE
    )

    for match in task_pattern.finditer(content):
        task_id = match.group(1)
        title = match.group(2).strip()
        start = match.end()

        # 找到下一个 task 标题或文件结尾作为本任务范围
        next_match = task_pattern.search(content, start)
        task_block = content[start:next_match.start()] if next_match else content[start:]

        # 解析依赖
        deps = []
        dep_match = dep_pattern.search(task_block)
        if dep_match:
            dep_text = dep_match.group(1).strip()
            if dep_text.lower() not in ("无", "none", ""):
                deps = [d.strip() for d in re.split(r"[，,;；]", dep_text) if d.strip()]

        # 解析涉及文件
        files = []
        files_match = files_pattern.search(task_block)
        if files_match:
            files_block = files_match.group(1)
            files = [
                line.strip().lstrip("- ").split(" ")[0].strip().strip("`")
                for line in files_block.strip().split("\n")
                if line.strip().startswith("- ")
            ]

        # 解析增量 checkbox
        increments = []
        for inc_match in increment_pattern.finditer(task_block):
            checked = inc_match.group(1) == "x"
            inc_num = int(inc_match.group(2))
            inc_desc = inc_match.group(3).strip()
            increments.append({
                "number": inc_num,
                "description": inc_desc,
                "done": checked,
            })

        tasks.append({
            "id": task_id,
            "title": title,
            "dependsOn": deps,
            "files": files,
            "increments": increments,
        })

    return tasks


def compute_task_statuses(tasks: list[dict]) -> list[dict]:
    """基于 checkbox 事实和依赖关系计算每个任务的状态。

    按依赖顺序计算，与 derive-artifact-status.py 一致。
    """
    done_ids: set[str] = set()
    result = []

    for task in tasks:
        increments = task["increments"]
        total = len(increments)
        completed = sum(1 for i in increments if i["done"])

        # 依赖是否全部 done
        deps_met = all(d in done_ids for d in task["dependsOn"])

        if total > 0 and completed == total:
            status = "done"
            done_ids.add(task["id"])
        elif completed > 0:
            status = "in_progress"
        elif deps_met:
            status = "ready"
        else:
            status = "pending"

        result.append({
            "id": task["id"],
            "title": task["title"],
            "status": status,
            "dependsOn": task["dependsOn"],
            "files": task["files"],
            "currentIncrement": completed,
            "totalIncrements": total,
            "lastModified": datetime.now(tz=timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", ""),
        })

    return result


def derive(feature_dir: str) -> list[dict]:
    base = Path(feature_dir)
    content = read_tasks_file(base)

    if content is None:
        return []

    tasks = parse_tasks_from_markdown(content)
    return compute_task_statuses(tasks)


if __name__ == "__main__":
    # 定位项目根目录：从脚本位置 (skills/task-implement/scripts/) 向上 3 级
    SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent

    if len(sys.argv) > 1:
        arg = Path(sys.argv[1])
        # 支持相对路径（相对于项目根）和绝对路径
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
