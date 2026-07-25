---
name: edanspec:project-context
description: 建立或更新面向工程师的项目知识地图，使用 CodeGraph 索引优先生成 L0 系统、L1 模块、L2 业务流、L3 代码证据和 L4 影响分析文档。触发场景：新项目首次接入、初始化项目、建立/更新知识地图、理解大型代码库、追踪业务流、修改前分析影响。单个 feature 的需求分析使用 explore/create-spec。
---

# Project Context

为工程项目建立可导航、可验证、可增量更新的知识地图。

**核心原则：机器事实优先，分层下钻，证据与推断分离。**

## 事实来源与角色边界

事实优先级：

1. CodeGraph 返回的符号源码、静态关系和调用路径
2. 源码、构建文件、配置和接口定义
3. 现有项目文档
4. 命名或目录结构推断

`project.md`、`module.md` 和 `flow.md` 是人工确认的导航视图，不是压过源码的事实权威。下层证据与上层图冲突时，修正上层图。

| 角色 | 职责 | 禁止 |
|------|------|------|
| 主 Agent | 索引自检、CodeGraph 仓库级查询、L0 边界、用户确认、一致性门禁 | 用递归 grep 重建 CodeGraph 已有关系 |
| `scan-project.py` | 确定性采集构建文件、有限目录树、语言和索引路径 | 判定业务模块或调用关系 |
| `module-explorer` | 基于受限证据生成一个 L1 模块和 L3 证据 | 自由扫描全库、回传全文 |
| `flow-explorer` | 基于受限证据生成一个 L2 业务流和 L3 证据 | 把 impact 当业务调用链、回传全文 |

## 知识地图层级

| 层级 | 产物 | 图谱上限 | 回答的问题 |
|------|------|----------|------------|
| L0 | `EdanSpec/context/project.md` | 10-30 个领域/子系统/外部系统 | 系统由什么组成，边界在哪里 |
| L1 | `modules/{module}/module.md` | 每张图 ≤25 个核心构件 | 模块负责什么，入口、数据和依赖是什么 |
| L2 | `modules/{module}/flows/{flow}.md` | 每张图 8-20 个关键节点 | 一个业务场景如何端到端运行 |
| L3 | module/flow 内的证据附录 | 按需 | 哪些符号和源码证明了图中的关系 |
| L4 | `impacts/{target}.md` | 默认 2 层，最多 3 层 | 修改目标会影响什么，应该验证什么 |

不要生成全库类/函数大图。图中省略 getter/setter、日志、简单包装器、DTO 映射等无工程决策价值的节点。

## 按需加载资源

- CodeGraph 可用时，完整读取 [`references/codegraph.md`](references/codegraph.md)。
- 生成或评审任何图谱前，读取 [`references/evidence-contract.md`](references/evidence-contract.md)。
- 生成对应产物时只读取一个模板：
  - [`references/project-template.md`](references/project-template.md)
  - [`references/module-template.md`](references/module-template.md)
  - [`references/flow-template.md`](references/flow-template.md)
  - [`references/impact-template.md`](references/impact-template.md)
- 完成前读取 [`references/review-checklist.md`](references/review-checklist.md)。

## 执行模式

根据用户目标选择最小范围：

| 模式 | 适用场景 | 执行范围 |
|------|----------|----------|
| Bootstrap | 首次建立完整知识地图 | Step 0 → L0 → 逐模块 L1 → 用户选择 L2 |
| Targeted | 用户指定业务领域/流程 | Step 0 → 最小 L0 → 相关 L1 → 指定 L2/L3 |
| Update | 代码或结构变化 | Step 0 → CodeGraph 变化/影响 → 只更新受影响文档 |
| Impact | 修改前分析 | Step 0 → 指定目标的 L4 |

用户已经明确范围并要求连续执行时，不要在每层重复阻塞询问；记录假设和证据后按 Targeted 模式完成。模块边界存在多个合理答案时必须暂停确认。

## Step 0：目标、上下文与索引自检

### 0.1 确认路径

明确：

- `projectPath`：被分析工程的绝对路径
- `contextPath`：默认 `{projectPath}/EdanSpec/context`
- 本次模式和专题范围

