# C++ 编码风格

C++ 特定的编码约定。通用约定见 `common/coding-style.md`。Qt 框架约定见 `qt/coding-style.md`。

本规范以 **C++17 为下限、C++20 为新代码默认**，对齐 [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) 与 Qt 项目常见实践。

## 语言与工具链

- [必须]  新代码默认 C++20；存量项目不得无故降到 C++17 以下
- [必须]  用 CMake 声明标准：`set(CMAKE_CXX_STANDARD 20)` 且 `CMAKE_CXX_STANDARD_REQUIRED ON`
- [必须]  启用 `CMAKE_CXX_EXTENSIONS OFF`（不用 GNU 方言）
- [必须]  使用 **clang-format** 统一格式（4 空格缩进，行宽 120）
- [必须]  使用 **clang-tidy**（至少 `bugprone-*`、`clang-analyzer-*`、`modernize-*`、`performance-*`）
- [推荐]  额外启用 cppcheck；Qt 代码额外启用 clazy（见 Qt 规范）
- [禁止]  关闭警告来“过编译”；禁止无注释的 `#pragma warning disable` / `-Wno-error=...`

## 格式化

- [必须]  4 空格缩进，禁止 Tab
- [必须]  每行最多 120 字符
- [必须]  头文件使用 `#pragma once`，或标准 include guard，二者择一且全项目统一
- [必须]  include 顺序：对应 `.h` → 本工程头文件 → 第三方 → C++ 标准库 → C 库；组间空行
- [必须]  尖括号用于系统/第三方，引号用于本工程头文件
- [禁止]  在头文件中 `using namespace ...`
- [禁止]  在 `.cpp` 中 `using namespace std;`（允许 `using std::string;` 等精确 using）

## 所有权与资源

- [必须]  RAII：每个资源（内存、文件、锁、句柄、socket）都有对象析构时释放
- [必须]  堆对象默认 `std::unique_ptr`；共享所有权才用 `std::shared_ptr`
- [必须]  工厂函数返回 `unique_ptr` 或按值，不返回需要调用者 `delete` 的裸指针
- [必须]  观察指针用裸指针或 `T*`/`T&`，并在注释/类型上标明“非拥有”
- [禁止]  裸 `new` / `delete` / `malloc` / `free`（Qt 父子所有权场景见 Qt 规范）
- [禁止]  手动 `lock()`/`unlock()`；必须用 `std::lock_guard` / `std::unique_lock` / `std::scoped_lock`
- [禁止]  返回局部对象的指针或引用

## 类与特殊成员

- [必须]  能用 Rule of Zero 就不要手写拷贝/移动/析构
- [必须]  定义了析构、拷贝或移动中的任意一个，必须显式定义或 `= delete` 其余四个（Rule of Five）
- [必须]  多态基类析构函数为 `virtual`，或基类不可被多态删除
- [必须]  单参数构造函数标 `explicit`（拷贝/移动除外）
- [必须]  成员按声明顺序在初始化列表中初始化；优先类内默认初始化
- [禁止]  在构造函数中调用虚函数并依赖派生类覆写
- [禁止]  切片拷贝多态对象（按值传递基类）

## const、constexpr 与不可变性

- [必须]  不修改的参数、局部变量、成员函数标 `const`
- [必须]  编译期常量用 `constexpr` 或 `const`；枚举值用 `enum class`
- [必须]  只读视图优先 `std::string_view` / `std::span`，注意生命周期
- [禁止]  `const_cast` 去掉 const 后修改对象（除非对接无 const 的 C API，且对象本身并非 const）
- [禁止]  用宏定义常量（`#define MAX 10`）

## 类型与接口

- [必须]  错误码、状态、模式用 `enum class`，不用无作用域 `enum` 或魔数
- [必须]  可选值用 `std::optional`；多返回用结构化绑定或具名结构体
- [必须]  所有权转移的参数用 `unique_ptr` 或按值；只读用 `const T&`；可空观察用 `const T*`
- [必须]  重载 `==` 时同步考虑 `!=`（C++20 可用 `= default`）
- [禁止]  C 风格强制转换；用 `static_cast` / `dynamic_cast` / `const_cast` / `reinterpret_cast` 并说明理由
- [禁止]  `dynamic_cast` 作为常规控制流；优先虚函数或访问者模式
- [禁止]  函数参数超过 4 个——改为参数对象或拆函数

## 错误处理

- [必须]  项目级统一错误策略：异常 **或** `std::expected`/`QResult` 风格错误码，禁止混用两套而不加边界
- [必须]  异常安全：优先强保证（操作失败则状态回滚），最低基本保证（不泄漏、不破坏不变式）
- [必须]  不允许失败的函数标 `noexcept`（析构、移动、swap 默认 `noexcept`）
- [必须]  错误消息描述失败原因与上下文，不丢弃 `std::exception::what()`
- [禁止]  空 `catch (...)` 或只 `catch` 不处理
- [禁止]  析构函数抛异常
- [禁止]  用异常做正常控制流

