from flask import Blueprint, request, jsonify

from ReportOdt import KaForRssReport

routes = Blueprint('routes', __name__, url_prefix='/')

@routes.route('/')
def hello():
    return ''


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
            return jsonify(report.save_to_blob()), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        