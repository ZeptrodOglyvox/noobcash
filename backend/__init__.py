from flask import Flask


def create_app():
    app = Flask(__name__)

    from . import transactions
    app.register_blueprint(transactions.bp)

    return app
