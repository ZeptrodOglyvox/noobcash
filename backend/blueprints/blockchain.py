import json

import requests
from flask import Blueprint, make_response, jsonify, request
import backend as node
from backend import Blockchain
from backend.blockchain import Block
from backend.utils import required_fields

bp = Blueprint('blockchain', __name__, url_prefix='/blockchain')


@bp.route('/get_chain', methods=['GET'])
def get_chain():
    response = dict(
        length=len(node.blockchain),
        chain=node.blockchain.to_dict_list()
    )
    return make_response(jsonify(response)), 200


@bp.route('/mine_block', methods=['GET'])
def mine_block():
    mine_result = node.blockchain.mine()

    if not mine_result:
        response = dict(message='No unconfirmed transactions to mine.')
        return make_response(jsonify(response)), 400

    mined_block = node.blockchain.last_block
    response = mined_block.to_dict()
    return make_response(jsonify(response)), 200


@bp.route('/add_block', methods=['POST'])
@required_fields('index', 'timestamp', 'transactions', 'nonce', 'previous_hash', 'hash')
def add_block():
    # TODO: Needs work
    block_dict = request.get_json()
    try:
        block = Block.from_dict(block_dict)
    except (KeyError, TypeError):
        response = dict(message='Invalid block JSON provided.')
        return make_response(jsonify(response)), 400

    block_added = node.blockchain.add_block(block, block.hash)

    if not block_added:
        # TODO: Manage unconfirmed transactions
        longest_dump = dict(length=0)
        for address in node.peers:
            response = requests.get(address + '/blockchain/get_chain')
            dump = response.json()
            if dump['length'] >= longest_dump['length']:
                longest_dump = dump

        node.blockchain = Blockchain.from_dict_list(longest_dump['chain'])

    block_added = node.blockchain.add_block(block, block.hash)

    if not block_added:
        response = dict(message='Block not added, consesus failed.')
        return make_response(jsonify(response)), 400

    response = dict(message='Block added.')
    return make_response(jsonify(response)), 400


@bp.route('/broadcast_block', methods=['POST'])
@required_fields('index', 'timestamp', 'transactions', 'nonce', 'previous_hash', 'hash')
def broadcast_block():
    block_dict = request.get_json()

    try:
        block = Block.from_dict(block_dict)
    except (KeyError, TypeError):
        response = dict(message='Invalid block JSON provided.')
        return make_response(jsonify(response)), 400

    if block not in node.blockchain:
        response = dict(message='Please make sure to mine the block locally before broadcasting.')
        return make_response(jsonify(response)), 400

    for address in node.peers:
        response = requests.post(
            address + '/add_block',
            data=json.dumps(block_dict),
            content_type='application/json'
        )

        # TODO: Figure out when and why broadcast will fail
        if not response.status_code == 200:
            response = dict(message='Broadcast incomplete.')
            return make_response(jsonify(response)), 400

    response = dict(message='Block broadcast successful.')
    return make_response(jsonify(response)), 200
