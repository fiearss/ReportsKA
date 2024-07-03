import collections
import re
import io
from typing import Iterator
from utils import decode_base64, encode_base64

from odf import opendocument, text
from odf.draw import Frame, Image
from odf.element import Text, Element
from odf.table import TableRow, TableCell


def saxiter(node: Element) -> Iterator[Element]:
    """
    Возвращает итератор по всем элементам, доступным из узла: более поздним однуровневым элементам
     и рекурсивно по всем дочерним элементам.
    """
    while node:
        yield node
        if node.hasChildNodes():
            yield from saxiter(node.firstChild)
        node = node.nextSibling


def fill_table(elem, val):
    """
    Заполняет данными таблицу, к которой относится строка elem
    :param elem: Строка таблицы, содержащая теги для замены
    :param val: Данные для заполнения таблицы (json_array объектов, содержащих одинаковые ключи)
    :return:
    """
    base_row = elem.parentNode.parentNode.parentNode
    doc_table = base_row.parentNode
    if doc_table:
        for item_row in val:
            table_row = TableRow()
            doc_table.addElement(table_row)
            for base_cell in base_row.childNodes:
                match = re.search("\$\${.*}", str(base_cell.childNodes[0].childNodes[0].data))
                cell_text = str(item_row.get(match[0][3:-1].split('.')[1])) if match else ''
                column_data = TableCell()
                column_data.attributes = base_cell.attributes
                table_row.addElement(column_data)
                column_data.addElement(text.P(text=cell_text))
        doc_table.removeChild(base_row)


def fill_image(document, elem, val):
    """
    Заполняет картинкой обнаруженный тег
    :param document: Документ, к которому будет приложена картинка
    :param elem: Место встаки картинки
    :param val: Данные с описание картинки
    Должен содержать:
        - path - путь до картинки
        - type - если это обычная картинка, то тип 'image' (добавлено для будущей расширяемости)
        - width - ширина картинки
        - height - высота картинки
    """
    img = decode_base64(val.get('path'))
    # print(img)
    image_stream = io.BytesIO(img)
    image = Image()


    # img_name = "image.png"
    # temp_file = io.BytesIO(img_data)
    photoframe = Frame(width=str(val.get('width')) + "pt", height=str(val.get('height')) + "pt")
    # href = document.addPicture(image_stream)
    photoframe.addElement(image)
    elem.parentNode.insertBefore(photoframe, elem)
    elem.data = ''


def create_report(data, template_name='template_report/graph_template.odt'):
    """
    Создает отчет по передаваемому шаблону
    :param data: json с данными для отчета
    :param template_name: путь до шаблона в формате odt
    Шаблон должен содержать заменяемые параметры в виде $${tag1.tagN} (через точку в зависимости от уровня вложенности)
    :return:
    """
    document = opendocument.load(template_name)
    start_symbol = "$${"
    current_node = document.topnode

    for elem in saxiter(current_node):
        # Проверяем является ли элемент текстом, содержащим тег для данных
        if elem.__class__ is Text and start_symbol in str(elem):
            # Ищем в строке все теги
            for item in re.findall("\$\${.*}", str(elem)):
                key = item[3:-1].split('.')
                # Проверяем наличие тега в переданных данных
                if key[0] in data:
                    val = data.get(key[0])
                    # Проверяем является ли значение для найденного тега текстовым
                    if type(val) == str:
                        elem.data = val
                    # Проверяем является ли заполняемая строка строкой таблицы
                    elif isinstance(val, collections.abc.Sequence) \
                            and elem.parentNode.parentNode.parentNode.tagName == 'table:table-row':
                        fill_table(elem, val)
                    # Проверяем является ли заполняемый элемент картинкой
                    elif val.items() and val.get('type') == 'image':
                        fill_image(document, elem, val)

    output = io.BytesIO()
    document.save(output)
    output.seek(0)
    return output


# if __name__ == '__main__':
#     # data = {
#     #     "header_text": 'Отчет по системам мобильной космической связи',
#     #     "image": {
#     #         "binary": '1.png',
#     #         "type": 'image',
#     #         "width": 460,
#     #         "height": 300
#     #     },
#     #    "date": '01.01.2020',
#     # }
#     create_report(data)
