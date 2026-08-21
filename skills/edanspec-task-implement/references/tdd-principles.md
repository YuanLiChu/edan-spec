# TDD 原则

## 核心循环

```
RED（编写失败测试）→ GREEN（最小实现）→ REFACTOR（重构优化）→ 重复
```

### RED — 编写失败测试

测试必须先编写且先失败，否则无法证明实现正确。

```typescript
// TypeScript - 验证用户登录逻辑
it('authenticates user with valid email and password', async () => {
  const user = await authService.login({
    email: 'test@example.com',
    password: 'SecurePass123!',
  });
  expect(user.id).toBe('usr_001');
  expect(user.token).toBeDefined();
});
```

```python
# Python - 验证密码哈希
def test_password_is_hashed():
    hashed = hash_password('SecurePass123!')
    assert hashed != 'SecurePass123!'
    assert verify_password('SecurePass123!', hashed)
```

### GREEN — 最小实现

编写刚好满足测试通过的代码，不做过度设计。

```typescript
export async function createTask(input: { title: string }) {
  return { id: generateId(), title: input.title, status: 'pending' };
}
```

### REFACTOR — 重构优化

测试通过后再优化命名、消除重复、提取公共逻辑。每步重构后重新执行测试。

---

## Bug 修复 — 先复现再修复

```
编写复现测试 → 确认失败 → 实现修复 → 确认通过 → 全量回归
```

```typescript
// Bug：完成任务时 completedAt 字段未更新

// 1. 复现测试（应失败）
it('sets completedAt when task is completed', async () => {
  const task = await taskService.createTask({ title: 'Update docs' });
  const done = await taskService.completeTask(task.id);
  expect(done.completedAt).toBeInstanceOf(Date);  // 失败 → Bug 确认
});

// 2. 修复 → 测试通过 → Bug 修复完成，回归测试提供保护
```

---

## 测试金字塔

```
        ╱╲       E2E 测试（~5%）— 关键用户流程
       ╱──╲      集成测试（~15%）— API 边界、组件交互
      ╱────╲     单元测试（~80%）— 纯逻辑、毫秒级
     ╱──────╲
```

### 测试规模

| 规模 | 约束 | 示例 |
|------|------|------|
| 小规模 | 单进程、无 I/O、无网络 | 纯函数、数据转换、算法逻辑 |
| 中规模 | 仅 localhost、无外部服务 | API 测试 + 测试数据库、组件 |
| 大规模 | 允许外部服务 | E2E、性能基准、第三方集成 |

### 决策路径

```
纯逻辑、无副作用？            → 单元测试（小规模）
跨越系统边界（API/DB/文件）？  → 集成测试（中规模）
关键用户流程？                 → E2E 测试（大规模）— 仅限关键路径
```

---

## 编写原则

**验证行为结果，不验证内部调用**：断言最终状态，不验证中间过程。

```typescript
// 推荐：验证查询结果
expect(tasks[0].createdAt).toBeGreaterThan(tasks[1].createdAt);

// 不推荐：验证内部调用
expect(db.query).toHaveBeenCalledWith(expect.stringContaining('ORDER BY'));
```

**DAMP 优于 DRY**：测试代码中可读性优先于复用，每个测试用例自包含。

```python
# Python - 每个测试独立可读，不依赖共享 fixture
def test_rejects_empty_username():
    with pytest.raises(ValueError, match="username is required"):
        create_user(username="", email="a@b.com")

def test_rejects_invalid_email():
    with pytest.raises(ValueError, match="invalid email"):
        create_user(username="test", email="not-an-email")
```

**Arrange-Act-Assert 三段式**：准备测试数据 → 执行被测操作 → 断言预期结果。

```go
// Go - 三段式结构
func TestCalculateDiscount(t *testing.T) {
    // Arrange
    order := Order{Amount: 100, Tier: "gold"}

    // Act
    result := CalculateDiscount(order)

    // Assert
    if result != 15 {
        t.Errorf("expected 15%% discount for gold tier, got %d", result)
    }
}
```

**单一职责**：每个测试用例只验证一个行为。

**描述性命名**：测试名称应清晰描述被测行为和预期结果。

```
推荐：'returns 401 when auth token is expired'
推荐：'rejects order with negative quantity'
不推荐：'test auth'
不推荐：'handles errors'
```

---

## 覆盖场景

每个公共方法或函数至少覆盖以下三类场景：

| 场景 | 说明 | 示例 |
|------|------|------|
| **正常路径** | 输入合法，预期正常返回 | 正确用户名密码登录成功 |
| **边界值** | 空值、零值、最大/最小值、空集合 | 分页参数为 0 或 Integer.MAX_VALUE |
| **异常路径** | 输入非法，返回明确错误 | 负数金额、不存在的 ID |

覆盖率不达标时，优先按这三类场景补测试，不得为凑数字编写无意义测试。

---

## Mock 使用原则

```
优先级（高 → 低）：
1. 真实实现 → 最高置信度
2. Fake     → 内存版依赖替代
3. Stub     → 返回固定数据
4. Mock     → 验证方法调用，慎用
```

**仅在以下情况使用 Mock**：真实依赖执行过慢、结果具有不确定性、或存在不可控副作用（外部 API 调用、邮件发送、支付网关等）。

---

## 常见反模式

| 反模式 | 后果 | 修正 |
|--------|------|------|
| 测试内部实现细节 | 重构导致测试失败，即使行为正确 | 仅验证输入输出 |
| 非确定性测试 | 间歇性失败，失去信任 | 使用确定性断言，隔离测试状态 |
| 测试第三方代码 | 浪费资源验证不受控的行为 | 只测试自己的业务逻辑 |
| 快照滥用 | 大型快照无人审查，任何改动都触发失败 | 谨慎使用，变更必须审查 |
| 测试用例不隔离 | 单独通过、合并失败 | 每个测试独立搭建和清理环境 |
| 过度 Mock | 测试通过、生产环境崩溃 | 优先使用真实实现 |

---

## 需要警惕

- 实现了功能却没有对应测试
- 测试首次运行即通过（可能覆盖不足）
- Bug 修复缺少复现测试
- 测试名称无法表达验证意图
- 为维持测试全绿而跳过失败用例
