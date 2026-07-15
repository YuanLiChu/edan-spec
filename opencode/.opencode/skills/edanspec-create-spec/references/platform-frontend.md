# 前端项目技术参考（React / Vue / Angular）

> 供design-review 的阶段一决策确认时参考。

---

## 一、架构模式

### 架构对比

| 架构 | 职责分离 | 可维护性 | 适用规模 |
|-----|---------|---------|---------|
| **组件化** | 中 | 中 | 所有现代前端项目 |
| **状态管理** | 高 | 高 | 多组件共享状态场景 |
| **分层架构** | 最高 | 最高 | 大型项目、多团队协作 |

**组件化** — 按 UI 功能拆分为独立组件。复用性强、开发效率高。状态分散，跨组件共享需额外方案。

**状态管理** — 引入集中式状态管理（Redux / Vuex / Zustand）。状态集中、易于调试和追溯。简单项目属过度设计。

**分层架构** — 组件层 / Service 层 / Data 层分离。职责清晰、易于测试。代码量多，需约定各层边界。

### 选型建议

| 项目规模 | 推荐架构 |
|---------|---------|
| < 10 页面 | 组件化 + Context / Zustand |
| 10-30 页面 | 组件化 + Redux / Zustand / Vuex |
| > 30 页面 | 分层架构（组件层 + Service 层 + Data 层） |

---

## 二、技术栈

### 技术选型

| 决策项 | 选项 | 推荐 | 说明 |
|--------|------|------|------|
| 前端框架 | React、Vue、Angular | **React**（灵活）、**Vue**（易上手） | 大型灵活用 React，快速开发用 Vue |
| 状态管理 | Redux、Vuex、Zustand、Pinia | **Redux/Zustand**（React）、**Vuex/Pinia**（Vue） | 按框架匹配，简单场景用 Context |
| UI 组件库 | Ant Design、Element Plus、Material-UI | **Ant Design**（React）、**Element Plus**（Vue） | 按框架匹配 |
| CSS 方案 | Tailwind CSS、styled-components、Sass | **Tailwind CSS** | Utility-first，构建时优化 |
| 构建工具 | Vite、Webpack | **Vite** | 启动快、HMR 即时，新项目首选 |
| 语言 | TypeScript、JavaScript | **TypeScript** | 类型安全、重构友好 |
| 测试 | Jest、Vitest、Cypress | **Jest / Vitest**（单元）、**Cypress**（E2E） | |

### 推荐组合

| 项目规模 | 技术栈 |
|---------|--------|
| 小型 | Vue 3 + Pinia + Element Plus + Vite |
| 中型 | React + Redux Toolkit + Ant Design + TypeScript + Vite |
| 大型 | React + 分层架构 + TypeScript + Tailwind CSS + Jest + Cypress |
