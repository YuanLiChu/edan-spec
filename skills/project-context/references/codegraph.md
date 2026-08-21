# CodeGraph 契约与查询指南

本参考针对 `colbymchenry/codegraph`。每次执行仍应以本机 `codegraph version`、`codegraph help` 和 MCP 实际工具列表为准。

## 目录

1. 安装与初始化边界
2. 健康检查
3. 默认 MCP 工具
4. CLI 等价回退
5. 查询模式
6. 降级与禁止项

## 1. 安装与初始化边界

安装 CLI 和初始化项目是外部状态变更，只在用户明确授权时执行。

Windows 可使用官方安装脚本或 npm：

```powershell
irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
# 或
npm install -g @colbymchenry/codegraph
```

安装 CLI 后，`codegraph install` 才负责配置受支持的 Agent MCP。不要在 Skill 中自动修改 Agent 配置。

初始化目标项目：

```powershell
codegraph init "C:\absolute\project"
```

默认索引：

```text
<project>/.codegraph/codegraph.db
```

`CODEGRAPH_DIR` 可覆盖 `.codegraph` 目录名。因此存在性可用于快速提示，最终状态必须以 `codegraph status --json` 为准。

首次初始化使用 `init`。`index` 是已初始化项目的重建命令，不得替代首次 `init`。

## 2. 健康检查

```powershell
codegraph version
codegraph status "C:\absolute\project" --json
```

至少检查：

- `initialized`
- `version`
- `projectPath`
- `indexPath`
- `lastIndexed`
- `fileCount`
- `nodeCount`
- `edgeCount`
- `languages`
- `pendingChanges`
- `worktreeMismatch`
- `index.state`
- `index.pendingRefs`
- `index.reindexRecommended`

状态异常时：

- `initialized=false`：报告并请求是否执行 `init`。
- `worktreeMismatch=true`：确认索引与当前工作树是否对应。
- `pendingChanges` 非空：等待自动同步或按提示处理。
- `reindexRecommended=true`：报告原因；不要自行重建。
- 命令失败：记录 stderr 与退出码，转入受限降级。

## 3. 默认 MCP 工具

当前默认 MCP 只要求：

```text
codegraph_explore
```

输入：

```json
{
  "query": "一个明确的架构、业务流或影响问题",
  "maxFiles": 12,
  "projectPath": "C:\\absolute\\project"
}
```

- `query`：必填。
- `maxFiles`：默认 12；一次只回答一个问题。
- `projectPath`：显式传绝对路径，避免查询错误工程。MCP 无默认工程时该字段会成为必填。

其他工具可能通过 `CODEGRAPH_MCP_TOOLS` 启用，但不是默认契约：

```text
codegraph_node
codegraph_search
codegraph_callers
codegraph_callees
codegraph_impact
codegraph_files
codegraph_status
```

只有实际枚举到工具时才能使用，不得在核心流程中假设它们存在。

## 4. CLI 等价回退

子 Agent、非 MCP Agent 或当前会话未加载 MCP 时：

```powershell
codegraph explore "<query>" --path "C:\absolute\project" --max-files 12
```

该命令和 MCP `codegraph_explore` 使用同一处理逻辑。不要再用多轮 `query` + `impact` 模拟 `explore`。

## 5. 查询模式

### L0 系统边界

```text
Survey the architecture of this repository. Identify entry points, domain or subsystem
boundaries, public interfaces, data stores, external systems, and verified cross-module
dependencies. Return exact symbols/files and distinguish direct graph edges from inferred
grouping. Keep the proposed L0 map within 10-30 nodes.
```

### L1 模块

```text
Explain how <module> works. Identify its responsibility, entry points, public interfaces,
core components, data stores, outbound dependencies, inbound callers, and independent
business flows. Limit the L1 component map to 25 nodes. Return exact source and unresolved
dynamic hops.
```

### L2 业务流

查询中同时命名入口、业务词和终点：

```text
Trace <entry symbol or UI action> through <business terms> to <persistence/external call/UI
update>. Return caller-to-callee paths, data writes, events, callbacks, and failure exits.
Distinguish direct calls, graph heuristics, and unresolved dynamic hops.
```

### L4 影响

```text
Survey the blast radius of changing <symbol or data contract>. Include direct callers,
callees, implementations, affected files, related tests, indirect runtime risks, and
unresolved dynamic relationships. Default to two levels and do not exceed three.
```

### 查询收敛

- 一次只问一个模块、业务流或修改目标。
- query 点名已知符号和文件，减少模糊召回。
- `maxFiles` 默认 12；证据不足时追加第二个定向查询，而不是一次扩大到全库。
- CodeGraph 返回的源码视为已读取，不用 grep 重复验证。
- 只对 QML、宏、配置装配、生成代码和动态跳转做小范围补证。

## 6. 降级与禁止项

允许的降级：

1. 运行 `scan-project.py --fast` 获取确定性结构。
2. 读取构建文件、项目规则和用户指定文档。
3. 在明确模块/目录内执行小范围 Glob/Grep/Read。
4. 将无法证明的关系标为 `Inferred` 或 `Unknown`。

禁止：

- 虚构 MCP 工具或参数。
- 使用不存在的 `codegraph stats`、`codegraph languages`、`impact --db`。
- 把 `query` 的 BM25/FTS score 当作语义置信度。
- 把 impact radius 当作入口到结果的业务调用链。
- 未授权执行安装、Agent 配置、初始化、重建或删除索引。
