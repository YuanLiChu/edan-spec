---
name: edanspec:security-review
author: yuanlichu
description: 合入前安全审查——输入验证、认证/授权、数据保护、机密管理、依赖漏洞。触发场景：涉及用户输入、认证/授权、数据存储、外部集成、文件上传的代码变更，用户要求「安全检查」「审查安全性」「安全漏洞」「跨站脚本」「SQL 注入」。不适用于纯 UI 样式调整或文档变更。
---

# 安全审查

合入前系统性地审查安全风险。**安全不是事后补丁——每一行接触用户数据、认证、外部系统的代码都必须经过审查。**

> **职责分工**：本 skill 负责流程编排（确定范围 → 启动审查 → 处理结果）。审查维度定义、检查项细则、输出格式以 `agents/security-reviewer.md` 为准。

## 流程

### 1. 确定范围

理解变更意图：实现什么功能？涉及哪些模块？是否接触用户输入/认证/敏感数据？

超过 200 行的变更很难发现所有安全问题——建议拆分，先审查核心模块。

### 2. 启动 Security Reviewer Agent

```
任务：对以下变更进行五维度安全审查

变更范围：[描述审查的文件/变更]
项目类型：[Qt 桌面 / Qt 嵌入式 / 纯 C++ 库]
语言：[C++17/20 + Qt 6]

要求：
1. 按五维度审查：输入验证、认证/授权、数据保护、机密管理、依赖安全
2. 每个发现分级：CRITICAL / IMPORTANT / SUGGESTION
3. 每个问题给出文件位置和修复建议
4. 输出结构化报告
```

**上下文隔离**：agent 在独立子进程执行。

### 3. 处理结果

| 级别 | 含义 | 处理 |
|------|------|------|
| **CRITICAL** | 可被利用的漏洞（SQL注入、硬编码密钥、明文密码） | 必须修复才能合并 |
| **IMPORTANT** | 潜在风险（缺少授权检查、敏感日志、无速率限制） | 应该修复再合并 |
| **SUGGESTION** | 安全加固建议（加密升级、CSP 收紧） | 可以考虑 |

**有 CRITICAL → 不批准合并。**

## 状态更新

如果在 feature 目录下（`status.json` 存在），审查完成后更新 `reviewGate`：
```json
{ "reviewGate": { "securityReview": { "status": "passed" 或 "failed", "lastRun": "...", "hasCritical": true/false, "findings": { "critical": N, "important": N, "suggestion": N } } } }
```
- 有 CRITICAL → `status: "failed"`, `hasCritical: true`
- 无 CRITICAL → `status: "passed"`, `hasCritical: false`

**`findings` 记录各严重度问题的数量**，便于后续关卡和 archive 了解审查质量。

如果不在 feature 目录下（无 `status.json`），只输出报告，不更新状态。

## 常见误区与反驳

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "框架会处理安全" | 框架提供工具，不是保证。你仍需正确使用它们 |
| "这个端点只是测试用的" | 测试端点上线后被遗忘 = 最大的后门 |

## 警示信号

- 用户输入直接传递给数据库查询、shell 命令或 HTML 渲染
- 源码或 git 历史中有密钥
- API 端点缺少认证或授权检查
- CORS 配置为通配符 `*`
- 认证端点无速率限制
- 错误消息暴露堆栈跟踪或内部路径

## 验证

- [ ] 五维度均已审查
- [ ] 无 CRITICAL 问题遗留
- [ ] 每个发现都有文件位置和修复建议
- [ ] 审查结论与问题级别一致（有 CRITICAL = REQUEST CHANGES）
