# Qt 编码风格

Qt / QML 特定约定。C++ 语言约定见 `cpp/coding-style.md`，通用约定见 `common/coding-style.md`。

本规范以 **Qt 6** 为准。新项目禁止以 Qt 5 为默认目标；维护 Qt 5 存量时须在 design.md 中显式记录，且不得把 Qt 5 API 引入新模块。

## 版本与构建

- [必须]  新项目 Qt **6.5 LTS 或 6.8 LTS**；同一产品线主版本一致
- [必须]  构建系统优先 **CMake**（`find_package(Qt6 REQUIRED COMPONENTS ...)`）
- [必须]  开启 `CMAKE_AUTOMOC`、`CMAKE_AUTORCC`、`CMAKE_AUTOUIC`
- [必须]  用 `qt_add_executable` / `qt_add_library` / `qt_add_qml_module`
- [必须]  链接只选需要的组件（`Core` `Gui` `Widgets` `Quick` `Network` `Sql` 等），禁止“全量 Qt”
- [禁止]  新项目使用 qmake（`.pro`）作为主构建；存量迁移须列入任务
- [禁止]  提交 `moc_*.cpp`、`ui_*.h`、`qrc_*.cpp` 生成物
- [禁止]  混用 Qt 5 与 Qt 6 头路径（`QtWidgets/QWidget` vs `Qt6` 安装前缀混乱）

## QObject 模型

- [必须]  需要信号槽、属性系统、父子所有权的类型才继承 `QObject`
- [必须]  `Q_OBJECT` 宏放在类声明的私有段第一行
- [必须]  父对象用 `QObject* parent = nullptr` 参数表达所有权；堆上 `QObject` 必须有 parent 或由 `unique_ptr` 独占
- [必须]  子对象由父对象析构树释放——**不要**再 `delete` 已有 parent 的子对象
- [必须]  需要跨线程观察 `QObject` 时用 `QPointer`，不要持有裸指针假定对象仍在
- [必须]  禁止拷贝的 `QObject` 子类：`Q_DISABLE_COPY_MOVE(ClassName)`
- [禁止]  在栈上创建将进入对象树且被异步使用的 `QObject`（生命周期结束即悬垂）
- [禁止]  多重继承两个 `QObject` 子类
- [禁止]  在未 `moveToThread` 的对象上假设“谁调用就在谁的线程”

## 信号与槽

- [必须]  使用成员函数指针语法：
  `connect(sender, &Sender::valueChanged, this, &Receiver::onValueChanged)`
- [必须]  跨线程连接显式指定 `Qt::QueuedConnection` 或 `Qt::BlockingQueuedConnection`，并文档化为何阻塞
- [必须]  槽名表达响应（`onXxx` 或 `handleXxx`）；信号名用过去式或状态（`clicked`、`stateChanged`、`errorOccurred`）
- [必须]  信号参数用值或 `QPrivateSignal` 保护；大数据用隐式共享类型（`QByteArray`、`QString`、`QImage`）
- [必须]  对象销毁时连接随 `QObject` 自动断开；lambda 捕获 `this` 必须用 `context` 参数：
  `connect(sender, &Sender::foo, this, [this] { ... })`
- [禁止]  `SIGNAL()` / `SLOT()` 宏（字符串连接，无编译期检查）
- [禁止]  信号循环：A→B→A 无守卫（用 blocker、标志或事务）
- [禁止]  在析构函数里 emit 仍被外部连接的信号（对象已部分销毁）
- [禁止]  GUI 对象直接从非 GUI 线程 emit 且连接类型为 `Auto` 却未确认 receiver 线程亲和性——应 queued

## 线程模型

- [必须]  **GUI 线程（主线程）只做 UI 与轻量调度**；采集、编解码、磁盘、网络解析放到 worker
- [必须]  `QWidget` / `QQuickItem` / `QWindow` 只能在创建它们的线程使用
- [必须]  Worker 优先：`QObject` + `moveToThread(QThread*)`，或 `QtConcurrent` / `QThreadPool` 做无状态任务
- [必须]  线程间通信用信号槽 queued，或 `QMetaObject::invokeMethod(..., Qt::QueuedConnection)`
- [必须]  退出时 `quit()` + `wait()` 线程，或 `QThread::deleteLater` 与事件循环配合，禁止强杀后访问其对象
- [禁止]  在 GUI 线程 `sleep`、忙等、同步等待网络/设备（允许短超时的本地锁，须说明）
- [禁止]  在非主线程构造 `QPixmap`（用 `QImage` 再在主线程转换）
- [禁止]  无锁共享 `QObject` 树；禁止两个线程同时写同一 `QObject`

## 字符串、容器与类型

- [必须]  Qt API 边界使用 `QString` / `QByteArray` / `QVariant`；内部算法可 `std::string`，边界显式转换
- [必须]  用户可见字符串用 `tr()` / `QCoreApplication::translate`，不得硬编码到 UI
- [必须]  UTF-8 源文件；`QString::fromUtf8` / `QString::fromStdString` 明确编码
- [必须]  与 Qt API 交互时可用 `QVector`/`QList`/`QHash`；纯算法优先 `std::vector`/`std::unordered_map`
- [必须]  隐式共享类型按值传递（`QString`、`QImage`、`QByteArray`），避免无谓的 `const QString&` 微优化破坏 NRVO 可读性时除外
- [禁止]  `QString::sprintf` 处理用户数据（格式漏洞）；用 `QStringLiteral`、`QString::arg`、`QLatin1String`
- [禁止]  在热路径反复 `QString::fromStdString` 无缓存
- [禁止]  `QList<T>` 存储大型非隐式共享值类型作为热路径默认（Qt 6 的 `QList` 已是数组，仍需避免频繁插入头部）

