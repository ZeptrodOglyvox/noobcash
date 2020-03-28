from flask import Flask
from blockchain import Blockchain

blockchain = Blockchain()
wallet = None


def create_app(testing=False):
    app = Flask(__name__)

    app.config.from_mapping(
        TESTING=testing
    )

    from . import transactions
    app.register_blueprint(transactions.bp)

    return app


