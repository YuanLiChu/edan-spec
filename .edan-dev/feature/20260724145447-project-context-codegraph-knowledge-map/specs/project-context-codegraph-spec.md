# Project Context CodeGraph 知识地图规格

## Requirements

### Requirement: 使用真实 CodeGraph 契约 [MODIFIED]

系统 SHALL 以 `colbymchenry/codegraph` 当前官方契约为准，不虚构 MCP 工具或数据库路径。

#### Scenario: 默认 MCP 工具

- **WHEN** CodeGraph MCP 已连接且仅暴露默认工具
- **THEN** Skill 使用 `codegraph_explore` 完成架构、流程和影响查询

#### Scenario: 子 Agent 无 MCP 工具

- **WHEN** 子 Agent 无法直接调用 MCP
- **THEN** Skill 使用等价的 `codegraph explore "<query>"` CLI，而不是递归 grep 全库

#### Scenario: 无索引

- **WHEN** 项目根不存在 `.codegraph/codegraph.db`
- **THEN** Skill 报告索引缺失并建议执行 `codegraph init`
- **THEN** 仅在用户允许降级时使用受限的 Glob/Grep/Read

### Requirement: 分层生成人类可读知识地图 [ADDED]

系统 SHALL 生成 L0-L4 分层知识地图，并限制每张图的复杂度。

#### Scenario: 系统地图

- **WHEN** 生成 `project.md`
- **THEN** L0 图只包含 10-30 个领域、子系统或外部系统节点
- **THEN** 每条边具有明确的调用、依赖、读写、发布或订阅语义

#### Scenario: 模块地图

- **WHEN** 生成 `module.md`
- **THEN** L1 图不超过 25 个核心构件
- **THEN** 节点同时包含工程职责和实际代码符号

#### Scenario: 业务流

- **WHEN** 生成 `flow.md`
- **THEN** L2 图只描述一个业务场景且包含 8-20 个关键节点
- **THEN** 省略 getter、setter、日志和无业务意义的包装层

#### Scenario: 影响分析

- **WHEN** 用户提出修改目标
- **THEN** L4 默认展开两层、最多三层，并区分直接影响、间接影响、运行时风险和测试范围

### Requirement: 所有重要关系可追溯 [ADDED]

系统 SHALL 为重要节点和关系提供源码证据与证据等级。

#### Scenario: CodeGraph 直接证明

- **WHEN** CodeGraph 返回符号、源码和调用路径
- **THEN** 文档将关系标为 `Verified` 并记录源码路径或符号

#### Scenario: CodeGraph 启发式关系

- **WHEN** CodeGraph 明确把动态分派、合成边或启发式关系作为查询线索返回
- **THEN** 文档将关系标为 `Graph-Heuristic`，不得提升为源码直接证明的 `Verified`

#### Scenario: 合理推断

- **WHEN** 关系由命名、目录或多个间接事实推导
- **THEN** 文档将关系标为 `Inferred`，在 Mermaid 中使用虚线，并说明推断依据

#### Scenario: 证据不足

- **WHEN** 动态调用、配置装配、Qt signal/slot、QML/C++ 绑定或宏使关系无法确认
- **THEN** 文档将其标为 `Unknown` 或“待确认”，不得写成事实

### Requirement: 大仓库索引优先 [MODIFIED]

系统 SHALL 在大仓库中优先消费 CodeGraph 压缩事实，只做少量确认性源码读取。

#### Scenario: 70 万行项目

- **WHEN** 项目源码规模约 70 万行
- **THEN** 主 Agent 不全量读取源码或递归 grep 调用链
- **THEN** 扫描脚本可使用快速模式跳过逐文件行数统计
- **THEN** 模块与业务流逐个生成并逐级确认

### Requirement: 主 Agent 与 Explorer 边界清晰 [MODIFIED]

系统 SHALL 避免主 Agent、CodeGraph 和 explorer 重复探索同一代码范围。

#### Scenario: 主 Agent 生成 L0

- **WHEN** 建立项目级地图
- **THEN** 主 Agent使用 CodeGraph 的仓库级查询形成候选模块和跨模块关系
- **THEN** 用户确认边界后才进入 L1

#### Scenario: Explorer 生成专题文档

- **WHEN** `module-explorer` 或 `flow-explorer` 接收任务
- **THEN** 其优先使用传入证据和 CodeGraph 定向查询
- **THEN** 只读取证据缺口对应的最少源码
- **THEN** 只返回结构化摘要，不回传完整文档

### Requirement: 真实项目闭环 [ADDED]

系统 SHALL 在 `C:\code\new-alarm\nxapp` 上完成可复现验证。

#### Scenario: 初始化索引

- **WHEN** CodeGraph 安装完成
- **THEN** 在目标目录执行 `codegraph init`
- **THEN** `.codegraph/codegraph.db` 存在且 `codegraph status` 成功

#### Scenario: 报警限推荐知识地图

- **WHEN** 执行改造后的 `project-context`
- **THEN** 生成项目地图、相关模块地图、报警限推荐业务流和证据表
- **THEN** 产物明确区分 Verified、Graph-Heuristic、Inferred 和 Unknown

### Requirement: 单一源码与跨平台适配 [MODIFIED]

系统 SHALL 以 `claudecode/.claude/` 为 project-context 唯一源码。

#### Scenario: 离线包生成

- **WHEN** 生成 OpenCode 或 Kilo 离线包
- **THEN** 打包流程从 Claude Code 源码复制并做平台路径、名称和 agent 格式适配
- **THEN** 不要求人工同步三份 project-context 内容

### Requirement: 质量闭环 [ADDED]

系统 SHALL 通过自动化测试、Skill 校验、真实产物验证和代码审查。

#### Scenario: 验证失败

- **WHEN** 测试、Skill 校验、文档一致性或代码审查发现 CRITICAL/IMPORTANT
- **THEN** 修复问题并重新执行完整相关验证
- **THEN** 未闭环前不得声明完成