## 内存与父子所有权 vs 智能指针

Qt 对象树与 C++ 智能指针不要双重释放：

| 场景 | 做法 |
|------|------|
| `QWidget` / `QObject` 进入对象树 | `new Foo(parent)`，由 parent 释放 |
| 无 parent 的堆对象、非 QObject | `std::unique_ptr` |
| 需要与 Qt 树共存且由 C++ 拥有 | `parent = nullptr` + `unique_ptr`，或 `QObject::setParent` 后释放 `unique_ptr` 所有权 |
| 跨对象弱引用 | `QPointer<T>` |

- [禁止]  `unique_ptr<QObject>` 同时 `setParent` 到另一对象（双重 delete）
- [禁止]  `std::shared_ptr<QWidget>` 作为默认 UI 所有权模型

## Widgets

- [必须]  布局用 `QLayout`，禁止写死控件几何作为唯一适配手段（除必须像素对齐的绘制控件）
- [必须]  自定义绘制走 `paintEvent` + `QPainter`；状态变化 `update()`，需要立刻重绘才 `repaint()`
- [必须]  资源图用 Qt Resource（`.qrc`）或受控文件系统路径，禁止未处理的相对 cwd
- [必须]  尺寸策略与 `sizeHint`/`minimumSizeHint` 正确，避免布局抖动
- [禁止]  在 `paintEvent` 里分配重资源、读设备、取锁
- [禁止]  事件处理中修改正在遍历的对象树导致迭代器失效

## QML / Qt Quick

- [必须]  新 UI 在团队具备 QML 能力且交互偏动态时优先 Qt Quick；复杂原生控件/工业表格可 Widgets 或 `QQuickWidget` 混合，须在 design.md 记录
- [必须]  用 `qt_add_qml_module` 声明 URI 与版本；QML 里 import 该 URI，禁止散落 `Qt.include`
- [必须]  C++ 暴露给 QML 的类型：`QML_ELEMENT` / `qmlRegisterType` 等现代注册，属性用 `Q_PROPERTY`，集合用 `QAbstractListModel`
- [必须]  属性绑定保持无副作用；JS 里不要在绑定中写业务逻辑
- [必须]  大列表用 `ListView`/`TableView` 虚拟化，不用 Repeater 加载数千项
- [必须]  图像用 `QQuickImageProvider` 或异步 `Image`，注意 cache 与 sourceSize
- [禁止]  在 QML 热路径创建/销毁复杂 object；禁止绑定里 `console.log`
- [禁止]  从 QML 直接调用可能阻塞的 C++（设备 I/O）——应异步信号
- [禁止]  `eval`、动态拼接外部字符串当 QML 源

## 属性、元对象与 DPC

- [必须]  可被 QML/样式/调试观察的状态用 `Q_PROPERTY`，`NOTIFY` 信号在值真正变化时再 emit
- [必须]  setter 内比较新旧值，无变化不 emit
- [必须]  二进制兼容的库用 PIMPL + `Q_DECLARE_PRIVATE` / `d_ptr`
- [禁止]  在 getter 里修改状态或 emit
- [禁止]  `QVariant` 作为模块间主契约而不定义类型（调试时变成无类型泥团）

## 事件循环、定时器与 I/O

- [必须]  周期任务用 `QTimer`，单次用 `Qt::TimerType` 明确精度（`PreciseTimer` / `CoarseTimer`）
- [必须]  `QNetworkAccessManager` 按应用或按模块复用，不要每个请求 new 一个
- [必须]  网络/设备回调检查对象是否仍存活（`QPointer` 或 context connect）
- [必须]  长任务可取消：`QFutureWatcher` / 自己的 cancel flag，UI 有进度与取消
- [禁止]  `QEventLoop loop; loop.exec()` 重入主事件循环（模态对话框除外，且须评估重入风险）
- [禁止]  自定义 `QEvent` 不注册类型

## 日志与诊断

- [必须]  使用 `QLoggingCategory` + `qCDebug`/`qCInfo`/`qCWarning`/`qCCritical`
- [必须]  日志默认不输出敏感数据（路径中的用户目录、密钥、完整患者/用户标识等）
- [必须]  发布构建可关闭 debug 分类，保留 warning/critical
- [禁止]  用 `qDebug() <<` 打印大块二进制
- [禁止]  留在提交里的临时 `qDebug() << "here"`

## 测试

- [必须]  纯 C++ 逻辑用 Google Test；Qt 信号槽、事件、UI 用 **QTest**（`QTEST_MAIN` / `QTEST_GUILESS_MAIN`）
- [必须]  GUI 测试用 `QTest::qWaitFor` / 信号 spy（`QSignalSpy`），禁止固定 `sleep` 当同步
- [必须]  测试命名：`should_expected_when_method_given_scene`
- [必须]  不依赖屏幕焦点的逻辑放到无 GUI 测试（`QT_QPA_PLATFORM=offscreen`）
- [禁止]  单测依赖真实显示器、真实设备（设备测试标为集成/硬件测试并跳过 CI 无硬件任务）

## 静态分析

- [必须]  Qt 代码跑 **clazy**（至少 level1）
- [必须]  处理 clazy 的 `qcolor-from-literal`、`connect-3arg-lambda`、`incorrect-emit`、`range-loop-detach` 等
- [禁止]  为过 CI 全局禁用 clazy

## 禁止行为

- [禁止]  过时 API：`QMatrix`、`foreach` 宏、`QPtrList`、Qt 4 风格 connect
- [禁止]  `QString::null`、`QList::toSet` 等已删除 API 的兼容 hack 扩散到新文件
- [禁止]  在头文件用 `using namespace` 导入 Qt 命名空间
- [禁止]  把业务规则只写在 QML 里导致无法单测——领域逻辑在 C++
