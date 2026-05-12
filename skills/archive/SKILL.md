---
name: edanspec:archive
description: 归档已完成的 feature——引导验证（可选）、delta spec 合并、移动到归档目录。触发场景：feature 完成准备归档、用户说「归档这个」「看看能归档哪些」「归档」。不适用于未完成或有 CRITICAL 问题的 feature。
---

# Feature 归档

把已完成的 feature 安全移入归档目录。**先验证，再合并，最后归档。**

## 流程

```
确认目标 feature → 检查 status.json 审查状态
                      ├─ 验证状态 pending → 引导执行 edanspec:verify，等待结果后回来
                      ├─ 审查关卡未完成 → 引导回退到 edanspec:task-implement 完成剩余关卡
                      ├─ 审查全部通过 → delta spec 合并 → 冲突检测 → mv 到 archive
                      └─ 已验证但有 IMPORTANT → 展示报告，用户确认后继续 → delta spec 合并 → mv 到 archive
```

## 1. 确认目标

如果用户指定了 feature 名称，直接使用该 feature。
否则列出所有活跃 feature（`state: "active"`），让用户选择：

```bash
find EdanSpec/feature/ -maxdepth 1 -mindepth 1 -type d | sort
```

对每个 feature 读 `status.json` 和 `tasks.md` 显示完成状态。

## 2. 检查审查与验证状态

读取目标 feature 的 `status.json`，检查 `reviewGate` 字段。按以下顺序逐一检查（先验证，再审查）：

### 2.1 验证未执行（reviewGate.verify.status = pending）

> "`{feature}` 尚未执行验证。**请先调用 `edanspec:verify` 跑一遍三维度验证**，完成后再回来执行归档。"

**停止后续步骤，等待用户回来。**

### 2.2 审查关卡未完成（reviewGate 中 codeReview 或 securityReview 为 pending 或 failed）

> "`{feature}` 的审查关卡尚未全部完成。**请先调用 `edanspec:task-implement` 完成剩余的审查关卡**，完成后再回来执行归档。"

**停止后续步骤，等待用户回来。**

### 2.3 审查全部通过（reviewGate 全部 passed）

展示审查和验证报告摘要，直接进入步骤 3（delta spec 合并）。

### 2.4 已验证但有 IMPORTANT（verify.status = passed 且 verify.findings.important > 0）

展示验证报告，告知用户存在 `{verify.findings.important}` 个 IMPORTANT 建议，确认是否继续归档。用户确认后进入步骤 3。

### 2.5 验证失败（reviewGate.verify.status = failed 或 verify.findings.critical > 0）

展示验证报告，拒绝归档：

> "发现 N 个 CRITICAL 问题，解决前不能归档。请调用 `edanspec:task-implement` 修复对应任务，修复后重新运行 verify。"

**停止后续步骤。**

## 3. Delta Spec 合并

### 3.0 什么是 Delta Spec

每个 feature 中的 spec 是**增量变更**，不是完整规范的副本。

```
EdanSpec/specs/                          EdanSpec/feature/xxx/specs/
├── auth-spec.md      ◄──── delta spec ──├── auth-spec.md
└── api-spec.md       ◄──── delta spec ──└── api-spec.md
    (主 spec / 权威)                         (delta spec / 增量)
```

**主 spec**：`EdanSpec/specs/` 下的权威需求规格，长期维护。
**delta spec**：feature 中只包含本次变更**新增/修改/删除/重命名**的需求。

### 3.1 操作步骤

```
确保主 spec 目录存在（create-spec 初始化时已创建，此处仅验证）：
  [ -d EdanSpec/specs ] || mkdir -p EdanSpec/specs

对 feature 中每个 delta spec（specs/{capability}-spec.md）执行：
  ├─ 主 spec（EdanSpec/specs/{capability}-spec.md）不存在？
  │   → 直接将 delta spec 复制到 EdanSpec/specs/ 下，完成
  └─ 主 spec 存在？
     ├─ 提取 delta 中每个需求的操作类型（见下方格式约定）
     ├─ ADDED    → 追加到主 spec 末尾
     ├─ MODIFIED → 按需求名匹配主 spec 中对应需求，替换整块内容
     ├─ REMOVED  → 从主 spec 删除对应需求整块
     └─ RENAMED  → 更新主 spec 中对应需求名，内容不变
```

### 3.2 Delta Spec 格式约定

Delta spec 中每个需求块**必须在需求名后用标记注明操作类型**：

