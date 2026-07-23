# EdanSpec Implementation Contract Handoff Implementation Plan

> **For agentic workers:** Execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `review/detail.md` 变成可直接指导编码的实现契约，并闭合 `design-review -> task-plan -> task-implement` 的信息传递。

**Architecture:** 保留现有文件和工作流状态模型。通过模板约束、消费规则和结构测试实现交接门禁，不新增运行时服务或额外 Skill。

**Tech Stack:** Markdown Skills/Templates、Python pytest、Claude Code/OpenCode 分发目录。

---

### Task 1: 建立失败的合同结构测试

**Files:**
- Create: `tests/test_implementation_contract_workflow.py`

- [ ] **Step 1: 写结构测试**

测试必须检查两套平台中的实现契约八章、任务卡必填字段、实现阶段上下文加载与 UI 视觉门禁。

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python -m pytest tests/test_implementation_contract_workflow.py -q`

Expected: FAIL，指出当前模板缺少实现契约章节或下游交接规则。

### Task 2: 升级详细设计模板

**Files:**
- Modify: `claudecode/.claude/skills/design-review/templates/detail-design-template.md`
- Modify: `opencode/.opencode/skills/edanspec-design-review/templates/detail-design-template.md`

- [ ] **Step 1: 用八章实现契约替换通用详细设计**
- [ ] **Step 2: 运行结构测试，确认详细设计相关断言通过**

### Task 3: 改造任务规划合同

**Files:**
- Modify: `claudecode/.claude/skills/task-plan/SKILL.md`
- Modify: `claudecode/.claude/skills/task-plan/templates/task-template.md`
- Modify: `opencode/.opencode/skills/edanspec-task-plan/SKILL.md`
- Modify: `opencode/.opencode/skills/edanspec-task-plan/templates/task-template.md`

- [ ] **Step 1: 增加实现契约编译规则与任务字段**
- [ ] **Step 2: 移除固定三文件/0.5 人天硬限制，改为可验证行为切片**
- [ ] **Step 3: 运行结构测试**

### Task 4: 改造任务实现加载与门禁

**Files:**
- Modify: `claudecode/.claude/skills/task-implement/SKILL.md`
- Modify: `opencode/.opencode/skills/edanspec-task-implement/SKILL.md`

- [ ] **Step 1: 强制加载任务关联的 spec、实现契约和项目上下文**
- [ ] **Step 2: 增加代码锚点/协议漂移门禁**
- [ ] **Step 3: 修正 UI 视觉验收静默跳过行为**
- [ ] **Step 4: 运行结构测试**

### Task 5: 全量验证

**Files:**
- Verify: `tests/`

- [ ] **Step 1: 运行 Python 测试**

Run: `python -m pytest -q`

- [ ] **Step 2: 运行 Node 测试**

Run: `node --test tests/context_browser_app.test.mjs`

- [ ] **Step 3: 检查格式和范围**

Run: `git diff --check`

- [ ] **Step 4: 创建临时实现契约和任务样本，运行结构校验后删除临时产物**

