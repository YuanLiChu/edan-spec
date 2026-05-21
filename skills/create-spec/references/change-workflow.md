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
  1. 重新生成 proposal.md（根据新的意图/范围）
  2. 重新生成所有 spec 文件（新增、修改、删除后的最终状态）
  3. 重新生成 design.md（与新的 specs 一致）
  ↓
展示变更摘要，用户确认
```

**为什么要全量重写而非局部修改？** 局部追加容易导致文件膨胀、标记混乱（[ADDED]/[REMOVED]/[MODIFIED]）、以及各文件之间逻辑不一致。完整重写确保 proposal → specs → design 三者自洽，差异由 git 历史追溯。

## 变更示例

```
场景：用户说"登录功能还要支持手机号验证码"

Agent 操作：
1. 重新读取 proposal.md、auth-spec.md、design.md
2. 理解变更：在原有登录方案基础上增加手机号验证码方式
3. 重新生成 proposal.md（What Changes 中追加手机号登录）
4. 重新生成 auth-spec.md（包含密码登录 + 手机号登录，而非标记 ADDED）
5. 重新生成 design.md（技术决策中包含短信服务选型，与新的 spec 一致）
6. 展示变更摘要
```

## 关键规则

- **完整重写而非局部追加**——确保 proposal / specs / design 三者自洽，不要留下 [REMOVED] 等历史标记
- **生成顺序**：proposal（why）→ specs（what）→ design（how），每一步都以最新的前置产物为上下文
- **展示变更摘要**——让用户确认改了什么
- **若涉及架构层面变更且 designReviewState 为 "none"**——将其更新为 "recommended"
