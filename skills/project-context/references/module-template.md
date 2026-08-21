# Module: {ModuleName}

## 阅读入口

{2-4 句话说明模块为什么存在、主要入口、最重要依赖和本图边界。}

## 职责边界

- **负责**：
  - {responsibility}
- **不负责**：
  - {excluded responsibility，由 other-module 负责}

## 公共入口与接口

| 工程入口 | 代码符号/端点 | 调用方 | 用途 | Evidence ID |
|----------|---------------|--------|------|-------------|
| {human-readable entry} | `{Class::method / API / event}` | {caller} | {purpose} | M-001 |

## 核心数据

| 数据/实体/协议 | 读写方式 | 用途 | 位置 | Evidence ID |
|----------------|----------|------|------|-------------|
| `{Type/Table/Message}` | Read / Write / Publish / Subscribe | {purpose} | `{path}` | M-002 |

## L1 核心构件图

```mermaid
flowchart LR
    ENTRY[业务入口<br/>{EntrySymbol}] -->|调用 M-003| ORCH[业务编排<br/>{OrchestratorSymbol}]
    ORCH -->|读取 M-004| MODEL[状态模型<br/>{ModelSymbol}]
    ORCH -->|调用 M-005| OUT[外部边界<br/>{PortSymbol}]
```

### 图例

- 实线：Verified
- 虚线：Graph-Heuristic / Inferred
- 点线到“待确认”：Unknown

> 每张 L1 图 ≤25 个工程构件。节点名称使用“工程职责 + 代码符号”，省略工具类、DTO 和简单包装器。

## 核心构件目录

| 工程职责 | 代码符号 | 类型 | 源码位置 | 模块归属 | Evidence ID |
|----------|----------|------|----------|----------|-------------|
| {responsibility} | `{Symbol}` | Entry / Orchestrator / Model / Repository / Adapter / External | `{path:line}` | {module} | M-006 |

## 跨模块关系

| 方向 | 对方模块 | 关系/协议 | 用途 | Evidence ID |
|------|----------|-----------|------|-------------|
| 入站/出站 | {module} | Direct / REST / gRPC / Event / Data | {purpose} | M-007 |

## 关键业务场景

| 业务流 | 入口 | 结果/副作用 | L2 文档 | Evidence ID |
|--------|------|-------------|---------|-------------|
| {flow-name} | `{entry}` | {result} | [flow.md](flows/{flow-name}.md) | M-008 |

> 没有独立业务流时写“本模块无独立业务流”，不要创建空 `flows/`。

## 配置与运行时装配

| 配置/机制 | 默认/绑定 | 用途 | 证据状态 | Evidence ID |
|-----------|-----------|------|----------|-------------|
| `{config / DI / signal-slot}` | {value/binding} | {purpose} | Verified / Unknown | M-009 |

## L3 证据

| Evidence ID | 事实/关系 | 来源 | 定位 | 证据状态 | 置信度 | 备注 |
|-------------|-----------|------|------|----------|--------|------|
| M-001 | {fact} | CodeGraph / Source / Config | `{path:line or symbol}` | Verified | High | caller→callee |

## 已知盲区

| 盲区 | 影响的构件/关系 | 当前状态 | 补证方法 |
|------|-----------------|----------|----------|
| {dynamic mechanism} | {M-xxx / symbol} | Unknown | {targeted source/runtime/manual check} |

## 与 L0 的一致性

- L0 对本模块的职责描述：{description}
- 已验证的跨模块边：{edges}
- 需要修正 L0 的证据：{none or evidence}
