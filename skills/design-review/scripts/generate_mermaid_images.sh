#!/bin/bash
# Mermaid 图表转 PNG/SVG 图片脚本

set -e

echo "=== Mermaid 图表转图片脚本 ==="

# 检查是否安装了 mermaid-cli
if ! command -v mmdc &> /dev/null; then
    echo "⚠️  未安装 mermaid-cli，正在安装..."
    echo "安装命令: npm install -g @mermaid-js/mermaid-cli"
    npm install -g @mermaid-js/mermaid-cli
fi

echo "✅ mermaid-cli 已安装"
echo ""

# 参数设置
INPUT_FILE="${1:-solution-design-draft.md}"
OUTPUT_DIR="${2:-mermaid-images}"
IMAGE_FORMAT="${3:-png}"  # png 或 svg

echo "输入文件: $INPUT_FILE"
echo "输出目录: $OUTPUT_DIR"
echo "图片格式: $IMAGE_FORMAT"
echo ""

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 提取 mermaid 代码块并转换为图片
echo "正在提取 mermaid 代码块..."

# Python 脚本提取 mermaid 代码块
python3 << 'PYEOF'
import re
import os
import subprocess

input_file = os.environ.get('INPUT_FILE', 'solution-design-draft.md')
output_dir = os.environ.get('OUTPUT_DIR', 'mermaid-images')
image_format = os.environ.get('IMAGE_FORMAT', 'png')

# 读取 Markdown 文件
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有 mermaid 代码块
pattern = r'```mermaid\n(.*?)\n```'
blocks = re.findall(pattern, content, re.DOTALL)

print(f"找到 {len(blocks)} 个 mermaid 代码块")

# 转换每个代码块为图片
for i, block in enumerate(blocks, 1):
    # 创建临时 mermaid 文件
    temp_file = f"/tmp/mermaid-block-{i}.mmd"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(block)

    # 定义输出图片文件名
    output_file = f"{output_dir}/diagram-{i}.{image_format}"

    # 使用 mmdc 转换
    print(f"转换代码块 {i} -> {output_file}")

    cmd = [
        'mmdc',
        '-i', temp_file,
        '-o', output_file,
        '-b', 'white',  # 白色背景
        '-w', '1200',   # 宽度 1200px
        '-H', '800',    # 高度 800px（自动调整）
        '--scale', '2'  # 2倍缩放（高清）
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ 转换失败: {result.stderr}")
    else:
        print(f"✅ 转换成功: {output_file}")

    # 删除临时文件
    os.remove(temp_file)

print("")
print(f"✅ 完成！所有图片已保存到 {output_dir}/ 目录")

PYEOF

export INPUT_FILE OUTPUT_DIR IMAGE_FORMAT

echo ""
echo "=== 转换完成 ==="
echo "图片目录: $OUTPUT_DIR"
echo ""

# 显示生成的图片列表
ls -lh "$OUTPUT_DIR"/*.png 2>/dev/null || ls -lh "$OUTPUT_DIR"/*.svg 2>/dev/null || echo "未生成图片"

echo ""
echo "=== 使用建议 ==="
echo "1. 图片已生成，可在 Word 文档中插入"
echo "2. 图片尺寸：1200px 宽，自动高度"
echo "3. 图片质量：2倍缩放（高清）"
echo "4. 图片背景：白色（适合打印）"