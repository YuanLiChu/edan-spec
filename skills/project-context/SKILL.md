---
name: project-context
description: 建立/更新项目知识地图——扫描工程项目结构，生成项目级上下文（project.md）、模块设计文档（module.md）和业务流设计文档（flow.md）。触发场景：新项目首次接入 edan-dev、用户要求「初始化项目」「建立项目上下文」「更新知识地图」、项目结构发生重大变化后。不适用于单个 feature 的需求分析（用 explore/create-spec）。
---

# Project Context

为工程项目建立结构化的知识地图，让后续所有 skill 拥有可索引的项目上下文。

**核心原则：先建立地图，再深入细节。分层渐进，用户可控。**

## 触发条件

- "初始化这个项目"
- "建立项目上下文"
- "更新知识地图"
- "项目结构变了，重新扫描"
- 新项目首次接入 edan-dev 工作流

## 目录结构

本 skill 在 `EdanSpec/context/` 下生成持久性知识文档：

```
EdanSpec/
├── context/                          # 项目持久知识
│   ├── project.md                    # 项目级知识地图
│   └── modules/                      # 模块级知识
│       └── {module-name}/
│           ├── module.md             # 模块设计文档
│           └── flows/
│               └── {flow-name}.md    # 业务流设计文档
│
├── specs/                            # 主 spec（已有）
├── feature/                          # 变更工单（已有）
│   └── {timestamp}-{topic}/
└── archive/                          # 归档（已有）
```

**注意**：知识文档放在 `context/`，与 `feature/` 变更工单分离——知识是持久的，feature 是临时的。

## 工作流程

```
检测 context/ 是否存在
  ├─ 已存在 → 询问「更新」还是「重建」
  └─ 不存在 → 进入 Step 1

Step 1: 生成 project.md（项目级）
  ↓ 用户确认
Step 2: 生成 module.md（模块级，逐模块）
  ↓ 用户确认
Step 3: 生成 flow.md（业务流级，逐流）
  ↓ 用户确认
完成
```

---

## Step 0: 前置检测

启动时检测 `EdanSpec/context/` 是否存在：

| 检测结果 | 行为 |
|----------|------|
| `context/` 不存在 | 直接进入 Step 1 |
| `context/` 存在，且用户明确要求「更新」 | 执行「更新范围检测」，仅对变更部分进入对应 Step |

### 更新范围检测

用户选择「更新」时，先读取现有 `project.md`，对比当前项目扫描结果，识别实际变更范围：

```
读取现有 project.md → 提取模块列表
  ↓
扫描当前项目 → 提取模块列表
  ↓
对比差异：
  ├─ 无差异 → 仅检查 project.md 技术栈/版本号等元数据 → 结束
  ├─ 新增模块 → 在 project.md 追加索引 → 跳到 Step 2（仅新模块）
  ├─ 删除模块 → 在 project.md 标记 DEPRECATED → 结束
  ├─ 模块结构变化（重命名/合并/拆分）→ 按「增量更新规则」处理 → 跳到对应 Step
  └─ 无模块级变更，但用户指定更新某模块 → 跳到 Step 2（指定模块）
```

**规则**：更新模式下不从 Step 1（project.md）从头重做，只处理发生变更的部分。
| `context/` 存在，且用户明确要求「重建」 | 备份后删除 `context/`，重新进入 Step 1 |
| `context/` 存在，用户未说明意图 | 询问用户：更新现有 / 重建 / 添加新模块 |

**询问话术：**

> 检测到 `EdanSpec/context/` 已存在。请选择：
> - **更新** — 基于现有文档补充新增模块/业务流
> - **重建** — 删除现有文档，重新扫描整个项目
> - **添加模块** — 只扫描指定模块，追加到现有 context

---

## Step 1: 生成 project.md

### 1.1 扫描项目根目录

```bash
# 识别构建工具和技术栈
ls build.gradle* pom.xml package.json go.mod Cargo.toml 2>/dev/null

# 识别模块/服务结构
find . -maxdepth 2 -type d | grep -v node_modules | grep -v .git | sort
```

### 1.2 识别模块边界

