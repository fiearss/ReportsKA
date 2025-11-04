# generator/ReportDocx.py
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import base64


class ReportDocx:
    def __init__(self):
        self.doc = Document()
        # Убираем интервалы по умолчанию для всех Normal абзацев
        style = self.doc.styles['Normal']
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.line_spacing = 1.15

    # ==========================
    #  Добавление заголовка
    # ==========================
    def add_title(self, text, formatting=None):
        paragraph = self.doc.add_heading(text, level=1)
        # Стандартное форматирование для заголовка
        default_formatting = {
            "font_name": "Times New Roman",
            "font_size": 14,
            "alignment": "center",
            "bold": True,
            "font_color": "#000000"
        }
        # Объединяем стандартные настройки с пользовательскими
        if formatting:
            final_formatting = {**default_formatting, **formatting}
        else:
            final_formatting = default_formatting
            
        self._apply_text_formatting(paragraph, final_formatting)
        return paragraph

    # ==========================
    #  Добавление параграфа
    # ==========================
    def add_paragraph(self, text, formatting=None):
        paragraph = self.doc.add_paragraph(text)
        # Стандартное форматирование для параграфа
        default_formatting = {
            "font_name": "Times New Roman",
            "font_size": 14,
            "font_color": "#000000"
        }
        # Объединяем стандартные настройки с пользовательскими
        if formatting:
            final_formatting = {**default_formatting, **formatting}
        else:
            final_formatting = default_formatting
            
        self._apply_text_formatting(paragraph, final_formatting)
        return paragraph

    # ==========================
    #  Добавление таблицы
    # ==========================
    def add_table(self, headers, rows, formatting=None):
        # создаём таблицу с одной строкой для заголовков
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        hdr_cells = table.rows[0].cells
        
        # Форматирование для заголовков (всегда по центру)
        header_formatting = {
            "font_name": "Times New Roman",
            "font_size": 12,
            "font_color": "#000000",
            "alignment": "center"
        }
        
        # Форматирование для данных
        data_formatting = {
            "font_name": "Times New Roman", 
            "font_size": 12,
            "font_color": "#000000"
        }
        
        # Объединяем с пользовательскими настройками если есть
        if formatting:
            header_formatting = {**header_formatting, **formatting}
            data_formatting = {**data_formatting, **formatting}
        
        # Заполняем заголовки с выравниванием по центру
        for i, header in enumerate(headers):
            hdr_cells[i].text = str(header)
            # Применяем форматирование к каждой ячейке заголовка
            for paragraph in hdr_cells[i].paragraphs:
                self._apply_text_formatting(paragraph, header_formatting)

        # добавляем строки данных с обычным выравниванием
        for row_data in rows:
            row_cells = table.add_row().cells
            for j, cell_value in enumerate(row_data):
                row_cells[j].text = str(cell_value)
                # Применяем форматирование к каждой ячейке данных
                for paragraph in row_cells[j].paragraphs:
                    self._apply_text_formatting(paragraph, data_formatting)

        return table

    # ==========================
    #  Добавление картинки
    # ==========================
    def add_picture(self, image_bytes, formatting=None, caption=None):
        """Добавляет картинку из BytesIO"""
        try:
            picture = self.doc.add_picture(image_bytes)
            
            # Всегда применяем форматирование, даже если formatting=None
            # Если formatting=None, передаем пустой словарь
            format_to_apply = formatting if formatting is not None else {}
            self._apply_picture_formatting(picture, format_to_apply)

            if caption:
                # Для подписи используем стандартное форматирование параграфа
                paragraph = self.doc.add_paragraph(caption)
                default_formatting = {
                    "font_name": "Times New Roman",
                    "font_size": 14,
                    "font_color": "#000000"
                }
                if formatting:
                    final_formatting = {**default_formatting, **formatting}
                else:
                    final_formatting = default_formatting
                self._apply_text_formatting(paragraph, final_formatting)
                    
            return picture
            
        except Exception as e:
            # В случае ошибки добавляем параграф с сообщением об ошибке
            error_paragraph = self.doc.add_paragraph(f"Ошибка загрузки изображения: {str(e)}")
            self._apply_text_formatting(error_paragraph, {
                "font_name": "Times New Roman", 
                "font_size": 14,
                "font_color": "#000000"
            })
            return error_paragraph

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

        # Цвет (по умолчанию черный)
        font_color = formatting.get("font_color", "#000000")
        color = font_color.replace("#", "")
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
                    # Цвет (по умолчанию черный)
                    font_color = formatting.get("font_color", "#000000")
                    color = font_color.replace("#", "")
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

    def _scale_size_image(self, width_px, height_px, max_width=580, max_height=850):
        print(f"width_px: {width_px}, height_px: {height_px}, max_width: {max_width}, max_height: {max_height}")
        """Масштабирование размеров изображения."""
        scale = max_width / width_px
        new_height = height_px * scale

        if new_height > max_height:
            new_height = max_height

        print(f"scale: {scale}, new_height: {new_height}")
        return max_width, new_height

    def _apply_picture_formatting(self, picture, formatting):
        """Форматирование картинок с автоматическим расчетом размера."""
        # Получаем оригинальные размеры картинки в дюймах
        original_width_in = picture.width.inches
        original_height_in = picture.height.inches
        
        # Конвертируем в пиксели (1 дюйм = 96 пикселей)
        original_width_px = original_width_in * 96
        original_height_px = original_height_in * 96
        
        print(f"Original size - inches: {original_width_in}x{original_height_in}, pixels: {original_width_px}x{original_height_px}")
        
        if "width" in formatting or "height" in formatting:
            # Если указаны конкретные размеры
            if "width" in formatting:
                picture.width = Inches(formatting["width"] / 96)
            if "height" in formatting:
                picture.height = Inches(formatting["height"] / 96)
        else:
            # Автоматическое масштабирование с использованием _scale_size_image
            new_width_px, new_height_px = self._scale_size_image(
                original_width_px, original_height_px
            )
            
            # Конвертируем обратно в дюймы
            new_width_in = new_width_px / 96
            new_height_in = new_height_px / 96
            
            picture.width = Inches(new_width_in)
            picture.height = Inches(new_height_in)
            
            print(f"New size - inches: {new_width_in}x{new_height_in}, pixels: {new_width_px}x{new_height_px}")


    # ==========================
    #  Получение файла в памяти
    # ==========================
    def get_bytes(self):
        file_stream = BytesIO()
        self.doc.save(file_stream)
        file_stream.seek(0)
        return file_stream