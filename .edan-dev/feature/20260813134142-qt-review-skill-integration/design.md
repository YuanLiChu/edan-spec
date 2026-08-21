# 可配置技术栈专项代码走读技术设计

## 目标

建立“通用入口 + 项目级注册表 + 独立专项 skill”的最小架构。新增技术栈时，只增加专项 skill 和注册表项，不修改 `edanspec-code-review` 的核心流程。

## 配置契约

配置文件位置固定为被审查项目根目录的 `.edan-dev/review-stack.yaml`：

```yaml
version: 1
stacks:
  - id: qt-cpp
    enabled: true
    skill: qt-cpp-review
    match:
      extensions: [.cpp, .cc, .cxx, .h, .hh, .hpp]
      content_any: ['\\bQ_OBJECT\\b']
      build_any: ['find_package\\s*\\(\\s*Qt6']
    guidance: [.edan-dev/review-notes/qt-cpp.md]
```

字段含义：

- `id`：报告中的稳定键，新增技术栈不能复用已有 ID。
- `enabled`：项目是否启用该专项；只有 `true` 才参与匹配。
- `skill`：平台可发现的专项 skill 名称。
- `match.extensions`：候选文件扩展名。
- `match.content_any`：候选文件内容正则，命中任一即匹配。
- `match.build_any`：构建文件内容正则；只可将命名或关联的源文件加入匹配范围。
- `guidance`：项目/团队补充说明文件，作为专项输入，不是通用规则来源。

注册表只放路由元数据，不放 Qt 检查清单正文。缺少注册表时执行 generic-only；配置语法错误时继续通用审查，但结论为 `INCOMPLETE`。

## 执行流程

```text
固化 allFiles
    ↓
读取 review-stack.yaml
    ↓
generic reviewer(allFiles)
    ↓
foreach enabled stack:
    matchedFiles = match(allFiles, stack.match)
    specialist(stack.skill, matchedFiles, stack.guidance)
    ↓
统一报告(genericReview, specialists.<stack-id>, conclusion)
```

通用入口只负责范围、调度、状态和来源聚合。专项 skill 自己负责 lint、深度分析、框架模式确认、专项报告和专项经验加载。专项 skill 不得扩大调用方给出的文件范围。

## Qt 专项边界

`skills/qt-cpp-review/SKILL.md` 和 `skills/qt-qml-review/SKILL.md` 是专项入口；详细编排分别位于各自 `references/review-workflow.md`。稳定规则留在官方 checklist，项目经验写入 `.edan-dev/review-notes/`，通用经验成熟后再晋升到专项 references。

Qt C++ framework/module 模式继续遵守原 skill 的“检测后建议、用户确认后启用”契约。QML 的 `qmllint` 继续作为可选阶段，不可用时记录 warning。

## 报告与错误

统一报告必须记录：

- `genericReview`：`complete` 或 `failed`；
- `specialists.<stack-id>`：`complete`、`partial`、`failed` 或 `not-applicable`；
- `conclusion`：`APPROVE`、`REQUEST_CHANGES` 或 `INCOMPLETE`。

确认的 `CRITICAL` 产生 `REQUEST_CHANGES`。没有 `CRITICAL` 但配置错误、启用专项失败、必要阶段缺失或报告无法解析时产生 `INCOMPLETE`。没有匹配文件的启用专项为 `not-applicable`，不生成专项报告。

## 扩展方式

增加 Java 或 C# 时：

1. 新增 `skills/java-review/` 或 `skills/csharp-review/`，包含入口、workflow、checklist 和经验文件。
2. 在项目 `.edan-dev/review-stack.yaml` 增加一个 `stacks` 项。
3. 为匹配、禁用、失败和报告状态补充契约测试。

不修改 `edanspec-code-review` 的技术栈分支，因为入口没有技术栈名称依赖。
