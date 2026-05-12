#!/usr/bin/env python3
"""Markdown → Word 转换器，pandoc 不可用时的备选方案。

用法:
    python3 generate_docx.py input.md [output.docx]

支持: 标题、粗体、代码块、列表、表格、Mermaid 图片链接。
"""

import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
except ImportError:
    print("错误: 需要 python-docx 库。安装: pip install python-docx")
    sys.exit(1)


def convert_md_to_docx(input_path: str, output_path: str) -> None:
    doc = Document()
    # 默认字体
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Consolas"
    font.size = Pt(11)

    in_code_block = False
    code_lines: list[str] = []
    table_rows: list[list[str]] = []
    in_table = False
    list_buffer: list[tuple[str, int]] = []  # (text, indent_level)

    def flush_list():
        for text, level in list_buffer:
            p = doc.add_paragraph(text, style="List Bullet")
            p.paragraph_format.left_indent = Pt(20 * (level + 1))
        list_buffer.clear()

    def flush_table():
        if not table_rows:
            return
        table = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
        table.style = "Table Grid"
        for i, row in enumerate(table_rows):
            for j, cell_text in enumerate(row):
                table.cell(i, j).text = cell_text.strip()
        doc.add_paragraph()  # 表格后空行
        table_rows.clear()

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        raw = line.rstrip("\n")

        # 代码块
        if raw.strip().startswith("```"):
            if in_code_block:
                p = doc.add_paragraph()
                run = p.add_run("\n".join(code_lines))
                run.font.name = "Consolas"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                in_code_block = False
                code_lines.clear()
            else:
                flush_list()
                flush_table()
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(raw)
            continue

        # 表格
        if "|" in raw:
            cells = [c.strip() for c in raw.split("|")]
            # 去掉首尾空单元格
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]
            # 分隔行（---|---）跳过
            if all(re.match(r"^[-:]+$", c) for c in cells):
                continue
            flush_list()
            in_table = True
            table_rows.append(cells)
            continue
        elif in_table:
            flush_table()
            in_table = False

        # 空行
        if raw.strip() == "":
            flush_list()
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)", raw)
        if m:
            flush_list()
            level = len(m.group(1))
            text = m.group(2)
            heading = doc.add_heading(text, level=min(level, 9))
            continue

        # 列表
        m = re.match(r"^(\s*)[-*]\s+(.*)", raw)
        if m:
            indent = len(m.group(1)) // 2
            list_buffer.append((m.group(2), indent))
            continue
        else:
            flush_list()

        # 行内粗体
        bold_text = re.sub(r"\*\*(.+?)\*\*", r"\1", raw)
        p = doc.add_paragraph()
        # 拆分粗体和非粗体
        parts = re.split(r"(\*\*.+?\*\*)", raw)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                p.add_run(part)

    flush_list()
    flush_table()
    doc.save(output_path)
    print(f"已生成: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 generate_docx.py <input.md> [output.docx]")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else Path(inp).with_suffix(".docx")
    convert_md_to_docx(inp, str(out))
