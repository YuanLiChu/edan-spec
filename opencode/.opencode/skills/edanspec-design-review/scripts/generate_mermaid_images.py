#!/usr/bin/env python3
"""
Mermaid 图表转 PNG/SVG 图片脚本

功能：
- 从 Markdown 文件中提取 mermaid 代码块
- 使用 mermaid-cli (mmdc) 转换为 PNG/SVG 图片
- 支持自定义图片尺寸、背景色、缩放比例
- 自动替换 Markdown 中的代码块为图片链接

使用方法：
    python3 generate_mermaid_images.py <input_file> [--output-dir <dir>] [--format <png|svg>]

示例：
    python3 generate_mermaid_images.py solution-design-draft.md
    python3 generate_mermaid_images.py solution-design-draft.md --output-dir images --format svg
"""

import re
import os
import sys
import subprocess
import argparse
from pathlib import Path


class MermaidImageGenerator:
    """Mermaid 图表转图片生成器"""

    def __init__(self, input_file, output_dir='mermaid-images', image_format='png',
                 width=1200, scale=2, background='white'):
        """
        初始化生成器

        Args:
            input_file: 输入 Markdown 文件路径
            output_dir: 输出图片目录
            image_format: 图片格式（png 或 svg）
            width: 图片宽度（像素）
            scale: 缩放比例（1-3）
            background: 背景颜色
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.image_format = image_format
        self.width = width
        self.scale = scale
        self.background = background

        # 验证输入文件
        if not self.input_file.exists():
            raise FileNotFoundError(f"输入文件不存在: {self.input_file}")

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 检查 mermaid-cli 是否安装
        self._check_mmdc_installed()

    def _check_mmdc_installed(self):
        """检查 mermaid-cli 是否安装"""
        try:
            result = subprocess.run(['mmdc', '--version'],
                                    capture_output=True, text=True)
            print(f"✅ mermaid-cli 已安装: {result.stdout.strip()}")
        except FileNotFoundError:
            print("⚠️  未安装 mermaid-cli")
            print("安装命令: npm install -g @mermaid-js/mermaid-cli")
            sys.exit(1)

    def extract_mermaid_blocks(self):
        """从 Markdown 文件提取所有 mermaid 代码块"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用正则提取 mermaid 代码块
        pattern = r'```mermaid\n(.*?)\n```'
        blocks = re.findall(pattern, content, re.DOTALL)

        print(f"找到 {len(blocks)} 个 mermaid 代码块")
        return blocks

    def convert_block_to_image(self, block, index):
        """
        将单个 mermaid 代码块转换为图片

        Args:
            block: mermaid 代码块内容
            index: 代码块索引（用于命名）

        Returns:
            图片文件路径
        """
        # 创建临时 mermaid 文件
        temp_file = Path(f"/tmp/mermaid-block-{index}.mmd")
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(block)

        # 定义输出图片文件
        output_file = self.output_dir / f"diagram-{index}.{self.image_format}"

        print(f"转换代码块 {index} -> {output_file}")

        # 构建 mmdc 命令
        cmd = [
            'mmdc',
            '-i', str(temp_file),
            '-o', str(output_file),
            '-b', self.background,  # 背景色
            '-w', str(self.width),   # 宽度
            '--scale', str(self.scale),  # 缩放比例
        ]

        # 执行转换
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ 转换失败: {result.stderr}")
            return None
        else:
            print(f"✅ 转换成功: {output_file}")

        # 删除临时文件
        temp_file.unlink()

        return output_file

    def generate_all_images(self):
        """生成所有 mermaid 图表的图片"""
        blocks = self.extract_mermaid_blocks()

        if not blocks:
            print("⚠️  未找到 mermaid 代码块")
            return []

        generated_images = []
        for i, block in enumerate(blocks, 1):
            image_file = self.convert_block_to_image(block, i)
            if image_file:
                generated_images.append(image_file)

        print(f"\n✅ 完成！生成 {len(generated_images)} 张图片")
        return generated_images

    def replace_mermaid_with_images(self, output_md_file=None):
        """
        替换 Markdown 文件中的 mermaid 代码块为图片链接

        Args:
            output_md_file: 输出 Markdown 文件路径（可选，默认为原文件名加 -images.md）

        Returns:
            输出文件路径
        """
        if not output_md_file:
            output_md_file = self.input_file.parent / f"{self.input_file.stem}-images.md"

        # 读取原文件
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换 mermaid 代码块为图片链接
        pattern = r'```mermaid\n.*?\n```'

        def replace_block(match, index=[0]):
            index[0] += 1
            image_file = self.output_dir / f"diagram-{index[0]}.{self.image_format}"
            return f"![图表{index[0]}]({image_file})"

        new_content = re.sub(pattern, replace_block, content, flags=re.DOTALL)

        # 写入新文件
        with open(output_md_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Markdown 文件已更新: {output_md_file}")
        return output_md_file


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Mermaid 图表转 PNG/SVG 图片')
    parser.add_argument('input_file', help='输入 Markdown 文件路径')
    parser.add_argument('--output-dir', '-o', default='mermaid-images',
                        help='输出图片目录（默认: mermaid-images）')
    parser.add_argument('--format', '-f', default='png', choices=['png', 'svg'],
                        help='图片格式（png 或 svg，默认: png）')
    parser.add_argument('--width', '-w', type=int, default=1200,
                        help='图片宽度（像素，默认: 1200）')
    parser.add_argument('--scale', '-s', type=int, default=2, choices=[1, 2, 3],
                        help='缩放比例（1-3，默认: 2）')
    parser.add_argument('--background', '-b', default='white',
                        help='背景颜色（默认: white）')
    parser.add_argument('--replace', '-r', action='store_true',
                        help='替换 Markdown 文件中的 mermaid 代码块为图片链接')

    args = parser.parse_args()

    # 创建生成器
    generator = MermaidImageGenerator(
        input_file=args.input_file,
        output_dir=args.output_dir,
        image_format=args.format,
        width=args.width,
        scale=args.scale,
        background=args.background
    )

    # 生成图片
    generated_images = generator.generate_all_images()

    # 替换 Markdown 文件中的代码块（可选）
    if args.replace:
        generator.replace_mermaid_with_images()

    # 显示生成的图片列表
    print("\n=== 生成的图片列表 ===")
    for image in generated_images:
        file_size = image.stat().st_size / 1024  # KB
        print(f"  {image.name}: {file_size:.2f} KB")

    print("\n=== 使用建议 ===")
    print(f"1. 图片目录: {args.output_dir}")
    print(f"2. 图片尺寸: {args.width}px 宽，{args.scale}x 缩放")
    print(f"3. 图片格式: {args.format}")
    print("4. 可在 Word 文档中插入图片")
    print("5. 可使用 pandoc 生成 Word（自动包含图片）")


if __name__ == '__main__':
    main()