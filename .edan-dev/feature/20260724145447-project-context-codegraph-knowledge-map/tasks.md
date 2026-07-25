# Project Context CodeGraph 知识地图任务

## Task 1：锁定 CodeGraph 契约与测试基线

**描述**：把上游默认 MCP、CLI、索引路径和自动同步行为固化为可执行测试，先让旧实现暴露失败。

**关联需求**：使用真实 CodeGraph 契约；大仓库索引优先。

**涉及文件**：
- `tests/test_project_context_codegraph.py`
- `tests/test_scan_project.py`

**验收标准**：
- [ ] 测试断言默认能力是 `codegraph_explore`，不依赖隐藏 MCP 工具。
- [ ] 测试断言索引路径为 `.codegraph/codegraph.db`。
- [ ] 测试覆盖扫描脚本快速模式和完整模式。

**验证步骤**：
- [ ] `python -m unittest tests.test_project_context_codegraph tests.test_scan_project -v`

**依赖关系**：无。

**估算**：0.5 人天。

## Task 2：改造扫描与编排层

**描述**：更新 `scan-project.py` 和 `project-context/SKILL.md`，实现索引自检、L0-L4、MCP 优先、CLI 等价回退和大仓库门禁。

**关联需求**：真实 CodeGraph 契约；分层知识地图；大仓库索引优先；主 Agent 与 Explorer 边界。

**涉及文件**：
- `claudecode/.claude/skills/project-context/scripts/scan-project.py`
- `claudecode/.claude/skills/project-context/SKILL.md`
- `tests/test_scan_project.py`
- `tests/test_project_context_codegraph.py`

**验收标准**：
- [ ] Skill 使用 `codegraph_explore` 作为唯一必需 MCP 能力。
- [ ] 大仓库默认不递归 grep 调用链。
- [ ] L0-L4 每层有节点上限、输入、输出和停止条件。
- [ ] 扫描脚本可快速跳过逐文件行数统计。

**验证步骤**：
- [ ] Task 1 两组测试全部通过。
- [ ] `python claudecode/.claude/skills/project-context/scripts/scan-project.py --fast .` 返回有效 JSON。

**依赖关系**：依赖 Task 1。

**估算**：0.75 人天。

## Task 3：改造 Explorer 与人类可读模板

**描述**：更新 module/flow explorer 输入输出契约，新增证据、盲区、图例和影响分析模板。

**关联需求**：分层知识地图；关系可追溯；主 Agent 与 Explorer 边界。

**涉及文件**：
- `claudecode/.claude/agents/module-explorer.md`
- `claudecode/.claude/agents/flow-explorer.md`
- `claudecode/.claude/skills/project-context/references/project-template.md`
- `claudecode/.claude/skills/project-context/references/module-template.md`
- `claudecode/.claude/skills/project-context/references/flow-template.md`
- `claudecode/.claude/skills/project-context/references/impact-template.md`

**验收标准**：
- [ ] Explorer 优先消费传入证据并定向调用 CodeGraph，不全库 grep。
- [ ] 图谱节点使用“工程职责 + 代码符号”命名。
- [ ] 每个模板包含证据表、证据等级和已知盲区。
- [ ] flow 核心参与者与 module 一致，但允许辅助节点进入 L3 证据并触发 module 增量更新。

**验证步骤**：
- [ ] `python -m unittest tests.test_project_context_codegraph -v`
- [ ] Mermaid 代码块与模板占位符静态检查通过。

**依赖关系**：依赖 Task 2。

**估算**：0.75 人天。

## Checkpoint A：Skill 实现验证

- [ ] project-context 契约测试全部通过。
- [ ] scan-project 单元测试全部通过。
- [ ] Skill 快速校验通过。
- [ ] `git diff --check` 无新增格式问题。

## Task 4：验证 Claude 单一源码与跨平台派生

**描述**：确认离线包/安装流程从 Claude Code 源码适配 project-context，不把 OpenCode/Kilo 副本作为手工维护源。

**关联需求**：单一源码与跨平台适配。

**涉及文件**：
- 现有离线包生成脚本与测试（若已实现）
- project-context 平台适配测试

**验收标准**：
- [ ] Claude Code 版本是唯一编辑源。
- [ ] OpenCode/Kilo 派生包包含新模板、脚本和 explorer 等价配置。
- [ ] 不覆盖当前工作区其他未提交变更。

**验证步骤**：
- [ ] 运行现有离线包构建测试或记录“构建器尚未实现”的明确边界。
- [ ] 检查派生包内 project-context 关键契约。

**依赖关系**：依赖 Checkpoint A。

**估算**：0.25 人天。

## Task 5：安装并初始化 CodeGraph

**描述**：安装官方 npm 包，连接必要的 agent 配置，在目标项目构建索引并验证状态。

**关联需求**：真实项目闭环。

**涉及文件**：
- 全局 npm 安装目录
- `C:\code\new-alarm\nxapp\.codegraph\`

**验收标准**：
- [ ] `codegraph --version` 成功。
- [ ] `codegraph init` 在目标目录成功。
- [ ] `.codegraph/codegraph.db` 存在。
- [ ] `codegraph status` 成功并报告项目统计。

**验证步骤**：
- [ ] `codegraph --version`
- [ ] `codegraph status C:\code\new-alarm\nxapp`

**依赖关系**：依赖 Checkpoint A。

**估算**：0.25 人天，不含首次索引耗时。

## Task 6：生成报警限推荐知识地图

**描述**：用改造后的 project-context 在 `nxapp` 生成项目、相关模块、报警限推荐业务流和证据文档。

**关联需求**：真实项目闭环；所有重要关系可追溯。

**涉及文件**：
- `C:\code\new-alarm\nxapp\EdanSpec\context\project.md`
- `C:\code\new-alarm\nxapp\EdanSpec\context\modules\*\module.md`
- `C:\code\new-alarm\nxapp\EdanSpec\context\modules\*\flows\*alarm*.md`

**验收标准**：
- [ ] L0 系统地图包含报警限推荐相关模块边界。
- [ ] L1 模块图不超过 25 个核心构件。
- [ ] L2 业务流图只描述报警限推荐场景。
- [ ] L3 证据表能定位实际符号和源码路径。
- [ ] 动态关系和解析盲区明确标为 Unknown。

**验证步骤**：
- [ ] 所有 Mermaid 代码块可解析。
- [ ] 所有证据路径存在。
- [ ] 所有 Verified 符号可由 CodeGraph 或源码确认。

**依赖关系**：依赖 Task 5。

**估算**：0.5 人天。

## Task 7：验证、审查与闭环

**描述**：执行全量测试、Skill 校验、三维验证和四维代码审查，修复所有必须项。

**关联需求**：质量闭环。

**涉及文件**：
- 本 feature 全部变更
- `.edan-dev/feature/20260724145447-project-context-codegraph-knowledge-map/review/`

**验收标准**：
- [ ] 自动化测试全部通过。
- [ ] 完整性、正确性、一致性无 CRITICAL。
- [ ] 代码审查无 CRITICAL/IMPORTANT。
- [ ] 真实项目产物满足节点、证据和盲区约束。

**验证步骤**：
- [ ] `python -m unittest discover -s tests -v`
- [ ] Skill `quick_validate.py` 通过。
- [ ] `git diff --check` 通过。
- [ ] 输出验证与代码审查报告并复验修复项。

**依赖关系**：依赖 Task 4 和 Task 6。

**估算**：0.5 人天。
