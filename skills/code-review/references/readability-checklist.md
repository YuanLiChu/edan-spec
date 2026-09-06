# 可读性检查清单

用于代码审查中的可读性维度检查。代码是写给人看的，其次才是机器。默认栈：C++ / Qt。

## 核心检查项

### 1. 命名清晰

| 检查项 | 说明 |
|--------|------|
| **无缩写** | 除非是团队通用（ID、URL、UI、Qt 类型本身） |
| **无模糊名称** | 避免 `data`、`info`、`temp`、`flag`、`ptr` |
| **动词 + 名词** | 函数 `startAcquisition()`，布尔 `isConnected()` |
| **一致性** | 同一概念全项目同一词（`sampleRate` 不要有的地方叫 `fs`） |
| **Qt 前缀** | 成员 `m_`，与 `rules/qt` 一致 |

```cpp
// 错误
QVariant proc(const QList<QVariantMap>& d)
{
    QVariant r;
    for (const auto& i : d) {
        if (i.value("a").toBool()) {
            r = i;
        }
    }
    return r;
}

// 正确
std::optional<User> findFirstActiveUser(const std::vector<User>& users)
{
    const auto it = std::find_if(users.begin(), users.end(),
                                 [](const User& u) { return u.isActive; });
    if (it == users.end()) {
        return std::nullopt;
    }
    return *it;
}
```

### 2. 控制流简洁

- [ ] 无深层嵌套（≤ 3 层）
- [ ] early return / 守卫减少嵌套
- [ ] 复杂条件提取为谓词函数
- [ ] 长 `switch` 考虑表驱动或策略

```cpp
// 错误
Result processOrder(const Order& order)
{
    if (order.isValid) {
        if (order.isPaid) {
            if (order.hasStock) {
                return ship(order);
            }
        }
    }
    return Result::failed();
}

// 正确
Result processOrder(const Order& order)
{
    if (!order.isValid) {
        return Result::failed();
    }
    if (!order.isPaid) {
        return Result::failed(QStringLiteral("Order not paid"));
    }
    if (!order.hasStock) {
        return Result::failed(QStringLiteral("Out of stock"));
    }
    return ship(order);
}
```

### 3. 函数大小

| 指标 | 阈值 |
|------|------|
| **行数** | < 50 行（理想 < 30 行） |
| **参数** | ≤ 4 个（超过用参数对象） |
| **职责** | 1 个 |

### 4. 注释恰当

- [ ] 注释解释 **为什么**
- [ ] 无废话注释
- [ ] 公开头文件有 Doxygen/`///`
- [ ] 线程与所有权写在声明处
- [ ] 不在注释里放密钥、内网主机、真实姓名

```cpp
// 错误
user.name = name; // 设置用户名称

// 正确
// 设备时钟可能无 RTC，序号用上电单调计数，避免墙钟回拨导致文件覆盖
const quint64 sequence = m_monotonicSeq.fetch_add(1);
```

### 5. 表达式简洁

- [ ] 用标准库与 Qt 已有算法，不手写已有的 `std::find_if`
- [ ] 无死代码、注释掉的大段
- [ ] 链式调用可读（中间变量优于 8 段 `.`）
- [ ] 避免宏函数

### 6. 格式一致

- [ ] clang-format 通过
- [ ] include 分组
- [ ] 类成员顺序稳定：类型/常量 → 构造析构 → 公开接口 → 信号 → 槽 → 私有

## C++ / Qt 特定

- [ ] 遵循 `rules/cpp` 与 `rules/qt` 命名
- [ ] `const` 打在该打的地方
- [ ] `override` 显式
- [ ] 信号槽新语法
- [ ] QML id 与文件名能对上模块职责
- [ ] 不在头文件 `using namespace`

```cpp
// 错误
void process(const QByteArray* data)
{
    if (data != nullptr) {
        parse(*data);
    }
}

// 正确：前置失败
void process(const QByteArray* data)
{
    if (data == nullptr) {
        return;
    }
    parse(*data);
}
```

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **聪明代码** | 难懂 | 直白写法 |
| **缩写癖** | `AcqMgr` | 完整拼写 |
| **注释重复代码** | 噪声 | 删或写意图 |
| **过长链式** | 调试难 | 中间变量 |
| **魔法字符串** | `"USR"` | `enum class` |

## 审查技巧

1. 大声朗读函数名
2. 新成员能否在不读 cpp 的情况下用头文件
3. 6 个月后能否改协议而不怕

## 警示信号

- 需要超过 2 句话解释函数在做什么
- 函数名和实现不一致
- 未使用的 include、成员
- 缩进超过 4 层
- 单行超过 120 字符
