# generator/ReportDocx.py
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO


class ReportDocx:
    def __init__(self):
        self.doc = Document()
        # Убираем интервалы по умолчанию для всех Normal абзацев
        style = self.doc.styles['Normal']
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.line_spacing = 1  # по желанию, можно 1.0 или другое
    # ==========================
    #  Добавление заголовка
    # ==========================
    def add_title(self, text, formatting=None):
        paragraph = self.doc.add_heading(text, level=1)
        if formatting:
            self._apply_text_formatting(paragraph, formatting)
        return paragraph

    # ==========================
    #  Добавление параграфа
    # ==========================
    def add_paragraph(self, text, formatting=None):
        paragraph = self.doc.add_paragraph(text)
        if formatting:
            self._apply_text_formatting(paragraph, formatting)
        return paragraph

    # ==========================
    #  Добавление таблицы
    # ==========================
    def add_table(self, headers, rows, formatting=None):
        # создаём таблицу с одной строкой для заголовков
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"  # ✅ добавляет границы
        hdr_cells = table.rows[0].cells
        for i, header in enumerate(headers):
            hdr_cells[i].text = str(header)

        # добавляем строки данных
        for row_data in rows:
            row_cells = table.add_row().cells
            for j, cell_value in enumerate(row_data):
                row_cells[j].text = str(cell_value)

        if formatting:
            self._apply_table_formatting(table, formatting)

        return table

    # ==========================
    #  Добавление картинки
    # ==========================
    def add_picture(self, image_bytes, formatting=None, caption=None):
        # image_bytes — это BytesIO или путь к файлу
        picture = self.doc.add_picture(image_bytes)

        if formatting:
            self._apply_picture_formatting(picture, formatting)

        if caption:
            paragraph = self.doc.add_paragraph(caption)
            if formatting:
                self._apply_text_formatting(paragraph, formatting)
        return picture

    # ==========================
    #  Внутренние функции
    # ==========================
    def _apply_text_formatting(self, paragraph, formatting):
        """Форматирование текста (заголовков и параграфов)."""
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()

        # Шрифт
        if "font_name" in formatting:
            run.font.name = formatting["font_name"]
        if "font_size" in formatting:
            run.font.size = Pt(formatting["font_size"])

        # Цвет
        if "font_color" in formatting:
            color = formatting["font_color"].replace("#", "")
            if len(color) == 8:  # RGBA
                color = color[:6]
            run.font.color.rgb = RGBColor.from_string(color)

        # Стили текста
        if "bold" in formatting:
            run.bold = formatting["bold"]
        if "italic" in formatting:
            run.italic = formatting["italic"]
        if "underline" in formatting:
            run.underline = formatting["underline"]

        # Выравнивание
        align_map = {
            "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
            "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
            "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
            "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
        }
        paragraph.alignment = align_map.get(
            formatting.get("alignment", "left").lower(),
            WD_PARAGRAPH_ALIGNMENT.LEFT
        )

        # Интервалы
        if "space_before" in formatting:
            paragraph.paragraph_format.space_before = Pt(formatting["space_before"])
        if "space_after" in formatting:
            paragraph.paragraph_format.space_after = Pt(formatting["space_after"])

    def _apply_table_formatting(self, table, formatting):
        """Форматирование таблиц."""
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
                    # Шрифт и размер
                    if "font_name" in formatting:
                        run.font.name = formatting["font_name"]
                    if "font_size" in formatting:
                        run.font.size = Pt(formatting["font_size"])
                    # Цвет
                    if "font_color" in formatting:
                        color = formatting["font_color"].replace("#", "")
                        if len(color) == 8:
                            color = color[:6]
                        run.font.color.rgb = RGBColor.from_string(color)
                    # Стиль
                    if "bold" in formatting:
                        run.bold = formatting["bold"]
                    if "italic" in formatting:
                        run.italic = formatting["italic"]
                    if "underline" in formatting:
                        run.underline = formatting["underline"]
                    # Выравнивание
                    align_map = {
                        "left": WD_PARAGRAPH_ALIGNMENT.LEFT,
                        "center": WD_PARAGRAPH_ALIGNMENT.CENTER,
                        "right": WD_PARAGRAPH_ALIGNMENT.RIGHT,
                        "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
                    }
                    paragraph.alignment = align_map.get(
                        formatting.get("alignment", "left").lower(),
                        WD_PARAGRAPH_ALIGNMENT.LEFT
                    )

    def _apply_picture_formatting(self, picture, formatting):
        """Форматирование картинок (размер)."""
        if "width" in formatting:
            picture.width = Pt(formatting["width"])
        if "height" in formatting:
            picture.height = Pt(formatting["height"])

    # ==========================
    #  Получение файла в памяти
    # ==========================
    def get_bytes(self):
        file_stream = BytesIO()
        self.doc.save(file_stream)
        file_stream.seek(0)
        return file_stream
