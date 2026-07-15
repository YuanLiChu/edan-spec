# 项目环境检测

实现前自动确认项目的测试、构建、Lint 工具链。

## 检测顺序

按以下优先级依次查找，命中即停止：

1. **build.gradle.kts / build.gradle** → Android / Kotlin / Java 项目
2. **pubspec.yaml** → Flutter 项目
3. **package.json** → 读取 `scripts.test` / `scripts.build`
4. **Makefile** → 识别 `make test` / `make build`
5. **Cargo.toml** → `cargo test` / `cargo build`
6. **go.mod** → `go test ./...` / `go build ./...`
7. **pyproject.toml / setup.py** → `pytest` / `python -m build`

## 常见项目速查

| 项目类型 | 测试 | 构建 | Lint |
|----------|------|------|------|
| Android (Gradle) | `./gradlew test` | `./gradlew assembleDebug` | `./gradlew lint` |
| Android (KMP) | `./gradlew allTests` | `./gradlew assemble` | `./gradlew lint` |
| Flutter | `flutter test` | `flutter build` | `flutter analyze` |
| 前端 (Vite) | `npx vitest` / `npm test` | `npm run build` | `npm run lint` |
| 前端 (Webpack) | `npm test` / `npx jest` | `npm run build` | `npm run lint` |
| Node.js | `npm test` / `npx vitest` | `npm run build` | `npm run lint` |
| Python | `pytest` | `python -m build` | `ruff check .` |
| Go | `go test ./...` | `go build ./...` | `golangci-lint run` |
| Rust | `cargo test` | `cargo build` | `cargo clippy` |

### 项目类型识别指引

**Android / Gradle 项目：**

检测标志：`build.gradle.kts` 或 `build.gradle` 存在。

| 模块结构 | 识别方法 |
|----------|----------|
| 单模块 | 根目录有 `build.gradle.kts` + `app/` 目录 |
| 多模块 | 根目录 + 子目录均有 `build.gradle.kts`，存在 `settings.gradle.kts` |
| KMP | `build.gradle.kts` 中包含 `kotlin("multiplatform")` 插件 |

常用命令：
```bash
./gradlew test                    # 运行所有单元测试
./gradlew test --tests "*ClassName*"  # 运行指定测试
./gradlew assembleDebug           # 构建 debug 版本
./gradlew lint                    # 运行 Lint 检查
./gradlew ktlintCheck             # Kotlin 代码风格检查（如配置了 ktlint）
```

**Flutter 项目：**

检测标志：`pubspec.yaml` 存在且包含 `flutter` 依赖。

常用命令：
```bash
flutter test                      # 运行所有测试
flutter test test/xxx_test.dart   # 运行指定测试文件
flutter build apk                 # 构建 Android APK
flutter build ios                 # 构建 iOS
flutter analyze                   # 静态分析
```

**前端（Vite / Webpack）项目：**

检测标志：`package.json` 存在。进一步区分：

| 构建工具 | 识别方法 |
|----------|----------|
| Vite | `package.json` 的 `devDependencies` 含 `vite` |
| Webpack | `package.json` 的 `devDependencies` 含 `webpack`，或存在 `webpack.config.js` |
| Next.js | `package.json` 的 `dependencies` 含 `next` |
| Nuxt | `package.json` 的 `dependencies` 含 `nuxt` |

前端项目还需检测 UI 框架（React / Vue / Svelte / Angular）：
- `package.json` 的 `dependencies` 中查找 `react`、`vue`、`svelte`、`@angular/core`
- 存在 `tsconfig.json` → TypeScript 项目

常用命令：
```bash
npm test / npx vitest / npx jest  # 运行测试
npm run build / npx vite build    # 构建
npm run lint / npx eslint .       # Lint 检查
npx tsc --noEmit                  # TypeScript 类型检查
```

## 未识别到项目类型

上述配置文件均不存在时，询问用户项目的测试和构建方式。

## 工具链验证

检测完成后执行一次验证，确认命令可用：

```bash
{检测到的测试命令} --version || true
{检测到的构建命令} --version || true
```

后续所有增量的验证步骤统一使用该组命令。
