---
name: create-spec
description: 创建/恢复/变更 feature 的方案文档。触发场景：准备启动新需求、继续上次工作、需求变更需要更新方案。不适用于一行修复、拼写错误或纯调研分析。
---

# Create Spec

为需求创建或更新方案文档（proposal + spec + design），一个 feature 目录 = 完整上下文。**先想清楚再动手。**

## 自动识别场景

启动时，按以下逻辑自动判断场景，**不要问用户选哪个模式**。

### 第一步：检测活跃 feature

```bash
find .edan-dev/feature/ -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort
```

### 第二步：匹配场景

| 检测结果 | 场景 | 行为 |
|----------|------|------|
| 无任何活跃 feature | **新建** | 跳到「新建流程」 |
| 有 1 个活跃 feature，且对话上下文指向同一需求 | **恢复** | 跳到「恢复流程」 |
| 有 1 个活跃 feature，但用户描述了明显不同的新需求 | **新建** | 确认旧 feature 状态 → 创建新 feature |
| 有 2+ 活跃 feature | 列出让用户选择 | 选恢复或新建 |

> **判断"同一需求"的依据：** 用户描述中的关键词与 feature name / proposal.md 标题的语义匹配度。匹配则恢复，不匹配则新建。

## 目录结构

```
.edan-dev/feature/{timestamp}-{topic}/
├── proposal.md            # 为什么做、影响范围
├── specs/                 # 需求规格
│   └── {capability}-spec.md
├── design.md              # 技术设计
├── review/                # 正式评审产物（可选）
├── tasks.md               # 实施任务清单（task-plan 产出）
└── status.json            # 当前状态（自动生成）
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

- `specs` 和 `design` 都依赖 `proposal`，但两者之间无依赖，可并行
- `proposal` 不可省略，即使只有一两句话也要写
- 所有产物完成 → 引导进入 task-plan

## 状态模型

`status.json` 中的 `artifactGraph` 定义每个产物的生命周期：

```json
{
  "artifactGraph": [
    { "id": "proposal", "file": "proposal.md", "status": "done", "dependsOn": [], "lastModified": "2026-05-12T10:00:00" },
    { "id": "specs", "file": "specs/", "status": "ready", "dependsOn": ["proposal"], "items": ["auth"] },
    { "id": "design", "file": "design.md", "status": "pending", "dependsOn": ["proposal"] }
  ]
}
```

**状态流转：**

```
pending → ready → done
  ↑                │
  └──(文件变更)────┘
```

**状态计算规则：**

- `pending`：初始状态，或依赖未满足
- `ready`：dependsOn 中所有 artifact 的 status 为 done，且本地文件不存在或内容为空
- `draft`：文件存在但内容不完整或需要用户确认，依赖已满足
- `done`：文件存在且内容非空，用户已确认
- 每次读写文件后**必须重新计算**所有 artifact 的 status，不要缓存

## 恢复流程

1. 读 `status.json`，重新计算每个 artifact 的 status（基于文件是否存在 + 依赖关系）
2. 找出第一个 `ready` 的 artifact → 从它开始继续
3. 如果全部 done（proposal + specs + design）→ 告知用户方案已完成，引导进入 task-plan；若 tasks 也 done → 告知任务已拆分完毕，可进入实施阶段
4. 如果全部 pending → 从零开始

```
恢复示例：
  proposal done, specs done, design ready → 直接生成 design.md
  proposal done, specs ready, design ready → 先问用户"先做哪个？"或按 specs→design 顺序
```

## 变更流程

在方案生成过程中或生成后，用户提出需求变更时进入此流程。

### 触发条件

用户表达了以下意图：

- "不对，XX 应该改成..."
- "再加一个 XX"
- "XX 不要了"
- "换个方案，不用 A 用 B"
- "这个需求要调整"

### 变更算法

```
用户提出变更
  ↓
识别影响范围：
  1. 只影响 proposal（意图/范围变了）→ 更新 proposal.md
  2. 影响 spec（新增/修改/删除需求）→ 更新对应 spec
  3. 影响 design（技术方案/决策变了）→ 更新 design.md
  4. 级联影响（需求变了 → 设计也要变）→ 先更新 spec，再更新 design，最后更新 proposal
  ↓
按变更影响自底向上更新：specs(what) → design(how) → proposal(summary)
  ↓
展示变更摘要，用户确认
  ↓
