---
name: create-spec
description: 创建 feature 目录 + 生成 proposal、spec、design 文档。触发场景：准备启动新需求/功能/修复，用户说「做个新功能」「修复这个 bug」「做个设计」「这个功能怎么设计」「先出方案再写代码」「我想要...」「创建一个 feature」「开干吧」「开始做」「按任务来」。不适用于一行修复、拼写错误或纯调研分析。
---

# Create Spec

为每个独立需求创建隔离的工作目录，并按复杂度生成结构化产物。**一个 feature = 一个目录 = 完整上下文。先想清楚再动手。**

## 目录结构

```
.edan-dev/feature/{timestamp}-{topic}/
├── proposal.md            # 为什么做、影响范围（大功能时生成）
├── specs/                 # 需求规格（中等/大功能时生成）
│   └── {capability}-spec.md
├── design.md              # 技术设计（中等/大功能时生成）
├── review/                # 正式评审产物（由 design-review 产出，可选）
│   ├── solution.md
│   └── detail.md
├── tasks.md               # 实施任务清单（由 task-plan 产出）
└── status.json            # 当前状态（自动生成，不手动编辑）
```

## 何时使用

| 场景 | 操作 |
|------|------|
| 新功能/新模块 | 创建 feature + 生成核心文档（proposal + spec + design） |
| Bug 修复（非一行修复） | 创建 feature + 按需生成 |
| 重构（超过 2 个文件） | 创建 feature + 按需生成 |
| 一行修复/拼写错误 | 不创建，直接改 |
| 快速原型/实验 | 可选 |

## 流程

```
确认范围 → 创建 feature → 按需生成产物 → 冲突检测
                        ↓
    proposal.md + specs/ + design.md → task-plan
```

### 1. 确认范围

从用户描述中提取：
- 要解决什么问题？
- 涉及哪些模块/文件？
- 有没有约束条件（性能、兼容性、已有技术栈）？

信息不够时问 2-3 个澄清问题，不要猜。

### 2. 创建 feature

**自动命名**：用命令生成带时间戳的目录名，不要手动拼接。

```bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NAME="${TIMESTAMP}-${topic}"  # topic 用 kebab-case，从用户描述派生
mkdir -p ".edan-dev/feature/${NAME}/specs"
```

> 例如用户说"加个登录功能" → topic = `login` → 目录名 = `20260507143022-login`

初始化 `status.json`：

```json
{
  "name": "{topic}",
  "created": "YYYY-MM-DDTHH:mm:ss",
  "base_commit": "当前 HEAD commit SHA",
  "artifacts": {
    "proposal": false,
    "specs": [],
    "design": false,
    "tasks": false
  },
  "conflicts": [],
  "review_skipped": false,
  "state": "active"
}
```

| 字段 | 说明 |
|------|------|
| `base_commit` | feature 创建时的 HEAD commit SHA，用于归档时判断哪些 commit 属于此 feature |
| `artifacts.specs` | 已创建的 capability 列表（如 `["auth", "api"]`），非单一 boolean |
| `conflicts` | 与其他活跃 feature 的 spec 冲突记录（如 `[{capability: "auth", other_features: ["feature-A"]}]`） |
| `review_skipped` | 复杂度评估后用户选择跳过 design-review 时标记为 true |

### 3. 冲突检测

创建 feature 后、生成 spec 前，扫描活跃 feature 的 `specs/` 目录：

1. 如果用户指定了涉及的 capability，检查是否有其他活跃 feature 修改了同一 capability（扫描 `feature/*/specs/{capability}-spec.md`）
2. 如果有冲突 → **提前警告用户**："当前 feature-A 也在修改 auth 的 spec，建议确认分工避免冲突"
3. 用户确认后继续。如果确认继续，在 `status.json` 的 `conflicts` 字段记录：`[{capability: "auth", other_features: ["feature-A"]}]`

这一步是**提前发现**，不是阻止创建。归档时才会真正执行合并。完整冲突处理逻辑见 `edan-dev:archive` 步骤 3.3。

### 4. 生成产物

#### 自由问答澄清（中等/大功能时）

识别需求中的模糊点，逐一澄清。每次问一个，提供两三种方案，附带权衡。

**重点澄清：**
- 性能指标（响应时间、并发量、数据量级）
- 异常处理（网络超时、数据为空、并发冲突）
- 权限模型（谁可以做什么）
- 边界条件（最大值、最小值、空值）
- 数据流（输入 → 处理 → 输出 → 存储）

可跳过条件：需求文档已明确以上内容。

**每次生成产物后立即同步 status.json**：proposal → `artifacts.proposal: true`；spec → `artifacts.specs: 添加对应 capability 名`；design → `artifacts.design: true`。

#### 生成 proposal.md（大功能时）

```markdown
# {Topic} 提案

## Why

[1-2 句话，解决什么问题/什么机会]

## What Changes

- [变更要点，列点]

## Impact

- `src/path/to/file`：[变更内容]
```

#### 生成 spec.md

写入 feature 目录 `specs/{capability}-spec.md`（完整路径 `.edan-dev/feature/<name>/specs/`）：

