# Qt 桌面项目技术参考

> 供 create-spec / design-review 决策确认。目标栈：**C++20 + Qt 6 + CMake**。嵌入式 Linux 见 [platform-embedded.md](platform-embedded.md)。

---

## 一、架构模式

### 架构对比

| 架构 | 职责分离 | 可测试性 | 学习成本 | 状态管理 | 适用场景 |
|-----|---------|---------|---------|---------|---------|
| **MVC（Widgets）** | 低 | 低 | 低 | 手动 | 小型工具、对话框式程序 |
| **MVP（Widgets）** | 中 | 中 | 中 | 手动 | 中型 Widgets，Presenter 可单测 |
| **MVVM（Quick/QML）** | 高 | 高 | 中 | 属性绑定 + Model | Qt Quick 默认选择 |
| **单向数据流 / Store** | 高 | 高 | 高 | 不可变状态 + 命令 | 复杂交互、多视图同步 |
| **分层 + 端口适配器** | 最高 | 最高 | 高 | 由外向内依赖 | 大型桌面、多 UI 壳（Widgets/QML/无头） |

**MVC** — `QWidget` 子类同时管界面与流程。起步快，主窗口易膨胀，业务难测。

**MVP** — View 接口只暴露显示与输入，Presenter 操作接口。Widgets 项目最稳妥的可测结构。

**MVVM** — C++ `QObject` 为 ViewModel，`Q_PROPERTY` + 信号驱动 QML。UI 与逻辑分离，QML 保持声明式。

**单向数据流** — Intent/Command → Reducer → State → 绑定。调试时问“当前状态是什么”即可，适合多面板联动。

**分层** — `app`（组合根）/ `ui` / `application`（用例）/ `domain` / `adapters`（设备、文件、网络、数据库）。Domain 不依赖 Qt GUI；允许依赖 `QtCore` 需在 design.md 写明。

### 选型建议

| 项目规模 | 推荐架构 | UI |
|---------|---------|-----|
| 单窗口工具 | MVP 或简单 MVVM | Widgets |
| 多文档 / 多面板桌面 | MVP + 用例层 | Widgets 或 Quick |
| 动画多、定制皮肤、触控 | MVVM | Qt Quick |
| 同一套领域逻辑多壳 | 分层 + 端口 | UI 可替换 |

**Widgets vs Qt Quick 决策：**

| 选 Widgets | 选 Qt Quick |
|-----------|------------|
| 桌面控件密集（菜单、停靠栏、复杂表格编辑） | 触控、动画、自定义视觉 |
| 团队现有 Widgets 资产多 | 需要设计师改 QML 皮肤 |
| 对 QPA/平台原生观感要求高 | 嵌入式 GPU 合成已验证 |

禁止无 design 决策就把两种 UI 框架对半混用。必须混合时，以一侧为壳，另一侧用 `QQuickWidget` 或 `QWidget` 嵌入，并定义插件边界。

---

## 二、技术栈

### 技术选型

| 决策项 | 选项 | 推荐 | 说明 |
|--------|------|------|------|
| 语言 | C++17、C++20、C++23 | **C++20** | concepts、span、jthread 视编译器而定 |
| UI | Widgets、Quick/QML、两者混合 | **按上表选择，新触控 UI 用 Quick** | 同一产品线保持一致 |
| 构建 | CMake、qmake、Meson | **CMake 3.21+** | `qt_add_*` API |
| 异步 | 信号槽 queued、`QtConcurrent`、`std::jthread` | **QObject worker 线程做有状态 I/O；QtConcurrent 做无状态并行** | 禁止 GUI 线程阻塞 |
| 依赖注入 | 构造注入、服务定位器、宏容器 | **构造函数注入** | 组合根在 `main` / `Application` |
| 本地数据 | SQLite（Qt SQL）、JSON/CBOR 文件、QSettings | **结构化用 SQLite；偏好/窗口几何用 QSettings** | |
| 网络 | `QNetworkAccessManager`、gRPC、自定义 TCP | **HTTP(S) 用 QNAM；实时设备用独立协议层** | TLS 必须校验证书 |
| 日志 | `QLoggingCategory`、spdlog | **QLoggingCategory** | 与 Qt 生态一致 |
| 测试 | Google Test、QTest、Catch2 | **GTest（逻辑）+ QTest（信号/UI）** | 见测试策略 |
| 包管理 | vcpkg、Conan、系统包、Vendoring | **vcpkg 或 Conan，全项目统一** | 锁定版本文件入库 |

