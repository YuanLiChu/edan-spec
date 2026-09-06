---
name: edanspec:verify
author: yuanlichu
description: 三维度（完整性/正确性/一致性）+ 三级严重度报告。触发场景：feature 完成准备归档、用户要求「验证一下」「检查完成度」「看看还缺什么」。不适用于单行修复或小改动。
---

# 结构化验证

feature 归档前的最终关卡。"拿证据说话"——但结构化告诉你**需要什么证据**。

## 三维度

| 维度 | 回答的问题 | 验证方式 |
|------|-----------|---------|
| **完整性** | 做完了吗？ | tasks checkbox、spec 覆盖率 |
| **正确性** | 做对了吗？ | 代码证据、测试覆盖 |
| **一致性** | 风格对吗？ | 设计遵循、项目模式 |

完整验证需要三维度，产物不足时按降级策略执行，并在报告中注明跳过的维度及原因。

## 验证流程

### 1. 加载上下文

读取 feature 中的全部产物：
- `tasks.md` — 任务清单
- `specs/{capability}-spec.md` — delta spec（feature 目录下，相对路径 `EdanSpec/feature/<name>/specs/`）
- `design.md` — 技术设计
- `proposal.md` — 提案（如有）

### 2. 完整性验证（Completeness）

**任务完成度：**
- 解析 `tasks.md` 中的 checkbox：`- [ ]`（未完成）vs `- [x]`（已完成）
- 统计：X/Y 任务完成
- 未完成的任务 → 每条记为 CRITICAL

**Spec 覆盖率：**
- 从 delta spec 提取所有需求（`### Requirement:` 标记）
- 通过以下方式定位每个需求的实现：
  1. 从 `tasks.md` 的 `关联需求` 字段获取任务-to-需求映射
  2. 从任务的 `涉及的文件` 字段获取具体文件列表
  3. 在上述文件中搜索需求关键词，确认实现位置
- 找不到对应实现的 → CRITICAL
- 找到部分实现的 → IMPORTANT

### 3. 正确性验证（Correctness）

**需求实现映射：**
- 对每个 spec 需求，在代码中定位实现位置
- 评估实现是否匹配需求意图
- 发现偏离 → IMPORTANT："实现可能与 spec 不符：<详情>"

**场景覆盖：**
- 对每个 spec 场景（WHEN/THEN 格式），检查：
  - 代码中是否处理了该场景
  - 是否有测试覆盖该场景
- 场景无覆盖 → IMPORTANT

**测试覆盖率：**
- 运行项目覆盖率工具，确认达标
- 标准见 `AGENT.md`「质量标准」章节
- 任一项不达标 → IMPORTANT

### 4. 一致性验证（Coherence）

**设计遵循：**
- 从 `design.md` 提取关键决策（Goals/Non-Goals、Decisions 段落）
- 检查实现是否遵循这些决策
- 发现矛盾 → IMPORTANT："未遵循设计决策：<决策项>"

**代码模式一致性：**
- 检查新代码的命名、目录结构、编码风格是否与项目现有代码一致
- 按文件后缀加载 `rules/` 下的编码风格规范
- 明显偏离 → SUGGESTION

## 报告格式

```markdown
# 验证报告：{feature-name}

## 摘要

| 维度         | 状态              |
|--------------|-------------------|
| 完整性       | X/Y 任务, N 需求  |
| 正确性       | M/N 需求已覆盖    |
| 一致性       | 遵循设计 / N 处偏离 |

**CRITICAL（必须解决，否则不能归档）**

- `文件:行号` 未完成任务：<任务描述>
  → 建议：完成任务或标记为已完成

## IMPORTANT（应该解决）

- `文件:行号` spec 需求未覆盖：<需求名称>
  → 建议：实现该需求或从 spec 中移除

- `文件:行号` 未遵循设计决策：<决策项>
  → 建议：修改实现或更新 design.md

## SUGGESTION（可选改进）

- `文件:行号` 代码风格偏离：...
  → 建议：调整为项目现有模式

## 结论

- 有 CRITICAL → "发现 N 个 CRITICAL 问题，解决前不能归档"。回退路径：调 `edanspec:task-implement` 修复对应任务 → 修复后重新运行 verify
- 仅有 IMPORTANT → "无 CRITICAL 问题，N 个 IMPORTANT 建议归档前处理"
- 全部通过 → "验证通过，可以归档"
```

## 降级策略

| 已有产物 | 验证维度 |
|---------|---------|
| 只有 tasks.md | 仅验证任务完成度 |
| tasks + specs | 验证完整性 + 正确性 |
| 完整核心文档 | 验证全部三维度 |

跳过的维度在报告中注明原因。

## 归档前流程

1. 运行三维度验证
2. 有 CRITICAL → 拒绝归档，返回报告。引导用户回退到 `edanspec:task-implement` 修复对应任务。更新 `status.json`：`reviewGate.verify.status = "failed"`，`reviewGate.verify.hasCritical = true`，记录各严重度数量到 `reviewGate.verify.findings`
3. 有 IMPORTANT（无 CRITICAL）→ 展示报告，说明存在 N 个 IMPORTANT 建议，用户确认后可归档。更新 `status.json`：`reviewGate.verify.status = "passed"`，`reviewGate.verify.hasCritical = false`，记录 findings（`important > 0`）
4. 全部通过 → 展示报告，输出"验证通过，可以归档"。更新 `status.json`：`reviewGate.verify.status = "passed"`，`reviewGate.verify.hasCritical = false`，`findings` 记录实际发现数量（可能全为 0，也可能有少量 SUGGESTION）

**`status` 字段语义**：

| 值 | 含义 | 归档 |
|---|------|------|
| `pending` | 尚未执行 | 不允许 |
| `passed` | 无 CRITICAL，可进入下一步 | 允许（IMPORTANT 时需用户确认） |
| `failed` | 有 CRITICAL，必须修复 | 不允许 |

**`findings` 字段**：`{ "critical": N, "important": N, "suggestion": N }`，记录各严重度发现数量。archive 据此判断是否存在遗留问题。

**verify 只负责验证、输出报告和更新 status.json。delta spec 合并和文件移动由 `edanspec:archive` 负责。**

## 常见误区与反驳

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "代码能跑就不用验了" | 能跑 ≠ 完整。可能漏了异常处理和边界条件 |
| "小改动不需要验证" | 小改动最难回滚，漏一个 spec 就是生产 bug |
| "测试绿了就够了" | 测试绿 = 写了的测试通过了。spec 里没被写成测试的需求呢？ |

## 警示信号

- 只验证了一个维度就声称"验证通过"
- 报告中只有 SUGGESTION，没有认真查 CRITICAL/IMPORTANT
- 没有给出具体文件位置和建议
- 批准了有 CRITICAL 问题的 feature 归档

## 验证

- [ ] 三维度均已验证（或有降级说明）
- [ ] 每个发现都有文件位置和修复建议
- [ ] CRITICAL 问题已全部解决（否则拒绝归档）
