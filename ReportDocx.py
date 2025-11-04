# generator/ReportDocx.py
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import base64
import re


class ReportDocx:
    def __init__(self):
        self.doc = Document()

    # ============== PUBLIC API ==============
    def build_from_content(self, data):
        title_obj = data.get("title")
        if title_obj:
            text = title_obj.get("text", "Отчёт")
            fmt = title_obj.get("formatting")
            self.add_title(text, fmt)

        content_blocks = data.get("content", [])
        for block in content_blocks:
            if not block:
                continue
                
            btype = block.get("type")

            if btype == "paragraph":
                self.add_paragraph(block.get("text", ""), block.get("formatting"))

            elif btype == "table":
                self.add_table(
                    block.get("headers", []),
                    block.get("rows", []),
                    block.get("formatting"),
                )

            elif btype == "image":
                self.add_image_from_base64(
                    block.get("data"),
                    block.get("formatting"),
                    block.get("caption")
                )

            elif btype == "page_break":
                self.doc.add_page_break()

    def add_title(self, text, formatting=None):
        p = self.doc.add_heading(text, level=1)
        self._apply_text_formatting(p, formatting)

    def add_paragraph(self, text, formatting=None):
        p = self.doc.add_paragraph(text)
        self._apply_text_formatting(p, formatting)

    def add_table(self, headers, rows, formatting=None):
        if not headers and not rows:
            return
            
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = str(h)
            # Применяем форматирование к заголовкам
            if formatting:
                for paragraph in hdr_cells[i].paragraphs:
                    self._apply_text_formatting(paragraph, formatting)

        for row in rows:
            row_cells = table.add_row().cells
            for j, cell in enumerate(row):
                row_cells[j].text = str(cell)
                # Применяем форматирование к ячейкам
                if formatting:
                    for paragraph in row_cells[j].paragraphs:
                        self._apply_text_formatting(paragraph, formatting)

    def add_image_from_base64(self, data_url, formatting=None, caption=None):
        if not data_url:
            return
        
        try:
            base64_str = re.sub("^data:image/.+;base64,", "", data_url)
            img_bytes = base64.b64decode(base64_str)
            img_stream = BytesIO(img_bytes)

            # Добавляем изображение с выравниванием
            paragraph = self.doc.add_paragraph()
            paragraph.alignment = self._get_alignment(formatting.get("alignment") if formatting else "center")
            run = paragraph.add_run()
            run.add_picture(img_stream, width=Inches(6))  # Фиксированная ширина

            if caption:
                p = self.doc.add_paragraph(caption)
                self._apply_text_formatting(p, formatting)
        except Exception as e:
            print(f"Ошибка при добавлении изображения: {e}")

    # ============== FORMATTING ==============
    def _apply_text_formatting(self, paragraph, fmt):
        if not fmt:
            return
        
        # Если в параграфе нет runs, создаем один
        if not paragraph.runs:
            paragraph.add_run(paragraph.text)
            paragraph.text = ""  # Очищаем текст, так как он теперь в run

        # Применяем форматирование ко всем runs в параграфе
        for run in paragraph.runs:
            if "font_name" in fmt:
                run.font.name = fmt["font_name"]
            if "font_size" in fmt:
                run.font.size = Pt(fmt["font_size"])
            if "font_color" in fmt:
                color = fmt["font_color"].replace("#", "")
                if len(color) == 8:
                    color = color[:6]
                try:
                    run.font.color.rgb = RGBColor.from_string(color)
                except:
                    pass  # Игнорируем ошибки цвета
            if "bold" in fmt:
                run.bold = bool(fmt["bold"])
            if "italic" in fmt:
                run.italic = bool(fmt["italic"])
            if "underline" in fmt:
                run.underline = bool(fmt["underline"])

        # Выравнивание параграфа
        paragraph.alignment = self._get_alignment(fmt.get("alignment", "left"))

        # Отступы
        if "space_after" in fmt:
            paragraph.paragraph_format.space_after = Pt(fmt["space_after"])
        if "space_before" in fmt:
            paragraph.paragraph_format.space_before = Pt(fmt["space_before"])

    def _get_alignment(self, align_str):
        align_map = {
            "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
            "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
            "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
            "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
        }
        return align_map.get(align_str.lower(), WD_PARAGRAPH_ALIGNMENT.LEFT)

    def _apply_table_formatting(self, table, fmt):
        if not fmt:
            return
        
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    self._apply_text_formatting(p, fmt)

    # ============== OUTPUT ==============
    def get_bytes(self):
        mem = BytesIO()
        self.doc.save(mem)
        mem.seek(0)
        return mem
