---
name: edanspec-task-implement
description: 依据任务文档执行代码实现。增量式开发 + 测试驱动（TDD），每个增量独立验证后原子提交。触发场景：用户要求开始实现功能或修复 bug、按任务计划执行、继续上次工作。不适用于纯配置变更、文档更新、简单重命名。
---

<!-- SCRIPTS: scripts/（相对本 SKILL.md 所在目录）。脚本双版本：.py（Python 3.7+，优先）与 .cjs（Node.js，无 Python 时），行为一致。正文用 {{SCRIPTS}} 引用 -->

# 任务实现

把任务变成代码。核心原则：**增量开发 + TDD + 原子提交**。

> 概念：**任务**是 plan 阶段的规划单元，**增量**是 implement 阶段的执行单元。一个任务包含一个或多个增量，每个增量独立完成一条验收标准。

```
恢复（从 tasks.md 事实驱动，脚本计算状态）
  ↓
加载（读 tasks.md → 检查依赖 → 判定串行/并行）
  ↓
准备（检测环境命令 → 加载规范 → 内联计划）
  ↓
执行（串行 TDD 循环 或 并行 SubAgent + worktree）
  ↓
提交 + 更新（原子提交 → checkbox）
  ↓
审查关卡（code-review、security-review、verify，全部必须通过）
```

## 状态模型

> `{{SCRIPTS}}` 引用自文件顶部 SCRIPTS 锚点。

任务状态以 `tasks.md` checkbox 为唯一事实来源。优先运行 `{{SCRIPTS}}/derive-task-status.py` 推导，不缓存。脚本不存在时，直接从 tasks.md 手工推导。

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

**检测流程**：`EdanSpec/feature/` 下有活跃工单 → 运行 `{{SCRIPTS}}/derive-task-status.py` 获取 taskGraph 事实状态，脚本不存在则直接解析 tasks.md → 从第一个 `status != "done"` 的任务恢复；无活跃工单 → 继续步骤二。

**恢复操作**：
1. `find EdanSpec/feature/ -maxdepth 1 -mindepth 1 -type d | sort` 定位工单
2. 运行 `{{SCRIPTS}}/derive-task-status.py <feature-dir>` 获取状态（脚本不存在时，手工解析 tasks.md checkbox 推导：全 `[x]` → `done`，部分 `[x]` → `in_progress`，无 `[x]` 且依赖满足 → `ready`，依赖未满足 → `pending`）
3. 从 taskGraph 中找出第一个 `status != "done"` 的任务 → 断点
4. 如果全部 done → 运行 `{{SCRIPTS}}/derive-review-status.py` 检查审查状态，见步骤六
5. 如果 tasks.md 无任务 → 确认是否需要调用 task-plan
6. `git log --oneline -10` + `git status` 确认分支和提交状态
7. 跑一次测试确认代码正常

| 场景 | 操作 |
|------|------|
| taskGraph 全部 done，审查关卡全部 passed | 引导进入 archive |
| taskGraph 全部 done，审查关卡有 pending/failed | 从审查关卡第一个 pending/failed 关卡继续（步骤六） |
| 部分任务 in_progress | 从该任务的 currentIncrement 继续 |
| 有 ready 但未开始 | 从第一个 ready 任务开始 |
| tasks.md 无任务/缺失 | 无任务可执行，确认是否需要调用 task-plan |
| 测试失败 | 调 `edanspec-debugging` 排障 |

**taskGraph 事实来源**：taskGraph 通过脚本从 `tasks.md` 实时计算，不持久化到任何文件。优先运行 `{{SCRIPTS}}/derive-task-status.py`，脚本不存在时手工解析 tasks.md checkbox 推导。

**审查状态事实来源**：通过 `{{SCRIPTS}}/derive-review-status.py` 从报告文件实时解析。报告文件不存在即视为 pending。

**警示信号**：不检查 git 状态就继续、checkbox 与 git 提交不一致却不修正、taskGraph 与 tasks.md 不一致时不重新计算。

---

## 步骤二：加载

读取 `EdanSpec/feature/<name>/tasks.md`，记录验收标准、涉及文件、任务依赖关系。

### 依赖检查

前置未完成 → 停下来先完成依赖。

| 依赖类型 | 检查方法 |
|---------|---------|
| 同 feature 内 | 对应 checkbox 为 `[x]` |
| 跨 feature | 运行 `{{SCRIPTS}}/derive-task-status.py`（不存在则手工解析）确认目标 feature 所有任务为 `done` |

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

