# Qt QML 专项走读编排

本文件定义 `qt-qml-review` 被通用代码走读调用时的专项执行契约。它不改变 QML 检查清单，只规定输入边界、阶段顺序和报告保真要求。

## 输入边界

- 只审查调用方传入的 `matchedFiles`，不扫描范围外的 QML 文件。
- 读取注册项传入的 `guidance` 文件；项目经验不能覆盖 Qt 官方规则。
- 用户明确要求 diff/commit 范围时，只报告变更行及必要上下文中的问题。
- 全程只读，不修改被审查项目源代码。

## 阶段顺序

1. Phase 1：运行 `references/lint-scripts/qt_qml_lint.py`，完整收集确定性 lint 输出。
2. Phase 1b：系统存在 `qmllint` 时执行类型级检查；不可用时记录 warning 并继续。
3. Phase 2：并行执行 bindings/properties、layout/anchoring、component loading/lifecycle、ListView/delegates、states/structure、performance/code quality 六个专项分析。
4. Phase 3：按 QML 原始报告格式整理发现，保留规则 ID、置信度、文件位置和追踪信息。

Python 不可用时记录 lint 阶段未运行并将专项状态降为 `partial`；`qmllint` 不可用本身不降低其他阶段的完成状态。

## 聚合接口

专项报告返回给通用入口时必须包含：`stackId`、`status`、`scope`、`qmllint` 可用性、原始报告路径（如已写入）和发现列表。通用入口只做来源标记、位置/语义去重和严重度映射，不复制 QML 规则。
