from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from typing import List, Dict, Optional


def apply_formatting(paragraph, run, formatting: Optional[Dict] = None):
    if formatting is None:
        formatting = {}

    font = run.font
    font.name = formatting.get("font_name", "Times New Roman")
    font.size = Pt(formatting.get("font_size", 14))
    font.bold = formatting.get("bold", False)
    font.italic = formatting.get("italic", False)
    font.underline = formatting.get("underline", False)

    # Цвет текста
    color_hex = formatting.get("font_color", "#000000")
    if color_hex:
        # Удаляем символ "#" если есть
        hex_value = color_hex.lstrip("#")
        try:
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)
            font.color.rgb = RGBColor(r, g, b)
        except Exception:
            print(f"⚠️ Неверный цвет: {color_hex}")

    # Выравнивание
    align_map = {
        "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
        "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
        "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
        "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
    }
    align_str = formatting.get("alignment", "justify").lower()
    paragraph.alignment = align_map.get(align_str, WD_PARAGRAPH_ALIGNMENT.JUSTIFY)

    # Интервалы
    paragraph.paragraph_format.space_before = Pt(formatting.get("space_before", 0))
    paragraph.paragraph_format.space_after = Pt(formatting.get("space_after", 0))
    paragraph.paragraph_format.line_spacing = formatting.get("line_spacing", 1.0)


class ReportDocx:
    def __init__(self):
        self.doc = Document()

    def add_title(self, text: str, level: int = 0, formatting: Optional[Dict] = None):
        paragraph = self.doc.add_heading(text, level=level)
        run = paragraph.runs[0]
        apply_formatting(paragraph, run, formatting)

    def add_paragraph(self, text: str, formatting: Optional[Dict] = None):
        paragraph = self.doc.add_paragraph(text)
        run = paragraph.runs[0]
        apply_formatting(paragraph, run, formatting)

    def add_table(self, headers: List[str], rows: List[List[str]], formatting: Optional[Dict] = None):
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = 'Table Grid'

        # Заголовки
        for i, header in enumerate(headers):
            p = table.rows[0].cells[i].paragraphs[0]
            run = p.add_run(header)
            apply_formatting(p, run, formatting)

        # Строки данных
        for row in rows:
            row_cells = table.add_row().cells
            for i, val in enumerate(row):
                p = row_cells[i].paragraphs[0]
                run = p.add_run(str(val))
                apply_formatting(p, run, formatting)

    def add_image(self, image_path: str, width_inches: float = 4.5, caption: Optional[str] = None, formatting: Optional[Dict] = None):
        try:
            self.doc.add_picture(image_path, width=Inches(width_inches))
            if caption:
                paragraph = self.doc.add_paragraph(caption)
                run = paragraph.runs[0]
                apply_formatting(paragraph, run, formatting)
        except Exception as e:
            print(f"Ошибка при вставке изображения: {e}")

    def save(self, filename: str):
        self.doc.save(filename)

