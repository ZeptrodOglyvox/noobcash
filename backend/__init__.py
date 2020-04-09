"""
A module representing the node instance backend. API endpoint implementations in corresponding blueprints.
"""

from flask import Flask

blkchain = None
wallet = None  # Initialized by GET to /generate_wallet endpoint
network = []  # Updated with dicts of the form {node_id: ..., url: ..., public_key: ...}
node_id = None


def create_app(testing=False):
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