不要把 Skill 所在仓库误当作被分析工程。调用 CodeGraph 时始终显式传 `projectPath`。

### 0.2 检测已有文档

| 状态 | 行为 |
|------|------|
| `contextPath` 不存在 | 建立新地图 |
| 已存在且用户要求更新 | 保留已有文档，只修改受影响部分 |
| 已存在且用户要求重建 | 先列出将替换的文件并获得明确授权 |
| 已存在但意图不明 | 询问“更新、专题补充还是重建” |

不得未经授权删除现有 `context/`。

### 0.3 运行结构扫描

大仓库或已有 CodeGraph 索引时：

```bash
python .claude/skills/project-context/scripts/scan-project.py --fast "<projectPath>"
```

只有确实需要精确行数时才运行完整模式：

```bash
python .claude/skills/project-context/scripts/scan-project.py "<projectPath>"
```

### 0.4 CodeGraph 健康检查

执行：

```bash
codegraph status "<projectPath>" --json
```

检查 `initialized`、`projectPath`、`indexPath`、`fileCount`、`nodeCount`、`edgeCount`、`languages`、`pendingChanges`、`worktreeMismatch` 和 `index.state`。

- 未安装：报告缺失；只有用户明确要求时才安装。
- 未初始化：建议 `codegraph init "<projectPath>"`；只有用户明确授权时执行。
- 建议重建或有待解析引用：先报告状态，再决定是否继续。
- `.codegraph/codegraph.db` 仅是默认路径；健康状态以 `status --json` 为准。

### 0.5 CodeGraph 查询梯

1. 主 Agent 能调用 MCP：

```text
codegraph_explore({
  query: "<一个明确的架构或业务问题>",
  maxFiles: 12,
  projectPath: "<projectPath>"
})
```

2. 子 Agent 或 MCP 不可用：

```bash
codegraph explore "<同一问题>" --path "<projectPath>" --max-files 12
```

3. 仅当具体证据缺失时，对配置、QML、宏、生成代码或动态装配做小范围 Read/Grep。

不要用 grep 复核 CodeGraph 已返回的相同源码。若返回含陈旧提示，按提示读取受影响文件的实时内容。

## Step 1：生成 L0 系统地图

### 1.1 收集候选边界

结合结构扫描和 1-3 个仓库级 `codegraph_explore` 查询识别：

- 入口、路由和外部接口
- 领域/子系统和主要职责
- 公共接口、继承/实现边界
- 数据存储、消息、外部服务
- 高价值跨模块调用
- 测试与工具代码边界

显式构建声明优先于目录猜测。目录聚类只能标为 `Inferred`。

### 1.2 生成 `project.md`

按 project 模板生成：

- 索引健康与覆盖范围
- 10-30 节点 L0 图
- 关系必须带“调用/读取/写入/发布/订阅/实现/包含”等语义
- 模块索引
- 证据摘要与已知盲区

展示模块边界摘要。用户修正后更新 L0，再进入 L1。

## Step 2：生成 L1 模块与 L3 证据

一次只处理一个模块。

### 2.1 准备受限证据包

主 Agent传给 `module-explorer`：

```text
任务：为 {module-name} 生成 L1 module.md 与 L3 证据
projectPath：{absolute-project-path}
modulePath：{module-path}
project.md：{contextPath}/project.md
模板：.claude/skills/project-context/references/module-template.md
CodeGraph 状态：{status 摘要}
已验证线索：{符号/文件/跨模块关系的短列表}
待回答问题：{职责、入口、数据、依赖、业务流}
节点上限：25
```

不要把 CodeGraph 返回的完整源码复制进 prompt，只传符号、路径、关系和待确认项。

### 2.2 Explorer 输出

`module-explorer` 写入：

```text
{contextPath}/modules/{module-name}/module.md
```

主 Agent只接收摘要：职责、核心构件数、证据覆盖、Unknown、业务流索引、跨模块依赖和冲突。

### 2.3 一致性门禁

- L1 与 L0 冲突 → 以证据修正 L0，不强迫 L1 服从旧图。
- 核心构件图 >25 → 拆成多个图或保留入口/边界构件。
- 重要边无 Evidence ID → 降级为 Inferred/Unknown 或补证。

