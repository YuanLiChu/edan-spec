# 测试模式参考

C++ / Qt 测试模式速查。逻辑用 **Google Test**，信号槽与 Qt 对象用 **QTest**。

## 目录

- [测试结构（AAA 模式）](#测试结构aaa-模式)
- [测试命名规范](#测试命名规范)
- [断言速查](#断言速查)
- [Mock 策略](#mock-策略)
- [Qt 特定模式](#qt-特定模式)
- [测试反模式](#测试反模式)

---

## 测试结构（AAA 模式）

**Arrange（准备）→ Act（执行）→ Assert（断言）**。每个测试都遵循这个三段式结构。

### Google Test

```cpp
TEST(PriceCalculator, should_sumPriceTimesQuantity_when_calculateTotal_given_twoItems)
{
    // Arrange
    const std::vector<Item> items{
        {"book", 10.0, 2},
        {"pen", 5.0, 3},
    };
    PriceCalculator calculator;

    // Act
    const double total = calculator.calculateTotal(items);

    // Assert
    EXPECT_NEAR(total, 35.0, 0.01);
}
```

### QTest

```cpp
void WaveformBufferTest::should_dropOldest_when_push_given_capacityFull()
{
    // Arrange
    WaveformBuffer buffer;
    buffer.setCapacity(2);
    buffer.push(1.0);
    buffer.push(2.0);

    // Act
    buffer.push(3.0);

    // Assert
    QCOMPARE(buffer.size(), 2);
    QCOMPARE(buffer.at(0), 2.0);
    QCOMPARE(buffer.at(1), 3.0);
}
```

---

## 测试命名规范

**格式：** `should_<预期结果>_when_<被测方法>_given_<给定场景>`

### Google Test

```cpp
TEST(UserStore, should_returnUser_when_findById_given_existingId) {}
TEST(UserStore, should_throwUserNotFound_when_findById_given_unknownId) {}
TEST(UserStore, should_handleEmpty_when_clear_given_alreadyEmpty) {}
```

### QTest 槽

```cpp
private slots:
    void should_emitStateChanged_when_start_given_idle();
    void should_notEmit_when_start_given_alreadyRunning();
```

### 测试类/文件命名

| 层级 | 命名规则 | 示例 |
|------|---------|------|
| 单元测试 | `<ClassName>Test` | `UserServiceTest.cpp` |
| Qt 测试 | `<ClassName>Test` + `QObject` | `DeviceControllerTest.cpp` |
| 集成测试 | `<ClassName>IntegrationTest` | `SqliteStoreIntegrationTest.cpp` |

---

## 断言速查

### Google Test

```cpp
EXPECT_EQ(actual, expected);
EXPECT_NE(a, b);
EXPECT_TRUE(cond);
EXPECT_FALSE(cond);
EXPECT_NEAR(a, b, 1e-6);
EXPECT_STREQ(a, b);          // C 字符串
EXPECT_THAT(vec, testing::ElementsAre(1, 2, 3));

EXPECT_THROW(expr, UserNotFoundError);
EXPECT_NO_THROW(expr);

ASSERT_NE(ptr, nullptr);     // 失败则中止本测试
```

比较 `QString`：`EXPECT_EQ(actual, QStringLiteral("Alice"))`。

### QTest

```cpp
QCOMPARE(actual, expected);
QVERIFY(condition);
QVERIFY2(condition, "why it failed");
QTRY_COMPARE(spy.count(), 1);          // 等事件循环
QFAIL("unreachable");
```

### 信号

```cpp
QSignalSpy spy(device, &DeviceClient::stateChanged);
device->connectToHost();
QTRY_COMPARE(spy.count(), 1);
QCOMPARE(spy.front().at(0).value<DeviceState>(), DeviceState::Connected);
```

---

## Mock 策略

### 何时 Mock vs 不 Mock

| Mock / Fake 这些（边界） | 不 Mock 这些（内部） |
|---|---|
| 设备端口、串口、socket | 内部计算、校验器 |
| 文件系统、数据库 | 数据转换 |
| 网络 HTTP | 纯函数 |
| 时钟 | 值类型 |

优先 **Fake**（内存实现接口），其次 Google Mock。

### 接口 + Fake

```cpp
class DevicePort {
public:
    virtual ~DevicePort() = default;
    virtual bool write(const QByteArray& frame) = 0;
};

class FakeDevicePort final : public DevicePort {
public:
    QList<QByteArray> frames;
    bool write(const QByteArray& frame) override
    {
        frames.append(frame);
        return true;
    }
};
```

### Google Mock

```cpp
class MockDevicePort : public DevicePort {
public:
    MOCK_METHOD(bool, write, (const QByteArray& frame), (override));
};

TEST(Session, should_sendHeartbeat_when_tick_given_connected)
{
    MockDevicePort port;
    EXPECT_CALL(port, write(testing::_)).Times(1);
    Session session(&port);
    session.tick();
}
```

不要 mock 值类型（`QString`、简单 struct）。

---

## Qt 特定模式

### 事件循环

```cpp
QTRY_VERIFY(server.isListening());
QTest::qWaitFor([&] { return client.isConnected(); }, 1000);
```

禁止 `QThread::sleep` 当同步。

### 无界面

```cpp
QTEST_GUILESS_MAIN(ProtocolParserTest)
```

GUI 测试：`QT_QPA_PLATFORM=offscreen`。

### 线程亲和性

单测默认单线程。涉及 `moveToThread` 时：

1. 创建 `QThread` + worker
2. 用 queued 信号与 `QSignalSpy` 等待
3. `quit()` + `wait()` 清理

### QML

C++ 测 ViewModel 属性与信号，不把 QML 当单元测试入口。UI 冒烟可单独目标，不阻塞纯逻辑覆盖率。

---

## 测试反模式

| 反模式 | 问题 | 正确做法 |
|---|---|---|
| 测试实现细节 | 重构时测试会坏 | 测试输入/输出，不测试中间步骤 |
| 固定 sleep | 闪烁、拖慢 CI | `QTRY_*` / 条件等待 |
| 共享可变状态 | 测试互相污染 | 每个测试独立 setup/teardown |
| 测试 Qt 框架本身 | 浪费时间 | 只测自己的槽与状态 |
| 永久 `QSKIP` / `DISABLED_` | 死代码 | 修复或删除 |
| 在 GUI 线程测设备 I/O | 超时、假绿 | Fake 端口 |
| Mock 一切 | 测试失去意义 | 只 Fake 外部边界 |
| 比较浮点用 `==` | 偶发失败 | `EXPECT_NEAR` |
