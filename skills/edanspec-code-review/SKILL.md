---
name: edanspec-code-review
description: 合并前四维度审查（正确性、可读性、架构、性能）。触发场景：代码实现完成后、合并前、用户要求「审查代码」「代码审查」「看看这段代码」「有没有问题」。不适用于纯文档修改或格式调整。
---

# 代码审查

合入前从四个维度评估代码质量。审查不是找茬——是在代码合入前发现真正的问题。涉及安全维度（认证/授权/用户输入/密钥管理）时，建议用户另行执行 `edanspec-security-review`。

> **职责分工**：本 skill 负责流程编排（确定范围 → 启动审查 → 处理结果）。审查维度定义、检查项细则、输出格式以 `reviewer-agent.md` 为准。

## 流程

### 1. 确定审查范围

理解变更意图：实现什么功能？变更规模？涉及哪些模块？

**没上下文就开始审查 = 盲人摸象。**

超过 200 行的变更很难发现所有问题——建议拆分，先审查核心模块。

### 2. 启动 Reviewer Subagent

读取 `reviewer-agent.md` 全文，拼上本次审查上下文（变更范围、项目类型），
通过**当前平台的 subagent 机制**传给通用代理执行。

**平台适配：**

| 平台 | 调用写法 |
|------|---------|
| Claude Code | `Agent tool`（通用代理），prompt = 文件全文 + 上下文 |
| OpenCode | `task({ subagent_type: "general", prompt: 文件全文 + 上下文 })` |

**上下文隔离**：独立子进程执行，保证审查的专业性和独立性。

### 3. 处理结果

| 级别 | 含义 | 处理 |
|------|------|------|
| **CRITICAL** | 安全漏洞、数据丢失、功能错误 | 必须修复才能合并 |
| **IMPORTANT** | 缺少测试、错误处理不足、抽象不当 | 应该修复再合并 |
| **SUGGESTION** | 命名优化、代码风格 | 可以考虑 |

**有 CRITICAL → 不批准合并。**

## 报告持久化

审查完成后，**必须将报告写入文件**，以便 task-implement 步骤六基于事实检查。

| 条件 | 操作 |
|------|------|
| 在 feature 目录下（存在 `EdanSpec/feature/` 路径） | 将报告写入 `{feature-dir}/code-review-report.md`，并输出报告到控制台 |
| 不在 feature 目录下 | 仅输出报告到控制台，不写文件 |

**判定规则：**
- 有 CRITICAL → 报告结论为 `REQUEST_CHANGES`，`code-review-report.md` 中 CRITICAL 数量 > 0
- 无 CRITICAL → 报告结论为 `APPROVE`，`code-review-report.md` 中 CRITICAL 数量为 0

**报告文件路径**：`{feature-dir}/code-review-report.md`。task-implement 恢复时通过读取此文件判断是否已通过。

## 常见误区与反驳

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
- [ ] 涉及认证/授权/用户输入/密钥管理时，已引导执行 `edanspec-security-review`

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
| 位置格式 | 必须是 `文件：行号` 如 `PointCalculator.kt:23` |
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