## 现代 C++ 特性

- [必须]  用 `nullptr`，不用 `NULL` 或 `0` 表示空指针
- [必须]  用 `override` 标记覆写；禁止依赖名字碰巧相同
- [必须]  范围 for、`auto` 用于迭代器和明显类型；接口与成员声明写明类型
- [必须]  用 `std::move` 转移即将销毁的对象；禁止对再使用的对象 `std::move`
- [必须]  用 `[[nodiscard]]` 标记不得忽略的返回值（工厂、错误码、资源句柄）
- [推荐]  C++20：`concepts` 约束模板、`std::span`、`std::format`（或 Qt 的 `QString::arg`）、ranges
- [禁止]  `using namespace` 导入用户定义字面量以外的整命名空间到头文件
- [禁止]  VLAs、零长数组等非标准扩展

## 命名约定

Qt 工程（含 `QObject`、QML 交互、signals/slots）遵循 Qt 命名，与 `rules/qt/` 一致：

- [必须]  类、枚举、类型别名：`PascalCase`（`WaveformRenderer`、`DeviceState`）
- [必须]  函数、方法：`camelCase`（`startAcquisition()`、`isConnected()`）
- [必须]  成员变量：`m_` 前缀 + camelCase（`m_sampleRate`）
- [必须]  静态成员：`s_` 前缀；常量：`k` 前缀或 `SCREAMING_SNAKE_CASE`，全项目统一
- [必须]  命名空间：全小写，短且与目录对应（`app::device`）
- [必须]  布尔：`is`/`has`/`can`/`should` 前缀
- [禁止]  匈牙利命名（`pPtr`、`nCount`、`szName`）
- [禁止]  接口用 `I` 前缀（`IDevice`）——用角色后缀（`DevicePort`、`IpcClient`）或纯抽象类名

纯算法 / 无 Qt 依赖的库模块允许 STL 风格 `snake_case` 函数名，但同一目录不得混用两套。

## 头文件与模块边界

- [必须]  头文件自给自足：只 include 自己用到的，可用前向声明则不用完整定义
- [必须]  一个头文件一个主要职责；`QObject` 子类的 moc 头文件与实现一一对应
- [必须]  公共 API 头文件不泄漏第三方类型（除非该依赖是公共契约的一部分）
- [推荐]  ABI 稳定的库用 PIMPL（`Q_DECLARE_PRIVATE` 或 `std::unique_ptr<Impl>`）
- [禁止]  循环 include；CMake 里用 include 图或 clangd 检测
- [禁止]  在头文件写 using 别名污染全局命名空间

## 并发

- [必须]  共享可变状态有明确保护（mutex、无锁结构或消息传递）
- [必须]  文档化每个对象的线程约定（谁拥有、哪条线程调用）
- [必须]  跨线程所有权转移用 `std::unique_ptr` 或 Qt 的 queued 调用，不在两边同时写
- [禁止]  数据竞争（C++ 定义为未定义行为）
- [禁止]  在持锁时做 I/O、回调用户代码、或再获取未文档化的锁（防死锁）

## 未定义行为与安全

- [必须]  数组/容器访问前检查边界，或使用 `.at()` / 已证明合法的 `[]`
- [必须]  整数运算注意溢出；位运算用无符号类型并写明宽度
- [必须]  Debug 构建开启 sanitizer：ASan + UBSan（MSVC 用 `/fsanitize=address` 或对应方案）
- [禁止]  未初始化读取、悬垂指针、迭代器失效后解引用、signed overflow 依赖
- [禁止]  `memcpy` 非平凡可复制类型；用 `std::copy` 或类型提供的接口
- [禁止]  函数指针/模板回调里捕获悬垂 `this`

## 测试方法命名

- [必须]  Google Test：`TEST(ClassName, should_expected_when_method_given_scene)`
- [必须]  或 `TEST_F(Fixture, should_returnFalse_when_parse_given_emptyBuffer)`
- [必须]  命名使用英文，语义清晰，描述意图、触发条件、输入
- [推荐]  示例：`should_returnFalse_when_deleteContent_given_invokeFailed`
- [推荐]  示例：`should_ignoreDuplicate_when_enqueue_given_sameSequenceId`

## 禁止行为

- [禁止]  预处理宏实现函数（用 `inline`/`constexpr`/模板）
- [禁止]  全局可变状态（除经评审的 Meyer's singleton 或进程级服务定位，且可测试注入）
- [禁止]  忽略 `[[nodiscard]]` 返回值
- [禁止]  `std::endl` 刷新热路径日志（用 `'\n'`）
- [禁止]  在热路径抛异常作为预期分支
