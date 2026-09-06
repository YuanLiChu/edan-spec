# 修复策略

meddev:debugging skill 的补充参考文档，详述各类错误的修复方法和反模式。

> 测试编写模式（AAA、命名、断言、Mock）详见 `testing-patterns.md`。

## 最小改动原则

**只修必要的部分，不改动其他代码。**

```cpp
// 场景：计算总价时没有乘以数量

// 原代码
double calculateTotal(const std::vector<Item>& items)
{
    double sum = 0;
    for (const auto& item : items) {
        sum += item.price;
    }
    return sum;
}

// 错误修复：顺便改结构和空列表分支
double calculateTotal(const std::vector<Item>& items)
{
    if (items.empty()) {
        return 0.0;
    }
    return std::accumulate(items.begin(), items.end(), 0.0,
                           [](double s, const Item& i) { return s + i.price * i.quantity; });
}

// 正确修复：最小改动
double calculateTotal(const std::vector<Item>& items)
{
    double sum = 0;
    for (const auto& item : items) {
        sum += item.price * item.quantity;
    }
    return sum;
}
```

## 常见错误修复策略

### 1. 逻辑错误修复

**类型**：条件判断错误、算法错误、返回值错误

```cpp
TEST(EmailValidator, should_returnTrue_when_validate_given_validAddress)
{
    EmailValidator validator;
    EXPECT_TRUE(validator.validate("test@example.com")); // Actual: false
}

// 原代码：逻辑反转
bool EmailValidator::validate(const QString& email) const
{
    return !email.contains(QLatin1Char('@'));
}

// 修复：纠正逻辑
bool EmailValidator::validate(const QString& email) const
{
    return email.contains(QLatin1Char('@'));
}
```

### 2. 边界情况修复

**类型**：空值、零值、边界值未处理

```cpp
TEST(PriceCalculator, should_returnZero_when_calculateTotal_given_emptyList)
{
    PriceCalculator calculator;
    EXPECT_DOUBLE_EQ(calculator.calculateTotal({}), 0.0);
}

// 原代码：对空容器解引用
double PriceCalculator::calculateTotal(const std::vector<Item>& items)
{
    return items.front().price; // empty → UB / throw
}

// 修复：空容器合法
double PriceCalculator::calculateTotal(const std::vector<Item>& items)
{
    if (items.empty()) {
        return 0.0;
    }
    double sum = 0;
    for (const auto& item : items) {
        sum += item.price * item.quantity;
    }
    return sum;
}
```

### 3. 空指针 / 悬垂对象修复

**类型**：对象未初始化、parent 已销毁、跨线程持有裸指针

```cpp
TEST(UserService, should_throw_when_getUser_given_unknownId)
{
    UserService service(repository);
    EXPECT_THROW(service.getUser("123"), UserNotFoundError);
}

// 修复：不要解引用可空观察指针
User UserService::getUser(const QString& id) const
{
    const User* user = m_repository->findUserById(id);
    if (user == nullptr) {
        throw UserNotFoundError(id);
    }
    return *user;
}
```

Qt 对象树：

```cpp
// 错误：parent 销毁后仍用 raw pointer
auto* panel = new Panel(parent);
// ... later parent->deleteLater();
panel->refresh(); // 悬垂

// 正确：弱引用
QPointer<Panel> panel = new Panel(parent);
if (panel) {
    panel->refresh();
}
```

### 4. Mock / Fake 配置修复

**类型**：桩数据不正确、信号未 emit、线程亲和性不对

```cpp
TEST(UserService, should_returnAlice_when_getUser_given_id123)
{
    FakeUserRepository repo;
    repo.add(User{"123", QStringLiteral("Alice")});
    UserService service(&repo);
    EXPECT_EQ(service.getUser("123").name, QStringLiteral("Alice"));
}
```

信号槽：用 `QSignalSpy` 断言真实 emit，不要只 spy 再改测试期望。

## 常见修复反模式

### 反模式 1：过度修复

修复一个 bug 时重写了整个方法，引入新问题。

### 反模式 2：修复测试而非代码

修改测试期望值来让错误代码"通过"。

### 反模式 3：引入新问题

修复空值时用 `QEventLoop` 死等，或在槽里 `sleep`。

### 反模式 4：治标不治本

只在表面添加 null check，而不追查所有权为何为空（parent 过早 delete、错误的 `moveToThread`）。
