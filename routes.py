from flask import Blueprint

routes = Blueprint('routes', __name__, url_prefix='/')

@routes.route('/')
def hello():
    return 'Hello, World!'


@routes.route('/general-report')
def generate_report():
    return create_general_report(data)