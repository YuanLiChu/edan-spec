---
name: edanspec:task-implement
author: yuanlichu
description: 依据任务文档执行代码实现。增量式开发 + 测试驱动（TDD），每个增量独立验证后原子提交。触发场景：用户要求开始实现功能或修复 bug、按任务计划执行、继续上次工作。不适用于纯配置变更、文档更新、简单重命名。
---

# 任务实现

把任务变成代码。核心原则：**增量开发 + TDD + 原子提交**。

> 概念：**任务**是 plan 阶段的规划单元，**增量**是 implement 阶段的执行单元。一个任务包含一个或多个增量，每个增量独立完成一条验收标准。

```
恢复（从 status.json taskGraph 状态驱动）
  ↓
加载（读 tasks.md → 检查依赖 → 判定串行/并行）
  ↓
准备（检测环境命令 → 加载规范 → 内联计划）
  ↓
执行（串行 TDD 循环 或 并行 SubAgent + worktree）
  ↓
提交 + 更新（原子提交 → checkbox → status.json taskGraph）
  ↓
审查关卡（code-review、security-review、verify，全部必须通过）
```

## 状态模型

`status.json` 中的 `taskGraph` 定义每个任务的生命周期：

```json
{
  "taskGraph": [
    {
      "id": "Task-001",
      "title": "用户登录功能",
      "status": "done",
      "dependsOn": [],
      "files": ["src/auth/LoginController.cpp", "tests/unit/auth/LoginControllerTest.cpp"],
      "currentIncrement": 3,
      "totalIncrements": 3,
      "lastModified": "2026-05-12T10:00:00"
    },
    {
      "id": "Task-002",
      "title": "用户注册功能",
      "status": "in_progress",
      "dependsOn": ["Task-001"],
      "files": ["src/auth/RegisterController.cpp", "tests/unit/auth/RegisterControllerTest.cpp"],
      "currentIncrement": 1,
      "totalIncrements": 3,
      "lastModified": "2026-05-12T10:30:00"
    }
  ]
}
```

**状态流转：**

```
pending ──(依赖全done)──→ ready ──(开始执行)──→ in_progress ──(全部增量完成)──→ done
  ↑                                                                                       │
  └────────────────────(回退/修复)────────────────────────────────────────────────────────┘
```

**状态计算规则：**

- `pending`：初始状态，或依赖未满足
- `ready`：dependsOn 中所有任务的 status 为 done
- `in_progress`：正在执行中，有部分增量完成但未全部完成
- `done`：tasks.md 中该任务的所有增量 checkbox 均为 `[x]`
- 每次提交后**必须重新计算**所有任务的 status，不要缓存

## 步骤一：恢复

有活跃 feature 时自动执行，从状态驱动恢复，不依赖会话记忆。

**检测流程**：`EdanSpec/feature/` 下有活跃工单 → 读 `status.json` + `tasks.md` → 从 taskGraph 中第一个 `status != "done"` 的任务恢复；无活跃工单 → 继续步骤二。

**恢复操作**：
1. `find EdanSpec/feature/ -maxdepth 1 -mindepth 1 -type d | sort` 定位工单
2. 读 `status.json`，**重新计算每个任务的 status**（基于 tasks.md checkbox + 依赖关系）
3. 从 taskGraph 中找出第一个 `status != "done"` 的任务 → 断点
4. 如果全部 done → 检查 reviewGate，见步骤六
5. 如果 taskGraph 为空或与 tasks.md 不一致 → 从 tasks.md 重新生成 taskGraph
6. `git log --oneline -10` + `git status` 确认分支和提交状态
7. 跑一次测试确认代码正常

| 场景 | 操作 |
|------|------|
| taskGraph 全部 done，reviewGate 全部 passed | 引导进入 archive |
| taskGraph 全部 done，reviewGate 有 pending/failed | 从 reviewGate 第一个 pending 关卡继续（步骤六） |
| 部分任务 in_progress | 从该任务的 currentIncrement 继续 |
| 有 ready 但未开始 | 从第一个 ready 任务开始 |
| taskGraph 为空/缺失 | 从 tasks.md 重新生成 taskGraph |
| 测试失败 | 调 `edanspec:debugging` 排障 |

> **reviewGate 缺失处理**：如果 `status.json` 中不存在 `reviewGate` 字段（例如跳过了 create-spec 直接调用 task-implement），在步骤六开始前先初始化 reviewGate 为全 pending 状态，参见 create-spec/SKILL.md 中的初始化格式。

