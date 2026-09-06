# 架构检查清单

用于代码审查中的架构维度检查。好架构的标志：变更成本低、测试容易、理解简单。默认栈：C++ / Qt。

## 核心检查项

### 1. 分层清晰

| 层级 | 职责 | 依赖方向 |
|------|------|---------|
| **UI（Widgets / QML）** | 显示、输入、绑定 | 仅依赖 ViewModel / Presenter |
| **应用/用例层** | 流程编排 | 依赖领域与端口接口 |
| **领域层** | 规则、实体 | 无 GUI、无设备驱动 |
| **适配器** | Qt SQL、串口、网络、文件 | 实现端口，隔离第三方 |

**检查项**：
- [ ] 上层依赖下层，不反向依赖
- [ ] 无跨层调用（如 `QWidget` 直接 `QSqlQuery`）
- [ ] 数据流单向（无循环依赖）
- [ ] 层间通过抽象接口通信
- [ ] `domain` 不 include `QWidget` / `QQuickItem`

```cpp
// 错误：UI 直接依赖设备
class MainWindow : public QMainWindow {
    QSerialPort m_port;
    void onStart() { m_port.write("START\n"); }
};

// 正确：经端口抽象
class MainWindow : public QMainWindow {
    DeviceController* m_controller = nullptr;
    void onStart() { m_controller->start(); }
};
```

### 2. 依赖方向

- [ ] 依赖指向抽象，不指向具体 `QSerialPort` / 第三方 SDK
- [ ] 无循环依赖（A 的头文件 include B，B include A）
- [ ] 外部库被 adapter 隔离
- [ ] CMake `target_link_libraries` 不把 Qt::Widgets 链到 domain 目标

**循环依赖检测**：

```bash
# include 环（示例）
cmake --build build --target cmake_graph 2>/dev/null || true
# 或 clangd / iwyu / 自写 include 图
```

### 3. 抽象合理

| 检查项 | 说明 |
|--------|------|
| **抽象必要性** | 只有一个实现且无测试替换，不要为了“接口”再包一层 |
| **单一职责** | 每个类只有一个变更理由 |
| **接口分离** | 纯虚端口小而专注 |
| **依赖倒置** | 用例不依赖 `QNetworkAccessManager` 细节 |

**抽象过度的信号**：
- 只有一个实现且从不 Fake
- 接口名是 `IWhatever`
- 抽象比实现更难理解
- 为了“将来扩展”而抽象

```cpp
// 错误：三层纯虚，实际一个实现
class IUserService { public: virtual User fetch(const QString&) = 0; };
class IUserRepository { public: virtual User fetch(const QString&) = 0; };
class IUserDataStore { public: virtual User fetch(const QString&) = 0; };

// 正确：一层端口
class UserRepository {
public:
    virtual ~UserRepository() = default;
    virtual std::optional<User> fetch(const QString& id) const = 0;
};
```

### 4. 模块边界

- [ ] 模块间通过 CMake target 与公共头通信
- [ ] 模块内高内聚
- [ ] 模块间低耦合
- [ ] 不在公共头泄漏 `Q_OBJECT` 实现细节（可用 PIMPL）

### 5. 可测试性

- [ ] 依赖可注入（构造函数注入优先）
- [ ] 无 `Xxx::instance()` 硬单例作为唯一入口
- [ ] 无进程级可变全局
- [ ] 设备/网络/磁盘可 Fake

```cpp
// 错误
class DeviceController {
    QSerialPort m_port; // 无法替换
};

// 正确
class DeviceController {
public:
    explicit DeviceController(DevicePort* port) : m_port(port) {}
private:
    DevicePort* m_port = nullptr; // 测试传入 Fake
};
```

### 6. 扩展性

- [ ] 新增协议版本通过策略/表驱动，而不是改遍 switch
- [ ] 配置外部化（`QSettings`、JSON、构建选项）
- [ ] QML 主题/字符串不嵌入业务常量散落各处

## 设计原则检查（SOLID）

| 原则 | 检查项 |
|------|--------|
| **SRP 单一职责** | 每个类/函数只有一个变更理由 |
| **OCP 开闭原则** | 对扩展开放，对修改关闭 |
| **LSP 里氏替换** | 子类可替换基类而不破坏不变式 |
| **ISP 接口分离** | 接口小而专注 |
| **DIP 依赖倒置** | 依赖抽象 |

### Qt 补充

- [ ] `QObject` 只出现在需要信号槽/对象树的边界
- [ ] 继承层级浅（优先组合：`QObject` 成员而不是深继承窗体）
- [ ] GUI 线程与 worker 边界清晰，接口文档写明线程
- [ ] QML 只绑定 ViewModel，不 new 设备对象

```cpp
// 错误：DIP 违反
class NetworkService {
    QNetworkAccessManager m_nam; // 硬依赖
};

// 正确
class HttpClient {
public:
    virtual ~HttpClient() = default;
    virtual QByteArray get(const QUrl& url) = 0;
};

class NetworkService {
public:
    explicit NetworkService(HttpClient* client) : m_client(client) {}
private:
    HttpClient* m_client = nullptr;
};
```

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **上帝窗口** | `MainWindow.cpp` 三千行 | 拆 Presenter/控件/用例 |
| **循环依赖** | A↔B | 抽出接口或事件 |
| **依赖泄露** | UI include 厂商 SDK | adapter |
| **过度抽象** | 5 层 1 个实现 | 删除 |
| **单例滥用** | 全局 `App::inst()` | 组合根注入 |
| **QML 写业务** | 无法单测 | 逻辑回 C++ |
| **对象树+unique_ptr 双拥有** | double free | 只选一种所有权 |

## 审查技巧

1. **依赖图**：CMake target 与 include 有没有环
2. **变更追踪**：改协议要动几个目录？
3. **测试难度**：能否不插真串口跑通用例
4. **线程**：画出 GUI / worker / 设备

## 警示信号

- 一个文件超过 800 行
- 一个函数超过 50 行
- 类名包含 `Manager`、`Helper`、`Util` 且什么都做
- 测试需要启动整个 `QApplication` 才能测加法
- 新增功能必须改 `MainWindow` 的 10 处
