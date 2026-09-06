# 并行执行

主 Agent 作为协调者，为并行组中每个任务创建 worktree 并 spawn SubAgent。

## 适用条件

并行执行必须全部满足以下前置条件：
- 并行任务的**前置依赖任务已全部完成**（checkbox 全 `[x]`）
- 项目已有**基础骨架**（初始化/构建配置已完成，worktree 中可正常编译）
- 两者的文件修改无交集

任一不满足 → 走串行路径，并向用户说明原因。

## 执行流程

```
主 Agent 向用户报告并行组并确认
    ↓
为每个任务创建独立 worktree（基于当前主分支）
    ↓
主 Agent 并行 spawn SubAgent（isolation: "worktree"）
    ├── 每个 Agent 独立执行 TDD 循环 + 提交（不合并）
    └── 等待所有 Agent 完成
    ↓
主分支依次 cherry-pick 各 worktree commit
    ↓
统一验证：全量测试 + 构建 + Lint + 覆盖率
```

任何一项失败 → 定位哪个 SubAgent 引入的问题，回退对应 commit 后修复。

## SubAgent prompt 模板

```
任务：实现 {task-id} — {task-title}

验收标准：
- {标准1}
- {标准2}

涉及文件：
- 新增：{文件列表}
- 修改：{文件列表}

编码规范：
{对应语言的 rules/ 规范内容}

要求：
1. 按 TDD 循环执行：先写失败测试 → 最小实现 → 重构
2. 每个增量验证：测试通过 + 构建成功 + clang-format/clang-tidy/clazy 通过
3. 任务完成后必须运行覆盖率工具检测（不得推算），标准：行覆盖≥80%、分支≥70%、主要路径100%
4. 完成后提交 commit，不要合并
5. 遇到问题调 edanspec:debugging 排障
```

## 验证

- [ ] 并行条件已全部确认满足
- [ ] 已向用户报告并行组并获得确认
- [ ] 每个 SubAgent 独立 worktree 已创建
- [ ] 所有 SubAgent 已完成提交
- [ ] 主分支 cherry-pick 成功
- [ ] 统一验证通过（全量测试 + 构建 + Lint + 覆盖率）
