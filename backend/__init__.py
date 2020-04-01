from flask import Flask
from backend.blockchain import Blockchain

"""
A module representing the node instance backend. API endpoint implementations in corresponding blueprints.
"""

blockchain = None
wallet = None  # Initialized by GET to /generate_wallet endpoint
peers = []  # Updated with addresses of peers in the form 'url:port'
node_id = None


def create_app(testing=False):
    app = Flask(__name__)

    app.config.from_mapping(
        TESTING=testing
    )

    from .blueprints import transactions
    app.register_blueprint(transactions.bp)

    from .blueprints import blockchain
    app.register_blueprint(blockchain.bp)

    return app
