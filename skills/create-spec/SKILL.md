---
name: edanspec:create-spec
description: 为需求创建或更新方案文档（proposal + spec + design）。**触发场景：** 新功能、"做一个XX"、"加个XX"、"继续上次"、"方案调整"、"需求变了"。**不适用：** 一行修复、拼写错误、纯调研。需求简单也建议用——先花 5 分钟确认范围和验收标准，比写完后发现理解偏差返工几小时划算。
---

<!-- SCRIPTS: .claude/skills/create-spec/scripts/ — 正文中统一用 {{SCRIPTS}} 引用 -->

# Create Spec

为需求创建或更新方案文档（proposal + spec + design），一个 feature 目录 = 完整上下文。**先想清楚再动手。**

## 自动识别场景

启动时自动判断当前场景，不要求用户手动选择。

> `{{SCRIPTS}}` 引用自文件顶部 SCRIPTS 锚点。

1. 扫描 `EdanSpec/feature/` 下所有子目录，运行脚本 `{{SCRIPTS}}/derive-artifact-status.py` 获取产物状态
2. 扫描所有 feature 的 `status.json`，收集 `state = "completed"` 的 feature 列表
3. **遗留归档检查**：如果存在已完成的未归档 feature，使用 **AskUserQuestion** 让用户选择：

| 问题 | "有已完成但未归档的 feature：`{列表}`，是否先归档？" |
|------|--------|
| **header** | "遗留归档" |
| **选项 1** | "先归档，再继续" → 引导调用 `edanspec:archive`，归档完成后继续后续流程 |
| **选项 2** | "暂不处理，继续原流程" → 接受，不阻塞，继续自动识别场景分流 |

4. 根据匹配结果分流：

| 检测结果 | 场景 | 下一步 |
|----------|------|--------|
| 无活跃 feature | **新建** | 新建流程 |
| 1 个活跃 feature，对话指向同一需求 | **恢复** | 恢复流程 |
| 1 个活跃 feature，用户描述明显不同的新需求 | **新建** | 确认旧 feature 后创建新的 |
| 2+ 活跃 feature | 歧义 | 列出选项让用户选择 |

判断"同一需求"的依据：用户描述中的关键词与 feature name / proposal.md 标题的语义匹配度。

## 目录结构

```
EdanSpec/feature/{timestamp}-{topic}/
├── proposal.md            # 为什么做、影响范围
├── specs/                 # 需求规格（验收条件）
│   └── {capability}-spec.md
├── design.md              # 技术设计（实现方案）
├── review/                # 正式评审产物（可选）
└── status.json            # 元数据（state / conflicts）
```

产物状态（proposal/specs/design 是否完成）从文件系统事实推导，不写入 status.json。运行脚本 `{{SCRIPTS}}/derive-artifact-status.py` 获取。

## 产物依赖图

```
                proposal
                   │
              ┌────┴────┐
              ▼         ▼
           specs      design
```

`specs` 和 `design` 都依赖 `proposal`，但两者之间无依赖。产物状态由 `{{SCRIPTS}}/derive-artifact-status.py` 从文件存在性自动推导，全部完成 → 引导进入 task-plan。

## 恢复流程

1. 运行 `{{SCRIPTS}}/derive-artifact-status.py <feature-dir>` 获取各 artifact 状态
2. 找到第一个 `ready` 的 artifact → 从它开始继续
3. 全部 done → 方案已完成，引导进入 task-plan
4. 全部 pending → 从零开始

## 变更流程

详见 [references/change-workflow.md](references/change-workflow.md)。用户在已有方案基础上提出修改时：

1. 重新读取 `proposal.md`、`specs/`、`design.md`，理解当前方案全貌
2. 根据用户变更意图，从头生成所有产物——不是局部修改，而是完整重写，确保各文件之间逻辑一致
3. 将旧文件替换为新内容（不追加、不遗留历史标记），保留 git 历史即可追溯差异
4. 完成后展示变更摘要，让用户确认改了什么

## 新建流程

### 步骤 1 — 确认范围

从用户描述中提取：要解决什么问题？涉及哪些模块/文件？有没有约束条件？

信息不够时，按 [references/clarification-guide.md](references/clarification-guide.md) 逐步澄清。描述已清晰则跳过。

### 步骤 2 — 创建 feature 目录和 status.json

```bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NAME="${TIMESTAMP}-${topic}"
mkdir -p "EdanSpec/feature/${NAME}/specs"
mkdir -p "EdanSpec/specs"
mkdir -p "EdanSpec/archive"
```

