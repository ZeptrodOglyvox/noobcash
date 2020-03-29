from flask import Flask
from blockchain import Blockchain

blockchain = Blockchain()
wallet = None  # Initialized by GET to /generate_wallet endpoint
peers = set()  # Updated with addresses of peers in the form 'url:port'
utxos = {}  # {'somepubkey': [utxo1]}


def create_app(testing=False):
    app = Flask(__name__)

    app.config.from_mapping(
        TESTING=testing
    )

    from . import transactions
    app.register_blueprint(transactions.bp)

    return app
