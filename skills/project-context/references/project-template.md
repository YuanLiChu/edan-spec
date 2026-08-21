# Project: {project-name}

## 阅读入口

{2-4 句话说明系统解决什么问题、从哪个入口读图、当前地图覆盖什么、不覆盖什么。}

## 基本信息

| 属性 | 值 |
|------|-----|
| 名称 | {name} |
| 项目类型 | {monolith / modular-monolith / multi-service / frontend / library / source-snapshot} |
| 技术栈 | {tech-stack-with-versions} |
| 构建工具 | {build-tool} |
| 代码规模 | {file/line summary or Unknown} |
| 分析根目录 | `{absolute-project-path}` |

## CodeGraph 索引健康

| 属性 | 值 |
|------|-----|
| 版本 | {codegraph-version} |
| 索引路径 | `{index-path}` |
| 状态 | {index.state / Unknown} |
| 文件 / 节点 / 边 | {fileCount} / {nodeCount} / {edgeCount} |
| 覆盖语言 | {languages} |
| 待同步 / 待解析 | {pendingChanges / pendingRefs} |
| 工作树匹配 | {worktreeMismatch} |

> 无法从实际命令获得的值写 `Unknown`，不要猜测。

## 基础设施与外部边界

| 类型 | 技术/系统 | 用途 | Evidence ID |
|------|-----------|------|-------------|
| 数据库/缓存/消息/外部服务 | {name} | {purpose} | P-001 |

## L0 系统地图

```mermaid
flowchart LR
    UI[用户入口<br/>{UISubsystem}] -->|调用 P-002| CORE[核心领域<br/>{CoreSubsystem}]
    CORE -->|写入 P-003| DB[(数据存储)]
    CORE -.->|推断 P-004| EXT[外部系统<br/>{ExternalSystem}]
```

### 图例

- 实线：Verified
- 虚线：Graph-Heuristic / Inferred
- 点线到“待确认”：Unknown

> L0 保持 10-30 个领域、子系统和外部边界节点。所有重要边标明关系语义和 Evidence ID。

## 模块索引

| 模块 | 工程职责 | 源码路径 | L1 文档 | 证据状态 |
|------|----------|----------|---------|----------|
| {module-name} | {responsibility} | `{source-path}` | [module.md](modules/{module-name}/module.md) | Verified / Inferred |

## 证据

| Evidence ID | 事实/关系 | 来源 | 定位 | 证据状态 | 置信度 | 备注 |
|-------------|-----------|------|------|----------|--------|------|
| P-001 | {fact} | CodeGraph / Source / Config / Existing Doc | `{path:line or symbol}` | Verified | High | {note} |

## 已知盲区

| 盲区 | 影响的模块/关系 | 当前状态 | 补证方法 |
|------|---------------|----------|----------|
| {dynamic mechanism} | {P-xxx / module} | Unknown | {targeted source/runtime/manual check} |

## 后续下钻

- 建议优先生成的 L1：{modules}
- 建议优先追踪的 L2：{flows}
- 当前未覆盖范围：{out-of-scope}
