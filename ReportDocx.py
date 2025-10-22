from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn


class ReportDocx:
    def __init__(self):
        self.doc = Document()

    # ---------- ПАРАГРАФЫ ----------
    def add_paragraph(self, text, formatting=None):
        formatting = formatting or {}
        style = formatting.get("style", None)
        paragraph = self.doc.add_paragraph(text, style=style)
        self._apply_paragraph_formatting(paragraph, formatting)
        return paragraph

    # ---------- ЗАГОЛОВОК ----------
    def add_title(self, text, formatting=None):
        formatting = formatting or {}
        style = formatting.get("style", "Title")
        paragraph = self.doc.add_paragraph(text, style=style)
        self._apply_paragraph_formatting(paragraph, formatting)
        return paragraph

    # ---------- ТАБЛИЦЫ ----------
    def add_table(self, headers, rows, formatting=None):
        formatting = formatting or {}
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = formatting.get("style", "Table Grid")

        # Заголовки
        hdr_cells = table.rows[0].cells
        for i, header in enumerate(headers):
            hdr_cells[i].text = str(header)
            self._apply_table_cell_formatting(hdr_cells[i], formatting)

        # Строки данных
        for row_data in rows:
            row_cells = table.add_row().cells
            for i, cell_value in enumerate(row_data):
                row_cells[i].text = str(cell_value)
                self._apply_table_cell_formatting(row_cells[i], formatting)

        return table

    # ---------- КАРТИНКИ ----------
    def add_image(self, image_path, width_inches=4, caption=None, formatting=None):
        formatting = formatting or {}
        picture = self.doc.add_picture(image_path, width=Inches(width_inches))
        last_paragraph = self.doc.paragraphs[-1]
        self._apply_paragraph_formatting(last_paragraph, formatting)

        if caption:
            caption_para = self.doc.add_paragraph(caption, style=formatting.get("style", "Caption"))
            self._apply_paragraph_formatting(caption_para, formatting)

        return picture

    # ---------- СОХРАНЕНИЕ ----------
    def save(self, path):
        self.doc.save(path)

    # ---------- ВНУТРЕННИЕ МЕТОДЫ ФОРМАТИРОВАНИЯ ----------

    def _apply_paragraph_formatting(self, paragraph, formatting):
        # --- Текст внутри параграфа ---
        for run in paragraph.runs:
            font = run.font
            if "font_name" in formatting:
                font.name = formatting["font_name"]
                run._element.rPr.rFonts.set(qn("w:eastAsia"), formatting["font_name"])
            if "font_size" in formatting:
                font.size = Pt(formatting["font_size"])
            if "font_color" in formatting:
                color = formatting["font_color"].replace("#", "")
                font.color.rgb = RGBColor.from_string(color)

            # Стиль текста
            if formatting.get("bold") is not None:
                font.bold = formatting["bold"]
            if formatting.get("italic") is not None:
                font.italic = formatting["italic"]
            if formatting.get("underline") is not None:
                font.underline = formatting["underline"]

        # --- Выравнивание ---
        align_map = {
            "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
            "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
            "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
            "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
        }
        alignment = formatting.get("alignment", "left").lower()
        paragraph.alignment = align_map.get(alignment, WD_PARAGRAPH_ALIGNMENT.LEFT)

        # --- Интервалы ---
        if "space_before" in formatting:
            paragraph.paragraph_format.space_before = Pt(formatting["space_before"])
        if "space_after" in formatting:
            paragraph.paragraph_format.space_after = Pt(formatting["space_after"])
        if "line_spacing" in formatting:
            paragraph.paragraph_format.line_spacing = formatting["line_spacing"]

    def _apply_table_cell_formatting(self, cell, formatting):
        for paragraph in cell.paragraphs:
            self._apply_paragraph_formatting(paragraph, formatting)

    # ---------- Для будущего: можно добавить отдельное форматирование для картинок ----------


