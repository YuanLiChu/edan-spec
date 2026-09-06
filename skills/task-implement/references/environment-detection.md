# 项目环境检测

实现前自动确认项目的测试、构建、Lint 工具链。本 skill 面向 **C++ / Qt + CMake**。

## 检测顺序

按以下优先级依次查找，命中即停止：

1. **CMakeLists.txt**（含 `find_package(Qt6` 或 `find_package(Qt5`）→ Qt + CMake 项目
2. **CMakeLists.txt**（无 Qt）→ 纯 C++ CMake 项目
3. **\*.pro / \*.pro.user** → 遗留 qmake 工程（新功能不得以 qmake 为默认；检测后询问是否仍维护）
4. **meson.build** → Meson 项目
5. **Makefile** 且存在 `*.cpp` → 手写 Make 的 C++ 项目
6. 以上皆无 → 询问用户工具链，并建议补 CMake

同时检测：

- `CMakePresets.json` / `CMakeUserPresets.json`
- `conanfile.txt` / `conanfile.py` / `vcpkg.json`
- `.clang-format` / `.clang-tidy`
- `tests/`、`gtest`、`Qt6::Test`

## 常见项目速查

| 项目类型 | 测试 | 构建 | Lint / 静态分析 |
|----------|------|------|----------------|
| Qt 6 + CMake | `ctest --output-on-failure` | `cmake --build --preset <name>` 或 `cmake --build build` | `clang-tidy`、`clazy` |
| 纯 C++ CMake | `ctest --output-on-failure` | 同上 | `clang-tidy`、`cppcheck` |
| qmake 存量 | `make check` / 手动测例 | `qmake && make` | clazy（若套件提供） |

### 项目类型识别指引

**Qt + CMake：**

| 标志 | 含义 |
|------|------|
| `find_package(Qt6 REQUIRED COMPONENTS ...)` | Qt 6 |
| `qt_add_executable` / `qt_add_qml_module` | 现代 Qt CMake |
| `CMAKE_AUTOMOC ON` | moc 已接入 |
| 存在 `*.qml` | Qt Quick |
| 存在 `QWidget`/`QMainWindow` | Widgets |

常用命令：

```bash
cmake --preset default                  # 或 cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j
ctest --test-dir build --output-on-failure
ctest --test-dir build -R EmailValidator --output-on-failure
cmake --build build --target clang-tidy   # 若项目提供
clazy-standalone                          # Qt 代码
```

Windows（Ninja + Qt MSVC）：

```bat
cmake --preset windows-msvc
cmake --build --preset windows-msvc
ctest --preset windows-msvc --output-on-failure
```

**纯 C++ CMake：**

检测标志：`CMakeLists.txt` 存在且无 Qt。

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j
ctest --test-dir build --output-on-failure
```

**覆盖率构建：**

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON
cmake --build build -j
ctest --test-dir build
# GCC: lcov / gcovr；Clang: llvm-cov；MSVC: OpenCppCoverage
```

## 未识别到项目类型

上述配置文件均不存在时，询问用户：生成器（Ninja/MSVC）、Qt 路径、测试框架（GTest/QTest）。不得假设 Gradle/npm。

## 工具链验证

检测完成后执行一次验证，确认命令可用：

```bash
cmake --version
{编译器} --version
ctest --version
clang-format --version || true
```

后续所有增量的验证步骤统一使用该组命令。