**同时确认覆盖率工具已就绪，未就绪不得开始编写测试：**

| 场景 | 操作 |
|------|------|
| 全新项目初始化 | 初始化工程时同步配置覆盖率工具（如 JaCoCo、pytest-cov、Vitest coverage），不得留到后面补 |
| 已有项目 | 检查是否已配置覆盖率工具；未配置则在 `tasks.md` 中增加「配置覆盖率工具」任务，编码前先完成 |
| 覆盖率报告 | 必须能在构建或测试命令中一键生成，见 `references/coverage-check.md` |

### 加载规范

按 `AGENT.md` 映射表加载 `rules/` 下对应规范。spawn 子 Agent 时拼入 prompt。

### 内联计划

编码前用一两行说明思路，让用户有机会纠偏：
```
Plan:
1. 编写 createTask 的失败测试
2. 实现最小版本让测试通过
3. 重构：提取 id 生成逻辑
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

1. **测试通过** — 该增量涉及的测试文件全部通过
2. **构建成功** — 项目可编译
3. **Lint 通过** — 代码风格无违规
4. **类型检查通过** — 无类型错误
5. **覆盖率达标** — 运行覆盖率工具检测，新增/修改文件达到基线要求（详见 `references/coverage-check.md`）

> 覆盖率不得推算，必须实际运行覆盖率工具检测。

**验证分类**：

| 类型 | 执行方式 |
|------|---------|
| 自动化验证（上述 5 项） | Agent 自动执行命令 |
| 手动验证（模拟器操作、UI 视觉检查、完整流程走查） | **跳过，不执行**。Agent 仅执行自动化验证 |

**规则**：
- 自动化验证不通过 → 调 `edanspec-debugging` 排障，不得跳过
- 所有验证均为 Agent 可自动执行的命令验证，无需用户手动确认
- 测试失败 → 调 `edanspec-debugging` 五步排障，不盲目改代码

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

Co-Authored-By: Claude
```

- `git add` 指定文件（禁止 `-A`）
- 提交前 `git status` 确认无无关变更

### 更新状态

增量完成后立即更新，不等全部完成。

| 操作 | 时机 |
|------|------|
| 增量验证通过 → 对应增量改为 `[x]` | 增量验证通过后 |
| 提交后运行脚本重算 taskGraph | 每次提交后 |

**taskGraph 重新计算**：每次提交后运行 `{{SCRIPTS}}/derive-task-status.py`（脚本不存在时手工解析 tasks.md checkbox）获取最新状态。

### 执行循环

每个增量的完整流程是一个循环：

```
执行 TDD → 验证（5 项） → 原子提交 → 更新状态 → 下一个增量
```

循环终止条件：tasks.md 中所有任务的增量 checkbox 均为 `[x]` → 进入步骤六（审查关卡）。

---

## 步骤六：完成后审查关卡

tasks.md 中所有任务完成后，**必须通过三个审查关卡**，全部通过后才算实现完成。

```
tasks.md 全部 done
  ↓
运行 {{SCRIPTS}}/derive-review-status.py 基于报告文件事实检查
  ↓
基于报告文件状态选择下一个 pending/failed 关卡执行
  ├─ code-review（代码审查，四维度）→ 写入 code-review-report.md
  ├─ security-review（安全审查，五维度）→ 写入 security-review-report.md
  └─ verify（三维度验证）→ 写入 verify-report.md
  ↓
allPassed = true → 实现完成，引导归档
```

三个关卡**推荐按 code-review → security-review → verify 顺序执行**，恢复时从任意 pending/failed 关卡继续，已通过的直接跳过。

### 6.1 恢复断点

**审查状态以报告文件为事实来源。** 优先运行 `{{SCRIPTS}}/derive-review-status.py` 推导，脚本不存在时手工检查 feature 目录下是否存在 `code-review-report.md`、`security-review-report.md`、`verify-report.md` 文件并解析内容。

```bash
# 获取当前 feature 的审查状态
python {{SCRIPTS}}/derive-review-status.py EdanSpec/feature/<name>
```

**脚本输出结构：** `{"feature": "<name>", "reviewStatus": { ... }, "allPassed": true/false}`。

