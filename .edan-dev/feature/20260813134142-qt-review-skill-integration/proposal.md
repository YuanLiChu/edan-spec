# Qt 专项代码审查 Skill 集成提案

## Why

现有 `edanspec:code-review` 以通用的正确性、可读性、架构和性能四个维度审查代码，但缺少 Qt 6 C++ 与 QML 的框架级契约检查。对于包含 Qt model/view、QObject 生命周期、线程亲和性、信号槽、QML binding、delegate 和渲染性能的变更，仅依赖通用检查容易遗漏 Qt 特有问题。

需要将 Qt 官方审查规则形成的 `qt-cpp-review` 与 `qt-qml-review` 完整打包进 EdanSpec，并由 `edanspec:code-review` 根据实际审查内容自动调用，同时保留专项报告并聚合到现有统一报告中。

## What Changes

- 将 `qt-cpp-review` 和 `qt-qml-review` 的完整 skill、参考检查清单、确定性 lint 脚本、说明文档和许可证纳入 EdanSpec。
- 以 Claude Code 目录为两个 Qt skill 的唯一权威源码；OpenCode 在离线构建时适配派生，Kilo 从 OpenCode 产物继续派生。
- 扩展 `edanspec:code-review` 的审查范围分类：实际范围包含有明确 Qt 证据的 C++ 文件时自动调用 `qt-cpp-review`，包含 QML 文件时自动调用 `qt-qml-review`。
- 保留原有通用四维审查；Qt/C++ 与 QML 同时存在时，两个专项审查分别处理匹配文件。
- 保留 Qt 专项原始报告，并按文件、行号和问题语义去重后聚合为 EdanSpec 的统一严重度报告。
- 增加 `INCOMPLETE` 结论，防止专项阶段缺失或失败时误报完整 `APPROVE`。
- 扩展离线包和行为测试，验证三平台均包含可执行、带许可证且路径适配正确的 Qt skill。

## Impact

- `claudecode/.claude/skills/qt-cpp-review/`：新增 Qt 6 C++ 专项审查 skill 的权威源码。
- `claudecode/.claude/skills/qt-qml-review/`：新增 Qt 6 QML 专项审查 skill 的权威源码。
- `claudecode/.claude/skills/code-review/SKILL.md`：增加内容识别、自动路由、专项执行和报告聚合规则。
- `claudecode/.claude/skills/code-review/reviews/`：扩展统一报告模板和示例，支持 Qt 专项来源与 `INCOMPLETE`。
- `claudecode/.claude/agents/code-reviewer.md`：对齐 Qt 专项发现的严重度映射和去重契约。
- `claudecode/.claude/skills/task-implement/SKILL.md`：将 `INCOMPLETE` 视为审查未通过，保持完成门禁闭合。
- `opencode/.opencode/skills/edanspec-code-review/`：同步适配后的总审查编排规则；Qt skill 由构建流程从 Claude Code 权威源码派生。
- `scripts/build_offline_bundles.py`：派生并验证 OpenCode、Kilo 的两个 Qt skill。
- `tests/`：新增自动路由、报告聚合、skill 完整性、许可证和三平台离线包测试。

## Out of Scope

- 修改 `project-context` 的项目知识地图或 CodeGraph 走读流程。
- 把 Qt 专项规则复制进 EdanSpec 通用四维检查清单。
- 审查或支持 Qt 5 专属兼容性问题；本次范围限定为 Qt 6。
- 自动启用 `qt-cpp-review framework` 模式；仅按原 skill 契约检测并建议，由用户确认后启用。
- 修改被审查项目的源代码；所有审查 skill 保持只读。
