from flask import Flask, jsonify, make_response
from backend.blockchain import Blockchain

"""
A module representing the node instance backend. API endpoint implementations in corresponding blueprints.
"""

blockchain = None
wallet = None  # Initialized by GET to /generate_wallet endpoint
network = []  # Updated with addresses of network in the form 'url:port'
node_id = None


def create_app(app_id=0, testing=False):
    app = Flask(__name__)

    app.config.from_mapping(
        TESTING=testing,
    )

    from .blueprints import transactions
    app.register_blueprint(transactions.bp)

    from .blueprints import blockchain
    app.register_blueprint(blockchain.bp)

    from .blueprints import nodes
    app.register_blueprint(nodes.bp)

    return app
