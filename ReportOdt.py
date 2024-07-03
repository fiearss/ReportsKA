import collections
import re
import io
from typing import Iterator

from odf import opendocument, text
from odf.draw import Frame, Image
from odf.element import Text, Element
from odf.table import TableRow, TableCell


# def fill_image(document, elem, val):
#     """
#     Заполняет картинкой обнаруженный тег
#     :param document: Документ, к которому будет приложена картинка
#     :param elem: Место встаки картинки
#     :param val: Данные с описание картинки
#     Должен содержать:
#         - path - путь до картинки
#         - type - если это обычная картинка, то тип 'image' (добавлено для будущей расширяемости)
#         - width - ширина картинки
#         - height - высота картинки
#     """
#     img = decode_base64(val.get('path'))
#     # print(img)
#     image_stream = io.BytesIO(img)
#     image = Image()


#     # img_name = "image.png"
#     # temp_file = io.BytesIO(img_data)
#     photoframe = Frame(width=str(val.get('width')) + "pt", height=str(val.get('height')) + "pt")
#     # href = document.addPicture(image_stream)
#     photoframe.addElement(image)
#     elem.parentNode.insertBefore(photoframe, elem)
#     elem.data = ''

class BaseReportOdt:
    def __init__(self, data, template_name):
        # Данные JSON
        self.data = data
        # Имя шаблона
        self.template_name = template_name
        # Загружаем шаблон
        self.document = opendocument.load(f'template_report/{self.template_name}.odt')
        # Начало тега который считываются из шаблона $${header} - пример
        self.start_symbol = "$${"
        # Начинаем поиск тегов с корня документа
        self.current_node = self.document.topnode


    def saxiter(self, node=None) -> Iterator[Element]:
            """
            Возвращает итератор по всем элементам, доступным из узла: более поздним одноуровневым элементам
            и рекурсивно по всем дочерним элементам.
            """
            if node is None:
                node = self.current_node
            # Генератор-итератор, сначала от корня дочерние, потом рядом, рекурсивно
            # Проверка, что есть текущий узел
            while node:
                # Возвращаем текущий узел
                yield node
                # Проверяем, есть ли у узла дочерние элементы
                if node.hasChildNodes():
                    # Заходим в первый дочерний элемент и возвращаем его (тут же начинаем рекурсию)
                    yield from self.saxiter(node.firstChild)
                # На этом же уровне переходим к следующему узлу
                node = node.nextSibling

    def create_report(self):
        # Проходимся по всем элементам (узлам), которые есть в документе
        for elem in self.saxiter():
            # Проверяем, является ли элемент текстом и является ли его содержимым тегом для данных
            if elem.__class__ is Text and self.start_symbol in str(elem):
                # Итерируемся по всем подстрокам (тегам) в строке
                for item in re.findall("\$\${.*}", str(elem)):
                    # Получаем список тегов из найденных (сплит для таблиц), обрезаем $${}
                    key = item[3:-1].split('.')
                    # Проверяем наличие тега из шаблона в переданных данных
                    if key[0] in self.data:
                        # Считываем значение из переданных данных для ключа
                        value = self.data.get(key[0])
                        # Проверяем, является ли значение для найденного тега текстовым (не словарь)
                        if type(value) == str:
                            # Записываем в документ текст
                            elem.data = value
                        # Проверяем, является ли значение последовательностью (можно итерироваться)
                        # и проверяем, является ли у elem отец..отец..отец..тегом table:table-row
                        elif isinstance(value, collections.abc.Sequence) \
                                and elem.parentNode.parentNode.parentNode.tagName == 'table:table-row':
                            # Передаем элемент и словарь с данными в функцию заполнения таблицы
                            self._fill_table(elem, value)
                        # Проверяем, является ли значение словарём и не пустой ли он, и есть ли ключ 'type' и его значение 'image'
                        elif value.items() and value.get('type') == 'image':
                            # Передаем шаблон (документ), элемент (узел), словарь 
                            # с данными картинки в функцию заполнения картинки
                            self._fill_image(self.document, elem, value)
        
    
    def save_to_blob(self):
        # Создаем поток для сохранения
        output = io.BytesIO()
        # Сохраняем документ в поток
        self.document.save(output)
        # Перемещаем указатель в начало потока
        output.seek(0)
        # Читаем поток и получаем blob сохраненного документа
        blob = output.read()

        # FIXME: Временно, для тестов
        # print(blob)
        # with open('report.odt', 'wb') as file:
        #     file.write(blob)

        return {
            'odt_doc': blob
        }
    

    def _fill_image(document, elem, val):
        # TODO: Сделать вставку картинки
        pass


    def _fill_table(self, elem, value):
        # Получаем первую строку таблицы
        base_row = elem.parentNode.parentNode.parentNode
        # Получаем элемент самой таблицы
        doc_table = base_row.parentNode
        # Проверяем что таблица существует
        if doc_table:
            # Итерируемся по всем строкам value (словаря)
            for item_row in value:
                # Создаем новую строку (элемент)
                table_row = TableRow()
                # Добавляем строку в таблицу (добавляем элемент в документ)
                doc_table.addElement(table_row)
                # Проходимся по всем ячейкам в строке
                for base_cell in base_row.childNodes:
                    # Ищем тег в ячейке
                    match = re.search("\$\${.*}", str(base_cell.childNodes[0].childNodes[0].data))
                    # Получаем значение по ключу (если они есть в value и match)
                    cell_text = str(item_row.get(match[0][3:-1].split('.')[1])) if match else ''
                    # Создаем ячейку в таблице
                    column_data = TableCell()
                    # Делаем такие же стили как в base_cell
                    column_data.attributes = base_cell.attributes
                    # Добавляем ячейку в строку
                    table_row.addElement(column_data)
                    # Добавляем текст в ячейку (через элемент абзаца (P))
                    column_data.addElement(text.P(text=cell_text))
            # Удаляет строку где содержались теги
            doc_table.removeChild(base_row)


class KaForRssReport(BaseReportOdt):
    pass