初始化 `status.json`：

```json
{
  "name": "20260520-user-login",
  "created": "2026-05-20T10:00:00",
  "base_commit": "abc1234",
  "state": "active",
  "designReviewState": "none",
  "conflicts": []
}
```

### 步骤 3 — 冲突检测

生成 specs 前，运行 `{{SCRIPTS}}/derive-artifact-status.py --detect-conflicts`。脚本会扫描所有活跃 feature 的 `specs/`，基于文件名归一化（去连字符/下划线、转小写）和前缀匹配检测冲突（如 `auth-spec.md` vs `authentication-spec.md`）。发现冲突则展示警告，用户确认后记录到 `status.json.conflicts`。

### 步骤 4 — 按依赖图顺序生成产物

依赖顺序：`proposal` → `specs` + `design`（后两者无依赖，可任意顺序）。

**流程**：每次生成一个 artifact 前，运行 `{{SCRIPTS}}/derive-artifact-status.py` 确认依赖已就绪。逐个处理而非并行——每个 artifact 生成时可能需要向用户提问，同时进入澄清阶段会让用户收到多个问题，体验混乱。

#### 步骤 4.1 — 提案（proposal.md）

**前置**：无依赖，第一个生成。

**生成前先分类**：对每个能力判断是 New 还是 Modified。
1. 读取 `EdanSpec/specs/` 下已归档的主规格，了解系统已有哪些能力
2. 在代码库中搜索对应实现（grep 关键词、搜索相关文件）
3. 归档 spec 中存在 或 代码中已实现 → Modified（**包括删除已有功能**），两者都不存在 → New

提案格式，小功能可以极简：

```markdown
# {Topic} 提案

## Why

[1-2 句话，解决什么问题/什么机会]

## What Changes

- [变更要点，列点]

## Capabilities

### New Capabilities
<!-- 新增的能力。每个创建 specs/<name>-spec.md -->
- `<name>`：[此能力覆盖的范围]

### Modified Capabilities
<!-- 需求发生变更的已有能力。每个也需创建 specs/<existing-name>-spec.md，使用 MODIFIED 分区描述变更。无变更则留空或删除此小节 -->
- `<existing-name>`：[哪个需求在变更，变更了什么]

## Impact

- `path/to/file`：[变更内容]
```

#### 步骤 4.2 — 规格（specs/{capability}-spec.md）

**前置**：proposal.md 已生成。

**生成规则**：proposal 中 `New Capabilities` 和 `Modified Capabilities` 下的每一项都必须生成对应的 `specs/<name>-spec.md` 文件，不得遗漏。

**New Capabilities** 使用 `## ADDED Requirements` 分区——描述全新引入的功能和验收条件：

```markdown
# {Capability} 规格

## ADDED Requirements

### Requirement: {名称}

{做什么}。

#### Scenario: {场景名}

- **WHEN** {触发条件}
- **THEN** {预期结果}
```

**Modified Capabilities** 使用 `## MODIFIED Requirements` 分区——描述已有需求中哪些条款在变更，需同时给出变更后的期望行为和回归场景：

```markdown
# {Capability} 规格

## MODIFIED Requirements

### Requirement: {被修改的需求名称}

{变更说明：原行为 → 新行为}。

#### Scenario: {变更场景名}

- **WHEN** {触发条件}
- **THEN** {变更后的预期结果}
```

首次创建且不影响已有能力时，只有 `## ADDED Requirements` 分区。涉及已有能力变更时才会出现 `## MODIFIED Requirements` / `## REMOVED Requirements` / `## RENAMED Requirements` 分区（见 change-workflow.md）。

> **Delta Spec ≠ 主规格**：此处生成的 `specs/{capability}-spec.md` 是增量变更，使用分区标题声明操作类型。归档合并时，分区标题作为操作指令被消耗，需求会被放入主规格（`EdanSpec/specs/`）的 `## Requirements` 扁平容器下。

Spec 是验收条件（what），不是实现方案（how）。代码结构、算法选型、数据库设计属于 design.md。模糊词（"应该""大概""可能"）意味着需求还没有想清楚——每条 spec 必须能被测试验证。

#### 步骤 4.3 — 设计（design.md）

**前置**：proposal.md 已生成（不依赖 specs）。

生成前先读取 [references/design-guide.md](references/design-guide.md)。

已有项目时沿用现有技术栈——自行更换框架会制造技术债和认知维护成本成倍增长。新项目参考 `references/platform-*.md` 逐项确认技术选型。

