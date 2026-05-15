# edan-dev

一套结构化的 AI 辅助软件开发工作流，包含 Agent 规范、编码规则、技能（Skills）和文档模板。

## 核心理念

- **先想清楚再动手** — 非平凡任务先出方案，5 分钟确认比 5 小时返工划算
- **拿证据说话** — 通过测试绿、构建过、数据对来验证，"看起来对"不算
- **增量开发** — 每个增量独立完成一条验收标准，原子提交
- **一个变更 = 一个目录** — 用 feature 目录聚合所有产物，从文件恢复上下文，不依赖会话记忆

## 目录结构

```
├── AGENT.md                    # Agent 基础规范（核心铁律 + 上下文管理 + 变更工单）
├── docs/                       # 补充文档
│   ├── anti-patterns.md        # 常见借口与反驳
│   └── git-conventions.md      # Git 操作规范
├── rules/                      # 编码规范
│   ├── common/                 # 通用编码风格（所有语言适用）
│   ├── java/                   # Java 编码风格
│   └── kotlin/                 # Kotlin 编码风格
├── skills/                     # 技能集合
│   ├── project-context/        # 项目上下文初始化（扫描项目 → 生成知识地图）
│   ├── explore/                # 探索模式（需求澄清 + 方案比较）
│   ├── create-spec/            # 创建 feature 目录 + 生成 proposal/spec/design
│   ├── design-review/          # 复杂功能的正式评审（八章方案 + 八章详细设计）
│   ├── task-plan/              # 任务规划（拆分为可执行任务清单）
│   ├── task-implement/         # 任务实现（TDD 循环 + 原子提交）
│   ├── debugging/              # 调试排障（五步流程）
│   ├── code-review/            # 代码审查（四维度评估）
│   ├── security-review/        # 安全审查（五维度检查）
│   ├── verify/                 # 结构化验证（三维度验收）
│   └── archive/                # 归档（delta spec 合并 + 文件移动）
└── .edan-dev/
    ├── context/                  # 项目知识地图（运行时生成，持久维护）
    │   ├── project.md            # 项目级上下文
    │   └── modules/              # 模块级设计文档
    │       └── {module-name}/
    │           ├── module.md     # 模块设计（职责边界、类图、时序图）
    │           └── flows/
    │               └── {flow-name}.md  # 业务流设计（输入输出、调用序列）
    ├── specs/                    # 主 spec（长期维护）
    ├── feature/                  # 变更工单（按 feature 组织）
    └── archive/                  # 归档（已完成 feature）
```

## 工作流

```
[项目首次接入] ──→ project-context ──→ [后续 feature 工作流]
                                            │
模糊需求 ──→ explore ──→ create-spec ──→ task-plan ──→ task-implement ──→ verify ──→ archive
                    │         │
                    │         ↓（大功能/架构变更时引导）
                    │      design-review
                    ↓（明确需求可跳过）
                create-spec
```

### 各阶段说明

| 阶段 | Skill | 做什么 |
|------|-------|--------|
| **项目上下文** | `project-context` | 扫描工程项目结构，生成 project.md + module.md + flow.md 知识地图 |
| **探索** | `explore` | 通过反问帮助明确需求，调查代码库，比较方案，不生成文件 |
| **建规格** | `create-spec` | 创建 feature 目录，生成 proposal + spec + design 文档（逐章确认） |
| **设计评审** | `design-review` | 大功能/架构变更时执行，产出八章方案文档 + 八章详细设计 |
| **任务规划** | `task-plan` | 按完整功能拆分需求，生成验收标准、验证步骤、工时估算、依赖关系 |
| **任务实现** | `task-implement` | TDD 循环（RED→GREEN→REFACTOR），每个增量独立验证后原子提交 |
| **调试排障** | `debugging` | 观察→复现→定位→修复→验证，五步流程，不盲目改代码 |
| **代码审查** | `code-review` | 四维度评估：正确性、可读性、架构、性能 |
| **安全审查** | `security-review` | 五维度检查：输入验证、认证/授权、数据保护、机密管理、依赖安全 |
| **结构化验证** | `verify` | 三维度验收：完整性、正确性、一致性，归档前最终关卡 |
| **归档** | `archive` | delta spec 合并到主规范，feature 移至归档目录 |

## Agent 核心铁律

1. **亮出假设** — 需求模糊时不要脑补，把假设列出来
2. **有疑问就停** — 碰到矛盾时停→说清问题→给选项→等回复
3. **该反对就反对** — 方案有明显问题时指出问题+给替代方案
4. **能简单别复杂** — 无聊的方案 > 聪明的方案
5. **只做分内事** — 只改被要求改的，不"顺手"
6. **拿证据说话** — 测试绿、构建过、数据对

## Git 规范

遵循 Conventional Commits：`<type>(<scope>): <description>`，原子提交，Trunk-Based 开发，Rebase 优先。详见 [docs/git-conventions.md](docs/git-conventions.md)。

## 编码规范

- 通用规范：[rules/common/coding-style.md](rules/common/coding-style.md)
- Java 规范：[rules/java/coding-style.md](rules/java/coding-style.md)
- Kotlin 规范：[rules/kotlin/coding-style.md](rules/kotlin/coding-style.md)

## 测试覆盖率基线

| 指标 | 基线 |
|------|------|
| 行覆盖率 | ≥ 80% |
| 分支覆盖率 | ≥ 70% |
| 主要路径 | 100% |
