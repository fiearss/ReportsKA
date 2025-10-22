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

        filename = data.get("filename", "report.docx")
        if not filename.endswith(".docx"):
            filename += ".docx"

        formatting = data.get("formatting", {})
        # title = data.get("title", "")
        paragraphs = data.get("paragraphs", [])
        table = data.get("table", {})
        image = data.get("image", {})

        doc = ReportDocx()
        title_obj = data.get("title")
        if isinstance(title_obj, dict):
            title_text = title_obj.get("text", "Отчёт")
            title_formatting = title_obj.get("formatting")
        else:
            title_text = title_obj or "Отчёт"
            title_formatting = None

        doc.add_title(title_text, formatting=title_formatting)

        for paragraph in paragraphs:
            doc.add_paragraph(paragraph, formatting=formatting)

        if "headers" in table and "rows" in table:
            doc.add_table(table["headers"], table["rows"], formatting=formatting)

        if "path" in image:
            doc.add_image(
                image["path"],
                width_inches=image.get("width", 4.5),
                caption=image.get("caption", None),
                formatting=formatting
            )

        # Создаём объект в памяти
        file_stream = io.BytesIO()
        doc.doc.save(file_stream)
        file_stream.seek(0)  # Вернуться в начало

        return send_file(
            file_stream,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500