更新 status.json 中对应 artifact 的 lastModified
```

### 变更规则

| 变更类型 | 操作 |
|----------|------|
| **新增能力** | 在对应 spec 中追加 `[ADDED]` 需求；在 design.md 中追加相关决策项；在 proposal.md 的 What Changes 中追加要点 |
| **修改需求** | 在对应 spec 中将原需求标记改为 `[MODIFIED]`；更新 design.md 中相关决策项；如果 proposal 的范围描述变了，同步更新 |
| **删除需求** | 在对应 spec 中将原需求标记改为 `[REMOVED]`；在 design.md 中标记相关决策项为"已废弃"；更新 proposal.md |
| **技术方案变更** | 直接更新 design.md 的对应决策项，追加"变更记录"段落（说明原因、时间）；检查 spec 是否因此需要调整 |
| **范围缩小** | 更新 proposal.md 的 Scope（移到 Out of scope）；不删除已生成的 spec/design，保留历史上下文 |

### 变更示例

```
场景：用户说"登录功能还要支持手机号验证码"

Agent 思考：
- 影响 spec：auth-spec 中新增手机号登录需求 [ADDED]
- 影响 design：技术决策中新增短信服务选型
- 影响 proposal：What Changes 追加"支持手机号验证码登录"

操作顺序：
1. 读 auth-spec.md → 追加手机号登录需求 → 保存
2. 读 design.md → 在技术决策中追加"短信服务"决策项 → 保存
3. 读 proposal.md → 在 What Changes 追加要点 → 保存
4. 更新 status.json 中 specs 和 design 的 lastModified
5. 展示变更摘要
```

**关键规则：**

- **不要删除重做**——在已有文件基础上追加/修改，保留历史上下文
- **级联更新时自底向上**：先改 spec（what），再改 design（how），最后改 proposal（why/what changes summary）
- **每次变更只改受影响的文件**，不碰无关产物
- **变更完成后展示 diff 摘要**，让用户确认改了什么

## 新建流程

### 1. 确认范围

从用户描述中提取初步信息：

- 要解决什么问题？
- 涉及哪些模块/文件？
- 有没有约束条件？

信息不够时，**必须使用 AskUserQuestion 工具逐步澄清**，不要猜，不要用自由文本提问。

**澄清规则：**

- 每次只澄清一个维度，不要一次抛出多个问题
- 提供 2-3 个带预设选项的问题，同时提供 "Other" 让用户自定义
- 如果用户描述已经足够清晰（问题、范围、约束都已明确），跳过澄清直接进入步骤 2
- 最多澄清 3 轮，超过后如果仍有不清楚，列出剩余疑问让用户确认是否继续

**澄清维度优先级：**

1. **问题/目标**（用户描述不清楚时）→ 问"这个功能主要解决什么问题？"
2. **范围/边界**（涉及多个模块时）→ 问"涉及哪些模块/页面？"
3. **约束条件**（性能、兼容性、技术栈）→ 问"有没有性能要求或技术限制？"

**示例：**

用户说"加个登录功能" → 信息不足，开始澄清：

```
AskUserQuestion:
  question: "登录功能主要解决什么问题？"
  options: [
    "现在没有登录，需要用户认证",
    "已有登录但要升级（加短信/OAuth）",
    "登录体验不好，需要优化"
  ]
```

用户回答后，继续下一个维度（如有必要）。所有澄清完成后进入步骤 2。

### 2. 创建 feature

```bash
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NAME="${TIMESTAMP}-${topic}"
mkdir -p ".edan-dev/feature/${NAME}/specs"
mkdir -p ".edan-dev/specs"
mkdir -p ".edan-dev/archive"
```

初始化 `status.json`：

```json
{
  "name": "{topic}",
  "created": "YYYY-MM-DDTHH:mm:ss",
  "base_commit": "当前 HEAD commit SHA",
  "state": "active",
  "artifactGraph": [
    { "id": "proposal", "file": "proposal.md", "status": "pending", "dependsOn": [], "lastModified": null },
    { "id": "specs", "file": "specs/", "status": "pending", "dependsOn": ["proposal"], "items": [], "lastModified": null },
    { "id": "design", "file": "design.md", "status": "pending", "dependsOn": ["proposal"], "lastModified": null }
  ],
  "conflicts": [],
  "review_skipped": false,
  "reviewGate": {
    "codeReview": { "status": "pending", "lastRun": null, "hasCritical": false },
    "securityReview": { "status": "pending", "lastRun": null, "hasCritical": false },
    "verify": { "status": "pending", "lastRun": null, "hasCritical": false }
  },
  "taskGraph": []
}
```

**`state` 字段取值与流转：**

| 值 | 含义 | 何时写入 |
|---|---|---|
| `active` | feature 进行中 | create-spec 初始化 |
| `completed` | 全部任务 + 审查关卡通过，待归档 | task-implement 步骤六完成后 |
| `archived` | 已移入 `.edan-dev/archive/` | archive 移动文件后 |
| `abandoned` | 用户主动放弃 | 用户明确说放弃时 |

```
active ──(全部任务+审查完成)──→ completed ──(归档)──→ archived
  │
  └──(用户放弃)──→ abandoned
