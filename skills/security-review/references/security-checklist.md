# 安全速查清单

应用安全的速查清单。与 `edan-dev:security-review` skill 配合使用。

## 目录

- [提交前检查](#提交前检查)
- [认证](#认证)
- [授权](#授权)
- [输入验证](#输入验证)
- [安全响应头](#安全响应头)
- [CORS 配置](#cors-配置)
- [数据保护](#数据保护)
- [依赖安全](#依赖安全)
- [错误处理](#错误处理)
- [OWASP Top 10 速查](#owasp-top-10-速查)

---

## 提交前检查

- [ ] 代码中无密钥（`git diff --cached | grep -i "password\|secret\|api_key\|token"`）
- [ ] `.gitignore` 包含：`.env`、`.env.local`、`*.pem`、`*.key`
- [ ] `.env.example` 使用占位值（非真实密钥）

## 认证

- [ ] 密码使用 bcrypt（≥12 轮）、scrypt 或 argon2 哈希
- [ ] Session Cookie 设置：`httpOnly`、`secure`、`sameSite: 'lax'`
- [ ] Session 设置了合理的过期时间（max-age）
- [ ] 登录端点有速率限制（≤10 次/15 分钟）
- [ ] 密码重置 Token 有时效（≤1 小时）且一次性使用
- [ ] 连续失败后账户锁定（可选，带通知）
- [ ] 敏感操作支持 MFA（推荐但非强制）

## 授权

- [ ] 每个受保护端点检查认证
- [ ] 每个资源访问检查所有权/角色（防止 IDOR）
- [ ] 管理端点需要管理员角色
- [ ] API Key 限制为最小必要权限
- [ ] JWT Token 验证（签名、过期时间、签发者）

## 输入验证

- [ ] 所有外部输入在系统边界验证（API 路由、表单处理）
- [ ] 使用白名单验证（而非黑名单）
- [ ] 字符串长度受限（最小/最大值）
- [ ] 数值范围已验证
- [ ] Email、URL、日期格式使用正确库验证
- [ ] 文件上传：类型受限、大小受限、内容已验证
- [ ] SQL 查询参数化（禁止字符串拼接）
- [ ] HTML 输出编码（使用框架自动转义）
- [ ] URL 在重定向前验证（防止开放重定向）

## 安全响应头

```
Content-Security-Policy: default-src 'self'; script-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0  （禁用，依赖 CSP）
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

## CORS 配置

```kotlin
// 推荐：限制性配置
corsConfiguration.apply {
    allowedOrigins = listOf("https://yourdomain.com")
    allowedMethods = listOf("GET", "POST", "PUT", "PATCH", "DELETE")
    allowedHeaders = listOf("Content-Type", "Authorization")
    allowCredentials = true
}

// 生产环境禁止：
corsConfiguration.apply {
    allowedOrigins = listOf("*")  // 允许任何来源
}
```

## 数据保护

- [ ] API 响应排除了敏感字段（`passwordHash`、`resetToken` 等）
- [ ] 日志中不记录敏感数据（密码、Token、完整卡号）
- [ ] PII 数据在需要时加密存储
- [ ] 所有外部通信使用 HTTPS
- [ ] 数据库备份已加密

## 依赖安全

```bash
# Gradle（依赖漏洞扫描）
./gradlew dependencies --configuration compileClasspath
# 使用 OWASP Dependency-Check 插件
./gradlew dependencyCheckAnalyze

# Node.js
npm audit
npm audit fix
npm audit --audit-level=critical

# Python
pip-audit
safety check
```

## 错误处理

```kotlin
// 生产环境：通用错误，不暴露内部细节
fun handleException(ex: Exception): ErrorResponse {
    log.error("Unexpected error", ex)
    return ErrorResponse("INTERNAL_ERROR", "Something went wrong")
}

// 生产环境禁止：
ErrorResponse(
    error = ex.message,        // 暴露内部细节
    stack = ex.stackTrace,     // 暴露调用栈
    query = ex.sql             // 暴露数据库细节
)
```

## OWASP Top 10 速查

| # | 漏洞 | 预防 |
|---|------|------|
| 1 | 访问控制失效 | 每个端点检查认证，验证所有权 |
| 2 | 密码学失效 | HTTPS、强哈希、代码中无密钥 |
| 3 | 注入 | 参数化查询、输入验证 |
| 4 | 不安全设计 | 威胁建模、规范驱动开发 |
| 5 | 安全配置错误 | 安全响应头、最小权限、依赖审计 |
| 6 | 脆弱组件 | 依赖扫描、保持更新、最小依赖 |
| 7 | 认证失效 | 强密码、速率限制、Session 管理 |
| 8 | 数据完整性失效 | 验证更新/依赖、签名产物 |
| 9 | 日志与监控失效 | 记录安全事件、不记录密钥 |
| 10 | SSRF | 验证/白名单 URL、限制出站请求 |