基于目录结构和构建文件，识别项目包含的模块：

- **单体项目**（如 Spring Boot）：按 `src/main/java/com/company/{module}/` 目录划分
- **多模块项目**（如 Gradle multi-project）：按子项目目录划分
- **微服务**：按服务目录划分
- **前端项目**：按 `src/{pages,components,features}/` 划分

**模块命名**：使用 kebab-case，如 `alarm-manager`、`data-collector`。

### 边界情况

- **空项目 / 纯文档项目**：project.md 中模块索引为空，标注「本项目无代码模块，仅包含文档」；跳过 Step 2 和 Step 3
- **单文件脚本项目**：将整个文件视为一个模块，模块名与项目名相同或取文件名；module.md 中类图简化为文件内函数/类列表
- **单模块单体项目**：project.md 中模块索引只有一个条目（模块名可与项目名相同或不同）；Step 2 只执行一次
- **混合语言项目**：find / grep 命令已覆盖 Kotlin、Java、Go、TypeScript、Python、Rust、C#、C++、C 等主流语言；遇到未覆盖语言时，先询问用户模块边界，再扫描
- **无明确目录边界的模块**（如按 package 而非目录划分）：以 package / namespace 为模块单位，在 project.md 中标注「模块按包结构划分，非目录结构」

### 1.3 生成 project.md

写入 `EdanSpec/context/project.md`，参考模板文件：

> **模板**：[`references/project-template.md`](references/project-template.md)
>
> 生成时按实际项目信息填充占位符，遵循下方图表规范。

**图表规范**：
- 使用 Mermaid 语法
- 架构概览只画模块级节点，不画类级细节
- 每个节点标注模块名和核心职责（≤10 字）
- **架构概览是模块间关系的权威来源**，module.md 的「模块交互」应与之保持一致

### 1.4 用户确认

展示 project.md 摘要（项目名、技术栈、模块列表），等待用户确认：

> 已生成项目知识地图，包含 N 个模块：
> - alarm-manager：报警规则管理
> - data-collector：实时数据采集
> - ...
>
> 模块边界对吗？有遗漏或需要调整吗？

用户确认后进入 Step 2；用户要求修正 → 就地修改 → 重新确认。

---

## Step 2: 生成 module.md

### 2.1 模块选择

**方式 A — 用户指定**：用户直接说"先扫描 alarm-manager"

**方式 B — 批量建议**：Agent 根据模块复杂度建议分批处理：
- 核心模块优先（被最多其他模块依赖的）
- 每次处理 1-3 个模块，避免上下文膨胀

**询问话术：**

> 准备生成模块设计文档。建议分批处理：
> - **第一批**：alarm-manager（核心模块，被 3 个模块依赖）
> - **第二批**：data-collector、notification-service
>
> 先处理第一批？或者你指定优先模块？

### 2.2 扫描模块源码

```bash
# 扫描模块目录结构
find {module-path} -type f \( -name "*.kt" -o -name "*.java" -o -name "*.go" -o -name "*.ts" -o -name "*.py" \) | sort

# 识别核心类（Service、Repository、Controller、Domain 等）
grep -r "class .*Service\|interface .*Repository\|class .*Controller" {module-path} --include="*.kt" --include="*.java" --include="*.go" --include="*.ts" --include="*.py" --include="*.rs" --include="*.cs" --include="*.cpp" --include="*.c"
```

### 2.3 生成 module.md

写入 `EdanSpec/context/modules/{module-name}/module.md`，参考模板文件：

> **模板**：[`references/module-template.md`](references/module-template.md)
>
> 生成时按实际模块信息填充占位符，遵循下方图表规范。

**图表规范**：
- 类图只包含模块内核心类（≤10 个），省略工具类、DTO
- 模块内时序图聚焦 1 个最核心场景，调用链限制在本模块内部
- 跨模块协作场景单独放在「跨模块场景」节
- 模块交互图标注调用方向（同步/异步、REST/gRPC/消息队列），且应与 project.md「架构概览」保持一致

### 2.4 用户确认

展示 module.md 摘要（职责边界、核心类数量、业务流列表），等待确认。

