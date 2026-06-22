from flask import Flask, jsonify
from werkzeug.serving import WSGIRequestHandler
from routes import routes
import os
import sys
import logging
import traceback

# Увеличиваем лимит рекурсии для глубоких XML/ODT структур
sys.setrecursionlimit(10_000)

app = Flask(__name__, static_folder='website/static', template_folder='website/templates')

# Увеличиваем максимальный размер запроса до 200 МБ
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB

# Увеличиваем таймаут для обработки больших запросов (в секундах)
app.config['PERMANENT_SESSION_LIFETIME'] = 600

# Настройка логирования для отладки ошибок
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.register_blueprint(routes)


# ──────────────────────────────────────────────────────────────────
# CORS: WSGI-обёртка — гарантированно добавляет CORS-заголовки
# ко ВСЕМ ответам, включая ошибки, которые возникают до
# срабатывания @after_request.
# ──────────────────────────────────────────────────────────────────
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept',
}


class CorsMiddleware:
    """WSGI-обёртка: добавляет CORS-заголовки к каждому ответу."""

    def __init__(self, wsgi_app):
        self.app = wsgi_app

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            # Добавляем CORS-заголовки, если их ещё нет
            header_keys = [h[0].lower() for h in headers]
            for key, value in CORS_HEADERS.items():
                if key.lower() not in header_keys:
                    headers.append((key, value))
            return start_response(status, headers, exc_info)

        try:
            return self.app(environ, custom_start_response)
        except Exception as e:
            logger.exception("CorsMiddleware caught exception: %s", e)
            # Возвращаем 500 с CORS-заголовками
            body = jsonify({"error": str(e)}).get_data(as_text=True).encode('utf-8')
            headers = [
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(body))),
            ]
            for key, value in CORS_HEADERS.items():
                headers.append((key, value))
            start_response('500 Internal Server Error', headers, sys.exc_info())
            return [body]


# Оборачиваем WSGI-приложение
app.wsgi_app = CorsMiddleware(app.wsgi_app)


# Разрешаем CORS запросы — @after_request для успешных ответов
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'
    return response


# Обработчик OPTIONS-запросов (preflight) — CORS
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 204


# Глобальный обработчик ошибок — возвращаем CORS-заголовки даже при 500
@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception("Unhandled exception: %s", e)
    response = jsonify({"error": str(e)}), 500
    response[0].headers['Access-Control-Allow-Origin'] = '*'
    response[0].headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response[0].headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'
    return response


@app.errorhandler(413)
def request_entity_too_large(e):
    logger.warning("Request too large: %s", e)
    response = jsonify({"error": "Размер запроса превышает допустимый лимит (200 МБ)"}), 413
    response[0].headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == '__main__':
    # threaded=True — параллельная обработка запросов (критично для больших отчётов)
    # host='0.0.0.0' — доступ извне
    # Увеличиваем таймаут на стороне Werkzeug (по умолчанию 5 сек)
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(debug=True, host='0.0.0.0', port=8888, threaded=True)
