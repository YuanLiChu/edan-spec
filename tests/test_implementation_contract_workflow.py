from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {
    "root": REPO_ROOT / "skills",
}

DETAIL_HEADINGS = (
    "## 1. 代码基线与现有资产",
    "## 2. 需求到代码追踪",
    "## 3. 文件与符号级变更",
    "## 4. 端到端数据契约",
    "## 5. 生命周期、状态与线程",
    "## 6. 业务流实现合同",
    "## 7. 工程接入",
    "## 8. 验证合同与实现门禁",
)

TASK_CONTRACT_FIELDS = (
    "**实现契约引用**",
    "**复用锚点**",
    "**修改符号**",
    "**输入输出与副作用**",
    "**失败语义**",
    "**允许修改范围**",
    "**禁止修改范围**",
    "**协议/字段映射**",
)


def skill_path(platform: str, skill: str, relative: str = "SKILL.md") -> Path:
    return PLATFORMS[platform] / f"edanspec-{skill}" / relative


def read_skill(platform: str, skill: str, relative: str = "SKILL.md") -> str:
    path = skill_path(platform, skill, relative)
    assert path.is_file(), f"missing skill artifact: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("platform", PLATFORMS)
def test_detail_template_is_an_implementation_contract(platform: str) -> None:
    detail = read_skill(
        platform,
        "design-review",
        "templates/detail-design-template.md",
    )

    for heading in DETAIL_HEADINGS:
        assert heading in detail

    for required_contract in (
        "复用 / 扩展 / 新增",
        "代码证据",
        "需求 ID",
        "源文件",
        "符号",
        "生命周期",
        "线程",
        "失败处理",
        "构建/资源",
        "阻塞实现",
    ):
        assert required_contract in detail


@pytest.mark.parametrize("platform", PLATFORMS)
def test_task_plan_compiles_contract_into_executable_tasks(platform: str) -> None:
    plan_skill = read_skill(platform, "task-plan")
    task_template = read_skill(
        platform,
        "task-plan",
        "templates/task-template.md",
    )

    assert "实现契约编译" in plan_skill
    assert "review/detail.md" in plan_skill
    assert "按可验证业务行为切片" in plan_skill
    assert "每个任务 ≤ 0.5 人天、涉及文件 ≤ 3 个" not in plan_skill

    for field in TASK_CONTRACT_FIELDS:
        assert field in task_template


@pytest.mark.parametrize("platform", PLATFORMS)
def test_task_implement_loads_contract_and_blocks_drift(platform: str) -> None:
    implement_skill = read_skill(platform, "task-implement")

    for required_source in (
        "tasks.md",
        "review/detail.md",
        "specs/",
        "EdanSpec/context/",
    ):
        assert required_source in implement_skill

    for gate in (
        "代码锚点",
        "设计漂移",
        "先更新上游文档",
        "不得开始编码",
    ):
        assert gate in implement_skill


@pytest.mark.parametrize("platform", PLATFORMS)
def test_ui_visual_acceptance_is_never_silently_skipped(platform: str) -> None:
    implement_skill = read_skill(platform, "task-implement")

    assert "UI 视觉检查、完整流程走查） | **跳过，不执行**" not in implement_skill
    assert "视觉验收保持未完成" in implement_skill
    assert "截图" in implement_skill