用户确认后：
- 若还有未处理模块 → 回到 Step 2.1 处理下一批
- 若全部模块处理完毕 → 进入 Step 3（或用户选择跳过 flow 层）

---

## Step 3: 生成 flow.md

### 3.1 业务流选择

从已生成的 module.md 的「业务流索引」中选择：

**方式 A — 用户指定**：用户直接说"详细设计报警限推荐"

**方式 B — 批量建议**：Agent 建议每次处理 1-2 个业务流

**询问话术：**

> alarm-manager 模块有 3 个业务流：
> - alarm-suggest（报警限推荐）
> - alarm-suppress（报警抑制）
> - rule-lifecycle（规则生命周期管理）
>
> 先详细设计哪一个？

### 3.2 追踪代码调用链

通过代码扫描追踪业务流的完整调用链：

```bash
# 从入口方法开始追踪
grep -r "suggestThreshold\|AlarmSuggestService" {module-path} --include="*.kt" --include="*.java" --include="*.go" --include="*.ts" --include="*.py"

# 识别涉及的类、接口、状态转换
```

### 3.3 生成 flow.md

写入 `EdanSpec/context/modules/{module-name}/flows/{flow-name}.md`，参考模板文件：

> **模板**：[`references/flow-template.md`](references/flow-template.md)
>
> 生成时按实际业务流信息填充占位符，遵循下方图表规范。

**图表规范**：
- 时序图展示完整的调用链（从入口到返回）
- 数据流图与接口调用序列分工明确：前者关注数据格式转换，后者关注调用顺序和异常点
- 异常处理覆盖主流程中的关键失败点，区分可恢复与不可恢复异常

### 3.4 用户确认

展示 flow.md 摘要（输入输出、涉及类数、关键异常），等待确认。

确认后：
- 若还有未处理业务流 → 回到 Step 3.1
- 若全部完成 → 进入完成阶段

---

## 完成阶段

### 产物清单报告

```markdown
已建立项目知识地图：

- `EdanSpec/context/project.md` — 项目级（N 个模块）
- `EdanSpec/context/modules/{module}/module.md` — 模块级（共 M 个）
- `EdanSpec/context/modules/{module}/flows/{flow}.md` — 业务流级（共 K 个）

后续任何 feature 工作流均可读取 `context/` 作为项目背景知识。
```

### 引导下一步

- 用户要继续开发功能 → 引导 `edan-dev:explore` 或 `edan-dev:create-spec`
- 用户要补充更多业务流 → 回到 Step 3
- 用户要更新特定模块 → 回到 Step 2（增量更新）

---

## 增量更新规则

当项目结构发生变化（新增模块、新增业务流、类重构），使用「更新」模式：

| 变更类型 | 操作 |
|----------|------|
| 新增模块 | 在 project.md 模块索引追加 → 生成新 module.md |
| 删除模块 | 从 project.md 移除索引，保留 module.md（加 `DEPRECATED` 标记）|
| 模块内新增业务流 | 在 module.md 业务流索引追加 → 生成新 flow.md |
| 类重构 | 重新扫描该 module → 更新 module.md 和受影响 flow.md |
| 技术栈变更 | 更新 project.md 基本信息 |

**更新时保留已有文档的历史上下文**，不删除重做，在变更处追加/修改。

### 补充场景

| 变更类型 | 操作 |
|----------|------|
| 模块重命名 | 在 project.md 更新模块名和路径；保留原 module.md 内容，在顶部加 `> **注意**：本模块已重命名为 {new-name}，最新文档见 [module.md](../{new-name}/module.md)` |
| 模块合并 | 在 project.md 移除被合并模块的索引，保留 module.md（加 `DEPRECATED` 标记）；在合并后的 module.md 中标注「吸收了 {old-modules} 的职责」 |
| 模块拆分 | 在 project.md 用新模块名替换原模块；原 module.md 加 `DEPRECATED`；为每个新模块生成 module.md |
| 业务流删除 | 在 module.md 业务流索引中标记 `[已删除]`；保留 flow.md（加 `DEPRECATED` 标记），不删除 |
| 业务流重命名 | 在 module.md 更新索引；保留原 flow.md，加 `> **注意**：已重命名为 {new-name}` |
| 非重构性类变更（新增/删除个别类） | 重新扫描该 module → 更新 module.md 类图；检查受影响 flow.md，更新涉及的类与接口列表 |
| 无业务流的模块 | module.md 中「业务流索引」表格写「本模块无独立业务流」或删除该表格；不创建空 flows/ 目录 |

