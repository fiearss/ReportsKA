import csv
from io import StringIO, BytesIO
from flask import Blueprint, Response, request, jsonify, send_file, render_template, send_from_directory, redirect, url_for
import os
import io
from ReportOdt import KaForRssReport
from ReportDocx import ReportDocx


routes = Blueprint('routes', __name__, url_prefix='/')
TEMPLATE_REPORT_FOLDER = 'template_reports'
UPLOAD_PASSWORD = "1234"  # Пароль для загрузки файлов


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
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        # Имя файла берём из query params или по умолчанию
        filename = request.args.get("filename", "report.docx")
        if not filename.endswith(".docx"):
            filename += ".docx"

        # --- Проверка старого формата ---
        if "content" not in data:
            # Преобразуем старый формат в content
            content = []

            # Параграфы
            for p in data.get("paragraphs", []):
                if isinstance(p, dict):
                    text = p.get("text", "")
                    fmt = p.get("formatting")
                else:
                    text = str(p)
                    fmt = None
                content.append({"type": "paragraph", "text": text, "formatting": fmt})

            # Таблица
            table = data.get("table")
            if table and "headers" in table and "rows" in table:
                content.append({
                    "type": "table",
                    "headers": table["headers"],
                    "rows": table["rows"],
                    "formatting": table.get("formatting")
                })

            # Картинка
            img = data.get("image")
            if img:
                # В старом формате 'map' или 'path'
                img_data = img.get("map") or img.get("path")
                content.append({
                    "type": "image",
                    "data": img_data,
                    "formatting": img.get("formatting"),
                    "caption": img.get("caption")
                })

            # Заголовок
            title_obj = data.get("title")
            if isinstance(title_obj, dict):
                title = {"text": title_obj.get("text", "Отчёт"), "formatting": title_obj.get("formatting")}
            else:
                title = {"text": str(title_obj) if title_obj else "Отчёт", "formatting": None}

            # Новый формат для генератора
            data = {"title": title, "content": content}

        # --- Генерация DOCX ---
        doc = ReportDocx()
        doc.build_from_content(data)
        file_stream = doc.get_bytes()

        return send_file(
            file_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