```

### 3. 冲突检测

生成 specs 前，扫描活跃 feature 的 `specs/` 目录，检查是否有其他活跃 feature 修改了同一 capability。有冲突则展示警告，用户确认后记录到 `status.json.conflicts`。

### 4. 按依赖图生成产物

**核心循环：**

```
重复直到无 pending 且无 ready 的 artifact：
  1. 读 status.json，重新计算每个 artifact 的 status
  2. 找出所有 status == "ready" 的 artifact
  3. 无 ready → 全部 done 或依赖未满足 → 退出循环
  4. 对每个 ready artifact：
     a. 读取已完成的依赖文件（作为上下文）
     b. 缺失信息澄清（中等/大功能时）：
        - 识别当前产物生成所需的关键缺失信息（性能指标、异常处理、权限、边界条件等）
        - **每次只澄清一个维度**，使用 AskUserQuestion 工具提供 2-3 个预设选项 + Other
        - 不要一次抛出多个问题，等用户回答后再推进
        - 如果信息已充分，跳过澄清直接生成
        - 最多澄清 3 轮，超过后列出剩余疑问让用户确认是否继续
     c. 生成产物（见下方各产物指南）
     d. 验证文件存在且内容非空
     e. 更新 status.json：status → "done"，记录 lastModified
     f. 向用户展示生成摘要
```

#### 4.1 生成 proposal.md

所有功能都必须生成 proposal，小功能可以极简：

```markdown
# {Topic} 提案

## Why

[1-2 句话，解决什么问题/什么机会]

## What Changes

- [变更要点，列点]

## Impact

- `path/to/file`：[变更内容]
```

#### 4.2 生成 specs/{capability}-spec.md

写入 `specs/{capability}-spec.md`：

```markdown
# {Capability} 规格

## Requirements

### Requirement: {名称} [ADDED]

系统 SHALL {做什么}。

#### Scenario: {场景名}

- **WHEN** {触发条件}
- **THEN** {预期结果}
```

### Delta Spec 标记规则

| 标记 | 何时使用 |
|------|---------|
| `[ADDED]` | 新增需求（默认） |
| `[MODIFIED]` | 修改主 spec 中已有的需求 |
| `[REMOVED]` | 删除主 spec 中的需求 |
| `[RENAMED] 原名: X` | 重命名主 spec 中的需求 |

#### 4.3 生成 design.md

先读取 `references/design-guide.md`，再生成技术设计。

已有项目时沿用现有技术栈，不要自作主张换框架。新项目参考 `references/platform-*.md` 逐项确认技术选型。

### 5. 逐章确认

每个文档生成后展示摘要，用户确认后再继续。**不要一次性生成全部。**

### 6. 完成判定

所有产物生成完毕后：

1. 验证 `status.json` 中所有 artifactGraph 条目 status 为 "done"
2. 验证对应文件真实存在
3. 评估复杂度，判断是否需要 design-review

**触发 design-review 引导的信号（满足任一）：**

- 涉及 3 个以上模块/文件的变更
- 引入新的第三方依赖或技术选型
- 涉及架构层面变更
- 涉及多系统集成或跨服务调用
- 涉及安全/权限模型变更
- 涉及数据库 schema 变更或新表
- 性能指标有严格要求

引导话术后，用户选择继续则执行 design-review；跳过则记录 `review_skipped: true`。

### 7. 引导下一步

1. 报告产物清单
2. 提示：**"方案阶段完毕。要开始拆分任务吗？使用 `edan-dev:task-plan` 技能。"**
3. 用户同意则引导调用 task-plan

## 辅助资源（按需加载，不要一次全读）

- `references/design-guide.md` — 设计概要规范，生成 design.md 时读
- `references/platform-{android,flutter,web,frontend,embedded}.md` — 按项目类型读一个

## 常见借口

> 通用借口见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "需求很清楚了直接写代码吧" | 5 分钟确认比 5 小时返工划算 |
| "spec 写太细了没必要" | spec 不是文档，是可验证的验收条件 |
| "反正后面还会改，现在随便写写" | 方案的价值是写之前想清楚 |

## 警示信号

- 用户描述都没读完就开始生成
- spec 里出现"应该""大概"等模糊词
- design 自作主张换了项目已有的技术栈
- 核心文档一次性全部生成
- 未检测冲突就生成 spec
- 生成后未更新 status.json
- **恢复时不读 status.json 就直接重新生成**
- **需求变更时删除文件重做而不是就地修改**
- **级联变更不按依赖顺序更新（应先 spec → design → proposal）**

## 验证

- [ ] 场景识别正确（新建/恢复/变更）
- [ ] feature 目录已创建或已定位
- [ ] status.json 已初始化或已加载
- [ ] artifactGraph 状态与实际文件一致
- [ ] proposal.md 已生成或已更新（如需要）
- [ ] spec.md 已生成或已更新，每条可验证
- [ ] design.md 已生成或已更新，有 Goals 和 Decisions
- [ ] 用户已确认或已接受变更摘要
