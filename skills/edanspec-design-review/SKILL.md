---
name: edanspec-design-review
description: 复杂功能的正式评审流程——八章方案文档 + 八章详细设计。触发场景：用户明确说「出方案」「详细设计」「架构评审」「design review」。日常功能用 edanspec-create-spec 即可。前置条件：feature 下已有 proposal + spec + design 产物（由 create-spec 生成）。
---

<!-- SCRIPTS: scripts/（相对本 SKILL.md 所在目录），正文中统一用 {{SCRIPTS}} 引用 -->

# 设计评审（复杂评审）

> **日常功能用 `edanspec-create-spec` 就够了。** 本 skill 用于大功能/架构变更的正式评审——产出八章方案文档 + 八章详细设计。

在写代码之前，把需求变成重量级的结构化技术文档。

**核心原则：先想清楚再动手。5 分钟确认比 5 小时返工划算。**

## 工作流程

```
检测产物 → 缺少则提示先执行 create-spec
         ↓
    基于产物生成方案文档 → 基于方案生成详细设计 → Word 导出（可选）
```

**上下文管理**：按阶段加载，只读当前需要的内容；每章写完立即保存。详见 `AGENT.md` 中的「上下文管理」章节。

---

## 阶段零：产物检测

启动时先读 `status.json` 了解上下文，再检测 feature 下是否已有产物：

| status.json 状态 | 含义 | 处理 |
|-----------------|------|------|
| `designReviewState: "recommended"` | create-spec 推荐但尚未执行 | 正常执行，向用户确认"按 create-spec 建议进入 design-review" |
| `designReviewState: "skipped"` | 用户之前跳过，现在主动回来 | 正常执行，提示"之前跳过了 design-review，现在开始。产物将写入 review/ 目录" |
| `designReviewState: "none"` 或字段不存在 | 用户直接调用，未经 create-spec 引导 | 正常执行，不追问为什么来 |

然后检测产物（proposal.md + specs/ + design.md）：

| 检测 | 有产物 | 无产物 |
|------|--------|--------|
| proposal.md | 直接读取作为输入 | **提示用户先执行 `edanspec-create-spec`** |
| specs/*.md | 直接读取作为输入 | **提示用户先执行 `edanspec-create-spec`** |
| design.md | 直接读取作为输入 | **提示用户先执行 `edanspec-create-spec`** |

**产物缺失时不内联生成。** 提示用户先用 `edanspec-create-spec` 创建产物，再重新执行本 skill。

> **design.md 的角色**：design.md 由 create-spec 阶段生成，design-review 将其作为**输入**——在此基础上做更深入的架构评审，产出独立的 `review/solution.md` 和 `review/detail.md`。design-review 不覆盖、不重新生成 design.md，而是增强它。

有产物则直接读取，跳过生成。不跳过、不假设。

---

## 阶段一：方案文档生成

基于产物文档（proposal + spec + design），生成高层架构设计评审文档。

- **模板**：`templates/design-review-template.md`（八章，模块级架构）
- **输出**：`EdanSpec/feature/<name>/review/solution.md`
- **逐章生成**：读一章 → 写一章 → 保存 → 展示摘要 → 用户确认 → 下一章
- **禁止多章批量生成**——上下文膨胀，质量跳水

**技术选型**：直接读取 `design.md` 中的 Decisions 章节，沿用已记录的技术选型。不重新选型、不引入新依赖。design-review 是对 create-spec 产出的 design.md 的增强评审，不是替代。

---

## 阶段二：详细设计文档生成

基于方案文档和产物文档，生成代码级详细设计。

- **模板**：`templates/detail-design-template.md`（八章，代码级细节）
- **输出**：`EdanSpec/feature/<name>/review/detail.md`
- 同样逐章生成，不批量

---

## 阶段三：Word 导出（可选）

问用户是否要转 docx。pandoc 不渲染 Mermaid，先用 `{{SCRIPTS}}/generate_mermaid_images.py` 转 PNG。

> `{{SCRIPTS}}` 引用自文件顶部 SCRIPTS 锚点。

**优先方案 — pandoc：**
```bash
python3 {{SCRIPTS}}/generate_mermaid_images.py EdanSpec/feature/<name>/review/solution.md --replace
pandoc EdanSpec/feature/<name>/review/solution-images.md -o EdanSpec/feature/<name>/review/solution.docx
```

**备选方案 — generate_docx.py（pandoc 未安装时）：**
```bash
python3 {{SCRIPTS}}/generate_mermaid_images.py EdanSpec/feature/<name>/review/solution.md --replace
python3 {{SCRIPTS}}/generate_docx.py EdanSpec/feature/<name>/review/solution-images.md EdanSpec/feature/<name>/review/solution.docx
```

> `generate_docx.py` 使用 python-docx 渲染 Markdown（支持标题、粗体、代码块、列表、表格），不依赖 pandoc。

---

## 核心原则

1. **阶段零必须检测产物**——缺失则提示用户先执行 create-spec，不内联生成
2. **阶段一必须交互**——技术决策不得自行判断
3. **写完一章立即保存**——不攒到后面
4. **确认时只展示标题和要点**——全文用户按需查看
5. **模板不增删**——结构已验证
6. **Markdown 为主**——Word 仅供评审

## 常见误区与反驳

> 通用误区见 `AGENT.md`。

| 说辞 | 真相 |
|------|------|
| "用户没时间确认，我先做着" | 代用户做技术决策 = 方向跑偏概率极高 |
| "Mermaid 图太麻烦，跳过也行" | 架构图是最能传达设计意图的部分。跳过图 = 读者只能猜 |
| "create-spec 产物不全，我凭感觉设计吧" | 没有产物就跳方案 = 方向跑偏。提示用户先执行 create-spec |

## 警示信号

| 阶段 | 警示信号 |
|------|----------|
| 阶段零 | 未读 `status.json` 就跳过上下文检测；未检测产物就直接生成方案；产物缺失不提示先执行 create-spec |
| 阶段一/二 | 多章一次性生成；章节写完未保存；随意增删模板章节 |
| 通用 | 方案文档缺少模块设计的七个子章节 |

## 验证

开始前确认：
- [ ] 已读取 `status.json`，了解 `designReviewState` 状态
- [ ] feature已创建
- [ ] 已有产物（proposal + spec + design），否则提示用户先执行 create-spec
- [ ] 技术选型已逐项确认并记录
- [ ] 方案文档已生成且包含完整章节
- [ ] 详细设计已生成且包含核心类/接口设计
- [ ] 用户已确认方案和设计内容

## 下一步

设计评审完成后，用 `edanspec-task-plan` 拆分任务。

## 与 create-spec 的关系

本 skill 可被用户直接执行，也可由 `edanspec-create-spec` 引导调用（大功能/架构变更时）。两者产出不同重量的文档，互为补充而非替代。

**握手机制**：create-spec 通过 `status.json` 中的 `designReviewState` 记录状态（`"none"` / `"recommended"` / `"skipped"`）。design-review 启动时读取该字段，了解自身是被推荐调用的还是用户主动回来的。无论哪种来源，只要产物齐全就正常执行。

## 辅助资源（按需加载，不要一次全读）

- `templates/design-review-template.md` — 方案模板，阶段一读
- `templates/detail-design-template.md` — 详细模板，阶段二读
- `references/mermaid-to-image-guide.md` — Mermaid 转图，阶段三读
- `{{SCRIPTS}}/generate_mermaid_images.py` — Mermaid 转 PNG 脚本，阶段三用
- `{{SCRIPTS}}/generate_docx.py` — Markdown 转 Word 备选脚本，阶段三用（pandoc 未安装时）