```markdown
# {Capability} 规格

## Requirements

### Requirement: {名称} [ADDED]

系统 SHALL {做什么}。

#### Scenario: {场景名}

- **WHEN** {触发条件}
- **THEN** {预期结果}
```

每条 spec 必须是可验证的——"系统应该快"不行，"接口 p95 < 200ms"可以。

#### Delta Spec 标记规则

feature 中的 spec 是**增量规范（delta spec）**，只描述本次变更的影响。每个需求名后必须标记操作类型：

| 标记 | 何时使用 |
|------|---------|
| `[ADDED]` | 新增需求（默认，不写标记也按 ADDED 处理） |
| `[MODIFIED]` | 修改主 spec 中已有的需求 |
| `[REMOVED]` | 删除主 spec 中的需求（仅需需求名，无需场景） |
| `[RENAMED] 原名: X` | 重命名主 spec 中的需求 |

归档时由 `edan-dev:archive` 根据标记类型将 delta spec 合并到 `.edan-dev/specs/` 下的主 spec。

```
.edan-dev/specs/                       feature 目录
specs/auth-spec.md  ◄────  .edan-dev/feature/xxx/specs/auth-spec.md
  (主 spec，长期维护)              (delta spec，归档时合并)
```

**规则：**
- feature 中的 spec 只描述**本次变更新增/修改/删除/重命名的需求**
- 不复制已有主规范的内容到 feature spec 中
- 多个 feature 可能修改同一个 capability 的 spec，归档时按时间顺序合并

#### 生成 design.md

先读取 `references/design-guide.md` 了解决策记录格式，再生成技术设计：

```markdown
# {Topic} 技术设计

## Context

[当前状态简述]

## Goals / Non-Goals

**Goals：**
- [目标]

**Non-Goals：**
- [明确排除的内容]

## Decisions

### Decision 1: {决策项名称}

**决策**: [具体选择]

**理由**:
- [理由]

**替代方案对比**:
| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| [方案A] | ... | ... | ... |
| [方案B]（首选） | ... | ... | ... |

## Data Model

[数据结构/表设计/接口定义]

## Risks

- [潜在风险和应对措施]
```

**有项目时沿用现有技术栈**，不要自作主张换框架。新项目参考 `references/platform-{android,flutter,web,frontend,embedded}.md` 逐项确认技术选型。

### 5. 逐章确认

每个文档生成后展示摘要，用户确认后再继续。**不要一次性生成全部。**

```
proposal.md 已生成，要点：
- 解决 XX 问题
- 影响 3 个模块

是否继续生成 spec.md？
```

### 复杂度评估与引导

所有文档生成完毕后，评估功能复杂度，判断是否需要 design-review 正式评审：

**触发 design-review 引导的信号（满足任一即可）：**
- 涉及 3 个以上模块/文件的变更
- 引入新的第三方依赖或技术选型
- 涉及架构层面变更（新增层、拆分模块、重构数据流）
- 涉及多系统集成或跨服务调用
- 涉及安全/权限模型变更
- 涉及数据库 schema 变更或新表
- 性能指标有严格要求（p95 < X ms、支持 X 并发等）

**引导话术：**
```
design.md 已生成，要点：
- [设计要点]

当前功能涉及 {N} 个模块变更 + {新技术选型/架构变更}，复杂度较高。
建议执行 `edan-dev:design-review` 做正式评审，产出八章方案 + 详细设计。

是否继续执行 design-review？（或直接继续下一步）
```

用户选择继续则引导执行 `edan-dev:design-review`；用户选择跳过则记录到 status.json 的 `review_skipped: true` 并继续。

## 与 design-review 的关系

| skill | 何时用 | 产出 |
|-------|--------|------|
| **create-spec** | 日常功能/模块设计 | feature + proposal + spec + design（轻量） |
| **design-review** | 用户明确要求评审时 | 八章方案 + 八章详细设计（重量） |

**design-review 是被动入口**——只在用户明确说「出方案」「详细设计」「架构评审」「design review」时执行。启动时检测 feature 下是否已有 create-spec 的产物，缺失则提示用户先执行 create-spec。

## 辅助资源（按需加载，不要一次全读）

- `references/design-guide.md` — 设计概要规范，生成 design.md 时读
- `references/platform-{android,flutter,web,frontend,embedded}.md` — 按项目类型读一个，新项目技术选型时读

## 常见借口

> 通用借口见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "需求很清楚了直接写代码吧" | 5 分钟确认比 5 小时返工划算 |
| "spec 写太细了没必要" | spec 不是文档，是可验证的验收条件 |
| "直接归档不用验证" | 用户明确跳过时可以跳过。但不要自作主张跳过 |

## 警示信号

- 用户描述都没读完就开始生成
- spec 里出现"应该""大概"等模糊词
- design 自作主张换了项目已有的技术栈
- 核心文档一次性全部生成（应该逐章确认）
- 未检测冲突就生成 spec

## 验证

- [ ] feature 目录已创建
- [ ] status.json 已初始化
- [ ] feature 命名符合 `{timestamp}-{topic}` 格式
- [ ] proposal.md 已生成，说明了 Why
- [ ] spec.md 已生成，每条可验证
- [ ] design.md 已生成，有 Goals/Non-Goals 和 Decisions
- [ ] 用户已确认每个文档的内容