```markdown
# {Capability} 规格

### Requirement: 用户登录 [ADDED]

系统 SHALL 支持用户名密码登录。

#### Scenario: 正常登录
- **WHEN** 输入正确用户名密码
- **THEN** 跳转到首页

### Requirement: 密码复杂度 [MODIFIED]

系统 SHALL 要求密码至少 8 位，包含大小写字母和数字。

### Requirement: 邮箱验证 [REMOVED]

### Requirement: 用户名限制 [RENAMED] 原名: 用户名长度
```

**标记含义：**

| 标记 | 含义 | 合并行为 |
|------|------|---------|
| `[ADDED]` | 新增需求 | 追加到主 spec 末尾 |
| `[MODIFIED]` | 修改已有需求 | 按需求名匹配，替换整块 |
| `[REMOVED]` | 删除需求 | 从主 spec 删除对应需求整块 |
| `[RENAMED] 原名: X` | 重命名 | 主 spec 中将原名改为新名，内容不变 |
| 无标记 | 默认为 ADDED | 追加到主 spec 末尾 |

需求块范围：从 `### Requirement:` 到下一个 `### Requirement:` 或文件末尾。

### 3.3 变更冲突检测

在合并当前 feature 的 delta spec 之前，先检测是否有其他活跃 feature 也修改了同一 capability：

1. 读取当前 feature 的 `status.json`，检查 `conflicts` 字段是否有预记录的冲突
2. 扫描所有活跃 feature 的 `specs/` 目录，找出所有 `{capability}-spec.md`
3. 构建映射：`capability → [feature 列表]`
4. 如果某个 capability 被 2+ 个活跃 feature 修改 → 存在冲突

**冲突处理：**

| 情况 | 处理 |
|------|------|
| 只有当前 feature 修改了此 capability | 正常合并，无冲突 |
| 多个 feature 修改了同一 capability，但只有当前 feature 实现了代码 | 只合并当前 feature 的 delta，其他 feature 的 delta 保留不合并，警告用户 |
| 多个 feature 都实现了此 capability | 按 feature 创建时间顺序依次合并（先创建的优先，后创建的覆盖同名需求） |
| 多个 feature 都没实现此 capability | 跳过所有 delta 的合并，警告用户 |

"是否实现"的判断方法：比较 feature 的 `base_commit` 与当前 HEAD 之间的 diff（`git diff <base_commit>..HEAD --name-only`），如果包含 `.kt/.java/.py/.go/.ts` 等代码文件修改，则视为实现了代码；如果只有 `.md/.json` 等产物变更，则视为未实现。

冲突解决后继续。

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

## 与 verify 的关系

`edanspec:verify` 只做三维度验证并输出报告，**不执行 delta spec 合并、不移动文件**。
本 skill 在用户选择先验证时调用 verify，验证通过后负责 delta spec 合并和文件移动。

**verify 也可独立使用**——用户想"先看看做得怎么样再决定归档"时，直接调用 `edanspec:verify`，不需要经过 archive。

| skill | 触发方式 | 职责 |
|-------|---------|------|
| **verify** | 独立调用，或由 archive 引导 | 三维度验证 → 输出报告 → 更新 status.json 中 reviewGate.verify 状态 |
| **archive** | 用户主动调用 | 检查验证状态 → delta spec 合并 → 移动到 archive |

## 常见误区与反驳

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "直接归档不用验证" | 验证状态未 passed 时不能归档。引导去跑 verify，不要自作主张跳过 |
| "delta spec 后面再合并也行" | 归档后找回来合并更难。现在合并只需 2 分钟 |

## 警示信号

- verification 为 pending 时未引导验证就直接执行归档
- 主动执行验证而不是引导用户调用 verify
- verification 为 failed 仍批准归档
- delta spec 合并时覆盖了主 spec 的已有内容
- 未检测冲突就移动文件
- 合并 delta spec 前未确保 `EdanSpec/specs/` 目录存在

## 验证

- [ ] 目标 feature 已确认
- [ ] 验证状态已检查：reviewGate.verify.status 为 passed
- [ ] 若 reviewGate 有 pending：已引导用户执行 edanspec:task-implement
- [ ] 若 reviewGate.verify 为 failed：已拒绝归档
- [ ] findings 中的 IMPORTANT 已告知用户并确认
- [ ] delta spec 已合并（或确认无 delta spec）
- [ ] `EdanSpec/specs/` 目录存在且 delta 已正确合并到主 spec
- [ ] 冲突已检测并处理（或确认无冲突）
- [ ] feature 已移动至 `EdanSpec/archive/`
