# 正确性检查清单

用于代码审查中的正确性维度检查。正确性是最基本的要求——代码能跑不等于正确。默认栈：C++ / Qt。

## 核心检查项

### 1. 需求满足

- [ ] 功能行为与任务描述/spec 一致
- [ ] 所有验收标准已实现
- [ ] 无遗漏的边缘场景
- [ ] Bug 修复已验证（有复现测试 + 修复测试）

### 2. 边界条件

| 边界类型 | 检查项 |
|---------|--------|
| **空指针/可选** | `nullptr`、`std::optional`、`QPointer` 已处理 |
| **空容器** | 空 `vector`/`QList`/`QByteArray` |
| **零值** | 0、空 `QString` |
| **极值** | `numeric_limits`、缓冲区上限、协议最大帧长 |
| **负值** | 负数长度/索引已拒绝 |

```cpp
// 错误：空容器除零
double average(const std::vector<int>& numbers)
{
    int sum = 0;
    for (int n : numbers) {
        sum += n;
    }
    return sum / numbers.size(); // size==0 → UB
}

// 正确
std::optional<double> average(const std::vector<int>& numbers)
{
    if (numbers.empty()) {
        return std::nullopt;
    }
    const double sum = std::accumulate(numbers.begin(), numbers.end(), 0.0);
    return sum / static_cast<double>(numbers.size());
}
```

### 3. 错误处理

- [ ] 外部调用（设备、网络、文件、SQL）检查返回值或异常
- [ ] 不空 `catch`
- [ ] 错误消息可诊断，不把内部路径/密钥丢给 UI
- [ ] 资源 RAII 释放（含 `QObject` 树、`unique_ptr`）
- [ ] 失败有回滚或安全停机（设备状态机回到已知态）

```cpp
// 错误：吞掉
void loadConfig()
{
    try {
        m_store->load();
    } catch (const std::exception&) {
    }
}

// 正确
void loadConfig()
{
    try {
        m_store->load();
    } catch (const std::exception& ex) {
        qCCritical(lcConfig) << "load failed:" << ex.what();
        throw;
    }
}
```

### 4. 并发安全

- [ ] 共享可变状态有 mutex 或仅通过 queued 信号传递拷贝
- [ ] `QObject` 只在其线程亲和性内调用
- [ ] 无锁顺序死锁
- [ ] worker `quit`/`wait` 在析构前完成
- [ ] 无数据竞争（ASan/TSan/UBSan 在 CI 或本地跑过相关路径）

```cpp
// 错误
int g_count = 0;
void increment() { ++g_count; } // 数据竞争

// 正确
std::atomic<int> g_count{0};
void increment() { g_count.fetch_add(1, std::memory_order_relaxed); }
```

Qt：跨线程更新 UI 必须 queued；禁止 worker 直接 `m_label->setText`。

### 5. 状态转换

- [ ] 状态机转换完整（无死状态）
- [ ] 无效转换拒绝并打日志
- [ ] 状态变更 emit 对应信号
- [ ] 掉电/异常退出后可恢复或安全默认

### 6. 数据完整性

- [ ] 报文/文件有长度、校验和、版本
- [ ] 输出缓冲大小与协议一致
- [ ] SQL 参数绑定
- [ ] 写入使用事务或原子替换（写临时文件再 rename）

### 7. 测试正确性

- [ ] 测试验证行为
- [ ] 测试独立
- [ ] 覆盖正常 + 异常 + 边界
- [ ] Fake 合理
- [ ] 无依赖墙钟的脆弱断言（用 FakeClock）

## 语言 / 框架特定

### C++

- [ ] 无未初始化读取、无悬垂引用
- [ ] `override` 正确
- [ ] 整数转换无变窄且有意（`static_cast`）
- [ ] 析构不抛异常
- [ ] 容器失效后不使用迭代器

### Qt

- [ ] 无 `SIGNAL`/`SLOT` 宏连接新代码
- [ ] lambda connect 带 context object
- [ ] `QPointer` 用于可销毁观察
- [ ] 不在非 GUI 线程碰 `QWidget`/`QPixmap`
- [ ] setter 无变化不 emit（避免绑定环）
- [ ] `deleteLater` 与栈对象混用已排除

```cpp
// 错误：强制解引用可空 + 无 context lambda
connect(device, &Device::ready, [this] {
    m_view->show(*m_session); // session 可能已销毁
});

// 正确
connect(device, &Device::ready, this, [this] {
    if (!m_session) {
        return;
    }
    m_view->show(*m_session);
});
```

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **过早返回成功** | 未验证完成就 return true | 校验前置条件 |
| **异常当控制流** | try-catch 做分支 | 前置 if |
| **魔法数字** | 帧头写 `0xAA` 散落 | 命名常量 |
| **过度嵌套** | if 超 3 层 | early return |
| **忽略 QByteArray 大小** | 当 C 字符串用 | 带长度 API |

## 审查技巧

1. **逆向思维**：假设代码是错的，找证据
2. **边界优先**：空缓冲、短帧、超长帧
3. **追踪数据流**：从串口字节到 UI 属性
4. **问“如果”**：设备拔掉？半包？时钟回拨？

## 警示信号

- 没有处理空容器/`nullptr`
- catch 为空
- 测试只覆盖快乐路径
- 共享 `QObject` 未写线程约定
- `reinterpret_cast` 打协议结构体（对齐/端序）
