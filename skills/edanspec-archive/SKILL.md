---
name: edanspec-archive
description: 归档已完成的 feature——引导验证（可选）、delta spec 合并、移动到归档目录。触发场景：feature 完成准备归档、用户说「归档这个」「看看能归档哪些」「归档」。不适用于未完成或有 CRITICAL 问题的 feature。
---

<!-- SCRIPTS: .opencode/skills/task-implement/scripts/ — 跨 skill 引用，正文用 {{TASK_SCRIPTS}} 表示 -->

# Feature 归档

把已完成的 feature 安全移入归档目录。**先验证，再合并，最后归档。**

`edanspec-archive` 的职责：检查关卡状态 → 引导验证 → 合并 delta spec → 移动文件。
`edanspec-verify` 只负责三维度验证并输出报告，**不合并 spec、不移动文件**，可独立调用。

## 执行流程

```
确认目标 feature
  → 检查审查关卡状态
      ├─ verify = pending          → 引导调用 edanspec-verify，完成后继续
      ├─ codeReview/securityReview = pending/failed → 引导回退 edanspec-task-implement
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

读取每个 feature 的 `tasks.md` 显示任务完成状态。运行 `{{TASK_SCRIPTS}}/derive-review-status.py` 获取审查状态。

## 2. 检查关卡状态

运行 `{{TASK_SCRIPTS}}/derive-review-status.py EdanSpec/feature/<name>`（脚本不存在时手工检查 `code-review-report.md`、`security-review-report.md`、`verify-report.md` 是否存在并解析内容），按以下分支处理：

| 审查状态 | 操作 |
|---------|------|
| `verify.status = pending` | 引导用户调用 `edanspec-verify`，等待完成后继续 |
| `codeReview` 或 `securityReview` 为 pending/failed | 引导用户调用 `edanspec-task-implement` 完成剩余关卡 |
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
  ├─ 主 spec 不存在 → 创建新主规格文件
  │    ├─ 标题：# {capability}
  │    ├─ 添加 ## Purpose 部分（可简短标记为 TBD）
  │    ├─ 添加 ## Requirements 部分
  │    └─ 将 delta 中 ADDED 需求追加到 ## Requirements 下
  │         （跳过 MODIFIED/REMOVED 分区，无源可改）
  └─ 主 spec 存在 → 智能应用变更（见 3.3 关键原则）
     ├─ ADDED    → 需求不存在则追加到 ## Requirements 末尾；已存在则视为隐式 MODIFIED 更新
     ├─ MODIFIED → 按需求名匹配，场景级增量合并（保留未提及的场景/内容）
     ├─ REMOVED  → 从主 spec 删除对应需求
     └─ RENAMED  → 找到 FROM 需求，重命名为 TO，内容不变
```

> **重要**：delta spec 的分区标题（`## ADDED Requirements` 等）是操作指令，**不会**出现在主规格中。主规格始终是扁平结构：`# {capability}` → `## Purpose` → `## Requirements` → 若干 `### Requirement:` 块。

### 3.3 关键原则：智能合并

与程序化整块替换不同，运用判断来合理合并变更：

- **场景级增量**：MODIFIED 不需要复制整个需求块——只包含要添加/修改的场景
- **保留未提及内容**：delta 中未提到的现有场景/描述保持不变
- **幂等性**：同一 delta spec 合并两次应得到相同结果
- **变更前双读**：同时读取 delta spec 和主 spec，理解意图后再编辑
- **边做边展示**：每个能力改完后展示摘要（做了什么变更）

**示例**：主规格有 5 个场景，delta 只想新增 1 个场景 → 只加那个场景，保留其余 4 个。

### 3.4 Delta Spec 格式约定

Delta spec 使用**分区标题**声明操作类型，而非行内标签：

```markdown
# {Capability} 规格

## ADDED Requirements

### Requirement: 用户登录
支持用户名密码登录。

#### Scenario: 正常登录
- **WHEN** 输入正确的用户名和密码
- **THEN** 返回用户信息和认证令牌

## MODIFIED Requirements

### Requirement: 密码复杂度
#### Scenario: 增加大小写要求
- **WHEN** 设置密码
- **THEN** 密码必须包含至少一个大写字母和一个小写字母

## REMOVED Requirements

### Requirement: 邮箱验证

## RENAMED Requirements

- FROM: `### Requirement: 用户名长度`
- TO: `### Requirement: 用户名限制`
```

| 分区 | 合并行为 |
|------|---------|
| `## ADDED Requirements` | 需求不存在则追加；已存在则视为隐式 MODIFIED 更新 |
| `## MODIFIED Requirements` | 按需求名匹配，场景级增量合并（保留未提及内容） |
| `## REMOVED Requirements` | 从主 spec 删除对应需求 |
| `## RENAMED Requirements` | 主 spec 中改名，内容不变 |

需求块范围：从分区标题（`## ADDED Requirements` 等）到下一个分区标题。每个分区下的 `### Requirement:` 块到下一个 `### Requirement:` 或分区标题结束。

**MODIFIED 只写变更部分**：不需要复制整个需求——只列出要添加/修改的场景，未提及的场景自动保留。

### 3.5 冲突检测

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

"是否实现代码"：比较 `base_commit` 与 HEAD 的 diff，含 `.kt/.java/.py/.go/.ts` 等源码文件修改视为已实现，仅 `.md/.json` 变更视为未实现。

## 4. 移动到归档目录

```bash
mkdir -p EdanSpec/archive
mv EdanSpec/feature/{name} EdanSpec/archive/
```

移动后更新 `status.json`：`state = "archived"`。

归档前最终确认：
- [ ] 三个审查关卡全部 passed（通过 `{{TASK_SCRIPTS}}/derive-review-status.py` 确认）
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
- 合并 delta spec 时整块替换而非智能增量合并
- 合并 delta spec 时覆盖主 spec 已有未提及内容
- 未检测冲突就移动文件
- 合并前未确保 `EdanSpec/specs/` 目录存在

## 验证

- [ ] 目标 feature 已确认
- [ ] 审查关卡全部 passed（`{{TASK_SCRIPTS}}/derive-review-status.py` 输出 `allPassed = true`）
- [ ] 审查关卡有 pending/failed 时已引导至对应 skill
- [ ] verify 为 failed 时已拒绝归档
- [ ] IMPORTANT findings 已告知用户
- [ ] delta spec 已合并（或确认无 delta spec）
- [ ] `EdanSpec/specs/` 存在且 delta 已正确合并
- [ ] 冲突已检测并处理（或确认无冲突）
- [ ] feature 已移至 `EdanSpec/archive/`
