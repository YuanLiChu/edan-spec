# 性能检查清单

用于代码审查中的性能维度检查。默认栈：C++ / Qt 桌面与嵌入式 HMI。

## 核心检查项

### 1. 时间复杂度

- [ ] 循环嵌套 ≤ 2 层（O(n²) 是可接受的上限，须说明数据规模）
- [ ] 查找用合适结构（`unordered_map` / `QHash` vs 线性扫）
- [ ] 无指数递归
- [ ] 热路径无反复 `QString::fromUtf8` 无缓存

```cpp
// 错误：O(n²)
std::vector<User> findUsers(const std::vector<QString>& ids,
                            const std::vector<User>& all)
{
    std::vector<User> out;
    for (const auto& id : ids) {
        for (const auto& user : all) {
            if (user.id == id) {
                out.push_back(user);
            }
        }
    }
    return out;
}

// 正确：O(n)
std::vector<User> findUsers(const std::vector<QString>& ids,
                            const std::vector<User>& all)
{
    QHash<QString, const User*> index;
    index.reserve(all.size());
    for (const auto& user : all) {
        index.insert(user.id, &user);
    }
    std::vector<User> out;
    out.reserve(ids.size());
    for (const auto& id : ids) {
        if (const User* u = index.value(id, nullptr)) {
            out.push_back(*u);
        }
    }
    return out;
}
```

### 2. 空间复杂度

- [ ] 无无界队列（采集环形缓冲有上限与丢弃策略）
- [ ] 大文件流式读，不一次性 `readAll` 进内存
- [ ] 缓存有上限
- [ ] `QImage`/`QPixmap`/`QByteArray` 用完释放或复用

### 3. I/O 优化

- [ ] 批量写设备/数据库，避免逐条 syscall
- [ ] 文件有缓冲；关键落盘才 `fsync`
- [ ] I/O 不在 GUI 线程
- [ ] `QNetworkAccessManager` 复用

```cpp
// 错误：逐条 INSERT
void saveAll(QSqlQuery& q, const std::vector<User>& users)
{
    for (const auto& user : users) {
        q.exec(QStringLiteral("INSERT INTO users VALUES('%1')").arg(user.id));
    }
}

// 正确：事务 + 绑定
void saveAll(QSqlDatabase db, const std::vector<User>& users)
{
    db.transaction();
    QSqlQuery q(db);
    q.prepare(QStringLiteral("INSERT INTO users(id) VALUES(:id)"));
    for (const auto& user : users) {
        q.bindValue(QStringLiteral(":id"), user.id);
        q.exec();
    }
    db.commit();
}
```

### 4. 数据库 / 存储

- [ ] 查询有索引
- [ ] 避免 N+1
- [ ] 不 `SELECT *` 拉大 BLOB
- [ ] 分页或窗口

### 5. 缓存

- [ ] 热点解码帧、主题、字体有缓存
- [ ] key 无碰撞
- [ ] 有淘汰（LRU / 帧计数）

### 6. 并发与异步

- [ ] CPU 密集：`QtConcurrent` / 线程池，注意与 GUI 汇合
- [ ] I/O 密集：worker `QObject` + queued
- [ ] 线程数不超过硬件与问题规模
- [ ] 无锁竞争热点（profiling 后再优化）

## 平台特定

### Qt Widgets / Quick UI

- [ ] 主线程无 >16ms 的卡顿任务（60Hz）或产品规定的帧预算
- [ ] `paintEvent` / 场景图同步阶段不做 I/O
- [ ] 列表虚拟化（`QListView` model、`ListView`）
- [ ] 避免 `QList`/`QVector` 在绑定热路径 detach（clazy `range-loop-detach`）
- [ ] 图像 `sourceSize`、缓存、异步加载
- [ ] 不在动画里每帧 `new` 控件

### 嵌入式

- [ ] 启动时间、RSS、GPU 内存有预算
- [ ] 无 GPU 时不用过重的粒子/模糊
- [ ] 日志级别可降；debug 分类默认关

### 协议 / 采集

- [ ] 环形缓冲，满时策略明确（丢旧/丢新）
- [ ] 解析零拷贝或减少分配（`QByteArray` 切片注意生命周期）
- [ ] 定时器精度与周期匹配，避免 1ms `QTimer` 刷 UI

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **循环中 I/O** | 卡顿、超时 | 批量 / worker |
| **GUI 线程解析** | 掉帧 | 投递已解析 DTO |
| **过早优化** | 复杂度上升 | 先测再改 |
| **每帧 qDebug** | 比业务还慢 | 分类日志 + 采样 |
| **QString 拼热路径** | 分配 | `QStringBuilder` / 预分配 / `QLatin1String` |

## 性能测试

- [ ] 有基准（采集 fps、解析 ns/帧、启动 s）
- [ ] 有回归（CI 或发布前）
- [ ] 优化前有 profiler 证据（perf、VTune、Instruments、`QElapsedTimer`）

## 审查技巧

1. 数热路径上的分配与系统调用
2. 问 10 小时连续跑内存是否涨
3. 问 100 倍数据量 UI 是否仍可点

## 警示信号

- 嵌套循环里写串口
- 无界 `QList` 缓存波形
- 主线程 `QFile::readAll` 大文件
- 声称“性能没问题”但无测量
