import requests
from flask import Blueprint, request, make_response, jsonify
import backend as node
from backend.blockchain import Wallet, Transaction, TransactionOutput, Blockchain
from backend.utils import required_fields, bootstrap_endpoint, balance

bp = Blueprint('nodes', __name__)


@bp.route('/', methods=['GET'])
@bp.route('/get_info', methods=['GET'])
def get_info():
    if node.node_id == 0 or node.node_id:
        id_ = node.node_id
    else:
        id_ = -1

    response = dict(
        node_id=id_,
        address=request.host_url,
        public_key=node.wallet.public_key if node.wallet else '',
        chain_length=len(node.blockchain) if node.blockchain else -1,
        balance=balance() if node.wallet and node.blockchain else -1,
        network=node.network
    )
    return jsonify(response), 200


@bp.route('/setup_bootstrap', methods=['POST'])
@required_fields('initial_amount')
def setup_bootstrap():
    data = request.get_json()

    node.node_id = 0
    node.wallet = Wallet()
    init_tx = Transaction('0', node.wallet.public_key, data['initial_amount'])
    init_out = TransactionOutput(init_tx.transaction_id, node.wallet.public_key, data['initial_amount'])
    node.blockchain = Blockchain(
        create_genesis=True,
        initial_transaction=init_tx
    )
    node.blockchain.utxos[node.wallet.public_key] = [init_out]
    node.network = [dict(
        id=node.node_id,
        ip=request.host_url,
        public_key=node.wallet.public_key
    )]

    response, status = dict(message='Bootstrap node setup complete.'), 200
    return make_response(jsonify(response)), 200


@bp.route('/generate_wallet', methods=['GET'])
def generate_wallet():
    """
    Generate a wallet, add it to the node and return the keys to the user.
    """
    node.wallet = Wallet()

    response = {
        'private_key': node.wallet.private_key,
        'public_key': node.wallet.public_key
    }

    return jsonify(response), 200


@bp.route('/register', methods=['POST'])
@required_fields('bootstrap_address')
def register_with_bootstrap():
    data = request.get_json()

    if node.wallet is None:
        response = dict(message='Create a wallet for node before registering.')
        return jsonify(response), 400

    registration_response = requests.post(
        data['bootstrap_address'] + '/register_node',
        json=dict(
            ip=request.host_url,
            wallet_public_key=node.wallet.public_key
        )
    )

    registration_data = registration_response.json()
    id_ = registration_data.get('node_id')
    if id_ is None:
        response = dict(
            message='Registration failed, no node id provided by bootstrap.',
            bootstrap_message=registration_data.get('message') or 'Empty'
        )
        status = 400
    else:
        node.node_id = id_
        response = dict(
            message='Registration successful.',
            node_id=id_
        )
        status = 200

    return jsonify(response), status


@bp.route('/register_node', methods=['POST'])
@required_fields('ip', 'wallet_public_key')
@bootstrap_endpoint
def register_node():
    data = request.get_json()
    new_id = len(node.network)
    node.network.append(dict(
        id=new_id,
        ip=data['ip'],
        public_key=data['wallet_public_key']
    ))
    node.blockchain.utxos[data['wallet_public_key']] = []

    response, status = dict(node_id=new_id), 200
    return jsonify(response), status


@bp.route('/setup_network', methods=['GET'])
@bootstrap_endpoint
def setup_network():
    statuses = {}
    for node_ in node.network:
        if not node_['id'] == 0:
            resp = requests.post(
                node_['ip'] + '/setup_node',
                json=dict(
                    network=node.network,
                    blockchain=node.blockchain.to_dict()
                )
            )
            statuses[node_['ip']] = resp.status_code

    failed_nodes = [k for k in statuses if statuses[k] != 200]
    if not failed_nodes:
        response, status = dict(message='Network setup complete.'), 200
    else:
        response, status = dict(message=f'Nodes {failed_nodes} failed setup, the rest of network is complete.'), 202
    return jsonify(response), status


@bp.route('/setup_node', methods=['POST'])
@required_fields('network', 'blockchain')
def setup_node():
    data = request.get_json()
    try:
        node.blockchain = Blockchain.from_dict(data['blockchain'])
    except (KeyError, TypeError):
        response, status = dict('Invalid blockchain JSON provided.'), 400
        return jsonify(response), status

    node.network = data['network']

    response, status = dict(message='Node setup complete.'), 200
    return jsonify(response), status


@bp.route('/clear', methods=['GET'])
def clear():
    node.wallet = None
    node.node_id = None
    node.blockchain = None
    node.network = []

    return jsonify(dict(message='Node cleared.')), 200
