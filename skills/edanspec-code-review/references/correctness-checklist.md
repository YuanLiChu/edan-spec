# 正确性检查清单

用于代码审查中的正确性维度检查。正确性是最基本的要求——代码能跑不等于正确。

## 核心检查项

### 1. 需求满足

- [ ] 功能行为与任务描述/spec 一致
- [ ] 所有验收标准已实现
- [ ] 无遗漏的边缘场景
- [ ] Bug 修复已验证（有复现测试 + 修复测试）

### 2. 边界条件

| 边界类型 | 检查项 |
|---------|--------|
| **空值** | null/nil 已处理，Optional 已解包 |
| **空集合** | 空数组/字典/集合已处理 |
| **零值** | 0、空字符串已处理 |
| **最大值** | Int.max、集合上限已处理 |
| **负值** | 负数输入已拒绝或处理 |

```kotlin
// 错误：未处理空集合
fun calculateAverage(numbers: List<Int>): Int {
    return numbers.sum() / numbers.size  // size=0 时崩溃
}

// 正确：处理边界
fun calculateAverage(numbers: List<Int>): Int? {
    if (numbers.isEmpty()) return null
    return numbers.sum() / numbers.size
}
```

### 3. 错误处理

- [ ] 外部调用（网络、数据库、文件）有错误处理
- [ ] 异常捕获后不吞掉错误（至少记录日志）
- [ ] 错误消息清晰描述问题，不暴露内部细节
- [ ] 资源已正确关闭（连接、流、监听器）
- [ ] 失败后有合理的回滚或补偿

```kotlin
// 错误：静默吞掉错误
fun loadData() {
    try {
        repository.fetch()
    } catch (e: Exception) {
        // 什么都不做
    }
}

// 正确：记录并传播
fun loadData() {
    try {
        repository.fetch()
    } catch (e: Exception) {
        logger.error("Failed to load data", e)
        throw DataLoadException("Unable to refresh data")
    }
}
```

### 4. 并发安全

- [ ] 共享可变状态有同步机制
- [ ] 异步操作有完成/取消处理
- [ ] 无死锁风险（锁顺序一致）
- [ ] 回调/协程在线程正确
- [ ] 竞态条件已排除

```kotlin
// 错误：竞态条件
var count = 0
fun increment() {
    count++  // 非原子操作，多线程下会丢失更新
}

// 正确：使用原子类或同步
private val count = AtomicInteger(0)
fun increment() {
    count.incrementAndGet()
}
```

### 5. 状态转换

- [ ] 状态机转换完整（无死状态）
- [ ] 无效状态转换已拒绝
- [ ] 状态变更通知了观察者
- [ ] 持久化状态与实际一致

### 6. 数据完整性

- [ ] 输入数据已验证（类型、范围、格式）
- [ ] 输出数据符合预期格式
- [ ] 数据库事务有正确的隔离级别
- [ ] 级联删除/更新已处理
- [ ] 外键约束已遵守

### 7. 测试正确性

- [ ] 测试真正验证了行为（不是只跑代码）
- [ ] 测试独立（不依赖执行顺序）
- [ ] 测试覆盖了正常路径 + 异常路径
- [ ] Mock 使用合理（不过度模拟）
- [ ] 无脆弱的断言（如时间戳、随机数）

## 语言特定检查项

### Swift

- [ ] Optional 安全解包（避免 `!` 强制解包）
- [ ] weak/unowned 打破循环引用
- [ ] main 线程更新 UI
- [ ] async/await 正确传播 actor 隔离
- [ ] Result 类型处理成功/失败

```swift
// 错误：强制解包 + 循环引用
viewModel.onLogin = { user in
    self.user = user!  // user 可能为 nil，self 可能循环引用
}

// 正确：安全解包 + weak
viewModel.onLogin = { [weak self] user in
    guard let user = user else { return }
    self?.user = user
}
```

### Kotlin

- [ ] 避免 `!!` 强制解包
- [ ] 协程 scope 正确（Lifecycle 感知）
- [ ] Flow/StateFlow 正确处理背压
- [ ] sealed class 穷尽 when 表达式
- [ ] suspend 函数不阻塞线程

### Java

- [ ] Optional 正确使用（map/flatMap/orElseThrow）
- [ ] Stream 操作终止
- [ ] 线程池正确关闭
- [ ] Comparable 与 equals/hashCode 一致
- [ ] @Override 标注正确

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **过早返回成功** | 未验证完成就返回 | 验证所有前置条件 |
| **异常当控制流** | try-catch 做分支判断 | 用 if-else 前置检查 |
| **魔法数字** | 硬编码索引/长度 | 用命名常量 |
| **过度嵌套** | if 嵌套超 3 层 | 用 guard/early return |
| **隐式类型转换** | 依赖自动转换 | 显式转换 |

## 审查技巧

1. **逆向思维**：假设代码是错的，找证据证明
2. **边界优先**：先检查极端情况，再看正常路径
3. **追踪数据流**：从输入到输出，跟一遍数据
4. **问"如果"**：如果网络超时？如果数据库为空？如果并发调用？

## 警示信号

- 没有处理 null/空集合
- catch 块为空或只打印
- 测试只覆盖正常路径
- 函数有多个返回点但未覆盖所有路径
- 修改了共享状态但无同步
