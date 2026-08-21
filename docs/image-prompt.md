# EdanSpec Skills 工作流地图 - GPT-image 2 绘图提示词

## GPT-image 2 专用提示词

```text
请生成一张 16:9 横向中文信息图，白色背景，现代工程文档风格，适合放在 README 或项目介绍页中。

主题标题放在画面顶部居中：
"EdanSpec - AI 辅助软件开发的结构化工作流"

标题下方放一行副标题：
"11 个 Skills 串联需求澄清、方案设计、增量实现、审查验证与归档"

整体视觉要求：
- 使用清晰的无衬线中文字体，文字黑色或深灰色
- 背景保持纯白或极浅灰，不要使用复杂纹理
- 采用信息图风格，不要画成卡通插画
- 使用柔和但有区分度的色块：蓝、青、紫、橙、绿、金、灰
- 所有文字必须可读，避免小字过密
- 箭头、分组边框、图例清晰，整体干净克制
- 不要出现英文长段落，不要出现代码块

画面主体是一个从左到右的流程图，分为 5 个大阶段，每个阶段是一个浅色分组容器，容器内放对应 Skill 节点。节点使用圆角矩形，节点之间用箭头连接。

第一阶段：项目接入（浅蓝色分组）
节点：project-context
节点说明：
"扫描项目结构"
"生成知识地图"
"project.md / module.md / flow.md"

从 project-context 分出两条入口箭头：
1. 指向 explore，箭头标签："模糊需求"
2. 指向 create-spec，箭头标签："清晰需求"

第二阶段：需求与规格（浅青色分组）
节点 1：explore
节点说明：
"反问澄清需求"
"调查代码库"
"比较方案与风险"

节点 2：create-spec
节点说明：
"创建 feature 目录"
"生成 proposal / spec / design"
"一个变更 = 一个目录"

explore 用箭头连接到 create-spec。

第三阶段：设计与任务（浅紫色分组）
节点 1：design-review
节点说明：
"复杂功能架构评审"
"八章方案 + 八章详细设计"

节点 2：task-plan
节点说明：
"拆分可执行任务"
"验收标准 / 验证步骤 / 依赖关系"
"tasks.md 是唯一进度来源"

create-spec 分两条箭头：
1. 小功能直接到 task-plan，箭头标签："小功能"
2. 大功能到 design-review，再到 task-plan，箭头标签："大功能 / 架构变更"

第四阶段：实现与排障（浅橙色分组）
节点 1：task-implement
节点说明：
"TDD 循环"
"RED -> GREEN -> REFACTOR"
"每个增量独立验证后原子提交"

节点 2：debugging
节点说明：
"观察 -> 复现 -> 定位 -> 修复 -> 验证"
"反复失败时重新定位根因"

task-plan 用主箭头连接到 task-implement。
task-implement 到 debugging 使用虚线回流箭头，箭头标签："测试失败 / 反复修复失败"。
debugging 再用虚线箭头回到 explore，箭头标签："重估方案"。

第五阶段：审查、验证与归档（浅绿色分组）
在 task-implement 右侧放一个子分组，标题："三重质量关卡"。
子分组内从左到右放 3 个节点：

节点 1：code-review
节点说明：
"正确性 / 可读性 / 架构 / 性能"

节点 2：security-review
节点说明：
"输入验证 / 认证授权 / 数据保护"
"机密管理 / 依赖安全"

节点 3：verify
节点说明：
"完整性 / 正确性 / 一致性"
"归档前最终验收"

task-implement 用箭头连接到 code-review，再到 security-review，再到 verify。

verify 右侧放最终节点：archive（浅灰色）
节点说明：
"delta spec 合并"
"feature 移入 archive"
"完成变更闭环"

verify 用箭头连接到 archive。

在流程图下方放一条横向底座，标题："EdanSpec 运行时目录"。
底座中用 4 个小图标式区块展示：
1. context/
   "项目知识地图"
2. feature/{timestamp}-{topic}/
   "proposal / spec / design / tasks"
3. specs/
   "主规格沉淀"
4. archive/
   "完成变更归档"

在画面左下角放一个小型理念区，标题："核心目标"。
用三个并列徽章展示：
"可控：先澄清，再规划"
"可验证：构建与测试作为证据"
"可追溯：文件系统恢复上下文"

在画面右下角放一个小型规则区，标题："Agent 铁律"。
只列 4 条短句：
"亮出假设"
"有疑问就停"
"只做分内事"
"拿证据说话"

重要限制：
- 不要提到 status.json 作为状态来源；新版强调从文件系统事实推导状态
- 不要把流程画成只有 6 个 Skill；必须体现 11 个 Skills
- 不要把 archive 标成 Skill 8；archive 是第 11 个 Skill
- 不要使用过度装饰、3D、卡通人物、机器人头像或科技霓虹背景
- 不要生成无法阅读的小字密集表格
```
