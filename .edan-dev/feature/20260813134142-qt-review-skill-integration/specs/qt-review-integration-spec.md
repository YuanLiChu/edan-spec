# 可配置技术栈专项代码走读规格

## Requirement: 项目可注册专项技术栈

系统 SHALL 从被审查项目根目录读取 `.edan-dev/review-stack.yaml`。注册项 SHALL 包含 `id`、`enabled`、`skill` 和 `match`；可选 `guidance` 用于项目级补充说明。

### Scenario: 注册 Qt C++ 和 Qt QML

- **WHEN** 配置包含 `qt-cpp` 和 `qt-qml` 两个启用项
- **THEN** 系统 SHALL 分别使用 `qt-cpp-review` 和 `qt-qml-review`
- **AND** 不得把专项检查清单正文复制到通用 code-review skill

### Scenario: 扩展 Java 或 C#

- **WHEN** 项目新增一个指向 Java/C# skill 的注册项
- **THEN** 通用入口 SHALL 按相同协议匹配并调用该 skill
- **AND** 不需要修改通用入口的技术栈分支

## Requirement: 通用走读始终执行

- **WHEN** 任意审查范围被提交
- **THEN** 系统 SHALL 先执行通用四维走读
- **AND** 专项 skill 只能接收注册项匹配出的 `matchedFiles`

## Requirement: Qt 专项由各自 skill 编排

### Scenario: Qt C++ 匹配

- **WHEN** C++ 文件命中注册项的扩展名和 Qt 内容/构建证据
- **THEN** 系统 SHALL 调用 `qt-cpp-review`
- **AND** 专项 skill SHALL 执行其确定性 lint、六个深度分析阶段和原始报告整理

### Scenario: Qt QML 匹配

- **WHEN** 文件扩展名为 `.qml` 或 `.qmltypes`
- **THEN** 系统 SHALL 调用 `qt-qml-review`
- **AND** 专项 skill SHALL 执行 QML lint、可用时的 `qmllint`、六个深度分析阶段和原始报告整理

## Requirement: 经验可分层沉淀

- **WHEN** 注意事项具有跨项目通用性且已有证据
- **THEN** SHALL 写入对应专项 skill 的 `references/lessons-learned.md` 或 checklist
- **WHEN** 注意事项仅适用于当前项目或团队
- **THEN** SHALL 写入 `.edan-dev/review-notes/<stack-id>.md` 并通过 `guidance` 传入

## Requirement: 统一状态反映失败

- **WHEN** 配置缺失
- **THEN** 只执行通用走读，专项状态为 `not-applicable`
- **WHEN** 配置格式错误或启用专项无法执行
- **THEN** 继续通用走读，但结论 SHALL 为 `INCOMPLETE`
- **WHEN** 存在确认的 `CRITICAL`
- **THEN** 结论 SHALL 为 `REQUEST_CHANGES`

## Requirement: 离线包保持平台无关

- **WHEN** 构建 Claude Code、OpenCode 或 Kilo Code 离线包
- **THEN** 构建器 SHALL 通过通用 `skills/` 复制包含专项 skill
- **AND** 构建器不得为某一技术栈增加特判分支