**从 tasks.md 重新生成 taskGraph 的规则：**
1. 解析 tasks.md 中所有任务的 ID、标题、依赖关系、涉及文件
2. 解析每个任务的增量 checkbox：全 `[x]` → `done`，部分 `[x]` → `in_progress`，无 `[x]` 且依赖满足 → `ready`，依赖未满足 → `pending`
3. 估算每个任务的增量数（tasks.md 中增量计划的条目数 = 增量数）
4. 写入 status.json

**警示信号**：不检查 git 状态就继续、checkbox 与 git 提交不一致却不修正、taskGraph 与 tasks.md 不一致时不重新计算。

---

## 步骤二：加载

读取 `EdanSpec/feature/<name>/tasks.md`，记录验收标准、涉及文件、任务依赖关系。

### 依赖检查

前置未完成 → 停下来先完成依赖。

| 依赖类型 | 检查方法 |
|---------|---------|
| 同 feature 内 | 对应 checkbox 为 `[x]` |
| 跨 feature | 目标 feature `status.json.state` 为 `archived` 或对应 checkbox 已勾选 |

### 并行判定

**并行组解析**：从 tasks.md 中解析并行关系：
1. 扫描 `<!-- PARALLEL: Task-XXX, Task-YYY -->` 注释，提取并行组
2. 验证并行条件：两个任务可并行当且仅当：
   - 并行组注释中明确列出，且
   - 两者的"涉及的文件"列表无交集，且
   - 前置依赖任务均已完成（checkbox 全 `[x]`）
3. 确定并行组后，向用户报告并确认

**并行执行前置条件**（必须全部满足）：
- 并行任务的**前置依赖任务已全部完成**（checkbox 全 `[x]`）
- 项目已有**基础骨架**（初始化/构建配置已完成，worktree 中可正常编译）
- 两者的文件修改无交集

全部满足 → 标记并行组，走步骤三并行路径。任一不满足 → 串行，走步骤三串行路径，并向用户说明原因。

### 冲突检测

创建 feature 时做过一次冲突检测，但实现阶段可能有新 feature 创建并修改同一 capability。开始编码前再检查一次：

1. 读 `status.json` 的 `conflicts` 字段，确认是否有预记录的冲突
2. 扫描当前 feature 涉及的所有 capability（从 `specs/` 目录或 `design.md` 提取）
3. 检查其他活跃 feature 是否也在修改同一 capability
4. 发现新增冲突 → 提醒用户："当前 feature 与 `{other-features}` 均修改了 `{capability}`，建议确认分工"

冲突不阻塞实现，但必须在归档前解决。

---

## 步骤三：准备

### 检测环境

确定测试、构建、lint 命令。详见 `references/environment-detection.md`。后续所有增量统一使用这组命令。

### 加载规范

按 `AGENT.md` 映射表加载 `rules/` 下对应规范。spawn 子 Agent 时拼入 prompt。

### 内联计划

编码前用一两行说明思路，让用户有机会纠偏：
```
Plan:
1. 编写 FrameValidator 的失败测试
2. 实现最小版本让测试通过
3. 重构：提取校验和计算
→ 开始执行，除非你另有指示。
```

---

## 步骤四：执行

### TDD 循环（串行 + 并行通用）

```
RED（失败测试）→ GREEN（最小实现）→ REFACTOR（重构）→ 验证 → 提交
```

测试必须先写且先失败。实现刚好满足测试通过即可。编写测试前读 `references/tdd-principles.md`。

### 验证规则

每个增量提交前必须通过以下验证，全部必须通过：

1. **测试通过** — 该增量涉及的测试全部通过（`ctest` / GTest / QTest）
2. **构建成功** — `cmake --build` 可编译
3. **格式与静态分析通过** — clang-format；C++ 用 clang-tidy，Qt 代码加 clazy
4. **覆盖率达标** — 运行覆盖率工具检测，新增/修改文件达到基线要求（详见 `references/coverage-check.md`）

> 覆盖率不得推算，必须实际运行覆盖率工具检测。

**验证分类**：

| 类型 | 执行方式 |
|------|---------|
| 自动化验证（上述 4 项） | Agent 自动执行命令 |
| 手动验证（真机操作、UI 视觉检查、完整流程走查） | **跳过，不执行**。Agent 仅执行自动化验证 |

