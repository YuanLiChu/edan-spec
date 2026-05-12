# Web 后端项目技术参考

> 供design-review 的阶段一决策确认时参考。

---

## 一、架构模式

### 架构对比

| 架构 | 开发效率 | 运维复杂度 | 适用规模 |
|-----|---------|-----------|---------|
| **单体应用** | 高 | 低 | 小型（< 10 人，< 1 年） |
| **模块化单体** | 中 | 中 | 中型（10-30 人，1-2 年） |
| **微服务** | 低 | 高 | 大型（> 30 人，> 2 年） |
| **事件驱动** | 中 | 高 | 高并发、异步解耦场景 |

**单体应用** — 所有功能部署在同一进程。开发部署简单，但模块耦合度高，难以独立扩展。

**模块化单体** — 按业务域划分模块，同一进程部署。模块边界清晰，兼顾开发效率与可维护性。

**微服务** — 按业务域拆分为独立服务，独立部署扩展。服务间通过网络通信。运维复杂度高，需配套服务治理。

**事件驱动** — 服务间通过消息队列异步通信。天然解耦、高吞吐，但调试和排查链路复杂。

### 选型建议

| 项目规模 | 推荐架构 |
|---------|---------|
| 小型（< 10 人，< 1 年） | 单体应用 |
| 中型（10-30 人，1-2 年） | 模块化单体 |
| 大型（> 30 人，> 2 年） | 微服务架构 |
| 高并发 / 异步解耦 | 事件驱动架构 |

---

## 二、技术栈

### 技术选型

| 决策项 | 选项 | 推荐 | 说明 |
|--------|------|------|------|
| 后端框架 | Spring Boot、Node.js + Express、Django、Go + Gin | **Spring Boot**（Java）、**Django**（Python）、**Go + Gin**（高性能） | 企业级用 Spring Boot，快速原型用 Django |
| ORM | MyBatis、JPA/Hibernate、Sequelize、GORM | **MyBatis**（灵活）、**JPA**（简单） | 复杂 SQL 用 MyBatis，CRUD 用 JPA |
| 数据库 | MySQL、PostgreSQL、MongoDB | **MySQL**（主流）、**PostgreSQL**（高级特性） | 关系型用 MySQL/PG，文档型用 MongoDB |
| 缓存 | Redis、Memcached | **Redis** | 数据结构丰富、持久化支持 |
| 消息队列 | RabbitMQ、Kafka、RocketMQ | **RabbitMQ**（轻量）、**Kafka**（大数据） | 简单队列用 RabbitMQ，高吞吐用 Kafka |
| API 协议 | RESTful、GraphQL、gRPC | **RESTful** | 主流方案，生态完善 |
| 部署 | Docker、Kubernetes | **Docker**（容器化）、**K8s**（大规模编排） | |

### 推荐组合

| 项目规模 | 技术栈 |
|---------|--------|
| 小型 | Spring Boot + JPA + MySQL |
| 中型 | Spring Boot + MyBatis + MySQL + Redis |
| 大型 | Spring Cloud 微服务 + Kafka + K8s |
