# Kotlin 编码风格

Kotlin 特定的编码约定。通用约定见 `common/coding-style.md`。

## 格式化

- [必须]  使用 **ktlint** 或 **Detekt**
- [必须]  官方 Kotlin 代码风格（`kotlin.code.style=official`）

## 不可变性

- [必须]  优先 `val` 而非 `var`
- [必须]  值类型用 `data class`
- [必须]  状态更新用 `copy()`
- [禁止]  公共 API 中用可变集合

## 空安全

- [必须]  用安全调用：`?.`、`?:`
- [必须]  用 `requireNotNull()` 或 `checkNotNull()`
- [禁止]  用 `!!` 强制解包

## 命名约定

- [必须]  函数和属性：`camelCase`
- [必须]  类、接口、对象：`PascalCase`
- [必须]  常量：`SCREAMING_SNAKE_CASE`
- [禁止]  接口用 `I` 前缀

## 密封类型

- [必须]  用密封类/接口建模封闭状态
- [必须]  穷尽 `when`（不用 `else` 分支）

## 错误处理

- [必须]  用 `Result<T>` 或自定义密封类型
- [必须]  用 `runCatching {}` 包装可抛出代码
- [禁止]  捕获 `CancellationException`（必须重新抛出）
- [禁止]  用 `try-catch` 进行控制流

## 禁止行为

- [禁止]  深度嵌套作用域函数（最多 2 层）
- [禁止]  向 `Any` 或过度通用的类型添加扩展
