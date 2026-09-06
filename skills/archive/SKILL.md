---
name: edanspec:archive
author: yuanlichu
description: 归档已完成的 feature——引导验证（可选）、delta spec 合并、移动到归档目录。触发场景：feature 完成准备归档、用户说「归档这个」「看看能归档哪些」「归档」。不适用于未完成或有 CRITICAL 问题的 feature。
---

# Feature 归档

把已完成的 feature 安全移入归档目录。**先验证，再合并，最后归档。**

`edanspec:archive` 的职责：检查关卡状态 → 引导验证 → 合并 delta spec → 移动文件。
`edanspec:verify` 只负责三维度验证并输出报告，**不合并 spec、不移动文件**，可独立调用。

## 执行流程

```
确认目标 feature
  → 检查 reviewGate 状态
      ├─ verify = pending          → 引导调用 edanspec:verify，完成后继续
      ├─ codeReview/securityReview = pending/failed → 引导回退 edanspec:task-implement
      ├─ verify = failed           → 拒绝归档，展示报告
      ├─ verify = passed + IMPORTANT > 0 → 展示报告，用户确认后继续
      └─ 全部 passed               → 进入 delta spec 合并
  → delta spec 合并 → 冲突检测
  → 移动到 EdanSpec/archive/
```

## 1. 确认目标

用户指定了 feature 名称则直接使用。否则列出所有活跃 feature 供选择：

```bash
find EdanSpec/feature/ -maxdepth 1 -mindepth 1 -type d | sort
```

读取每个 feature 的 `status.json` 和 `tasks.md` 显示完成状态。

## 2. 检查关卡状态

读取 `status.json` 中的 `reviewGate` 字段，按以下分支处理：

| reviewGate 状态 | 操作 |
|-----------------|------|
| `verify.status = pending` | 引导用户调用 `edanspec:verify`，等待完成后继续 |
| `codeReview` 或 `securityReview` 为 pending/failed | 引导用户调用 `edanspec:task-implement` 完成剩余关卡 |
| `verify.status = failed` 或 `verify.findings.critical > 0` | 拒绝归档，展示报告 |
| `verify.status = passed` 且 `verify.findings.important > 0` | 展示报告，告知 `{verify.findings.important}` 个 IMPORTANT 建议，用户确认后继续 |
| 全部 passed | 展示审查和验证报告摘要，进入步骤 3 |

## 3. 合并 Delta Spec

### 3.1 概念

每个 feature 中的 spec 是**增量变更**，不是完整规范的副本：

```
EdanSpec/specs/                          EdanSpec/feature/xxx/specs/
├── auth-spec.md      ◄──── delta spec ──├── auth-spec.md
└── api-spec.md       ◄──── delta spec ──└── api-spec.md
    (主 spec / 权威)                         (delta spec / 增量)
```

- **主 spec**：`EdanSpec/specs/` 下的权威需求规格，长期维护
- **delta spec**：feature 中仅包含本次变更**新增/修改/删除/重命名**的需求

### 3.2 合并步骤

```
确保 EdanSpec/specs/ 目录存在

对 feature 中每个 delta spec（specs/{capability}-spec.md）：
  ├─ 主 spec 不存在 → 直接复制到 EdanSpec/specs/
  └─ 主 spec 存在 →
     ├─ 提取每个需求的操作类型（见 3.3 格式约定）
     ├─ ADDED    → 追加到主 spec 末尾
     ├─ MODIFIED → 按需求名匹配，替换整块
     ├─ REMOVED  → 从主 spec 删除对应需求
     └─ RENAMED  → 更新需求名，内容不变
```

### 3.3 Delta Spec 格式约定

需求块**必须在需求名后标记操作类型**：

```markdown
# {Capability} 规格

### Requirement: 用户登录 [ADDED]
系统 SHALL 支持用户名密码登录。

### Requirement: 密码复杂度 [MODIFIED]
系统 SHALL 要求密码至少 8 位，包含大小写字母和数字。

### Requirement: 邮箱验证 [REMOVED]

### Requirement: 用户名限制 [RENAMED] 原名: 用户名长度
```

| 标记 | 合并行为 |
|------|---------|
| `[ADDED]` | 追加到主 spec 末尾 |
| `[MODIFIED]` | 按需求名匹配，替换整块 |
| `[REMOVED]` | 从主 spec 删除对应需求 |
| `[RENAMED] 原名: X` | 主 spec 中改名，内容不变 |
| 无标记 | 视为 ADDED |

需求块范围：从 `### Requirement:` 到下一个 `### Requirement:` 或文件末尾。

### 3.4 冲突检测

合并前扫描是否有其他活跃 feature 修改了同一 capability：

1. 读当前 feature 的 `status.json`，检查 `conflicts` 字段
2. 扫描所有活跃 feature 的 `specs/`，构建 `capability → [feature 列表]` 映射
3. 某 capability 被 2+ 个 feature 修改 → 存在冲突

| 情况 | 处理 |
|------|------|
| 仅当前 feature 修改此 capability | 正常合并 |
| 多 feature 修改，但仅当前 feature 实现了代码 | 只合并当前 delta，警告用户 |
| 多 feature 都实现了代码 | 按创建时间依次合并（先建优先，后建覆盖） |
| 多 feature 都没实现代码 | 跳过合并，警告用户 |

"是否实现代码"：比较 `base_commit` 与 HEAD 的 diff，含 `.cpp/.cc/.cxx/.h/.hpp/.qml/.ui/.qrc/.cmake` 等源码或构建文件修改视为已实现，仅 `.md/.json` 变更视为未实现。

## 4. 移动到归档目录

```bash
mkdir -p EdanSpec/archive
mv EdanSpec/feature/{name} EdanSpec/archive/
```

移动后更新 `status.json`：`state = "archived"`。

归档前最终确认：
- [ ] reviewGate 三个关卡全部 passed
- [ ] delta spec 已合并（或无 delta spec）
- [ ] tasks.md 所有 checkbox 已勾选
- [ ] 代码已提交

## 常见误区与反驳

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "直接归档不用验证" | 验证未 passed 不能归档。引导去跑 verify，不要自作主张跳过 |
| "delta spec 后面再合并也行" | 归档后找回来合并更难。现在合并只需 2 分钟 |

## 警示信号

- verify 为 pending 时未引导就直接归档
- 主动执行验证而非引导用户调用 verify
- verify 为 failed 仍批准归档
- 合并 delta spec 时覆盖主 spec 已有内容
- 未检测冲突就移动文件
- 合并前未确保 `EdanSpec/specs/` 目录存在

## 验证

- [ ] 目标 feature 已确认
- [ ] reviewGate.verify.status 为 passed
- [ ] reviewGate 有 pending 时已引导至对应 skill
- [ ] reviewGate.verify 为 failed 时已拒绝归档
- [ ] IMPORTANT findings 已告知用户
- [ ] delta spec 已合并（或确认无 delta spec）
- [ ] `EdanSpec/specs/` 存在且 delta 已正确合并
- [ ] 冲突已检测并处理（或确认无冲突）
- [ ] feature 已移至 `EdanSpec/archive/`
