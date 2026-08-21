# Project Context Skill 使用说明

## 目标

`edanspec:project-context` 用于建立和增量更新工程师可读的项目知识地图。它不追求把所有类画进一张图，而是按问题逐层下钻：

| 层级 | 内容 | 默认规模 |
|------|------|----------|
| L0 | 系统、领域、外部边界 | 10–30 个节点 |
| L1 | 单个模块的核心工程构件 | 每图不超过 25 个节点 |
| L2 | 一个业务场景的端到端流程 | 每图 8–20 个节点 |
| L3 | 支撑图中关系的源码证据 | 按需 |
| L4 | 指定修改目标的影响范围 | 默认 2 层，最多 3 层 |

核心原则是：**CodeGraph 索引优先，源码证据兜底，推断必须显式标记。**

## 适用场景

- 新工程首次建立项目上下文
- 大型代码库的专题知识地图
- 代码变化后增量更新模块或流程
- 修改前分析影响面

单个 feature 的需求澄清使用 `explore` 或 `create-spec`。

## 前置条件

在目标工程安装并初始化官方 `@colbymchenry/codegraph`：

```powershell
npm install -g @colbymchenry/codegraph
codegraph init "C:\path\to\project"
codegraph status "C:\path\to\project" --json
```

默认索引位于 `.codegraph/codegraph.db`。如果环境设置了 `CODEGRAPH_DIR`，以 `codegraph status --json` 返回的实际路径为准。

## 四种执行模式

| 模式 | 用途 | 产物 |
|------|------|------|
| Bootstrap | 首次建立完整地图 | L0，再逐个建立 L1/L2 |
| Targeted | 用户指定模块或业务场景 | 最小 L0 + 相关 L1/L2/L3 |
| Update | 代码或结构已变化 | 只更新受影响文档 |
| Impact | 修改前检查风险 | L4 |

用户已经给出明确专题时，优先使用 Targeted，避免为无关模块做全库展开。

## 查询方式

主 Agent 优先直接调用默认 MCP 工具：

```text
codegraph_explore({
  query: "<一个明确的工程问题>",
  maxFiles: 12,
  projectPath: "<目标工程绝对路径>"
})
```

没有 MCP 的子 Agent 使用等价 CLI：

```powershell
codegraph explore "<同一问题>" --path "<目标工程绝对路径>" --max-files 12
```

一次查询只回答一个架构或业务问题。CodeGraph 已返回的源码不要再用全库 grep 重复读取；只针对 QML/C++ 绑定、Qt signal/slot、宏、反射、配置装配、生成代码等静态图盲区做小范围补证。

## 证据状态

| 状态 | 含义 |
|------|------|
| `Verified` | 已由具体源码、配置或接口定义直接证明 |
| `Graph-Heuristic` | CodeGraph 给出高价值静态线索，但仍有动态跳转未确认 |
| `Inferred` | 根据命名、目录或相邻事实推断 |
| `Unknown` | 现有证据不足，禁止补造关系 |

重要关系必须带 Evidence ID。每个 `Unknown` 都要写明下一步补证方法。

## 产物

```text
EdanSpec/context/
├── project.md
├── modules/
│   └── {module}/
│       ├── module.md
│       └── flows/
│           └── {flow}.md
└── impacts/
    └── {target}.md
```

文档是人工导航视图，源码才是事实权威。L1/L2 证据与 L0 冲突时，应修正 L0，而不是扭曲下层事实。

## 运行和校验

大仓库先做快速结构扫描：

```powershell
python .claude/skills/project-context/scripts/scan-project.py --fast "C:\path\to\project"
```

生成文档后运行：

```powershell
python .claude/skills/project-context/scripts/validate_context.py `
  "C:\path\to\project\EdanSpec\context" --json
```

校验器检查：

- 文档链接是否存在
- Evidence ID 是否定义且唯一
- 证据状态是否合法
- Mermaid 图是否超过层级上限
- 模板占位符是否残留

校验通过后仍需按 `references/review-checklist.md` 做人工评审，特别检查动态调用盲区、入口到结果的连续性、图文一致性和误导性推断。

## 常见误区

- 把 CodeGraph 的影响摘要当作完整业务流
- 把搜索分数当作事实置信度
- 按目录猜模块后直接标为 `Verified`
- 把所有类和函数画进一张图
- 强制 L2 的所有节点都出现在 L1 构件图
- 忽略 QML、Qt 信号槽、回调、宏和生成代码
- 未经授权删除或重建已有 `context/`

完整执行契约以 [`../skills/project-context/SKILL.md`](../skills/project-context/SKILL.md) 为准。
