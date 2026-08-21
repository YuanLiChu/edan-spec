---
name: edanspec-verify
description: 三维度（完整性/正确性/一致性）+ 三级严重度报告。触发场景：feature 完成准备归档、用户要求「验证一下」「检查完成度」「看看还缺什么」。不适用于单行修复或小改动。
---

# 结构化验证

feature 归档前的最终关卡。"拿证据说话"——但结构化告诉你**需要什么证据**。

> **职责分工**：本 skill 负责流程编排（准备上下文 → 启动验证 → 判定结论）。验证维度定义、检查项细则、级别定义、输出格式以 `verifier-agent.md` 为准。
>
> **边界**：verify 只负责验证和写入报告文件。delta spec 合并和文件移动由 `edanspec-archive` 负责。动态测试和覆盖率由 `edanspec-task-implement` 的 5 项自动化验证完成，verify 仅做静态检查。

## 流程

### 1. 准备上下文

1. **扫描已有文件**：检查 `tasks.md`、`specs/*.md`、`design.md`、`proposal.md`（不存在的跳过）。
2. **记录产物缺失**：对每个不存在的文件，在报告中注明"缺少 XXX 文档，该维度部分检查项无法执行"，但**不得跳过整个维度**。
3. **确定报告输出**：路径含 `EdanSpec/feature/` 则写入 `{feature-dir}/verify-report.md`，否则仅输出到控制台。
   该参数传给步骤 2 的验证代理，代理根据此参数决定是否写入文件。

### 2. 启动 Verifier Subagent

读取 `verifier-agent.md` 全文，将 `{feature-dir}`、`{existing-files}`、`{report-target}` 替换为步骤 1 确定的值，
通过**当前平台的 subagent 机制**传给通用代理执行。

**平台适配：**

| 平台 | 调用写法 |
|------|---------|
| Claude Code | `Agent tool`（通用代理），prompt = verifier-agent.md 全文 + 参数替换 |
| OpenCode | `task({ subagent_type: "general", prompt: verifier-agent.md 全文 + 参数替换 })` |

**上下文隔离**：独立子进程执行，保证验证的客观性和独立性。

### 3. 判定结论

验证代理执行完毕后，根据结果判定归档结论：

| 条件 | 结论 | 处理 |
|------|------|------|
| CRITICAL > 0 | 自动修复 | 修复所有 CRITICAL → 删除 `verify-report.md` → 重新执行 verify |
| CRITICAL = 0, IMPORTANT > 0 | 可归档（需用户确认） | 报告保留，引导用户决定是否处理 IMPORTANT |
| 全部通过 | 验证通过，可以归档 | 引导归档 |

> **与 task-implement 的一致性**：verify 发现 CRITICAL 时自动修复，与 task-implement 步骤 6 中 code-review、security-review、verify 三关卡统一采用"自动修复 CRITICAL → 删除报告 → 重跑"策略。`edanspec-archive` 在遇到 CRITICAL 时拒绝归档，因为归档前 verify 必须已 passed。

## 常见误区与反驳

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "代码能跑就不用验了" | 能跑 ≠ 完整。可能漏了异常处理和边界条件 |
| "小改动不需要验证" | 小改动最难回滚，漏一个 spec 就是生产 bug |
| "测试绿了就够了" | 测试绿 = 写了的测试通过了。spec 里没被写成测试的需求呢？ |

## 警示信号

- 未全量执行三维度就声称"验证通过"
- 报告中只有 SUGGESTION，没有认真查 CRITICAL/IMPORTANT
- 没有给出具体文件位置和建议
- 批准了有 CRITICAL 问题的 feature 归档

## 验证

- [ ] 三维度均已验证（或有降级说明）
- [ ] 每个发现都有文件位置和修复建议
- [ ] CRITICAL 问题已全部解决（否则拒绝归档）
