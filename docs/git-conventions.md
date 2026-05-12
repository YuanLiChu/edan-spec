# Git 规范

## 核心原则

### 1. 原子提交
每个提交做一件完整的事，可独立回滚。按功能点拆分，不要把多个不相关的改动塞在一个提交里。

### 2. Trunk-Based 开发
默认在 main 分支工作，不长寿命特性分支。超过 3 个增量的任务才用短分支，合并后立即删除分支。

### 3. 提交前验证
- 构建通过、测试全绿
- 不夹带无关变更
- 敏感文件、密钥在 .gitignore 中，不入库
- 推荐配置 pre-commit hook 自动格式化、检查敏感信息

### 4. 提交消息格式

遵循 Conventional Commits 规范：

```
<type>(<scope>): <description>

- [变更要点]

[footer]

Co-Authored-By: Claude
```

**Type 类型**：`feat` | `fix` | `refactor` | `test` | `docs` | `chore` | `style` | `perf`

**Scope（可选）**：变更影响的模块或功能，如 `user`、`auth`、`api`

**Breaking Change**：在 type 后加 `!`，如 `feat(api)!: 移除旧版认证接口`

**Footer**：`BREAKING CHANGE: ...` / `Closes #123` / `Fixes #456`

> `Co-Authored-By: Claude` 是 Git 标准的协作署名 metadata，AI 协作生成的提交必须包含此行。

## 分支管理

### 分支命名

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 新功能 | `feat/<简短描述>` | `feat/user-login` |
| 修复 | `fix/<简短描述>` | `fix/auth-token-expiry` |
| 紧急修复 | `hotfix/<简短描述>` | `hotfix/db-connection-leak` |

### 分支保护

- main 分支禁止 force push 和直接 push
- 所有合入 main 的变更必须通过 PR + 至少一人 review approve
- PR 合并后自动删除源分支

### Rebase 优先

- 合并前 `git rebase main` 保持线性历史，避免无意义的 merge commit
- 多人协作的共享分支用 `git merge`，避免 rebase 已推送的提交
- 交互式 rebase (`-i`) 用于合并琐碎提交、整理历史

## 常用操作

### 常规提交流程
1. `git status` 查看变更
2. `git add` 指定文件（禁止 `-A`）
3. `git diff --staged` 确认暂存内容
4. `git commit -m "消息"`
5. `git status` 确认工作区干净

### 合并冲突处理
1. 理解双方意图
2. 保留两边有效改动
3. 解决冲突后跑测试
4. `git add` + `git commit` 完成合并

### 回滚
- 安全回滚：`git revert <commit>`（保留历史）
- 危险回滚：`git reset --hard`（丢失历史，仅限本地未推送）
- 部分回退：`git checkout <commit> -- <文件>`（恢复单文件）

## Pull Request 规范

- PR 标题使用 Conventional Commits 格式
- 描述包含：变更目的、影响范围、测试方式、截图（UI 变更）
- 大 PR 拆分为多个小 PR，每个 PR 聚焦一个变更点
- 标记 `Draft` 状态表示未完成但想提前获取反馈

## Feature Flag

未完成功能需合并到 main 时使用：

- 前缀：`ENABLE_`
- 默认关闭
- 生命周期：创建 → 开发 → 验证 → 清理（3 个提交内）
- 禁止：长寿命 flag、嵌套超 2 层、核心业务逻辑放在 flag 分支内

## 数据库迁移

- 命名格式：`<timestamp>_<描述>.sql`，如 `20260508_add_user_avatar.sql`
- 每个 forward 脚本必须有对应的 `.down.sql` 反向脚本
- 迁移脚本不可修改，只能新增
- 禁止破坏性变更直接执行（删列、改类型），需分多步：新增 → 双写 → 迁移数据 → 删除旧字段
