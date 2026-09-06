---
name: meddev:create-spec
author: yuanlichu
description: 为需求创建或更新方案文档（proposal + spec + design）。**触发场景：** 新功能、"做一个XX"、"加个XX"、"继续上次"、"方案调整"、"需求变了"。**不适用：** 一行修复、拼写错误、纯调研。需求简单也建议用——先花 5 分钟确认范围和验收标准，比写完后发现理解偏差返工几小时划算。
---

# Create Spec

为需求创建或更新方案文档（proposal + spec + design），一个 feature 目录 = 完整上下文。**先想清楚再动手。**

## 自动识别场景

启动时自动判断当前场景，不要求用户手动选择。

1. 扫描 `MedSpec/feature/` 下所有子目录，查找 `state: "active"` 的 feature
2. 根据匹配结果分流：

| 检测结果 | 场景 | 下一步 |
|----------|------|--------|
| 无活跃 feature | **新建** | 新建流程 |
| 1 个活跃 feature，对话指向同一需求 | **恢复** | 恢复流程 |
| 1 个活跃 feature，用户描述明显不同的新需求 | **新建** | 确认旧 feature 后创建新的 |
| 2+ 活跃 feature | 歧义 | 列出选项让用户选择 |

判断"同一需求"的依据：用户描述中的关键词与 feature name / proposal.md 标题的语义匹配度。

## 目录结构

```
MedSpec/feature/{timestamp}-{topic}/
├── proposal.md            # 为什么做、影响范围
├── specs/                 # 需求规格（验收条件）
│   └── {capability}-spec.md
├── design.md              # 技术设计（实现方案）
├── review/                # 正式评审产物（可选）
├── tasks.md               # 实施任务清单（task-plan 产出）
└── status.json            # 当前状态
```

## 产物依赖图

```
                proposal
                   │
              ┌────┴────┐
              ▼         ▼
           specs      design
              │         │
              └────┬────┘
                   ▼
            task-plan（下一阶段）
```

`specs` 和 `design` 都依赖 `proposal`，但两者之间无依赖。每个产物完成后更新 `status.json`，全部完成 → 引导进入 task-plan。

## 恢复流程

1. 读 `status.json`，重新计算每个 artifact 的 status（详见 [references/status-model.md](references/status-model.md)）
2. 找到第一个 `ready` 的 artifact → 从它开始继续
3. 全部 done → 方案已完成，引导进入 task-plan
4. 全部 pending → 从零开始

## 变更流程

详见 [references/change-workflow.md](references/change-workflow.md)。用户在已有方案基础上提出修改时：

1. 重新读取 `proposal.md`、`specs/`、`design.md`，理解当前方案全貌
2. 根据用户变更意图，从头生成所有产物——不是局部修改，而是完整重写，确保各文件之间逻辑一致
3. 将旧文件替换为新内容（不追加、不标记 `[REMOVED]`），保留 git 历史即可追溯差异
4. 完成后展示变更摘要，让用户确认改了什么

## 新建流程

### 步骤 1 — 确认范围

从用户描述中提取：要解决什么问题？涉及哪些模块/文件？有没有约束条件？

信息不够时，按 [references/clarification-guide.md](references/clarification-guide.md) 逐步澄清（`AskUserQuestion` 工具，每次一个维度，最多 3 轮）。描述已清晰则跳过。

### 步骤 2 — 创建 feature 目录和 status.json

```bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NAME="${TIMESTAMP}-${topic}"
mkdir -p "MedSpec/feature/${NAME}/specs"
mkdir -p "MedSpec/specs"
mkdir -p "MedSpec/archive"
```

初始化 `status.json`，包含 `name`、`created`、`base_commit`、`state: "active"`、`artifactGraph`（proposal / specs / design 三条记录，均 `pending`）、`designReviewState: "none"`、`reviewGate`（三个 review 均 `pending`）、`taskGraph: []`。字段详情见 [references/status-model.md](references/status-model.md)。

### 步骤 3 — 冲突检测

生成 specs 前，扫描所有活跃 feature 的 `specs/` 目录。文件名相同或语义相近（如 `auth-spec.md` vs `authentication-spec.md`）视为同一 capability。发现冲突则展示警告，用户确认后记录到 `status.json.conflicts`。

### 步骤 4 — 按依赖图顺序生成产物

循环：重新计算 status → 找出 `ready` 的 artifact → 逐个处理（读取依赖上下文 → 按需澄清 → 生成 → 更新 status 为 done）。顺序处理而非并行，是因为每个 artifact 生成时可能需要向用户提问，同时进入澄清阶段会让用户收到多个问题，体验混乱。

