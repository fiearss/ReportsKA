from flask import Blueprint, request, jsonify
from reports import create_report
import base64

routes = Blueprint('routes', __name__, url_prefix='/')

@routes.route('/')
def hello():
    return 'Hello, World!'


# @routes.route('/general-report')
# def generate_report():
#     return create_general_report(data)


@routes.route('/graph-report', methods=['POST'])
def graph_report():
    if request.method == 'POST':
        # Получаем данные из POST-запроса
        data = request.get_json()  # Предполагаем, что данные в формате JSON
        if not data:
            return jsonify({"error": "Нет данных"}), 400
        try:
            report = create_report(data)
            # Кодирование содержимого BytesIO в Base64
            encoded_report = base64.b64encode(report.getvalue()).decode('utf-8')
            return jsonify({"report": encoded_report}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        