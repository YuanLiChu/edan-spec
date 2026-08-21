# Impact: {Target}

## 分析目标

- **拟修改对象**：`{symbol/file/contract}`
- **修改目的**：{why}
- **分析深度**：{2，必要时最多 3}
- **CodeGraph 状态**：{version/index.state/projectPath}

## L4 影响图

```mermaid
flowchart LR
    T[修改目标<br/>{Symbol}] -->|直接调用 I-001| D[直接影响<br/>{DirectConsumer}]
    D -->|间接依赖 I-002| N[间接影响<br/>{IndirectConsumer}]
    T -.->|运行时风险 I-003| U[待确认<br/>{DynamicPath}]
```

### 图例

- 实线：Verified
- 虚线：Graph-Heuristic / Inferred
- 点线到“待确认”：Unknown

## 影响清单

| 范围 | 对象 | 影响原因 | 建议动作 | Evidence ID |
|------|------|----------|----------|-------------|
| 直接 | `{symbol/file}` | {原因} | {修改/回归/观察} | I-001 |
| 间接 | `{symbol/file}` | {原因} | {验证} | I-002 |
| 运行时 | `{mechanism}` | {动态关系} | {人工/运行时确认} | I-003 |

## 测试范围

| 测试 | 覆盖风险 | 执行方式 | Evidence ID |
|------|----------|----------|-------------|
| `{test path/name}` | {风险} | {command/manual} | I-004 |

## 证据

| Evidence ID | 事实/关系 | 来源 | 定位 | 证据状态 | 置信度 | 备注 |
|-------------|-----------|------|------|----------|--------|------|
| I-001 | {事实} | CodeGraph | `{path:line}` | Verified | High | caller→callee |

## 已知盲区

| 盲区 | 可能遗漏的影响 | 当前状态 | 补证方法 |
|------|----------------|----------|----------|
| {动态机制} | {范围} | Unknown | {运行时/人工验证} |

## 结论

{用 3-5 条说明最可能破坏的路径、必须执行的测试和仍待确认的风险。}