**规则**：
- 自动化验证不通过 → 调 `edanspec:debugging` 排障，不得跳过
- 所有验证均为 Agent 可自动执行的命令验证，无需用户手动确认
- 测试失败 → 调 `edanspec:debugging` 五步排障，不盲目改代码

### 串行路径

每个任务按顺序执行 TDD 循环，每个增量完成后立即提交（见步骤五）。

### 并行路径

详见 `references/parallel-execution.md`。

---

## 步骤五：提交与状态更新

### 原子提交

提交消息格式：
```
feat: 实现任务创建功能

- 新增 createTask 函数
- 完成 Task-001 增量 1, 2
```

- `git add` 指定文件（禁止 `-A`）
- 提交前 `git status` 确认无无关变更

### 更新状态

增量完成后立即更新，不等全部完成。

| 操作 | 时机 |
|------|------|
| 增量验证通过 → 对应增量改为 `[x]` | 增量验证通过后 |
| 更新 taskGraph 中对应任务：`currentIncrement++`、`lastModified` | 每个增量完成后 |
| 重新计算 taskGraph 所有任务 status | 每次提交后 |
| 任务完成（所有增量 `[x]`）→ taskGraph status 改为 `done` | 任务所有增量完成后 |

**taskGraph 重新计算规则：**
1. 遍历每个任务，检查 tasks.md 中该任务的所有增量 checkbox
2. 全部 `[x]` → status = `done`
3. 部分 `[x]` → status = `in_progress`
4. 无 `[x]` 但依赖全 done → status = `ready`
5. 依赖未满足 → status = `pending`
6. 更新 `currentIncrement` = 已完成的增量数量
7. 更新 `totalIncrements` = 总增量数量

### 执行循环

每个增量的完整流程是一个循环：

```
执行 TDD → 验证（测试 / 构建 / 静态分析 / 覆盖率） → 原子提交 → 更新状态 → 下一个增量
```

循环终止条件：tasks.md 中所有任务的增量 checkbox 均为 `[x]` → 进入步骤六（审查关卡）。

---

## 步骤六：完成后审查关卡

tasks.md 中所有任务完成后，**必须通过三个审查关卡**，全部通过后才算实现完成。

```
tasks.md 全部 done
  ↓
基于 reviewGate 状态选择下一个 pending 关卡执行
  ├─ code-review（代码审查，四维度）
  ├─ security-review（安全审查，五维度）
  └─ verify（三维度验证）
  ↓
全部 status = "passed" 且 hasCritical 全 false → 实现完成，引导归档
```

三个关卡**推荐按 code-review → security-review → verify 顺序执行**，恢复时从任意 pending 关卡继续，已通过的直接跳过。

### 6.1 恢复断点

从 `status.json` 的 `reviewGate` 字段恢复：

```json
"reviewGate": {
  "codeReview":     { "status": "passed", "lastRun": "...", "hasCritical": false, "findings": { "critical": 0, "important": 2, "suggestion": 5 } },
  "securityReview": { "status": "pending", "lastRun": null, "hasCritical": false, "findings": { "critical": 0, "important": 0, "suggestion": 0 } },
  "verify":         { "status": "pending", "lastRun": null, "hasCritical": false, "findings": { "critical": 0, "important": 0, "suggestion": 0 } }
}
```

| reviewGate 状态 | 操作 |
|----------------|------|
| 全部 passed 且 hasCritical 全 false | 引导进入 archive |
| 任一 hasCritical=true | 自动修复该关卡所有 CRITICAL 问题，修复后重新执行该关卡 |
| 有 pending 关卡 | 执行第一个 pending 关卡（按 code-review → security-review → verify 顺序） |
| 有 passed 关卡 | **直接跳过**，不重复执行。即使 code-review 中已引导过 security-review，仍以 reviewGate 状态为准 |

> **关于重复审查**：code-review 可能识别到安全问题并引导用户单独执行 `edanspec:security-review`。此时 reviewGate.securityReview 可能已是 `passed`。步骤六不再重复执行，直接跳过已通过的关卡。

### 6.2 执行 code-review

调用 `edanspec:code-review` 对当前 feature 的代码变更进行四维度审查。

- **有 CRITICAL** → 展示报告，**自动修复**所有 CRITICAL 问题，修复后重新执行 code-review
- **无 CRITICAL** → 更新 `reviewGate.codeReview.status = "passed"`、`lastRun` 记录时间、`hasCritical = false`、`findings` 记录各严重度数量，继续下一阶段

