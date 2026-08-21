---
name: edanspec-code-review
description: 合并前四维度审查（正确性、可读性、架构、性能）。触发场景：代码实现完成后、合并前、用户要求「审查代码」「代码审查」「看看这段代码」「有没有问题」。不适用于纯文档修改或格式调整。
---

# 代码审查

合入前从四个维度评估代码质量。审查不是找茬——是在代码合入前发现真正的问题。涉及安全维度（认证/授权/用户输入/密钥管理）时，建议用户另行执行 `edanspec-security-review`。

> **职责分工**：本 skill 负责流程编排（确定范围 → 启动审查 → 处理结果）。审查维度定义、检查项细则、输出格式以 `reviewer-agent.md` 为准。

## Qt 专项自动路由

`edanspec-code-review` 是统一入口。通用四维审查始终执行；确定实际文件集后，按以下规则自动调用仓库内的 Qt 6 专项 skill：

1. 固化本次审查的 `allFiles`（diff、commit 或目录范围），不得让后续 reviewer 自行扩大范围。
2. 使用仓库内脚本生成一次分类结果：

   ```text
   python skills/edanspec-code-review/scripts/classify_qt_scope.py --json <allFiles...>
   ```

   分类结果包含 `allFiles`、`qtCppFiles`、`qmlFiles` 和逐文件 `evidence`，后续阶段必须复用该结果。
3. `qmlFiles` 非空时，调用 `qt-qml-review`，只传入 `qmlFiles`；`.qml` 与 `.qmltypes` 均属于 QML 范围。
4. `qtCppFiles` 非空时，调用 `qt-cpp-review`，只传入 `qtCppFiles`。普通 C++ 没有明确 Qt 证据时不得调用该 skill。
5. 同时存在两组文件时，两个专项阶段可以并行，但通用 reviewer 仍必须执行。每个专项 skill 必须保留其原有确定性 lint、可用的系统工具和六个深度分析阶段；不得把 Qt 规则复制进通用 reviewer。

Qt/C++ 的明确证据包括 Qt 头文件、Qt 类型、`Q_OBJECT`/`Q_PROPERTY` 等宏、signal/slot/emit 构造，或引用该源文件的 `find_package(Qt6 ...)`、`qt_add_executable`、`qt_add_qml_module` 等构建声明。检测到 `qt-cpp-review` 的 framework/module 信号时，只提出启用 framework 模式的建议，不得自动启用。

## 专项报告与统一结论

在 feature 目录（优先 `.edan-dev/feature/<name>`，兼容旧的 `EdanSpec/feature/<name>`）中保留：

- `qt-cpp-review-report.md`（仅在 Qt/C++ 阶段触发时生成）；
- `qt-qml-review-report.md`（仅在 QML 阶段触发时生成）；
- `code-review-report.md`（通用与专项结果的统一报告）。

统一报告必须记录三个阶段状态：`genericReview`、`qtCppReview`、`qmlReview`，状态可为 `complete`、`partial`、`failed` 或 `not-applicable`。按文件、行号和问题语义完全一致才去重；Qt 原始编号、规则 ID、置信度和来源必须保留，Qt 置信度不得直接映射为 EdanSpec 严重度。

结论矩阵如下：

- 存在确认的 `CRITICAL`：`REQUEST_CHANGES`；若专项同时未完成，完整性仍标记为不完整。
- 所有必要阶段完成且没有 `CRITICAL`：`APPROVE`。
- 任一必要阶段缺失、失败、报告无法解析或 Python lint 未运行：`INCOMPLETE`，不得报告为 `APPROVE`。
- Qt 报告中的 investigation target 进入统一报告的“待人工确认”章节，不单独升级为 `CRITICAL`。

不含 Qt/C++ 或 QML 文件时，不调用专项 skill，也不生成 Qt 专项报告。

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
| 在 feature 目录下（存在 `.edan-dev/feature/` 或 `EdanSpec/feature/` 路径） | 将报告写入 `{feature-dir}/code-review-report.md`，并输出报告到控制台 |
| 不在 feature 目录下 | 仅输出报告到控制台，不写文件 |

**判定规则：**
- 有 CRITICAL → 报告结论为 `REQUEST_CHANGES`，`code-review-report.md` 中 CRITICAL 数量 > 0
- 无 CRITICAL 且所有必要阶段完成 → 报告结论为 `APPROVE`，`code-review-report.md` 中 CRITICAL 数量为 0
- 无 CRITICAL 但专项阶段不完整 → 报告结论为 `INCOMPLETE`，不得进入完成或可合并状态

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