> **DEPRECATED 标记格式**：在文档顶部添加 `> **DEPRECATED**：{原因}，最后更新于 {日期}`。

---

## 与现有工作流的关系

```
[项目首次接入 edan-spec]
         │
         ▼
  project-context  ← 本 skill
         │
         ▼
    context/ 目录建立
         │
         ▼
[后续 feature 工作流]
         │
    explore ──→ create-spec ──→ task-plan ──→ task-implement
         │         │                │               │
         │         │                │               │
    读取 context/ 作为项目背景知识 ────────────────┘
```

**建议后续 skill 读取 context 的方式**：
- `explore`：调查代码库前，先读取 project.md 了解项目概况和模块分布，快速定位相关模块
- `create-spec`：生成方案时，读取相关 module.md 了解模块职责边界和已有设计决策
- `task-plan` / `task-implement`：拆分任务或实现时，读取相关 flow.md 了解业务流调用链和异常处理

> 当前下游 skill 尚未强制接入 context/。在后续迭代中，将逐步更新 explore、create-spec、task-plan、task-implement 的「输入来源」章节，明确把 context/ 作为优先级输入来源。

---

## 常见借口

> 通用借口见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "项目很简单，不用写这些文档" | 简单项目的 context 也只需 5 分钟，但后续 feature 开发时省 30 分钟 |
| "代码就是最好的文档" | 代码告诉你 what，context 告诉你 why 和 where。AI 读代码上下文有限，需要地图 |
| "后面再补 context" | 后面补 = 不会补。项目初始化时建立成本最低 |
| "一次性全量生成吧" | 大项目上下文爆炸，质量跳水。分层按需才是正确方式 |

## 警示信号

- 未检测 `context/` 是否存在就直接生成
- 把知识文档放在 `EdanSpec/feature/` 下（与变更工单混淆）
- 一次性扫描所有模块并批量生成（上下文膨胀）
- 类图包含过多类（>10 个）或工具类
- 模块内时序图跨越模块边界（应移至 module.md 的「跨模块场景」中）
- flow.md 中出现 module.md 类图未提及的类（违反子集约束）
- 生成后未向用户展示摘要就继续下一步
- 未引导用户确认模块边界是否正确
- 更新时删除已有文档重做（应增量修改）
- project.md「架构概览」与 module.md「模块交互」存在矛盾（模块关系不一致）

## 验证

- [ ] Step 0: 已检测 `context/` 是否存在，用户意图已确认
- [ ] Step 1: project.md 已生成，包含项目目标、基本信息、基础设施、架构概览、模块索引
- [ ] Step 1: project.md 已展示摘要并获得用户确认
- [ ] Step 1: project.md「架构概览」与所有 module.md「模块交互」无矛盾
- [ ] Step 2: module.md 已生成（逐模块），包含职责边界、公共接口、数据模型、类图、时序图、跨模块场景、模块交互、配置项、业务流索引
- [ ] Step 2: 每个 module.md 已展示摘要并获得用户确认
- [ ] Step 3: flow.md 已生成（逐业务流），包含概述、前置条件、输入输出、状态机/流程阶段、业务规则、类与接口、调用序列、数据流、异常处理、事务与幂等性
- [ ] Step 3: flow.md 中所有类均属于所属 module.md 类图的子集
- [ ] Step 3: 每个 flow.md 已展示摘要并获得用户确认
- [ ] 完成: 已输出产物清单，已说明后续 skill 如何读取 context/
- [ ] 一致性: project.md 模块索引中的链接指向实际存在的 module.md 路径
- [ ] 一致性: module.md 业务流索引中的链接与 flows/ 目录下的实际文件一一对应
- [ ] 一致性: 所有模块命名统一使用 kebab-case，无空格或下划线混用