### 步骤 5 — 完成判定

所有产物生成后：运行 `{{SCRIPTS}}/derive-artifact-status.py` 验证所有条目为 "done" 且文件真实存在 → 评估是否需要 design-review。

触发 design-review 引导的信号（任一满足）：3 个以上模块/文件变更、引入新的第三方依赖、架构层面变更 / 多系统集成 / 跨服务调用、安全/权限模型变更 / 数据库 schema 变更 / 性能有严格要求。

引导话术：
> "检测到架构层面变更，建议先出详细设计方案再拆分任务（如当前环境有 design-review 技能可调用）。也可以先跳过，直接拆分任务。要继续吗？"

- 继续 → 更新 `designReviewState: "recommended"`，引导调用 design-review（如有）
- 跳过 → 更新 `designReviewState: "skipped"`，进入步骤 6
- 无需 review → `designReviewState` 保持 `"none"`，直接进入步骤 6

### 步骤 6 — 下一步

报告产物清单 → 提示调用 `edanspec:task-plan` 技能拆分任务。

## 状态管理

### 产物状态

由 `{{SCRIPTS}}/derive-artifact-status.py` 从文件存在性推导，每次需要时重新运行，不缓存旧状态。三种状态：

| 状态 | 含义 |
|------|------|
| `done` | 文件存在且非空 |
| `ready` | 文件不存在或为空，但依赖已就绪 |
| `pending` | 文件不存在或为空，且依赖未满足 |

计算按依赖顺序进行：proposal → specs/design → 三者都 done 后引导进入 task-plan。

### Feature 生命周期（state）

```
active ──(全部任务+审查完成)──→ completed ──(归档)──→ archived
  │
  └──(用户放弃)──→ abandoned
```

| 值 | 含义 | 何时写入 |
|---|---|---|
| `active` | feature 进行中 | create-spec 初始化 |
| `completed` | 全部任务 + 审查关卡通过，待归档 | task-implement 步骤六完成后 |
| `archived` | 已移入 `EdanSpec/archive/` | archive 移动文件后 |
| `abandoned` | 用户主动放弃 | 用户明确说放弃时 |

## 验证

产物完成后逐项自检，全部打勾后再展示给用户。

### 文件完整性

- [ ] `proposal.md` 存在且非空
- [ ] `specs/` 目录下的 spec 文件数量 = proposal 中 `New Capabilities` + `Modified Capabilities` 的条目总数（不得遗漏）
- [ ] `design.md` 存在且非空
- [ ] 运行 `{{SCRIPTS}}/derive-artifact-status.py` 输出所有 artifact 为 done

### 内容质量

- [ ] `proposal.md` 包含 Why / What Changes / Capabilities / Impact 四个章节
- [ ] Capabilities 分类正确：代码中已有的功能（含删除）归入 Modified，真正从零开始的功能归入 New
- [ ] 每条 spec 描述明确可验证的需求，包含至少一个 `Scenario`
- [ ] spec 中无模糊词（"应该""大概""可能""或许"）
- [ ] spec 使用分区格式（`## ADDED Requirements` 或 `## MODIFIED Requirements`），而非行内标签 `[ADDED]`
- [ ] `design.md` 包含设计目标（Goals）、技术决策（Decisions）、风险与应对
- [ ] `design.md` 中每个技术决策有至少两种方案对比
- [ ] `design.md` 沿用项目已有技术栈，未自行更换框架

### 状态一致性

- [ ] `{{SCRIPTS}}/derive-artifact-status.py` 输出的 artifact 状态与文件存在情况一致

### 流程完整

- [ ] 场景识别正确（新建 / 恢复 / 变更）
- [ ] 新建时已初始化 `status.json`（state=active, conflicts=[]）
- [ ] 变更时完整重写了所有产物（非局部追加、使用分区格式）
- [ ] 恢复时已运行 `{{SCRIPTS}}/derive-artifact-status.py` 获取状态
- [ ] 已评估是否需要 design-review，并正确设置 `designReviewState`

## 常见误区与警示信号

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "需求很清楚了直接写代码吧" | 5 分钟确认比 5 小时返工划算 |
| "spec 写太细了没必要" | spec 不是文档，是可验证的验收条件 |
| "反正后面还会改，现在随便写写" | 方案的价值是写之前想清楚 |

出现以下任一信号时立即停下来修正：用户描述都没读完就开始生成 · spec 里出现"应该""大概"等模糊词 · design 自行更换了项目已有的技术栈 · 未检测冲突就生成 spec。