### 推荐组合

| 项目规模 | 技术栈 |
|---------|--------|
| 小型 | C++20 + Qt 6 Widgets + CMake + QSettings + GTest |
| 中型 | C++20 + Qt 6 Widgets 或 Quick + 分层 + SQLite + QNAM + GTest/QTest |
| 大型 | C++20 + 分层端口 + Quick 或 Widgets 壳 + SQLite + 独立设备线程 + GTest/QTest + clazy/clang-tidy |

---

## 三、构建与版本约束

| 决策项 | 推荐值 | 说明 |
|--------|--------|------|
| Qt | **6.8 LTS**（或产品已冻结的 **6.5 LTS**） | 记录补丁版本 |
| CMake | **≥ 3.21** | Qt6 CMake API |
| C++ 标准 | **20** | `CMAKE_CXX_STANDARD_REQUIRED ON` |
| 编译器（Windows） | MSVC 19.3x（VS 2022）或 MinGW 与 Qt 官方套件一致 | 不要混用两套 ABI |
| 编译器（Linux） | GCC 11+ / Clang 15+ | 与发行版/sysroot 一致 |
| 编译器（macOS） | Apple Clang 与 Qt 官方要求匹配 | |
| Ninja | 推荐为生成器 | 增量快 |
| sanitizers | Debug：ASan+UBSan（平台可用时） | 不得只在“有空时”开 |

### Qt 模块选择清单

生成 design.md 时必须列出实际链接的 Qt 模块及理由，例如：

| 模块 | 何时引入 |
|------|---------|
| Core | 始终 |
| Gui | 任何窗口/图像 |
| Widgets | Widgets UI |
| Quick / QuickControls2 / Qml | Qt Quick |
| Network | HTTP/TCP |
| Sql | Qt SQL |
| SerialPort / SerialBus | 串口 / CAN |
| Test | QTest 目标 |

### 版本约束检查清单

1. [ ] Qt 主版本全仓库一致，CI 镜像与开发机 major.minor 对齐
2. [ ] `CMAKE_CXX_STANDARD` 与 Qt 构建标准兼容
3. [ ] MSVC 运行库（`/MD` vs `/MT`）与 Qt 发行一致，通常 **`/MD`**
4. [ ] 未同时链接 Qt5 与 Qt6
5. [ ] `AUTOMOC` 已开，`Q_OBJECT` 类有独立头文件
6. [ ] 部署使用 `windeployqt` / `macdeployqt` / 发行版打包，不手工漏拷平台插件

---

## 四、工程结构（推荐）

```
src/
  app/              # main、组合根、应用生命周期
  ui/               # Widgets 或 QML 适配
  application/      # 用例、协调
  domain/           # 无 GUI 的业务规则
  adapters/         # 文件、网络、设备、数据库
tests/
  unit/             # GTest，无 GUI
  qt/               # QTest，offscreen
cmake/
resources/
```

- [必须]  `domain` 不 include `<QWidget>` / `<QQuickItem>`
- [必须]  设备 I/O 不放在 Widget 子类里

---

## 五、测试与覆盖率

| 层级 | 工具 | 命令示例 |
|------|------|---------|
| 单元 | Google Test | `ctest -R unit --output-on-failure` |
| Qt | QTest + offscreen | `QT_QPA_PLATFORM=offscreen ctest -R qt` |
| 覆盖率（GCC/Clang） | gcov/llvm-cov + lcov | `cmake -DENABLE_COVERAGE=ON` 后 `lcov`/`llvm-cov report` |
| 覆盖率（MSVC） | OpenCppCoverage 或 llvm-cov | 在 CI 产出 HTML/cobertura |

基线：行 ≥ 80%，分支 ≥ 70%，主路径 100%。阈值必须写进 CMake/CTest，不能只生成报告。

---

## 六、安全与部署要点（桌面）

- TLS：校验证书，禁止永远 `sslErrors` ignore
- 本地密钥：系统凭据库或 OS DPAPI/Keychain，禁止明文写 ini
- 插件目录：只加载签名或安装树内路径
- 更新：校验包哈希/签名
- Windows：注意 DLL 劫持（应用目录、`PATH`、延迟加载）

生成 design.md 时 Qt 桌面项目必须逐项确认本节与第三节清单。
