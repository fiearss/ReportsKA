from flask import Flask
from routes import routes

app = Flask(__name__)

app.register_blueprint(routes)

# Разрешаем CORS запросы
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'
    return response

if __name__ == '__main__':
    app.run(debug=True, port=8888)