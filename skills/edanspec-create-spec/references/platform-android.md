# Android 项目技术参考

> 供design-review 的阶段一决策确认时参考。

---

## 一、架构模式

### 架构对比

| 架构 | 职责分离 | 可测试性 | 学习成本 | 状态管理 | 适用场景 |
|-----|---------|---------|---------|---------|---------|
| **MVC** | 低 | 低 | 低 | 手动 | 小型项目、快速原型 |
| **MVP** | 中 | 中 | 中 | 手动 | 中型项目、需单测 |
| **MVVM** | 高 | 高 | 中 | 自动（LiveData/StateFlow） | Jetpack 项目、官方推荐 |
| **MVI** | 最高 | 最高 | 高 | 最佳（单向数据流） | 复杂状态管理、实时数据 |
| **Clean Architecture** | 最高 | 最高 | 高 | 自动 | 大型项目、多团队协作 |

**MVC** — Activity/Fragment 同时承担 View 和 Controller 职责。结构简单，但 Activity 过重、耦合度高、难以测试。

**MVP** — View 只负责 UI，Presenter 处理业务逻辑。View/Model 完全解耦、Presenter 可独立测试。接口数量多，需手动管理生命周期。

**MVVM** — ViewModel 管理 UI 状态，LiveData/StateFlow 自动更新 UI。自动生命周期管理，Jetpack 官方推荐。

**MVI** — 响应式单向数据流：Intent → State → View。UI 与业务完全解耦，状态不可变易调试。学习成本高，State 频繁重建。

**Clean Architecture** — Presentation / Domain / Data 三层分离，依赖方向由外向内。高度解耦，Domain 层不依赖任何框架。代码量多，小型项目属过度设计。

### 选型建议

| 项目规模 | 推荐架构 |
|---------|---------|
| < 5 界面 | MVC 或简单 MVVM |
| 5-15 界面 | MVVM + Repository |
| > 15 界面 | MVI 或 Clean Architecture |
| 医疗设备 / 实时数据 | MVI |

---

## 二、技术栈

### 技术选型

| 决策项 | 选项 | 推荐 | 说明 |
|--------|------|------|------|
| 编程语言 | Kotlin、Java | **Kotlin** | 空安全 + 协程，新项目统一 Kotlin |
| UI 框架 | Compose、XML | **Compose**（新项目） | 声明式、状态驱动 |
| 异步处理 | 协程、RxJava | **协程**（新项目） | Kotlin 原生、语法简洁 |
| 依赖注入 | Hilt、Koin | **Hilt**（中大型）、**Koin**（小型） | Hilt 编译时检查，Koin 轻量无编译开销 |
| 数据存储 | Room、DataStore | **Room**（结构化）、**DataStore**（键值） | Room 支持 SQL 查询，DataStore 协程安全 |
| 网络请求 | Retrofit + OkHttp、Ktor | **Retrofit** | 生态成熟、注解驱动 |
| 图片加载 | Coil、Glide | **Coil**（Compose） | Compose 原生支持 |

### 推荐组合

| 项目规模 | 技术栈 |
|---------|--------|
| 小型 | Kotlin + Compose + 协程 + Koin + DataStore + Retrofit |
| 中型 | Kotlin + Compose + 协程 + Hilt + Room + Retrofit + Coil |
| 大型 | Kotlin + MVI + Clean Architecture + Hilt + Room + Retrofit + Coil |

---

## 三、构建工具版本约束

| 决策项 | 推荐值 | 说明 |
|--------|--------|------|
| AGP（Android Gradle Plugin） | **8.12.0** | 与 Gradle 版本严格绑定，见 [兼容性矩阵](https://developer.android.com/studio/releases/gradle-plugin#updating-gradle) |
| Gradle Wrapper | **8.14.2** | `gradle/wrapper/gradle-wrapper.properties` 中的 `distributionUrl` |
| Kotlin | **2.1.20** | 与 AGP 兼容，`libs.versions.toml` 中声明 |
| compileSdk | **36** | `build.gradle.kts` 中 `compileSdk` |
| targetSdk | **36** | `build.gradle.kts` 中 `targetSdk` |
| minSdk | **26**（Android 8.0） | 按项目需求调整，过低会限制可用 API |
| JVM Target | **17** | `kotlinOptions.jvmTarget` / `jvmTarget = "17"` |
| Java Toolchain | **17** | `compileOptions { sourceCompatibility / targetCompatibility }` |

### 版本兼容性矩阵（必须严格匹配）

| AGP | Gradle | Kotlin（最低） | Java |
|-----|--------|---------------|------|
| 8.12.x | 8.14+ | 2.0.0+ | 17+ |
| 8.11.x | 8.13+ | 2.0.0+ | 17+ |
| 8.10.x | 8.11+ | 1.9.20+ | 17+ |
| 8.9.x | 8.11+ | 1.9.20+ | 17+ |
| 8.8.x | 8.10.2+ | 1.9.20+ | 17+ |
| 8.7.x | 8.9+ | 1.9.20+ | 17+ |
| 8.6.x | 8.9+ | 1.9.20+ | 17+ |

### 版本约束检查清单

生成 design.md 时，Android 项目必须逐项确认：

1. [ ] AGP 版本与 Gradle Wrapper 版本在兼容性矩阵内
2. [ ] Kotlin 版本与 AGP 兼容
3. [ ] compileSdk >= targetSdk >= minSdk
4. [ ] JVM Target 与 Java Toolchain 版本一致
5. [ ] 第三方库版本与上述版本兼容（尤其 Compose Compiler 与 Kotlin 版本匹配）

### Compose Compiler 与 Kotlin 版本映射

| Kotlin | Compose Compiler |
|--------|-----------------|
| 2.1.x | 2.1.0+ |
| 2.0.x | 2.0.0+ |
| 1.9.x | 1.5.x |
