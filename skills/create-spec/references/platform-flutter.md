# Flutter 项目技术参考

> 供design-review 的阶段一决策确认时参考。

---

## 一、架构模式

### 架构对比

| 架构 | 职责分离 | 可测试性 | 学习成本 | 状态管理 | 适用场景 |
|-----|---------|---------|---------|---------|---------|
| **Provider** | 中 | 中 | 低 | 自动 | 中小型项目、快速开发 |
| **Riverpod** | 高 | 高 | 中 | 编译时安全 | 中大型项目（推荐） |
| **BLoC** | 最高 | 最高 | 高 | 事件驱动（Stream） | 大型项目、复杂交互 |
| **GetX** | 低 | 低 | 低 | 自动 | 小型快速开发、全栈方案 |
| **MVVM** | 高 | 高 | 中 | 自动 | 数据驱动型应用 |

**Provider** — 基于 InheritedWidget 的状态管理。Google 官方推荐，学习成本低。编译时不安全，测试需额外 Mock。

**Riverpod** — Provider 改进版，编译时安全。不依赖 Widget 树，支持依赖注入。学习曲线较 Provider 陡。

**BLoC** — 基于 Stream 的事件驱动状态管理。单向数据流清晰，测试性极佳。模板代码多，学习成本高。

**GetX** — 路由 + 状态管理 + 依赖注入一体化。API 简洁、快速上手。过度耦合，不符合 Flutter 最佳实践。

**MVVM** — 数据绑定驱动，View 自动响应 ViewModel 状态变化。数据驱动清晰，适合表单类应用。

### 选型建议

| 项目规模 | 推荐架构 |
|---------|---------|
| < 10 页面 | Provider 或 GetX |
| 10-30 页面 | Riverpod |
| > 30 页面 | BLoC 或 Riverpod |
| 复杂表单 / 实时数据 | BLoC |

---

## 二、技术栈

### 技术选型

| 决策项 | 选项 | 推荐 | 说明 |
|--------|------|------|------|
| 状态管理 | Provider、Riverpod、BLoC、GetX | **Riverpod**（中大型）、**Provider**（小型） | 按项目规模选择 |
| 路由 | go_router、auto_route、Get 路由 | **go_router** | 官方推荐，支持 Deep Link |
| 网络请求 | Dio、http、Retrofit for Flutter | **Dio** | 拦截器、重试机制、下载管理 |
| 本地存储 | Hive、Isar、Drift | **Hive**（轻量）、**Isar**（高性能） | Hive NoSQL 快速读写，Isar 高性能查询 |
| 依赖注入 | get_it、injectable | **get_it** | 轻量 Service Locator |
| UI 组件 | Material、Cupertino | **Material** | Android/iOS 统一风格 |
| 图片加载 | cached_network_image、flutter_svg | **cached_network_image** | 网络图片缓存 |

### 推荐组合

| 项目规模 | 技术栈 |
|---------|--------|
| 小型 | Provider + go_router + Dio + Hive + Material |
| 中型 | Riverpod + go_router + Dio + Isar + get_it |
| 大型 | BLoC + auto_route + Dio + Drift + injectable |
