# Project Context CodeGraph 知识地图提案

## Why

现有 `project-context` 已尝试使用 CodeGraph，但把它建模为 `query`、`impact`、`stats` 等多工具 CLI，并依赖主 Agent/子 Agent 递归扫描源码。当前上游 `colbymchenry/codegraph` 默认只向 MCP 暴露 `codegraph_explore`，`codegraph init` 在项目根创建 `.codegraph/codegraph.db`，两者契约不一致。

在约 70 万行的工程中，继续依赖目录树、grep 和全文件读取会重复构建 CodeGraph 已有的调用关系，且容易生成节点很多但工程师无法理解的“毛线团”图。需要把 `project-context` 改造成索引优先、证据驱动、分层下钻的知识地图流程，并用真实项目“报警限推荐”完成闭环验证。

## What Changes

- 对齐 `colbymchenry/codegraph` 当前安装、索引、MCP 和 CLI 契约。
- 以 `codegraph_explore` 为主要语义查询入口，CLI `codegraph explore` 作为子 Agent 或 MCP 不可用时的等价回退。
- 将知识地图固定为 L0 系统、L1 模块、L2 业务流、L3 代码证据、L4 影响分析五层。
- 给 Mermaid 图增加节点上限、明确关系语义、证据表、可信度和已知盲区。
- 调整主 Agent 与 `module-explorer`、`flow-explorer` 的职责，避免重复源码扫描和原始上下文回传。
- 修正索引检测与扫描脚本，为大仓库提供快速结构扫描和明确的 CodeGraph 状态。
- 以 Claude Code 目录为唯一源码；OpenCode/Kilo 离线包由打包适配流程派生。
- 安装 CodeGraph，在 `C:\code\new-alarm\nxapp` 执行 `codegraph init`，生成“报警限推荐”项目、模块、业务流和证据文档。
- 执行自动化测试、Skill 校验、三维验证和四维代码审查，修复所有 CRITICAL/IMPORTANT。

## Impact

- `claudecode/.claude/skills/project-context/SKILL.md`：重写 CodeGraph 编排与 L0-L4 工作流。
- `claudecode/.claude/agents/module-explorer.md`：改为消费 CodeGraph 证据并生成 L1/L3 文档。
- `claudecode/.claude/agents/flow-explorer.md`：改为消费 CodeGraph 调用路径并生成 L2/L3 文档。
- `claudecode/.claude/skills/project-context/references/*.md`：加入人类可读图谱、证据和盲区模板。
- `claudecode/.claude/skills/project-context/scripts/scan-project.py`：修正索引检测并支持大仓库快速模式。
- `tests/`：新增或更新项目扫描、Skill 契约和站点产物测试。
- `C:\code\new-alarm\nxapp\.codegraph\`：由 `codegraph init` 创建的本地索引。
- `C:\code\new-alarm\nxapp\EdanSpec\context\`：真实项目知识地图产物。

## Out of Scope

- 修改 `nxapp` 业务代码。
- 将 CodeGraph 数据复制进 Skill 或提交 `.codegraph` 索引。
- 为 CodeGraph 本身修复解析器或调用关系识别缺陷。
- 手工长期维护 Claude Code、OpenCode、Kilo 三份独立 Skill 源码。
