# 变更工作流

## 触发条件

用户表达了以下意图时进入变更流程：

- "不对，XX 应该改成..."
- "再加一个 XX"
- "XX 不要了"
- "换个方案，不用 A 用 B"
- "这个需求要调整"

## 变更算法

```
用户提出变更
  ↓
重新读取 proposal.md、specs/、design.md，理解当前方案全貌
  ↓
根据变更意图，从头生成所有产物（不是局部修改，而是完整重写）
  1. 重新生成 proposal.md（更新 Capabilities 章节，标注新增/修改的能力）
  2. 重新生成所有 spec 文件（用分区格式表达新增/修改/删除/重命名）
  3. 重新生成 design.md（与新的 specs 一致）
  ↓
展示变更摘要，用户确认
```

**为什么要全量重写而非局部追加？** 局部追加容易导致文件膨胀、各文件之间逻辑不一致。完整重写确保 proposal → specs → design 三者自洽，差异由 git 历史追溯。

**Spec 分区格式示例**：

```markdown
# Auth 规格

## ADDED Requirements

### Requirement: 手机号验证码登录
支持手机号 + 短信验证码登录。

#### Scenario: 发送验证码
- **WHEN** 输入合法手机号并点击发送验证码
- **THEN** 短信在 60 秒内送达

## MODIFIED Requirements

### Requirement: 用户登录
#### Scenario: 验证码登录
- **WHEN** 输入手机号和有效验证码
- **THEN** 返回用户信息和认证令牌

## REMOVED Requirements

### Requirement: 邮箱验证
```

**关键规则**：
- 变更流程中的 spec 使用**分区格式**（`## ADDED Requirements` 等），而非行内标签
- `## MODIFIED Requirements` 只写变更部分——列出要添加/修改的场景，未提及的场景自动保留
- **生成顺序**：proposal（why）→ specs（what）→ design（how），每一步都以最新的前置产物为上下文
- **展示变更摘要**——让用户确认改了什么
- **若涉及架构层面变更且 designReviewState 为 "none"**——将其更新为 "recommended"
