# Qt 专项代码审查集成规格

## Requirements

### Requirement: Qt 审查 Skill 随 EdanSpec 分发 [ADDED]

系统 SHALL 将 `qt-cpp-review` 与 `qt-qml-review` 的完整内容纳入 EdanSpec，并以 Claude Code 目录为唯一权威源码。每个 skill SHALL 包含可独立使用的 `SKILL.md`、其引用的检查清单和 lint 脚本，以及原始许可证文件。

#### Scenario: 构建三平台离线包

- **WHEN** 构建 Claude Code、OpenCode 和 Kilo Code 离线包
- **THEN** 每个平台产物均包含两个可发现的 Qt review skill
- **AND** 每个 skill 引用的本地文件均存在
- **AND** lint 脚本与许可证文件均被包含

#### Scenario: 派生非 Claude Code 平台

- **WHEN** 从 Claude Code 权威源码构建 OpenCode 与 Kilo Code 产物
- **THEN** skill 名称、调用语法和内部路径 SHALL 适配目标平台
- **AND** 产物中不得残留指向错误平台目录的引用

#### Scenario: Qt skill 内容不完整

- **WHEN** 任一必要的 `SKILL.md`、检查清单、lint 脚本或许可证缺失
- **THEN** 离线包构建 SHALL 失败并指出缺失文件
- **AND** 不得发布不完整产物

### Requirement: EdanSpec 总审查自动识别 Qt 内容 [ADDED]

`edanspec:code-review` SHALL 在确定实际审查文件集后分类 Qt/C++ 与 QML 内容，并在保持通用四维审查的同时自动调用匹配的 Qt 专项 skill。

#### Scenario: 审查范围包含 Qt C++

- **WHEN** 实际审查范围包含 `.cpp`、`.cc`、`.cxx`、`.h`、`.hh` 或 `.hpp` 文件
- **AND** 文件或对应构建上下文包含明确 Qt 证据，例如 Qt 头文件、Qt 类型、`Q_OBJECT`、`Q_PROPERTY`、signal/slot 或 Qt 构建声明
- **THEN** 系统 SHALL 自动调用 `qt-cpp-review`
- **AND** 只将匹配的 Qt/C++ 文件交给该 skill

#### Scenario: 审查范围只包含普通 C++

- **WHEN** C++ 文件中没有明确 Qt 证据
- **THEN** 系统 SHALL 继续通用四维审查
- **AND** 不得调用 `qt-cpp-review`

#### Scenario: 审查范围包含 QML

- **WHEN** 实际审查范围包含 `.qml` 文件
- **THEN** 系统 SHALL 自动调用 `qt-qml-review`
- **AND** 只将 QML 文件交给该 skill

#### Scenario: 审查范围同时包含 Qt C++ 与 QML

- **WHEN** 同一审查范围同时匹配 Qt/C++ 和 QML
- **THEN** 系统 SHALL 执行两个专项 skill
- **AND** 两者 MAY 并行执行
- **AND** 通用四维审查仍 SHALL 执行

#### Scenario: 审查范围不包含 Qt 内容

- **WHEN** 实际审查范围不包含匹配的 Qt/C++ 或 QML 文件
- **THEN** 系统 SHALL 只执行原有通用四维审查
- **AND** 不生成 Qt 专项报告

### Requirement: 保持 Qt 专项审查契约 [ADDED]

系统 SHALL 按被引用 Qt skill 的既定阶段执行专项审查，不得用 EdanSpec 通用检查替代或跳过其必要阶段。

#### Scenario: 执行 Qt C++ 专项审查

- **WHEN** `qt-cpp-review` 被触发
- **THEN** 系统 SHALL 先执行确定性 lint，再执行六个深度分析维度，最后整理专项报告
- **AND** SHALL 保留原始规则 ID、类别、置信度和调用追踪

#### Scenario: 检测到 Qt framework/module 代码

- **WHEN** Qt/C++ 范围满足原 skill 的 framework 模式检测条件
- **THEN** 系统 SHALL 建议用户启用 framework 模式
- **AND** 未经用户确认不得自动启用该模式

#### Scenario: 执行 QML 专项审查

- **WHEN** `qt-qml-review` 被触发
- **THEN** 系统 SHALL 执行确定性 lint、可用时执行系统 `qmllint`、执行六个深度分析维度，并整理专项报告

#### Scenario: qmllint 不可用

- **WHEN** 系统无法找到 `qmllint`
- **THEN** QML 专项审查 SHALL 记录该阶段不可用
- **AND** 继续执行其余阶段

### Requirement: 保留专项报告并生成统一报告 [ADDED]

