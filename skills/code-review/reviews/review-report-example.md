# 代码审查报告示例

这是一个填充完整的审查报告示例，展示正确的格式和写法。

---

| 字段 | 值 |
|------|-----|
| **审查范围** | PointCalculator.cpp (L1-L76) |
| **变更类型** | 新功能 |
| **变更规模** | +76 行 -0 行，共 76 行 |
| **结论** | REQUEST_CHANGES |
| **审查完整性** | COMPLETE |

## 审查阶段

| 阶段 | 状态 | 文件范围/备注 |
|------|------|---------------|
| 通用四维审查 `genericReview` | complete | PointCalculator.cpp |
| 专项 `specialists.qt-cpp` | not-applicable | 无 Qt 头文件 / Q_OBJECT |

---

## 问题摘要

| 级别 | 数量 | 说明 |
|------|------|------|
| CRITICAL | 2 | 必须修复才能合并 |
| IMPORTANT | 5 | 应该修复再合并 |
| SUGGESTION | 3 | 可以考虑 |

---

## CRITICAL Issues（必须修复）

> 共 2 个。此类问题不修复，审查不通过。

```
#: 1
位置：PointCalculator.cpp:52
维度：正确性
问题描述：`m_userRepository->findById(userId)->name` 在用户不存在时解引用空指针
违反检查项：边界条件 - 空值处理
修复建议：先判空，或 `findById` 返回 `std::optional<User>` 后 `value_or` / 抛 `UserNotFoundError`
────────────────────────────────────────
```

```
#: 2
位置：PointCalculator.cpp:24
维度：正确性
问题描述：订单金额未处理负数场景（退款订单），导致退款也能获得积分
违反检查项：边界条件 - 负值处理
修复建议：添加 `isRefund()` 检查 `amount < 0`，过滤退款订单
────────────────────────────────────────
```

---

## IMPORTANT Issues（应该修复）

> 共 7 个。此类问题建议修复后再合并。

```
#: 1
位置：PointCalculator.cpp:23
维度：正确性
问题描述：魔法字符串 `"COMPLETED"` 直接硬编码在条件判断中
违反检查项：输入验证 - 使用白名单
修复建议：提取为 `enum class OrderStatus { Completed, Pending, Cancelled }`
────────────────────────────────────────
```

```
#: 2
位置：PointCalculator.cpp:30
维度：正确性
问题描述：魔法字符串 `"GOLD"` 和 `"SILVER"` 直接硬编码
违反检查项：输入验证 - 使用白名单
修复建议：提取为 `enum class MembershipLevel` 并关联倍数
────────────────────────────────────────
```

```
#: 3
位置：PointCalculator.cpp:38
维度：正确性
问题描述：魔法字符串 `"PROMOTION"` 直接硬编码
违反检查项：输入验证 - 使用白名单
修复建议：提取为 `enum class EventType`
────────────────────────────────────────
```

```
#: 4
位置：PointCalculator.cpp:18
维度：架构
问题描述：直接调用 `UserRepository::instance()` 单例，无法单元测试
违反检查项：可测试性 - 依赖可注入
修复建议：定义 `UserRepository` 接口，通过构造函数注入
────────────────────────────────────────
```

```
#: 5
位置：PointCalculator.cpp:18
维度：架构
问题描述：`calculatePoints` 混合了数据获取和积分计算逻辑，违反单一职责
违反检查项：分层清晰 - 无跨层调用
修复建议：拆分为 `calculateOrderPoints()`、`applyMultiplier()` 等私有方法
────────────────────────────────────────
```

```
#: 6
位置：UserService.cpp:20-24
维度：性能
问题描述：N+1 查询，对每个用户调用 findProfile
违反检查项：数据库性能 - 避免 N+1 查询
修复建议：添加批量查询 `findProfiles(const QStringList& userIds)`
────────────────────────────────────────
```

```
#: 7
位置：UserService.cpp:68-77
维度：性能
问题描述：O(n²) 时间复杂度，嵌套循环查找重复邮箱
违反检查项：时间复杂度 - 查找操作使用合适的数据结构
修复建议：使用 `QSet<QString>` 或 `std::unordered_set` 优化到 O(n)
────────────────────────────────────────
```

---

## SUGGESTION（可选改进）

> 共 3 个。此类问题可合并后处理。

```
#: 1
位置：PointCalculator.cpp:19
维度：可读性
问题描述：变量名 `points` 不够清晰，无法区分是基础积分还是总积分
建议：使用 `orderPoints`、`bonusPoints`、`totalPoints` 等具体命名
────────────────────────────────────────
```

---

## 待人工确认

> 共 0 个。专项 investigation target 放在此处，不升级为 CRITICAL。

---

## 做得好的地方

> 至少列出 1 项，如无则写"无明显亮点"。

- 使用值类型结构体定义 `Order` 和 `Event`，边界清晰
- 函数命名清晰，`calculatePoints`、`userName` 意图明确

---

## 验证记录

| 检查项 | 状态 | 备注 |
|--------|------|------|
| 测试覆盖 | ❌ | 未发现新增测试文件 |
| 构建通过 | ✅ | 本地 `cmake --build` 成功，无编译错误 |
| 安全检查 | ⚠️ | 涉及用户积分计算，建议执行 `edanspec:security-review` |

---

## 审查说明

- 本次审查基于 `PointCalculator.cpp` 单文件，未审查调用方代码
- 假设订单金额始终为正数，如有退款场景需额外处理
- 建议后续重构时按构造注入 + `enum class` 拆分状态
