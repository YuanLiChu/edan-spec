# TDD 原则

## 核心循环

```
RED（编写失败测试）→ GREEN（最小实现）→ REFACTOR（重构优化）→ 重复
```

### RED — 编写失败测试

测试必须先编写且先失败，否则无法证明实现正确。

```cpp
TEST(AuthService, should_authenticate_when_login_given_validPassword)
{
    FakeUserStore store;
    store.add(User{"usr_001", QStringLiteral("tester"), hashPassword("SecurePass123!")});
    AuthService auth(&store);

    const auto user = auth.login(QStringLiteral("tester"), QStringLiteral("SecurePass123!"));

    ASSERT_TRUE(user.has_value());
    EXPECT_EQ(user->id, QStringLiteral("usr_001"));
}
```

```cpp
TEST(PasswordHasher, should_notStorePlaintext_when_hash_given_secret)
{
    const QByteArray hashed = hashPassword(QByteArrayLiteral("SecurePass123!"));
    EXPECT_NE(hashed, QByteArrayLiteral("SecurePass123!"));
    EXPECT_TRUE(verifyPassword(QByteArrayLiteral("SecurePass123!"), hashed));
}
```

### GREEN — 最小实现

编写刚好满足测试通过的代码，不做过度设计。

```cpp
Task createTask(const QString& title)
{
    return Task{generateId(), title, TaskStatus::Pending};
}
```

### REFACTOR — 重构优化

测试通过后再优化命名、消除重复、提取公共逻辑。每步重构后重新执行测试。

---

## Bug 修复 — 先复现再修复

```
编写复现测试 → 确认失败 → 实现修复 → 确认通过 → 全量回归
```

```cpp
// Bug：完成任务时 completedAt 未更新

TEST(TaskService, should_setCompletedAt_when_complete_given_existingTask)
{
    TaskService service;
    const Task created = service.create(QStringLiteral("Update docs"));
    const Task done = service.complete(created.id);
    EXPECT_TRUE(done.completedAt.has_value());
}

// 失败 → 确认 Bug → 修复实现 → 测试通过
```

---

## 测试金字塔

```
        ╱╲       E2E / 板上冒烟（~5%）— 关键用户或设备流程
       ╱──╲      集成测试（~15%）— 协议、SQLite、Qt 事件循环
      ╱────╲     单元测试（~80%）— 纯逻辑、毫秒级
     ╱──────╲
```

### 测试规模

| 规模 | 约束 | 示例 |
|------|------|------|
| 小规模 | 单进程、无 I/O、无真实设备 | 纯函数、解析、状态机 |
| 中规模 | 仅 localhost、Fake 端口、offscreen | QTest 信号、SQLite 临时库 |
| 大规模 | 允许真实设备或显示 | HIL、安装包冒烟 |

### 决策路径

```
纯逻辑、无副作用？            → 单元测试（GTest）
跨越 Qt 事件/SQL/文件？       → 集成测试（QTest / 临时目录）
关键用户或设备流程？           → 冒烟 — 仅限关键路径
```

---

## 编写原则

**验证行为结果，不验证内部调用**：断言最终状态，不验证中间过程。

```cpp
// 推荐：验证排序结果
EXPECT_GT(tasks[0].createdAt, tasks[1].createdAt);

// 不推荐：验证 SQL 字符串
EXPECT_CALL(db, exec(testing::HasSubstr("ORDER BY")));
```

**DAMP 优于 DRY**：测试代码中可读性优先于复用，每个测试用例自包含。

```cpp
TEST(UserFactory, should_reject_when_create_given_emptyName)
{
    EXPECT_THROW(createUser(QString(), QStringLiteral("a@b.com")), std::invalid_argument);
}

TEST(UserFactory, should_reject_when_create_given_invalidEmail)
{
    EXPECT_THROW(createUser(QStringLiteral("test"), QStringLiteral("not-an-email")),
                 std::invalid_argument);
}
```

**Arrange-Act-Assert 三段式**：准备测试数据 → 执行被测操作 → 断言预期结果。

```cpp
TEST(Pricing, should_applyGoldDiscount_when_calculate_given_goldTier)
{
    // Arrange
    const Order order{100, MembershipLevel::Gold};

    // Act
    const int result = calculateDiscount(order);

    // Assert
    EXPECT_EQ(result, 15);
}
```

**单一职责**：每个测试用例只验证一个行为。

**描述性命名**：测试名称应清晰描述被测行为和预期结果。

```
推荐：should_returnUnauthorized_when_login_given_expiredToken
推荐：should_reject_when_enqueue_given_negativeQuantity
不推荐：test_auth
不推荐：handles_errors
```

---

## Mock 使用原则

```
优先级（高 → 低）：
1. 真实实现 → 最高置信度
2. Fake     → 内存版端口（FakeDevicePort）
3. Stub     → 返回固定数据
4. Mock     → 验证方法调用，慎用
```

**仅在以下情况使用 Mock**：真实依赖执行过慢、结果具有不确定性、或存在不可控副作用（真设备、真网络、支付）。

---

## 常见反模式

| 反模式 | 后果 | 修正 |
|--------|------|------|
| 测试实现细节 | 重构导致测试失败，即使行为正确 | 仅验证输入输出 |
| 非确定性测试 | 间歇性失败，失去信任 | Fake 时钟，禁止固定 sleep |
| 测试第三方代码 | 浪费资源验证 Qt/STL | 只测试自己的逻辑 |
| 测试用例不隔离 | 单独通过、合并失败 | 每个测试独立搭建和清理 |
| 过度 Mock | 测试通过、生产环境崩溃 | 优先 Fake |

---

## 需要警惕

- 实现了功能却没有对应测试
- 测试首次运行即通过（可能覆盖不足）
- Bug 修复缺少复现测试
- 测试名称无法表达验证意图
- 为维持测试全绿而 `QSKIP` / `DISABLED_`