系统 SHALL 保留每个已执行 Qt skill 的原始专项报告，并将可信发现聚合到 EdanSpec 统一代码审查报告中。

#### Scenario: 生成 Qt C++ 原始报告

- **WHEN** `qt-cpp-review` 已执行
- **THEN** feature 目录中 SHALL 生成 `qt-cpp-review-report.md`
- **AND** 报告 SHALL 保留该 skill 的原始结构和发现信息

#### Scenario: 生成 QML 原始报告

- **WHEN** `qt-qml-review` 已执行
- **THEN** feature 目录中 SHALL 生成 `qt-qml-review-report.md`
- **AND** 报告 SHALL 保留该 skill 的原始结构和发现信息

#### Scenario: 聚合重复发现

- **WHEN** 通用审查与一个或多个 Qt 专项报告发现同一文件、同一位置且语义相同的问题
- **THEN** `code-review-report.md` SHALL 只保留一个统一问题项
- **AND** 该问题项 SHALL 记录所有来源及 Qt 原始编号、规则 ID 和置信度

#### Scenario: 映射严重度

- **WHEN** Qt 专项报告产生高置信度确认问题
- **THEN** 系统 SHALL 根据 EdanSpec 的影响分级规则独立判定 `CRITICAL`、`IMPORTANT` 或 `SUGGESTION`
- **AND** 不得把 Qt 的置信度数值直接转换为严重度

#### Scenario: 聚合待人工确认项

- **WHEN** Qt 专项报告包含 investigation target
- **THEN** 统一报告 SHALL 将其列入独立的“待人工确认”章节
- **AND** 不得仅凭该状态自动判定为 `CRITICAL`

### Requirement: 审查结论反映专项完整性 [ADDED]

统一报告 SHALL 区分完整通过、需要修改和流程不完整，避免在应执行的 Qt 专项阶段缺失时报告完整通过。

#### Scenario: 存在 CRITICAL 问题

- **WHEN** 通用审查或任一 Qt 专项审查确认至少一个 `CRITICAL` 问题
- **THEN** `code-review-report.md` 的结论 SHALL 为 `REQUEST_CHANGES`

#### Scenario: 所有要求阶段完成且无 CRITICAL

- **WHEN** 通用审查和所有被触发的 Qt 专项阶段均完成
- **AND** 不存在 `CRITICAL` 问题
- **THEN** 统一报告结论 SHALL 为 `APPROVE`

#### Scenario: 应执行的专项审查未完成

- **WHEN** Qt skill 缺失、必要执行阶段异常退出或专项报告无法生成
- **THEN** 统一报告结论 SHALL 为 `INCOMPLETE`
- **AND** SHALL 记录未完成阶段、原因和补查建议
- **AND** 不得报告为 `APPROVE`

#### Scenario: CRITICAL 与专项不完整同时存在

- **WHEN** 已确认至少一个 `CRITICAL` 问题
- **AND** 任一应执行的专项阶段未完成
- **THEN** 统一报告结论 SHALL 为 `REQUEST_CHANGES`
- **AND** 审查完整性 SHALL 标记为“不完整”
- **AND** SHALL 同时保留 CRITICAL 问题和未完成阶段说明

#### Scenario: task-implement 消费不完整结论

- **WHEN** `task-implement` 读取结论为 `INCOMPLETE` 的 `code-review-report.md`
- **THEN** SHALL 将其视为审查尚未通过
- **AND** 不得进入完成或可合并状态

#### Scenario: Python 不可用

- **WHEN** Qt 专项 lint 所需的 Python 不可用
- **THEN** 系统 SHALL 按专项 skill 契约继续可执行的深度分析
- **AND** 在专项报告与统一报告中明确记录 lint 阶段未运行

### Requirement: 自动化验证覆盖路由、聚合与分发 [ADDED]

系统 SHALL 提供自动化测试证明 Qt 专项集成在内容识别、报告语义和三平台分发上符合本规格。

#### Scenario: 验证内容路由矩阵

- **WHEN** 测试 Java、普通 C++、Qt/C++、QML 以及 Qt/C++ 与 QML 混合样例
- **THEN** 每个样例 SHALL 只触发规格要求的专项 skill

#### Scenario: 验证报告结论与去重

- **WHEN** 测试重复发现、不同严重度、专项失败和完整通过样例
- **THEN** 系统 SHALL 生成正确的去重结果及 `APPROVE`、`REQUEST_CHANGES` 或 `INCOMPLETE` 结论

#### Scenario: 验证打包后 lint 可执行

- **WHEN** 从每个平台离线包解压两个 Qt skill
- **THEN** SHALL 能以最小样例运行其确定性 lint 脚本
- **AND** skill 引用完整性和许可证检查 SHALL 通过
