# 安全速查清单

C++ / Qt 应用安全速查。与 `edanspec:security-review` skill 配合使用。

## 目录

- [提交前检查](#提交前检查)
- [认证与本地服务](#认证与本地服务)
- [输入验证](#输入验证)
- [TLS 与网络](#tls-与网络)
- [数据保护](#数据保护)
- [依赖安全](#依赖安全)
- [错误处理](#错误处理)
- [OWASP 映射（桌面/设备）](#owasp-映射桌面设备)

---

## 提交前检查

- [ ] 代码中无密钥（`git diff --cached` 搜索 `password`、`secret`、`api_key`、`BEGIN PRIVATE`）
- [ ] `.gitignore` 包含：`.env`、`*.pem`、`*.key`、`*.pfx`、本地 Qt 套件路径
- [ ] 示例配置只有占位符

## 认证与本地服务

- [ ] 口令使用 Argon2/bcrypt/scrypt，禁止自写 MD5/SHA1 当口令哈希
- [ ] 本地 HTTP/socket 有鉴权或仅 Unix socket + 文件权限
- [ ] 管理接口独立权限
- [ ] 登录/调试口有失败节流
- [ ] 发布构建关闭未文档化的调试后门

## 输入验证

- [ ] 所有外部输入在边界验证（设备帧、文件、QML 文本、CLI）
- [ ] 白名单长度与字符集
- [ ] 文件上传/导入：类型、大小、内容
- [ ] SQL 绑定参数
- [ ] `QProcess` 用 program + arguments，不经过 shell
- [ ] 路径 `QFileInfo::canonicalFilePath` 限制在允许根目录下
- [ ] 协议解析检查剩余长度，拒绝超大 `size` 字段

## TLS 与网络

- [ ] HTTPS/TLS 启用，校验证书链与主机名
- [ ] 禁止无条件 `ignoreSslErrors`
- [ ] 证书钉扎若采用，须有轮换策略
- [ ] 出站 URL 白名单（防 SSRF 打到内网调试口）

```cpp
// 禁止生产环境
QObject::connect(reply, &QNetworkReply::sslErrors,
                 reply, [reply](const QList<QSslError>&) { reply->ignoreSslErrors(); });
```

## 数据保护

- [ ] 日志不写口令、令牌、完整标识、原始临床/客户数据
- [ ] DTO/JSON 不含 `passwordHash`
- [ ] `QSettings` 不存明文秘密
- [ ] 崩溃转储在发布配置中剥离敏感缓冲

## 依赖安全

```bash
# 锁文件必须入库
ls vcpkg.json conan.lock CMakeLists.txt

# 核对 Qt / OpenSSL 版本是否在已知漏洞范围外（查阅当前 CVE，勿沿用过期记忆）
```

- [ ] 第三方与 Qt 补丁版本可追溯
- [ ] 不拷贝老旧 `md5.cpp` 进树

## 错误处理

```cpp
// 生产：通用错误给 UI，细节只进分类日志
qCCritical(lcApp) << ex.what();
return ErrorResponse{ErrorCode::Internal, QStringLiteral("Operation failed")};

// 禁止
return ErrorResponse{ex.what(), stackTrace, lastSql};
```

## OWASP 映射（桌面/设备）

| # | 漏洞 | 预防 |
|---|------|------|
| 1 | 访问控制失效 | 本地服务鉴权、文件权限、角色 |
| 2 | 密码学失效 | TLS 校验、系统凭据库、禁止自写加密 |
| 3 | 注入 | SQL 绑定、QProcess 参数列表、格式化字符串 |
| 4 | 不安全设计 | 威胁建模、协议长度上限 |
| 5 | 安全配置错误 | 关闭调试口、最小 Qt 插件集 |
| 6 | 脆弱组件 | 锁定依赖、跟踪 Qt/OpenSSL 公告 |
| 7 | 认证失效 | KDF、节流、会话过期 |
| 8 | 数据完整性失效 | OTA 验签、更新包哈希 |
| 9 | 日志与监控失效 | 安全事件要记，秘密不记 |
| 10 | SSRF | URL 白名单 |