| 审查状态 | 操作 |
|---------|------|
| `allPassed = true` | 引导进入 archive |
| 任一关卡 `hasCritical = true` | 自动修复该关卡所有 CRITICAL 问题，修复后删除对应报告文件，重新执行该关卡 |
| 有 pending 关卡 | 执行第一个 pending 关卡（按 code-review → security-review → verify 顺序） |
| 有 passed 关卡 | **直接跳过**，不重复执行。即使 code-review 中已引导过 security-review，仍以报告文件状态为准 |

> **关于重复审查**：code-review 可能识别到安全问题并引导用户单独执行 `edanspec-security-review`。此时 security-review-report.md 可能已存在且状态为 passed。步骤六不再重复执行，直接跳过已通过的关卡。

### 6.2 执行 code-review

调用 `edanspec-code-review` 对当前 feature 的代码变更进行四维度审查。审查完成后报告必须写入 `{feature-dir}/code-review-report.md`。

- **有 CRITICAL** → 展示报告，**自动修复**所有 CRITICAL 问题，修复后删除 `code-review-report.md`，重新执行 code-review
- **无 CRITICAL** → 报告写入 `code-review-report.md`，继续下一阶段

### 6.3 执行 security-review

调用 `edanspec-security-review` 对当前 feature 的代码变更进行五维度安全审查。审查完成后报告必须写入 `{feature-dir}/security-review-report.md`。

- **有 CRITICAL** → 展示报告，**自动修复**所有 CRITICAL 问题，修复后删除 `security-review-report.md`，重新执行 security-review
- **无 CRITICAL** → 报告写入 `security-review-report.md`，继续下一阶段

### 6.4 执行 verify

调用 `edanspec-verify` 对当前 feature 执行三维度验证。verify 通过 task 工具启动通用代理在独立子进程中执行。验证完成后报告必须写入 `{feature-dir}/verify-report.md`。

- **有 CRITICAL** → 展示报告，**自动修复**所有 CRITICAL 问题，修复后删除 `verify-report.md`，重新执行 verify
- **无 CRITICAL** → 报告写入 `verify-report.md`，实现完成

### 6.5 审查完成判定

运行 `{{SCRIPTS}}/derive-review-status.py` 确认 `allPassed = true` → 更新 `status.json`：`state = "completed"`，然后提示用户归档：

使用 **AskUserQuestion 工具**让用户决定：

> "实现完成，全部审查通过。要现在归档这个 feature 吗？归档会合并 Delta Spec 到主规格并清理 feature 目录。"

| 用户选择 | 操作 |
|---------|------|
| 是，归档 | 引导调用 `edanspec-archive` |
| 暂不归档 | 接受，但告知风险："Delta Spec 未合并，后续新 feature 可能产生冲突误判。下次会话可用 `create-spec` 启动检测提醒归档。" |

**任一关卡未执行或未通过 → 不算实现完成。** 恢复时从报告文件推导的 pending/failed 关卡继续。

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
| 8 — 及时更新 | 任务完成后立即更新 tasks.md checkbox，运行脚本重算 taskGraph |
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
- 只更新增量 checkbox，未运行脚本重算 taskGraph
- 任务完成不及时运行脚本重算 taskGraph，恢复时状态不一致
- taskGraph 与 tasks.md checkbox 不一致时不重新运行脚本
- 并行条件不满足时强行并行（项目骨架未完成、文件有交集）
- 覆盖率报告未记录实际数值就提交
- **跳过审查关卡直接归档**（三个关卡必须全部通过，以报告文件状态为准，已通过的不重复执行）
- 报告文件显示有 CRITICAL 时未修复就进入下一阶段

## 验证与引导

**单个任务完成**：所有增量 checkbox 全 `[x]`、测试全通过、已提交、状态已更新。

**全部任务完成**：全量测试通过、构建产物干净、工作区无未提交变更、三个审查关卡全部通过。

**修复上限提醒**（详见 `edanspec-debugging`）：修复次数从尝试次数计数——同一问题修复超过 2 次未成功应停下来重新定位根因（第 3 次，调 `edanspec-debugging`）；超过 3 次应调 `edanspec-explore` 重新审视设计方案（第 4 次）；第 5 次停止并报告问题。

## 辅助资源（按需加载）

- `references/tdd-principles.md` — TDD 循环与测试编写原则
- `references/coverage-check.md` — 覆盖率检查流程与基线标准
- `references/parallel-execution.md` — 并行执行流程与 task prompt 模板
- `references/environment-detection.md` — 构建/测试/lint 命令检测
- `references/slicing-strategies.md` — 任务拆分策略
