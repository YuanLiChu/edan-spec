# 可读性检查清单

用于代码审查中的可读性维度检查。代码是写给人看的，其次才是机器。

## 核心检查项

### 1. 命名清晰

| 检查项 | 说明 |
|--------|------|
| **无缩写** | 除非是团队通用缩写（如 ID、URL） |
| **无模糊名称** | 避免 data、info、temp、flag 等无意义名称 |
| **动词 + 名词** | 函数名用 `doSomething()`，布尔用 `is/has/can` 前缀 |
| **一致性** | 同一概念在整个项目中用同一名称 |
| **长度适中** | 局部变量可短，公共 API 要完整 |

```kotlin
// 错误：模糊命名
fun proc(d: List<Map<String, Any>>): Map<String, Any> {
    var r = mapOf<String, Any>()
    for (i in d) {
        if (i["active"] == true) r = i
    }
    return r
}

// 正确：清晰命名
fun findFirstActiveUser(users: List<User>): User? {
    return users.find { it.isActive }
}
```

### 2. 控制流简洁

- [ ] 无深层嵌套（≤ 3 层）
- [ ] 用 early return / guard 减少嵌套
- [ ] 复杂条件提取为私有函数或布尔变量
- [ ] 无冗长的 if-else 链（用 when/match/策略模式）

```kotlin
// 错误：深层嵌套
fun processOrder(order: Order): Result {
    if (order.isValid) {
        if (order.isPaid) {
            if (order.hasStock) {
                return ship(order)
            }
        }
    }
    return Result.failed
}

// 正确：early return
fun processOrder(order: Order): Result {
    if (!order.isValid) return Result.failed
    if (!order.isPaid) return Result.failed("Order not paid")
    if (!order.hasStock) return Result.failed("Out of stock")
    return ship(order)
}
```

### 3. 函数大小

| 指标 | 阈值 |
|------|------|
| **行数** | < 50 行（理想 < 30 行） |
| **参数** | ≤ 4 个（超过用参数对象） |
| **职责** | 1 个（函数名能完整描述） |

**拆分信号**：
- 需要注释来解释一段代码在做什么
- 函数内有多个逻辑阶段
- 参数超过 4 个
- 缩进层级超过 3 层

### 4. 注释恰当

- [ ] 注释解释 **为什么** 而非 **做什么**
- [ ] 无废话注释（如 `i++ // i 加 1`）
- [ ] 复杂算法/业务规则有注释
- [ ] 公开 API 有文档注释
- [ ] 注释与代码同步更新

```kotlin
// 错误：废话注释
// 设置用户名称
user.name = name

// 错误：注释做什么
// 遍历用户列表并过滤活跃用户
val activeUsers = users.filter { it.isActive }

// 正确：注释为什么
// 使用 UTC 时间戳避免时区问题（后端存储要求）
val timestamp = Instant.now().toEpochMilli()
```

### 5. 表达式简洁

- [ ] 用标准库函数（map/filter/let/also）
- [ ] 无冗余代码（未使用的变量、死代码）
- [ ] 字符串用模板而非拼接
- [ ] 集合操作链式调用（不超过 5 步）

```kotlin
// 错误：冗余代码
var result: String? = null
if (user != null) {
    result = user.name
}
return result

// 正确：简洁表达式
return user?.name
```

### 6. 格式一致

- [ ] 缩进一致（2 空格或 4 空格）
- [ ] 空行分隔逻辑段落
- [ ] 导入按组排序
- [ ] 类成员顺序一致（属性→构造→公共→私有）

## 语言特定检查项

### Swift

- [ ] 遵循 Swift 官方 API 设计指南
- [ ] 用 `guard` 做前置条件检查
- [ ] 用 `defer` 做清理
- [ ] 闭包参数用 trailing closure 语法
- [ ] 枚举值用 camelCase

```swift
// 错误：未用 guard
func process(_ data: Data?) {
    if let data = data {
        // 处理数据
    }
}

// 正确：guard 前置检查
func process(_ data: Data?) {
    guard let data = data else { return }
    // 处理数据
}
```

### Kotlin

- [ ] 遵循 Kotlin 代码风格指南
- [ ] 用 `?.` `?:` 处理 null
- [ ] 用 `let`/`also`/`apply`/`takeIf`
- [ ] 对象声明用 `data class`/`sealed class`
- [ ] 扩展函数有明确接收者

### Java

- [ ] 遵循 Oracle Java 代码约定
- [ ] 用 `Optional` 代替 null 返回
- [ ] 用 record 代替冗长的 getter/setter
- [ ] 用 switch 表达式代替多分支
- [ ] Stream 操作可读（不超过 5 步链式）

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **聪明代码** | 用技巧炫技，难理解 | 用直白写法 |
| **缩写癖** | UserManager → UMgr | 用完整拼写 |
| **注释重复代码** | 注释只是翻译代码 | 解释意图或删除 |
| **过长链式** | a.b.c.d().e().f().g() | 拆分中间变量 |
| **魔法字符串** | `if type == "USR"` | 用常量或枚举 |

## 审查技巧

1. **大声朗读**：读不出来的命名就是不好的
2. **新人测试**：新人能看懂吗？
3. **6 个月测试**：6 个月后的你能看懂吗？
4. **删除注释测试**：删掉注释还能懂，说明代码够清晰

## 警示信号

- 需要超过 2 句话解释函数在做什么
- 函数名和实现不一致
- 有未使用的导入、变量、函数
- 缩进超过 4 层
- 单行超过 120 字符
- 有多个逻辑但只用一个函数名
