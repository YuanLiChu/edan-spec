---

name: edanspec:code-review
author: yuanlichu
description: 合并前四维度审查（正确性、可读性、架构、性能）。触发场景：代码实现完成后、合并前、用户要求「审查代码」「代码审查」「看看这段代码」「有没有问题」。不适用于纯文档修改或格式调整。
---

# 代码审查

合入前从四个维度评估代码质量。审查不是找茬——是在代码合入前发现真正的问题。涉及安全维度（认证/授权/用户输入/密钥管理）时，建议用户另行执行 `edanspec:security-review`。

> **职责分工**：本 skill 负责流程编排（确定范围 → 启动审查 → 处理结果）。审查维度定义、检查项细则、输出格式以 `agents/code-reviewer.md` 为准。

## 流程

### 1. 确定审查范围

理解变更意图：实现什么功能？变更规模？涉及哪些模块？

**没上下文就开始审查 = 盲人摸象。**

超过 200 行的变更很难发现所有问题——建议拆分，先审查核心模块。

### 2. 启动 Reviewer Agent

通过 Agent tool 启动独立的 code-reviewer agent：

```
任务：对以下变更进行四维度审查
变更范围：[文件/变更描述]
项目类型：[Qt 桌面 / Qt 嵌入式 / 纯 C++ 库]

要求：
1. 按正确性、可读性、架构、性能四维度逐一审查
2. 每个发现分级：CRITICAL / IMPORTANT / SUGGESTION
3. 每个问题给出文件位置和修复建议
4. 遵循 Chesterton's Fence 原则：先理解为什么存在，再判断
```

**上下文隔离**：独立子进程执行，保证审查的专业性和独立性。

### 3. 处理结果

| 级别 | 含义 | 处理 |
|------|------|------|
| **CRITICAL** | 安全漏洞、数据丢失、功能错误 | 必须修复才能合并 |
| **IMPORTANT** | 缺少测试、错误处理不足、抽象不当 | 应该修复再合并 |
| **SUGGESTION** | 命名优化、代码风格 | 可以考虑 |

**有 CRITICAL → 不批准合并。**

## 状态更新

如果在 feature 目录下（`status.json` 存在），审查完成后更新 `reviewGate`：
```json
{ "reviewGate": { "codeReview": { "status": "passed" 或 "failed", "lastRun": "...", "hasCritical": true/false, "findings": { "critical": N, "important": N, "suggestion": N } } } }
```
- 有 CRITICAL → `status: "failed"`, `hasCritical: true`
- 无 CRITICAL → `status: "passed"`, `hasCritical: false`

**`findings` 记录各严重度问题的数量**，便于后续关卡和 archive 了解审查质量。

如果不在 feature 目录下（无 `status.json`），只输出报告，不更新状态。

## 常见借口

> 通用借口见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "性能不是问题，数据量不大" | 现在的"不大"会变成明天的"很大"。N+1 查询在 10 条数据时没问题，1000 条时就超时 |

## 警示信号

- 没有先理解需求就开始审查
- 只关注格式/风格，忽略逻辑/架构
- 审查报告只有 SUGGESTION
- 没有给出具体修复建议，只说"这里有问题"
- 批准了有 CRITICAL 问题的代码

## 验证

- [ ] 四个维度均已审查
- [ ] 每个发现都有文件位置和修复建议
- [ ] 严重程度分级正确
- [ ] 没有 CRITICAL 问题遗留
- [ ] 涉及认证/授权/用户输入/密钥管理时，已引导执行 `edanspec:security-review`

## 输出格式

**必须使用结构化列表格式**，确保报告一致性。模板见 `reviews/review-report-template.md`，示例见 `reviews/review-report-example.md`。

### 报告结构

```markdown
# 代码审查报告

| 字段 | 值 |
|------|-----|
| **审查范围** | [文件列表或变更描述] |
| **变更类型** | [新功能 / Bug 修复 / 重构 / 性能优化] |
| **变更规模** | [+X 行 -Y 行，共 Z 行] |
| **结论** | APPROVE / REQUEST_CHANGES |

---

## 问题摘要

| 级别 | 数量 | 说明 |
|------|------|------|
| CRITICAL | N | 必须修复才能合并 |
| IMPORTANT | N | 应该修复再合并 |
| SUGGESTION | N | 可以考虑 |

---

## CRITICAL Issues（必须修复）
## IMPORTANT Issues（应该修复）
## SUGGESTION（可选改进）

> 每个级别使用代码块列表格式：
> ```
> #: 序号
> 位置：文件：行号
> 维度：正确性/可读性/架构/性能
> 问题描述：具体问题描述
> 违反检查项：检查项原文
> 修复建议：具体代码示例
> ────────────────────────────────────────
> ```

---

## 做得好的地方
## 验证记录
## 审查说明
```

### 填写要求

| 要求 | 说明 |
|------|------|
| 位置格式 | 必须是 `文件：行号` 如 `PointCalculator.cpp:23` |
| 维度分类 | 必须是：正确性、可读性、架构、性能 |
| 检查项 | 必须引用检查清单原文，如"边界条件 - 空值处理" |
| 修复建议 | 必须具体可执行，包含代码示例，不得只说"优化" |
| 无问题时 | 写"共 0 个"并留空代码块，不得省略章节 |

---

按审查维度加载对应清单：

- `references/correctness-checklist.md` — 正确性维度检查清单
- `references/readability-checklist.md` — 可读性维度检查清单
- `references/architecture-checklist.md` — 架构维度检查清单
- `references/performance-checklist.md` — 性能维度检查清单

**加载策略**：根据变更类型优先加载相关清单（如 bug 修复优先加载 correctness，重构优先加载 architecture），其他按需加载。
