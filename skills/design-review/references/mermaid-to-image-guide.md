# Mermaid 转图片指南

将 Markdown 中的 mermaid 图表转为 PNG/SVG 图片，用于 Word 文档、PPT 演示、打印等场景（pandoc 不渲染 mermaid 代码块）。

---

## 快速开始

### Python 脚本（推荐）

> `scripts/` 路径相对于 `skills/design-review/` 目录。

```bash
# 基本用法
python3 scripts/generate_mermaid_images.py MedSpec/feature/<name>/review/solution.md --replace

# 常用参数
--output-dir, -o   输出目录（默认: mermaid-images）
--format, -f       图片格式 png/svg（默认: png）
--width, -w        图片宽度 px（默认: 1200）
--scale, -s        缩放比例 1-3（默认: 2）
--background, -b   背景色（默认: white）
--replace, -r      将代码块替换为图片链接
```

### Bash 脚本

```bash
bash scripts/generate_mermaid_images.sh <输入文件> <输出目录> <格式>
# 例如：
bash scripts/generate_mermaid_images.sh MedSpec/feature/login-review/review/solution.md mermaid-images png
```

### 在线工具（免安装）

访问 [mermaid.live](https://mermaid.live/)，粘贴代码块，下载 PNG/SVG。

---

## 格式选择

| 格式 | 特点 | 适用场景 |
|------|------|---------|
| **PNG** | 位图、文件较大、通用兼容 | Word、PPT、打印 |
| **SVG** | 矢量、可缩放、文件小 | 网页、PDF |

**尺寸建议**：

| 场景 | 参数 |
|------|------|
| 文档 | `--width 1200 --scale 2` |
| 演示 | `--width 1600 --scale 2` |
| 高清打印 | `--width 1600 --scale 3` |

---

## 生成 Word 文档流程

```bash
# 1. 替换 mermaid 代码块为图片链接
python3 scripts/generate_mermaid_images.py MedSpec/feature/<name>/review/solution.md --replace

# 2. pandoc 转 Word
pandoc MedSpec/feature/<name>/review/solution-images.md -o MedSpec/feature/<name>/review/solution.docx
```

> 如果 pandoc 未安装，可使用备选方案 `scripts/generate_docx.py`，详见 design-review SKILL.md 阶段三。

---

## 依赖安装

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc --version  # 验证安装
```

---

## 常见问题

**未安装 mermaid-cli**：运行 `npm install -g @mermaid-js/mermaid-cli`

**语法错误**：先粘贴到 [mermaid.live](https://mermaid.live/) 验证语法

**图片模糊**：增大 `--scale`（2 → 3）或 `--width`

**背景色不匹配**：用 `--background transparent` 或自定义十六进制色值
