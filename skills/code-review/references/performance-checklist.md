# 性能检查清单

用于代码审查中的性能维度检查。

## 核心检查项

### 1. 时间复杂度

- [ ] 循环嵌套 ≤ 2 层（O(n²) 是可接受的上限）
- [ ] 查找操作使用合适的数据结构（HashMap vs 列表遍历）
- [ ] 无指数级复杂度（O(2^n) 递归）
- [ ] 大数据集上有早停机制

```kotlin
// 错误：O(n²) 查找
fun findUsers(userIds: List<String>): List<User> {
    return userIds.map { id -> allUsers.find { it.id == id } }
}

// 正确：O(n) 查找
fun findUsers(userIds: List<String>): List<User> {
    val userMap = allUsers.associateBy { it.id }
    return userIds.mapNotNull { userMap[it] }
}
```

### 2. 空间复杂度

- [ ] 无无界数据积累
- [ ] 大数据集使用流式处理
- [ ] 缓存有大小限制和淘汰策略
- [ ] 及时释放不用的引用（防内存泄漏）

### 3. I/O 优化

- [ ] 批量操作代替逐个操作
- [ ] 流/连接/资源正确关闭
- [ ] 同步 I/O 不阻塞主线程
- [ ] 文件读写有缓冲

```kotlin
// 错误：逐个 I/O，N 次查询
fun saveUsers(users: List<User>) {
    users.forEach { repository.save(it) }
}

// 正确：批量 I/O
fun saveUsers(users: List<User>) {
    repository.saveAll(users)  // 一次批量插入
}
```

### 4. 数据库性能

- [ ] 查询使用索引
- [ ] 避免 N+1 查询（用 JOIN 或批量加载）
- [ ] 只查询需要的字段（不 SELECT *）
- [ ] 大数据集分页/游标
- [ ] 慢查询有日志和告警

### 5. 缓存策略

- [ ] 热点数据有缓存
- [ ] 缓存 key 设计合理（无碰撞）
- [ ] 缓存有过期和淘汰
- [ ] 缓存穿透/雪崩有防护

### 6. 并发与异步

- [ ] CPU 密集用并行（多线程/协程）
- [ ] I/O 密集用异步（非阻塞）
- [ ] 线程池大小合理
- [ ] 无锁竞争或死锁

## 平台特定检查项

### Core Web Vitals（前端）

| 指标 | 目标 |
|------|------|
| LCP | < 2.5s |
| INP | < 200ms |
| CLS | < 0.1 |

- [ ] 图片优化（WebP/AVIF、适当尺寸、懒加载）
- [ ] JavaScript 拆分（code splitting、tree shaking）
- [ ] CSS 优化（critical CSS、移除未使用样式）
- [ ] 字体优化（font-display: swap、子集化）
- [ ] 减少主线程长任务（>50ms）
- [ ] 避免内存泄漏（事件监听器清理）

### Android

- [ ] 冷启动 < 2s
- [ ] 帧率稳定 60fps
- [ ] 内存无泄漏（MAT/LeakCanary）
- [ ] 网络请求合并/缓存
- [ ] Bitmap 正确回收
- [ ] RecyclerView 复用 ViewHolder

### iOS

- [ ] 主线程无阻塞操作
- [ ] 图片缓存使用 UIImage cache
- [ ] TableView/CollectionView 复用 cell
- [ ] 大图片 downsampling
- [ ] 无 retain cycle（weak/unowned）

### 后端 API

| 类型 | 响应时间基线 |
|------|-------------|
| 简单查询 | < 100ms |
| 复杂查询 | < 500ms |
| 批量操作 | < 1s |

- [ ] 连接池配置合理
- [ ] 超时设置正确（连接超时、读取超时）
- [ ] 限流/熔断保护
- [ ] 慢查询日志

## 常见反模式

| 反模式 | 问题 | 修复 |
|--------|------|------|
| **循环中 I/O** | 每次迭代查库/网络 | 批量加载 |
| **全表扫描** | 无条件/无条件索引 | 添加索引 |
| **过早优化** | 没测量就优化 | 先 profiling |
| **缓存一切** | 缓存无淘汰 | LRU/TTL |
| **同步阻塞** | 主线程做 I/O | 异步 |
| **过度序列化** | JSON 嵌套过深 | 扁平结构 |

## 性能测试

- [ ] 有基准测试（baseline）
- [ ] 有负载测试（峰值场景）
- [ ] 有压力测试（超出峰值）
- [ ] 性能回归有监控

## 审查技巧

1. **数据流追踪**：跟一遍数据，数 I/O 次数
2. **热点识别**：循环、递归、I/O 是三大热点
3. **规模思维**：10 条数据没事，100 万条呢？
4. **测量优先**：先 profiling，再优化

## 警示信号

- 嵌套循环（尤其Inside 循环有 I/O）
- SELECT * 或查询不需要的字段
- 无分页的大列表
- 缓存无大小限制
- 主线程/阻塞线程池做 I/O
- 没有性能测试就声称"性能不是问题"
