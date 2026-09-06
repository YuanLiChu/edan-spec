# 状态模型

## status.json artifactGraph 结构

```json
{
  "artifactGraph": [
    { "id": "proposal", "file": "proposal.md", "status": "done", "dependsOn": [], "lastModified": "2026-05-12T10:00:00" },
    { "id": "specs", "file": "specs/", "status": "ready", "dependsOn": ["proposal"], "items": ["auth"], "lastModified": null },
    { "id": "design", "file": "design.md", "status": "pending", "dependsOn": ["proposal"] }
  ]
}
```

## 状态流转

```
pending → ready → done
  ↑                │
  └──(文件变更)────┘
```

## 状态计算规则

每次读写文件后**必须重新计算**所有 artifact 的 status，不要缓存。

- **`pending`**：初始状态，或依赖未满足（dependsOn 中至少有一个 artifact 的 status 不是 "done"）
- **`ready`**：dependsOn 中所有 artifact 的 status 为 "done"，且本地文件不存在或内容为空
- **`done`**：文件存在且内容非空，用户已确认或接受

## 状态 feature 生命周期

`state` 字段取值与流转：

| 值 | 含义 | 何时写入 |
|---|---|---|
| `active` | feature 进行中 | create-spec 初始化 |
| `completed` | 全部任务 + 审查关卡通过，待归档 | task-implement 步骤六完成后 |
| `archived` | 已移入 `MedSpec/archive/` | archive 移动文件后 |
| `abandoned` | 用户主动放弃 | 用户明确说放弃时 |

```
active ──(全部任务+审查完成)──→ completed ──(归档)──→ archived
  │
  └──(用户放弃)──→ abandoned
```
