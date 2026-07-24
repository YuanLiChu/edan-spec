# EdanSpec 三平台离线 Skill 打包设计

## 1. 目标

基于 `C:\work\EdanSpec` 当前工作区生成三个可带入纯内网环境的独立 ZIP 包，分别供 Claude Code、OpenCode 和 Kilo Code 使用。压缩包解压到目标项目根目录后即可被对应工具发现，不需要联网下载依赖。

## 2. 已确认决策

- 同时交付 Claude Code、OpenCode、Kilo Code 三个平台包。
- 打包源为当前工作区，包含尚未提交的 Skill、模板、脚本和配套文档修改。
- 先把 Claude Code 中较新的功能修改定向适配到 OpenCode，再以 OpenCode 兼容 Skill 为基础生成 Kilo 包。
- 不直接整目录覆盖平台资源；保留各平台的名称、目录和前置元数据约束。

## 3. 范围

### 3.1 包含

- Claude Code 的 `.claude/` 资源。
- OpenCode 的 `.opencode/` 与 `opencode.json`。
- Kilo Code 的 `.kilo/skills/`、`.kilo/agents/` 与项目根 `AGENTS.md`。
- 每个平台独立的 `INSTALL.md`。
- 每个平台包内文件的 `MANIFEST.sha256`。
- 三个最终 ZIP 的汇总校验文件 `SHA256SUMS.txt`。
- Windows PowerShell 与 Linux Shell 的解压、安装和发现验证命令。

### 3.2 不包含

- Agent CLI、模型、运行时、Python、Node.js 或第三方依赖安装包。
- 用户凭证、模型配置、API 地址及内网环境配置。
- 当前工作区中的日志、缓存、`.DS_Store`、`__pycache__`、`.pyc`。
- 向远端仓库推送、创建 PR 或发布 Release。

## 4. 方案

采用定向适配同步：

1. 读取当前工作区差异，识别 Claude Code 中发生变化的 Skill 及其依赖资源。
2. 将对应内容同步到 OpenCode 目录，同时保留 OpenCode 的连字符 Skill 名称、目录名和平台路径。
3. 对代理定义、模板链接、脚本引用做平台路径检查，禁止残留 `.claude/` 路径进入 OpenCode/Kilo Skill。
4. 由同步后的 OpenCode Skill 生成 Kilo `.kilo/skills/`，确保 Skill 的 `name` 与目录名均为小写、数字、连字符格式且一致。
5. 分别建立三个暂存目录，加入平台安装说明和文件清单后生成 ZIP。

不采用以下方案：

- 整目录复制：会破坏 OpenCode/Kilo 的名称和路径约束。
- 临时生成器框架：本次只有三个固定目标，新增长期转换框架会扩大范围。

## 5. 输出结构

输出目录：

```text
dist/edan-spec-offline-20260724/
├── edan-spec-claudecode-20260724.zip
├── edan-spec-opencode-20260724.zip
├── edan-spec-kilocode-20260724.zip
└── SHA256SUMS.txt
```

Claude Code 包：

```text
/
├── .claude/
├── INSTALL.md
└── MANIFEST.sha256
```

OpenCode 包：

```text
/
├── .opencode/
├── opencode.json
├── INSTALL.md
└── MANIFEST.sha256
```

Kilo Code 包：

```text
/
├── .kilo/
│   ├── agents/
│   └── skills/
├── AGENTS.md
├── INSTALL.md
└── MANIFEST.sha256
```

所有 ZIP 均直接解压到目标项目根目录，不额外嵌套版本目录。

## 6. 平台适配规则

### 6.1 Claude Code

- 保留当前 `.claude/skills/<skill>/` 结构。
- 保留 Claude Code 使用的 Skill 名称和代理定义。
- 包含 Skill 所依赖的 `agents/`、`docs/`、`rules/`、模板与脚本。

### 6.2 OpenCode

- 对通用 EdanSpec Skill 使用 `edanspec-<name>` 目录和匹配的 frontmatter `name`。
- `project-context` 保留仓库当前的兼容命名。
- 将 Claude Code 新增或修改的功能内容适配到 `.opencode/` 路径。
- 保留 `opencode.json` 中现有权限和 Agent 配置，不引入内网地址或模型配置。

### 6.3 Kilo Code

- 从 OpenCode 兼容 Skill 复制到 `.kilo/skills/`。
- 将 `project-context` 依赖的 `module-explorer`、`flow-explorer` 适配为 Kilo `subagent`，放入 `.kilo/agents/`。
- Skill 目录名必须与 frontmatter `name` 一致。
- 名称只能使用小写字母、数字和连字符，不使用 Claude 风格的冒号。
- 根目录提供 `AGENTS.md`，使 Kilo 加载项目规范。
- 使用本机 Kilo CLI 验证其实际支持的发现路径；不把未经验证的 OpenCode 配置文件放入 Kilo 包。

## 7. 安装说明

每个 `INSTALL.md` 至少包含：

- 包用途与适用平台。
- 解压到已有项目根目录的 PowerShell 和 Linux 命令。
- 覆盖已有配置前的备份提醒。
- Skill 发现验证命令。
- 常见问题：隐藏目录未复制、解压层级错误、Skill 名称不匹配、CLI 未安装。
- 纯内网边界：包内资源无需联网，但 Agent CLI 和模型服务必须由内网环境预先提供。

## 8. 错误处理

- 当前工作区存在未解决 Git 冲突时停止打包。
- 平台对应 Skill 缺失、frontmatter 无法解析或名称不匹配时停止打包。
- 目标暂存目录存在时创建新的临时目录，不覆盖来源文件。
- ZIP 生成后必须重新解压到独立临时目录验证，不能只检查压缩命令退出码。
- 本机缺少某个平台 CLI 时，完成静态结构验证，并在交付说明中明确该平台未做真实 CLI 发现测试。

## 9. 验证

### 9.1 仓库验证

- 运行现有 Python 测试。
- 运行现有 Node 测试。
- 运行 `git diff --check`，区分本次新增问题与既有未提交内容。

### 9.2 内容验证

- 三个 ZIP 均可在全新临时目录中解压。
- 解压后的文件数、相对路径和 SHA-256 与包内清单一致。
- 不包含 `.DS_Store`、`__pycache__`、`.pyc`、日志或 Git 元数据。
- Claude Code 与 OpenCode 包包含各自完整的平台入口。
- Kilo 包中每个 Skill 的目录名与 frontmatter `name` 一致。
- Kilo 包中的 `module-explorer`、`flow-explorer` 可由 `kilo debug agent <name>` 发现。

### 9.3 CLI 验证

- Claude Code：若本机 CLI 可用，验证 Skill 列表或最接近的只读发现命令。
- OpenCode：若本机 CLI 可用，验证配置和 Skill 可发现性。
- Kilo Code：使用临时项目运行 `kilo debug skill`，确认 Skill 被发现；不调用外部模型。

## 10. 验收标准

- 交付三个独立 ZIP 和一个汇总 SHA-256 文件。
- 三个平台包均来自当前工作区并通过对应适配规则检查。
- ZIP 可离线解压，目录层级无需人工调整。
- Kilo Skill 名称和目录规则全部通过。
- 所有可执行的本地测试通过；无法执行的 CLI 验证有明确说明。
- 不改动或提交用户已有的无关工作区修改。