#### proposal.md

所有功能都必须有 proposal，小功能可以极简：

```markdown
# {Topic} 提案

## Why

[1-2 句话，解决什么问题/什么机会]

## What Changes

- [变更要点，列点]

## Impact

- `path/to/file`：[变更内容]
```

#### specs/{capability}-spec.md

```markdown
# {Capability} 规格

## Requirements

### Requirement: {名称} [ADDED]

系统 SHALL {做什么}。

#### Scenario: {场景名}

- **WHEN** {触发条件}
- **THEN** {预期结果}
```

Spec 是验收条件（what），不是实现方案（how）。代码结构、算法选型、数据库设计属于 design.md。模糊词（"应该""大概""可能"）意味着需求还没有想清楚——每条 spec 必须能被测试验证。

#### design.md

生成前先读取 [references/design-guide.md](references/design-guide.md)。

已有项目时沿用现有技术栈——自行更换框架会在团队中制造技术债和认知分裂，也让后续维护成本成倍增长。新项目参考 `references/platform-qt.md` 或 `references/platform-embedded.md` 逐项确认技术选型。

### 步骤 5 — 完成判定

所有产物生成后：验证 status.json 中所有条目为 "done" 且文件真实存在 → 评估是否需要 design-review。

触发 design-review 引导的信号（任一满足）：3 个以上模块/文件变更、引入新的第三方依赖、架构层面变更 / 多系统集成 / 跨服务调用、安全/权限模型变更 / 数据库 schema 变更 / 性能有严格要求。

引导话术：
> "检测到架构层面变更，建议执行 `meddev:design-review` 出详细方案后再拆分任务。也可以先跳过，直接拆分任务。要继续吗？"

- 继续 → 更新 `designReviewState: "recommended"`，引导调用 design-review
- 跳过 → 更新 `designReviewState: "skipped"`，进入步骤 6
- 无需 review → `designReviewState` 保持 `"none"`，直接进入步骤 6

### 步骤 6 — 下一步

报告产物清单 → 提示调用 `meddev:task-plan` 技能拆分任务。

## 状态管理

详见 [references/status-model.md](references/status-model.md)。核心规则：状态流转 `pending → ready → done`，文件变更后回滚到 `ready`。每次读写文件后重新计算 status，不缓存旧状态。

## 验证

产物完成后逐项自检，全部打勾后再展示给用户。

### 文件完整性

- [ ] `status.json` 存在且是有效 JSON
- [ ] `proposal.md` 存在且非空
- [ ] `specs/` 目录下至少有一个 `{capability}-spec.md`
- [ ] `design.md` 存在且非空

### 内容质量

- [ ] `proposal.md` 包含 Why / What Changes / Impact 三个章节
- [ ] 每条 spec 使用 `SHALL` 描述需求，包含至少一个 `Scenario`
- [ ] spec 中无模糊词（"应该""大概""可能""或许"）
- [ ] `design.md` 包含设计目标（Goals）、技术决策（Decisions）、风险与应对
- [ ] `design.md` 中每个技术决策有至少两种方案对比
- [ ] `design.md` 沿用项目已有技术栈，未自行更换框架

### 状态一致性

- [ ] `status.json` 中 `artifactGraph` 的每个条目 `status` 与实际文件存在情况一致
- [ ] `artifactGraph` 中 `dependsOn` 指向的依赖项 `status` 均为 `done`
- [ ] 冲突检测结果（如有）已记录到 `status.json.conflicts`

### 流程完整

- [ ] 场景识别正确（新建 / 恢复 / 变更）
- [ ] 新建时已初始化 `status.json`（state=active, artifactGraph 三条 pending 记录）
- [ ] 变更时完整重写了所有产物（非局部追加、无 [REMOVED] 等历史标记）
- [ ] 恢复时已读取 `status.json` 并重新计算状态
- [ ] 已评估是否需要 design-review，并正确设置 `designReviewState`

## 常见误区与警示信号

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "需求很清楚了直接写代码吧" | 5 分钟确认比 5 小时返工划算 |
| "spec 写太细了没必要" | spec 不是文档，是可验证的验收条件 |
| "反正后面还会改，现在随便写写" | 方案的价值是写之前想清楚 |

出现以下任一信号时立即停下来修正：用户描述都没读完就开始生成 · spec 里出现"应该""大概"等模糊词 · design 自行更换了项目已有的技术栈 · 未检测冲突就生成 spec · 生成后未更新 status.json。
