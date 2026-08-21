# 测试模式参考

跨语言/框架的测试模式速查手册。

## 目录

- [测试结构（AAA 模式）](#测试结构aaa-模式)
- [测试命名规范](#测试命名规范)
- [断言速查](#断言速查)
- [Mock 策略](#mock-策略)
- [语言特定模式](#语言特定模式)
- [测试反模式](#测试反模式)

---

## 测试结构（AAA 模式）

**Arrange（准备）→ Act（执行）→ Assert（断言）**。每个测试都遵循这个三段式结构。

### Kotlin 示例

```kotlin
@Test
fun `should calculate total price correctly`() {
    // Arrange：准备测试数据和依赖
    val items = listOf(
        Item("book", price = 10.0, quantity = 2),
        Item("pen", price = 5.0, quantity = 3)
    )
    val calculator = PriceCalculator()

    // Act：执行被测方法
    val total = calculator.calculateTotal(items)

    // Assert：验证结果
    assertEquals(35.0, total, 0.01)
}
```

### Node.js/Jest 示例

```typescript
it('creates a task with default pending status', () => {
    // Arrange
    const input = { title: 'Test Task', priority: 'high' };

    // Act
    const result = createTask(input);

    // Assert
    expect(result.title).toBe('Test Task');
    expect(result.priority).toBe('high');
    expect(result.status).toBe('pending');
});
```

---

## 测试命名规范

**格式：** `should_<预期结果>_when_<触发条件>`

### Kotlin（反引号命名）

```kotlin
@Test
fun `should return user when id exists`() { }

@Test
fun `should throw UserNotFoundException when user does not exist`() { }

@Test
fun `should handle empty list gracefully`() { }
```

### Java（方法名 + @DisplayName）

```java
@Test
@DisplayName("应返回用户当ID存在时")
void getUser_whenIdExists_shouldReturnUser() { }

@Test
@DisplayName("应抛出异常当用户不存在时")
void getUser_whenUserNotFound_shouldThrowException() { }
```

### Node.js/Python（描述性字符串）

```typescript
it('should return user when valid id provided', () => { });
it('should throw ValidationError when title is empty', () => { });
it('should trim whitespace from title', () => { });
```

### 测试类/文件命名

| 层级 | 命名规则 | 示例 |
|------|---------|------|
| 单元测试 | `<ClassName>Test` | `UserServiceTest.kt` |
| 集成测试 | `<ClassName>IntegrationTest` | `UserRepositoryIntegrationTest.kt` |
| E2E 测试 | `<FeatureName>E2E` | `LoginE2E.spec.ts` |

---

## 断言速查

### Kotlin（JUnit + AssertJ/mockK）

```kotlin
// 相等
assertEquals(expected, actual)
assertEquals(expected, actual, 0.01)  // 浮点数容差

// 真/假
assertTrue(condition)
assertFalse(condition)

// Null 检查
assertNotNull(value)
assertNull(value)

// 异常（JUnit 5）
val ex = assertThrows<UserNotFoundException> {
    service.getUser("invalid")
}
assertEquals("User not found", ex.message)

// 集合
assertEquals(3, list.size)
assertTrue(list.contains(item))
```

### Node.js/Jest

```typescript
// 相等
expect(result).toBe(expected);           // 严格相等 (===)
expect(result).toEqual(expected);        // 深度相等 (对象/数组)
expect(result).toStrictEqual(expected);  // 深度相等 + 类型匹配

// 真/假
expect(result).toBeTruthy();
expect(result).toBeFalsy();
expect(result).toBeNull();
expect(result).toBeDefined();

// 数值
expect(result).toBeGreaterThan(5);
expect(result).toBeLessThanOrEqual(10);
expect(result).toBeCloseTo(0.3, 5);      // 浮点数

// 字符串
expect(result).toMatch(/pattern/);
expect(result).toContain('substring');

// 数组/对象
expect(array).toContain(item);
expect(array).toHaveLength(3);
expect(object).toHaveProperty('key', 'value');

// 异常
expect(() => fn()).toThrow();
expect(() => fn()).toThrow(ValidationError);
expect(() => fn()).toThrow('specific message');

// 异步
await expect(asyncFn()).resolves.toBe(value);
await expect(asyncFn()).rejects.toThrow(Error);
```

### Python（pytest）

```python
# 相等
assert result == expected

# 异常
with pytest.raises(ValueError, match="specific message"):
    function_that_raises()

# 近似值
assert result == pytest.approx(0.3, abs=1e-5)

# 列表/字典
assert item in result
assert len(result) == 3
assert result["key"] == "value"
```

---

## Mock 策略

### 何时 Mock vs 不 Mock

| Mock 这些（边界） | 不 Mock 这些（内部） |
|---|---|
| 数据库调用 | 内部工具函数 |
| HTTP 请求 | 业务逻辑 |
| 文件系统操作 | 数据转换 |
| 外部 API 调用 | 验证函数 |
| 时间/日期（需要时） | 纯函数 |

### Kotlin（mockK）

```kotlin
// 正确：Mock 外部依赖
val mockRepo = mockk<UserRepository> {
    every { findUserById("1") } returns User("1", "Alice")
}
val service = UserService(mockRepo)

// 验证调用
verify { mockRepo.findUserById("1") }

// 错误：Mock 简单数据类
val mockUser = mockk<User> {
    every { name } returns "Alice"
}
val realUser = User("Alice") // 直接用数据类
```

### Kotlin 协程测试

```kotlin
// StateFlow 测试用 Turbine
@Test
fun `should emit loading then data`() = runTest {
    viewModel.userState.test {
        assertEquals(UserState.Loading, awaitItem())
        assertEquals(UserState.Success(user), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

### Java（Mockito）

```java
// Mock 外部依赖
UserRepository mockRepo = mock(UserRepository.class);
when(mockRepo.findById("1")).thenReturn(Optional.of(user));

UserService service = new UserService(mockRepo);

// 验证调用
verify(mockRepo).findById("1");
```

### Node.js/Jest

```typescript
// Mock 整个模块
jest.mock('./database', () => ({
    query: jest.fn().mockResolvedValue([{ id: 1, title: 'Test' }]),
}));

// Mock 部分导出
jest.mock('./utils', () => ({
    ...jest.requireActual('./utils'),
    generateId: jest.fn().mockReturnValue('test-id'),
}));

// Mock 函数
const mockFn = jest.fn();
mockFn.mockReturnValue(42);
mockFn.mockResolvedValue({ data: 'test' });
expect(mockFn).toHaveBeenCalledTimes(3);
```

---

## 语言特定模式

### Kotlin 测试框架选择

| 项目类型 | 强制框架 | 说明 |
|---------|---------|------|
| **KMP 多平台** | kotlin.test | 必须用 kotlin.test |
| **Android 专用** | JUnit 4/5 | 必须用 JUnit |
| **Flow 测试** | Turbine | StateFlow 测试必须用 |
| **协程测试** | kotlinx-coroutines-test | 挂起函数测试必须用 |

### Java 测试框架

- **JUnit 5** — 主测试框架
- **Mockito** — Mock 框架
- **AssertJ** — 断言库
- **Testcontainers** — 集成测试

### Node.js 测试框架

- **Jest** — 单元测试 + 集成测试
- **Vitest** — Vite 项目替代方案
- **supertest** — API 集成测试
- **Playwright** — E2E 浏览器测试

### Python 测试框架

- **pytest** — 主测试框架
- **pytest-asyncio** — 异步测试
- **pytest-cov** — 覆盖率报告

---

## 测试反模式

| 反模式 | 问题 | 正确做法 |
|---|---|---|
| 测试实现细节 | 重构时测试会坏 | 测试输入/输出，不测试中间步骤 |
| 快照万能 | 没人 review 快照 diff | 断言具体值，快照只用于稳定的 UI |
| 共享可变状态 | 测试互相污染 | 每个测试独立 setup/teardown |
| 测试第三方代码 | 浪费时间，不是你的 bug | 在边界处 Mock 第三方 |
| 跳过测试过 CI | 掩盖真实 bug | 修复或删除测试，不要 skip |
| 永久 `@Disabled`/`@Ignore` | 死代码 | 修复它或删掉它 |
| 宽泛断言 | 无法捕获回归 | 断言要具体、精准 |
| 异步不 await | 吞错误，假通过 | 所有异步测试必须 `await` |
| 测试私有方法 | 耦合实现细节 | 通过公共 API 间接验证 |
| Mock 一切 | 测试失去意义 | 只 Mock 外部边界 |
