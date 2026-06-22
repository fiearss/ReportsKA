import csv
from io import StringIO
from flask import Blueprint, Response, request, jsonify, send_file, render_template, send_from_directory, render_template, redirect, url_for
import os
import io
from ReportOdt import KaForRssReport
from ReportDocx import ReportDocx


routes = Blueprint('routes', __name__, url_prefix='/')
TEMPLATE_REPORT_FOLDER = 'template_reports'
UPLOAD_PASSWORD = "1234"  # Пароль для загрузки файлов

# Увеличиваем лимит на чтение JSON (по умолчанию ~16MB в Werkzeug)
# Это позволяет обрабатывать большие POST-запросы с данными отчётов
from werkzeug.wsgi import LimitedStream

# Максимальный размер тела запроса: 200 МБ
MAX_REQUEST_BYTES = 200 * 1024 * 1024


@routes.route('/')
def index():
    files = os.listdir(TEMPLATE_REPORT_FOLDER)
    return render_template('root.html', files=files)


@routes.route('/upload', methods=['POST'])
def upload_file():
    password = request.form.get('password')
    if password != UPLOAD_PASSWORD:
        return redirect(url_for('routes.index'))  # Неправильный пароль, редирект на главную страницу

    if 'file' not in request.files:
        return redirect(url_for('routes.index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('routes.index'))
    if file:
        file.save(os.path.join(TEMPLATE_REPORT_FOLDER, file.filename))
    return redirect(url_for('routes.index'))

@routes.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    password = request.form.get('password')
    if password != UPLOAD_PASSWORD:
        return redirect(url_for('routes.index'))  # Неправильный пароль, редирект на главную страницу

    file_path = os.path.join(TEMPLATE_REPORT_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for('routes.index'))

@routes.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(TEMPLATE_REPORT_FOLDER, filename, as_attachment=True)


@routes.route('/report', methods=['POST'])
def rss_report():
    if request.method == 'POST':
        # Получаем данные из POST-запроса
        data = request.get_json()  # Предполагаем, что данные в формате JSON
        print(data)
        if not data:
            return jsonify({"error": "Нет данных"}), 400
        try:
            report = KaForRssReport(data=data, template_name=data.get('path_template'))
            report.create_report()
            return send_file(
                             report.save_to_blob(),
                             as_attachment=True, 
                             download_name='report.odt', 
                             mimetype='application/vnd.oasis.opendocument.text'
                             ), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        


@routes.route('/report/csv', methods=['POST'])
def create_report_csv():
    # Получаем данные из JSON-запроса
    body_data = request.get_json()
    header = body_data.get('header', {})
    rows = body_data.get('rows', {})
   
    output = StringIO(newline='')
    # Для поддержки UTF-8
    output.write('\uFEFF')  # Записываем BOM в начало файла как строку
    writer = csv.DictWriter(output, fieldnames=header.keys(), delimiter=';')
    # Записываем заголовок
    writer.writerow(header)
    # Записываем данные
    writer.writerows(rows)
    
    output.seek(0)  # Move cursor to start of StringIO
    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-disposition": "attachment; filename=output.csv"} 
    )


@routes.route('/report/docx', methods=['POST'])
def generate_docx_report():
    import logging
    import time
    import json
    import traceback

    logger = logging.getLogger(__name__)

    try:
        # Получаем сырые байты тела запроса, чтобы измерить размер
        raw_data = request.get_data(cache=True)
        logger.info("Получен запрос /report/docx, размер тела: %d байт (%.1f МБ)",
                     len(raw_data), len(raw_data) / (1024 * 1024))

        # Парсим JSON из сырых данных
        try:
            data = json.loads(raw_data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error("Ошибка парсинга JSON: %s", e)
            return jsonify({"error": f"Невалидный JSON: {e}"}), 400

        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        filename = data.get("filename", "report.docx")
        if not filename.endswith(".docx"):
            filename += ".docx"

        # Создаём экземпляр генератора
        doc = ReportDocx()

        # Обрабатываем элементы в том порядке, в которых они переданы
        elements = data.get("elements", [])
        logger.info("Количество элементов отчёта: %d", len(elements))

        start_time = time.time()
        
        for element in elements:
            element_type = element.get("type")
            
            if element_type == "title":
                # Заголовок
                text = element.get("text", "Отчёт")
                formatting = element.get("formatting")
                doc.add_title(text, formatting=formatting)
                
            elif element_type == "paragraph":
                # Параграф
                text = element.get("text", "")
                formatting = element.get("formatting")
                doc.add_paragraph(text, formatting=formatting)
                
            elif element_type == "table":
                # Таблица
                headers = element.get("headers", [])
                rows = element.get("rows", [])
                formatting = element.get("formatting")
                col_widths = element.get("col_widths")
                if headers and rows:
                    doc.add_table(headers, rows, formatting=formatting, col_widths=col_widths)
                    
            elif element_type == "image":
                # Картинка
                image_data = element.get("bytes")
                formatting = element.get("formatting")
                caption = element.get("caption")
                if image_data:
                    # Обрабатываем data URL
                    if isinstance(image_data, str) and image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]
                    
                    import base64
                    img_bytes = base64.b64decode(image_data)
                    img_stream = io.BytesIO(img_bytes)
                    
                    doc.add_picture(img_stream, formatting=formatting, caption=caption)

        elapsed = time.time() - start_time
        logger.info("Элементы обработаны за %.2f сек, генерируем файл...", elapsed)

        # --- Генерация файла в оперативке ---
        file_stream = doc.get_bytes()
        
        logger.info("Файл сформирован, отправляем клиенту...")
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        logger.error("Ошибка при генерации отчёта: %s\n%s", e, traceback.format_exc())
        # Возвращаем JSON с CORS-заголовками
        response = jsonify({"error": str(e)}), 500
        response[0].headers['Access-Control-Allow-Origin'] = '*'
        return response
