from flask import Flask, jsonify
from flask_cors import CORS
from routes import routes
import os
import sys
import logging

# Увеличиваем лимит рекурсии для глубоких XML/ODT структур
sys.setrecursionlimit(10_000)

# Настройка логирования для отладки ошибок
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='website/static', template_folder='website/templates')

# Увеличиваем максимальный размер запроса до 200 МБ
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB

# ──────────────────────────────────────────────────────────────────
# CORS: flask-cors — стандартная библиотека, обрабатывает CORS
# на уровне Flask, включая ответы с ошибками (4xx, 5xx).
# supports_credentials=False —因为我们使用 Access-Control-Allow-Origin: *
# ──────────────────────────────────────────────────────────────────
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(routes)


@app.errorhandler(413)
def request_entity_too_large(e):
    logger.warning("Request too large: %s", e)
    return jsonify({"error": "Размер запроса превышает допустимый лимит (200 МБ)"}), 413


@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception("Unhandled exception: %s", e)
    return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # threaded=True — параллельная обработка запросов (критично для больших отчётов)
    # host='0.0.0.0' — доступ извне
    app.run(debug=True, host='0.0.0.0', port=8888, threaded=True)