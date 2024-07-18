import csv
from io import StringIO
from flask import Blueprint, Response, request, jsonify, send_file, render_template, send_from_directory, render_template, redirect, url_for
import os
from ReportOdt import KaForRssReport

routes = Blueprint('routes', __name__, url_prefix='/')
TEMPLATE_REPORT_FOLDER = 'template_report'

# @routes.route('/')
# def root_page():
#     return render_template('root.html')

@routes.route('/')
def index():
    files = os.listdir(TEMPLATE_REPORT_FOLDER)
    print(os.getcwd())
    print(files)
    return render_template('root.html', files=files)

@routes.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('routes.index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('routes.index'))
    if file:
        file.save(os.path.join(TEMPLATE_REPORT_FOLDER, file.filename))
    return redirect(url_for('routes.index'))

@routes.route('/delete/<filename>')
def delete_file(filename):
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