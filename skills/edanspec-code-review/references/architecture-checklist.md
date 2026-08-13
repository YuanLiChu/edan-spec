# 架构检查清单

用于代码审查中的架构维度检查。好架构的标志：变更成本低、测试容易、理解简单。

## 核心检查项

### 1. 分层清晰

| 层级 | 职责 | 依赖方向 |
|------|------|---------|
| **UI/展示层** | 用户界面、视图状态 | 仅依赖 ViewModel/Presenter |
| **业务逻辑层** | 业务规则、用例 | 仅依赖领域模型、接口 |
| **数据访问层** | 持久化、网络请求 | 依赖外部库 |
| **领域层** | 核心业务模型 | 无外部依赖 |

**检查项**：
- [ ] 上层依赖下层，不反向依赖
- [ ] 无跨层调用（如 UI 直接调用 Repository）
- [ ] 数据流单向（无循环依赖）
- [ ] 层间通过接口/协议通信

```kotlin
// 错误：跨层调用
class LoginViewModel {
    private val api = RetrofitClient.create()  // UI 层直接依赖网络库
    
    fun login() {
        api.login(...)  // 应通过 Repository
    }
}

// 正确：通过 Repository 抽象
class LoginViewModel(
    private val authRepository: AuthRepository
) {
    fun login() {
        authRepository.login(...)
    }
}
```

### 2. 依赖方向

- [ ] 依赖指向抽象（接口/协议），不指向具体实现
- [ ] 无循环依赖（A 依赖 B，B 依赖 A）
- [ ] 外部库依赖被隔离（adapter 模式）
- [ ] 稳定依赖稳定（易变模块不依赖稳定模块）

**循环依赖检测**：
```bash
# 查找循环依赖（需要工具支持）
./gradlew dependencies --configuration compileClasspath
```

### 3. 抽象合理

| 检查项 | 说明 |
|--------|------|
| **抽象必要性** | 这个抽象真的需要吗？还是过度设计？ |
| **单一职责** | 每个类/模块只有一个变更理由 |
| **接口分离** | 接口小而专注，不臃肿 |
| **依赖倒置** | 高层模块不依赖低层细节 |

**抽象过度的信号**：
- 只有一个实现
- 接口名是 `IWhatever` 或 `WhateverProtocol`
- 抽象比实现更难理解
- 为了"将来扩展"而抽象

```swift
// 错误：过度抽象
protocol UserServiceProtocol {
    func fetchUser(id: String) async throws -> User
}
protocol UserRepositoryProtocol {
    func fetchUser(id: String) async throws -> User
}
protocol UserDataStoreProtocol {
    func fetchUser(id: String) async throws -> User
}
// 三层抽象，实际只有一个实现

// 正确：必要抽象
protocol UserRepository {
    func fetchUser(id: String) async throws -> User
}
// 一层抽象，足够
```

### 4. 模块边界

- [ ] 模块间通过明确定义的接口通信
- [ ] 模块内高内聚（相关代码在一起）
- [ ] 模块间低耦合（最小化跨模块依赖）
- [ ] 公共 API 精简（内部实现不暴露）

### 5. 可测试性

- [ ] 依赖可注入（构造函数注入优先）
- [ ] 无单例硬依赖（单例不可测试）
- [ ] 无全局状态（global/static 变量）
- [ ] 副作用隔离（I/O、网络、数据库可 Mock）

```kotlin
// 错误：硬依赖单例，无法测试
class LoginViewModel {
    private val api = ApiClient.instance  // 无法替换为 Mock
}

// 正确：依赖注入，可测试
class LoginViewModel(
    private val api: AuthApi  // 测试时可传入 Mock
)
```

### 6. 扩展性

- [ ] 新增功能不需要修改现有代码（开闭原则）
- [ ] 新增类型不需要修改现有逻辑
- [ ] 配置外部化（不硬编码）
- [ ] 插件点清晰（需要扩展的地方有抽象）

## 设计原则检查（SOLID）

| 原则 | 检查项 |
|------|--------|
| **SRP 单一职责** | 每个类/函数只有一个变更理由 |
| **OCP 开闭原则** | 对扩展开放，对修改关闭 |
| **LSP 里氏替换** | 子类可替换父类而不破坏程序 |
| **ISP 接口分离** | 接口小而专注，不强迫实现无关方法 |
| **DIP 依赖倒置** | 依赖抽象，不依赖具体实现 |

### SRP 检查
- [ ] 类名准确反映职责
- [ ] 一个类不做两件不相关的事
- [ ] 函数不做多件 unrelated 的事

### OCP 检查
- [ ] 新增功能通过新增类/函数，而非修改现有代码
- [ ] 用策略模式/多态代替 if-else 链
- [ ] 配置/规则外部化

### LSP 检查
- [ ] 子类不抛出父类不抛的异常
- [ ] 子类不缩小父类的前置条件
- [ ] 子类不扩大父类的后置条件

### ISP 检查
- [ ] 接口不超过 5 个方法
- [ ] 调用者不依赖它不用的方法
- [ ] 用多个小接口代替一个大接口

### DIP 检查
- [ ] 高层模块依赖抽象
- [ ] 低层模块实现抽象
- [ ] 具体实现依赖抽象

## 语言特定检查项

### Swift

- [ ] 协议定义清晰边界
- [ ] 类继承层级浅（≤ 3 层）
- [ ] 优先组合而非继承
- [ ] Actor 隔离正确（并发安全）
- [ ] 依赖注入用协议类型

```swift
// 错误：违反 DIP
class NetworkService {
    private let urlSession = URLSession.shared  // 硬依赖
}

// 正确：依赖抽象
protocol HTTPClient {
    func send(_ request: URLRequest) async throws -> Data
}

class NetworkService(client: HTTPClient) {
    private let client: HTTPClient  // 依赖抽象
}
```

### Kotlin

- [ ] 接口职责单一
- [ ] 继承层级浅（优先组合）
- [ ] 用 sealed class 建模状态
- [ ] CoroutineScope 注入（测试可控）
- [ ] Repository 模式正确隔离数据源

### Java

- [ ] 接口/抽象类职责清晰
- [ ] 依赖注入框架正确使用（Spring/Dagger）
- [ ] 包结构反映分层
- [ ] 公共 API 精简（internal 不暴露）
- [ ] 无循环依赖

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **上帝对象** | 一个类做所有事 | 拆分职责 |
| **循环依赖** | A 依赖 B，B 依赖 A | 引入抽象层 |
| **依赖泄露** | 上层依赖下层实现 | 依赖倒置 |
| **过度抽象** | 5 层抽象 1 个实现 | 删除不必要的 |
| **单例滥用** | 全局状态无法测试 | 依赖注入 |
| **跨层调用** | UI 直接调 DAO | 通过中间层 |

## 审查技巧

1. **依赖图**：画出来，看是否有环
2. **变更追踪**：改一个地方需要改几个地方？
3. **测试难度**：好架构的代码容易测试
4. **新人理解成本**：新人多久能理解结构？

## 警示信号

- 一个文件超过 800 行
- 一个函数超过 50 行
- 类名包含 `Manager`、`Helper`、`Util`（可能是上帝对象）
- 测试需要大量 Mock 设置
- 新增功能需要修改多处现有代码
- 导入了很多包但只用了一两个类