## Step 3：生成 L2 业务流与 L3 证据

一次只处理一个业务场景。业务流不是 impact radius。

### 3.1 准备受限证据包

主 Agent传给 `flow-explorer`：

```text
任务：为 {flow-name} 生成 L2 flow.md 与 L3 证据
projectPath：{absolute-project-path}
module.md：{module-doc-path}
模板：.claude/skills/project-context/references/flow-template.md
入口线索：{入口符号/API/UI 动作/事件}
终点线索：{持久化/外部调用/返回/UI 更新}
已验证路径：{CodeGraph 返回的短关系列表}
动态缺口：{事件、回调、Qt/QML、配置装配等}
节点上限：20
```

### 3.2 Flow 规则

- L2 必须从明确入口到明确结果。
- 记录 caller→callee 方向、同步/异步、事件、数据读写。
- L2 核心入口应回链到 L1；流程专属、跨模块和外部节点不要求全部出现在 L1。
- 新发现的模块核心构件应先增量更新 L1，再标为 Verified。
- 关键动态跳转无法证明时使用 Unknown，不补造边。

### 3.3 Explorer 输出

写入：

```text
{contextPath}/modules/{module-name}/flows/{flow-name}.md
```

主 Agent抽查节点数、证据覆盖、Unknown 和入口到结果的连续性。

## Step 4：按需生成 L4 影响分析

用户提出具体修改目标时，按 impact 模板生成：

```text
{contextPath}/impacts/{target}.md
```

默认两层，最多 3 层。区分：

- 直接调用/实现/数据契约影响
- 间接依赖
- 动态运行时风险
- 相关测试
- CodeGraph 无法确认的范围

优先使用 `codegraph_explore` 的 blast-radius 摘要。只有实际枚举到可选 `codegraph_impact` 时才可调用它；不得把结果冒充端到端业务流。

## 增量更新

| 变化 | 更新 |
|------|------|
| 新增/删除/拆分/合并模块 | 更新 L0，再更新受影响 L1 |
| 核心构件变化 | 更新 L1，检查相关 L2 |
| 新增/删除业务流 | 更新 L1 业务流索引和对应 L2 |
| 入口、接口或数据契约变化 | 用 L4 定位影响，再更新相关 L1/L2/L3 |
| 技术栈或外部系统变化 | 更新 L0 基本信息、边界和盲区 |

保留历史文档；删除或重建必须获得明确授权。废弃文档在顶部标记原因和日期。

## 完成与评审

完成前读取 review checklist，并验证：

- 运行 `python .claude/skills/project-context/scripts/validate_context.py "<contextPath>" --json`，修复全部 error。
- 所有产物路径和链接存在。
- L0/L1/L2 不超过节点上限，所有重要边有语义。
- Evidence ID 唯一，状态只使用 `Verified`、`Graph-Heuristic`、`Inferred`、`Unknown`。
- 搜索 score 未被当作置信度。
- QML/C++、Qt signal/slot、宏、反射、依赖注入、配置装配和生成代码等盲区已说明。
- project/module/flow 冲突已经按证据修正。
- 只向用户报告实际生成和实际验证过的产物。

完成报告包含：

```markdown
- L0：{project.md}
- L1：{module 文档列表}
- L2：{flow 文档列表}
- L3：{证据覆盖与 Unknown 数}
- L4：{影响文档列表或“未请求”}
- CodeGraph：{版本、索引状态、覆盖语言}
- 评审：{通过项、遗留 Unknown、建议人工确认项}
```

## 警示信号

- 写死默认不存在的 MCP 工具。
- 使用 `codegraph stats`、`codegraph languages` 或 `impact --db`。
- 把 `query` score 描述为语义置信度。
- 把 impact radius 当成业务调用链。
- CodeGraph 已覆盖却递归 grep/read 同一代码范围。
- 仅按目录生成架构并标为 Verified。
- 为满足 L1 图上限而删除真实 L2 节点。
- 让所有 L2 节点强制成为 L1 类图子集。
- 生成图后没有证据表、图例或已知盲区。
