import json

import requests
from flask import Blueprint, request, make_response, jsonify
import backend as node
from backend import Blockchain
from backend.blockchain import Wallet
from backend.utils import required_fields, bootstrap_endpoint

bp = Blueprint('nodes', __name__)


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

    # TODO: Should wallet also be broadcast and corresponding utxos entry added?

    return make_response(jsonify(response)), 200


@bp.route('/register', methods=['POST'])
@required_fields('bootstrap_address', 'port')
def register_with_bootstrap():
    data = request.get_json()

    registration_response = requests.post(
        data['bootstrap_address'] + '/register_node',
        data=json.dumps(dict(
            ip=request.url_root,
            port=request.port,
            wallet_public_key=node.wallet.public_key
        )),
        content_type='application/json'
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

    return make_response(jsonify(response)), status


@bp.route('/register_node', methods=['POST'])
@required_fields('ip', 'port', 'wallet_public_key')
@bootstrap_endpoint
def register_node():
    data = request.get_json()
    new_id = len(node.peers)
    node.peers.append(dict(
        id=new_id,
        ip=data['ip'] + ':' + data['port'],
        public_key=data['wallet_public_key']
    ))
    node.blockchain.utxos[data['wallet_public_key']] = []

    response, status = dict(node_id=new_id), 200
    return make_response(jsonify(response)), status


@bp.route('/setup_network', methods=['GET'])
@bootstrap_endpoint
def setup_network():
    for peer in node.peers:
        # TODO: Manage responses to setup
        requests.post(
            peer['ip'] + '/setup_node',
            data=json.dumps(dict(
                peers=node.peers,
                blockchain=node.blockchain.to_dict()
            )),
            content_type='application/json'
        )

    response, status = dict(message='Network setup complete.'), 200
    return make_response(jsonify(response)), status


@bp.route('/setup_node', methods=['POST'])
@required_fields('peers', 'blockchain')
def setup_node():
    data = request.get_json()
    try:
        node.blockchain = Blockchain.from_dict(data['blockchain'])
    except (KeyError, TypeError):
        response, status = dict('Invalid blockchain JSON provided.'), 400
        return make_response(jsonify(response)), status

    node.peers = data['peers']

    response, status = dict(message='Node setup complete.'), 400
    return make_response(jsonify(response)), status


@bp.route('/setup_bootstrap', methods=['POST'])
@required_fields('port')
def setup_bootstrap():
    node.node_id = 0
    node.blockchain = Blockchain(create_genesis=True)
    node.wallet = Wallet()
    node.peers = [dict(
        id=0,
        ip=request.host_url + ':' + 'port',
        wallet_public_key=node.wallet.public_key
    )]

    response, status = dict(message='Bootstrap node setup complete.'), 200
    return make_response(jsonify(response)), 200
