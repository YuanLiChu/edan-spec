# 修复策略

edanspec:debugging skill 的补充参考文档，详述各类错误的修复方法和反模式。

> 测试编写模式（AAA、命名、断言、Mock）详见 `testing-patterns.md`。

## 最小改动原则

**只修必要的部分，不改动其他代码。**

```kotlin
// 场景：计算总价时没有乘以数量

// 原代码
fun calculateTotal(items: List<Item>): Double {
    return items.sumOf { it.price }
}

// 错误修复：顺便"优化"代码结构
fun calculateTotal(items: List<Item>): Double {
    return if (items.isEmpty()) {
        0.0
    } else {
        items.map { it.price * it.quantity }.sum() // 提取为 map + sum
    }
}

// 正确修复：最小改动
fun calculateTotal(items: List<Item>): Double {
    return items.sumOf { it.price * it.quantity } // 只添加 quantity
}
```

## 常见错误修复策略

### 1. 逻辑错误修复

**类型**：条件判断错误、算法错误、返回值错误

```kotlin
// 测试失败
@Test
fun `should return true for valid email`() {
    val result = validator.validateEmail("test@example.com")
    assertTrue(result) // Actual: false
}

// 原代码：逻辑反转
fun validateEmail(email: String): Boolean {
    return !email.contains("@") // 错误：应该是 contains
}

// 修复：纠正逻辑（移除 !）
fun validateEmail(email: String): Boolean {
    return email.contains("@")
}
```

### 2. 边界情况修复

**类型**：空值、零值、边界值未处理

```kotlin
// 测试失败
@Test
fun `should handle empty list`() {
    val result = calculator.calculateTotal(emptyList())
    assertEquals(0.0, result) // Actual: 抛出 NoSuchElementException
}

// 原代码：边界未处理
fun calculateTotal(items: List<Item>): Double {
    return items.sumOf { it.price * it.quantity } // 空列表抛异常
}

// 修复：添加边界处理
fun calculateTotal(items: List<Item>): Double {
    return if (items.isEmpty()) 0.0 else items.sumOf { it.price * it.quantity }
}
```

### 3. 空指针修复

**类型**：对象未初始化、返回 null

```kotlin
// 测试失败
@Test
fun `should return user name`() {
    val user = service.getUser("123")
    assertEquals("Alice", user.name) // NullPointerException
}

// 修复：添加空值处理
fun getUser(id: String): User {
    return repository.findUserById(id)
        ?: throw UserNotFoundException(id)
}
```

### 4. Mock 配置修复

**类型**：Mock 数据不正确、Mock 行为不匹配

```kotlin
// 测试失败
@Test
fun `should return user from repository`() {
    val result = service.getUser("123")
    assertEquals("Alice", result.name) // Actual: "Bob"
}

// 修复：纠正 Mock 数据
every { findUserById("123") } returns User("Alice", "alice@example.com")
```

## 常见修复反模式

### 反模式 1：过度修复

修复一个 bug 时重写了整个方法，引入新问题。

### 反模式 2：修复测试而非代码

修改测试期望值来让错误代码"通过"。

### 反模式 3：引入新问题

修复空值时用死循环阻塞等待，或修复时引入新的依赖问题。

### 反模式 4：治标不治本

只在表面添加 null check，而不追查为什么应该是非空的地方返回了 null。