### 6.3 执行 security-review

调用 `edanspec:security-review` 对当前 feature 的代码变更进行五维度安全审查。

- **有 CRITICAL** → 展示报告，**自动修复**所有 CRITICAL 问题，修复后重新执行 security-review
- **无 CRITICAL** → 更新 `reviewGate.securityReview.status = "passed"`、`lastRun` 记录时间、`hasCritical = false`、`findings` 记录各严重度数量，继续下一阶段

### 6.4 执行 verify

调用 `edanspec:verify` 对当前 feature 执行三维度验证。

- **有 CRITICAL** → 展示报告，**自动修复**所有 CRITICAL 问题，修复后重新执行 verify
- **无 CRITICAL** → 更新 `reviewGate.verify.status = "passed"`、`lastRun` 记录时间、`hasCritical = false`、`findings` 记录各严重度数量，实现完成

### 6.5 审查完成判定

三个关卡全部 `status = "passed"` 且 `hasCritical = false` → 更新 `status.json`：`state = "completed"`，然后引导用户归档：

> "实现完成，全部审查通过。要现在归档这个 feature 吗？（`edanspec:archive`）"

**任一关卡未执行或未通过 → 不算实现完成。** 恢复时从 reviewGate 的 pending 关卡继续。

---

## 实现规则

| 规则 | 内容 |
|------|------|
| 0 — 简单优先 | 三行重复优于过早抽象 |
| 1 — 范围纪律 | 只改任务涉及的文件，不"顺手" |
| 2 — 单一关注 | 每个增量只做一件事 |
| 3 — 持续可构建 | 每个增量后项目可编译、测试全绿 |
| 4 — Feature Flag | 未完成功能用环境变量隐藏入口 |
| 5 — 可回滚 | 每个增量可独立回退 |
| 6 — 验证必执行 | 每个增量必须通过自动化验证，不可跳过 |
| 7 — 并行有界 | 仅无文件重叠且无依赖时并行，合并后统一验证 |
| 8 — 及时更新 | 任务完成后立即更新 checkbox 和 status.json |
| 9 — 覆盖率必检 | 每个增量完成后必须运行覆盖率工具检测并记录数值，不得推算 |
| 10 — 审查必过 | 全部任务完成后必须通过 code-review、security-review、verify，缺一不算完成 |

---

## 常见误区与反驳

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "顺便重构一下这段代码" | 范围纪律。与任务无关的代码不动 |
| "文档里没提到但应该加上" | 不添加规范外的功能，需回到任务文档更新 |

## 需要警惕

- 超过 100 行代码未执行测试
- 单个增量包含多个无关联改动
- 跳过测试/验证
- **跳过覆盖率检查或凭感觉判断**（必须运行工具检测）
- 修改任务范围之外的文件
- 只更新增量 checkbox，遗漏 taskGraph 状态更新
- 任务完成不及时更新 taskGraph，恢复时状态不一致
- taskGraph 与 tasks.md checkbox 不一致时不重新计算
- 并行条件不满足时强行并行（项目骨架未完成、文件有交集）
- 覆盖率报告未记录实际数值就提交
- **跳过审查关卡直接归档**（三个关卡必须全部通过，但以 reviewGate 状态为准，已通过的不重复执行）
- reviewGate 显示有 CRITICAL 时未修复就进入下一阶段

## 验证与引导

**单个任务完成**：所有增量 checkbox 全 `[x]`、测试全通过、已提交、状态已更新。

**全部任务完成**：全量测试通过、构建产物干净、工作区无未提交变更、三个审查关卡全部通过。

**修复上限提醒**（详见 `edanspec:debugging`）：修复次数从尝试次数计数——同一问题修复超过 2 次未成功应停下来重新定位根因（第 3 次，调 `edanspec:debugging`）；超过 3 次应调 `edanspec:explore` 重新审视设计方案（第 4 次）；第 5 次停止并报告问题。

## 辅助资源（按需加载）

- `references/tdd-principles.md` — TDD 循环与测试编写原则
- `references/coverage-check.md` — 覆盖率检查流程与基线标准
- `references/parallel-execution.md` — 并行执行流程与 SubAgent prompt 模板
- `references/environment-detection.md` — 构建/测试/lint 命令检测
- `references/slicing-strategies.md` — 任务拆分策略
