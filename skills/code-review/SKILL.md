---

name: code-review
description: 合并前四维度审查（正确性、可读性、架构、性能）。触发场景：代码实现完成后、合并前、用户要求「审查代码」「代码审查」「看看这段代码」「有没有问题」。不适用于纯文档修改或格式调整。
---

# 代码审查

合入前从四个维度评估代码质量。审查不是找茬——是在代码合入前发现真正的问题。涉及安全维度（认证/授权/用户输入/密钥管理）时，建议用户另行执行 `edan-dev:security-review`。

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
项目类型：[Android/Web/前端等]

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
{ "reviewGate": { "codeReview": { "status": "done" 或 "failed", "lastRun": "...", "hasCritical": true/false } } }
```
- 有 CRITICAL → `status: "failed"`, `hasCritical: true`
- 无 CRITICAL → `status: "done"`, `hasCritical: false`

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
- [ ] 涉及认证/授权/用户输入/密钥管理时，已引导执行 `edan-dev:security-review`

## 辅助资源（按需加载）

- `references/performance-checklist.md` — 性能维度检查清单
