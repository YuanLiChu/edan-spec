# 可配置技术栈专项代码走读提案

## Why

`edanspec-code-review` 需要保持通用，同时允许项目在检测到特定技术栈时调用对应的专项走读。Qt C++ 和 Qt QML 是第一批专项能力，后续还需要能够增加 Java、C# 等技术栈，而不修改通用编排器。

## What Changes

- 增加项目级 `.edan-dev/review-stack.yaml` 注册表，集中描述技术栈匹配规则、专项 skill 和项目级 guidance。
- `edanspec-code-review` 始终执行通用四维走读，再按注册表为每个启用技术栈计算 `matchedFiles` 并调用对应 skill。
- Qt C++/QML 的阶段编排、检查清单、lint、报告格式和经验沉淀放在各自 `skills/qt-*-review/` 目录。
- 专项报告以 `specialists.<stack-id>` 状态进入统一报告；配置错误或启用专项失败时结论为 `INCOMPLETE`。
- 离线包构建保持只复制和校验通用 `skills/` 目录，不增加 Qt 特判。

## Out of Scope

- 不改变 `project-context` 的 CodeGraph 知识图谱流程。
- 不把技术栈检查项复制到通用 reviewer。
- 不要求通用代码走读理解 Qt、Java 或 C# 语义。
- 不自动修改被审查项目源代码。
