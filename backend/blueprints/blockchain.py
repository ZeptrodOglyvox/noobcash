import json

import requests
from flask import Blueprint, make_response, jsonify, request
import backend as node
from backend.blockchain import Block
from backend.utils import required_fields, get_longest_blockchain

bp = Blueprint('blockchain', __name__, url_prefix='/blockchain')


@bp.route('/get_chain', methods=['GET'])
def get_chain():
    response = node.blockchain.to_dict()
    return jsonify(response), 200


@bp.route('/mine_block', methods=['GET'])
def mine_block():
    mine_result = node.blockchain.mine()

    if not mine_result:
        response = dict(message='No unconfirmed transactions to mine.')
        return jsonify(response), 400

    mined_block = node.blockchain.last_block
    response = mined_block.to_dict()
    return jsonify(response), 200


@bp.route('/add_block', methods=['POST'])
@required_fields('index', 'timestamp', 'transactions', 'nonce', 'previous_hash', 'hash')
def add_block():
    # The block received is proposed by the miner to be the next block in our chain. We attempt to append the block
    # and in case of failure we update the chain and attempt to insert it again or check if it is already in.
    # The broadcast argument can be used by the miner in case he manages to add it to his own chain first,
    # to give his block a fighting chance.

    #####################################################
    # Extra explanation on how this is supposed to work:
    #####################################################
    # We presume that if 1 proposed block manages to be accepted by all network in the network before any other has been
    # proposed, it has been accepted by the blockchain and its miner gets the dinner. Any later blocks should be
    # rejected.
    #
    # If >2 same-indexed blocks start being broadcasted simultaneously* to the network they are all equally deserving of
    # the position in the blockchain. One of them should prevail, else all miners will be informed of their rejection
    # while all local copies of the blockchain will have a different block at the same index. To achieve this, during
    # consensus we attempt to imply a random total ordering between same-length chains by using an additional
    # comparison that any candidate chain should be able to win but can't be easily manipulated to do so.
    #
    # When n blocks are broadcast simultaneously there will be n-1 collisions on all nodes, meaning all nodes will
    # update their chain to the longest (and also 'greatest' in terms of ordering) chain of their network. The block that
    # is meant to prevail will either be the first one to arrive at a node, or a copy of the chain containing it will
    # be received by the node during the update after a collision. All other proposed blocks will arrive after
    # the prevailing block and be rejected after the collision update in at least one node (since they are all broadcast
    # simultaneously). Any latent copies of theirs will disappear in a subsequent collision with the prevailing chain.
    #
    # *By 'simultaneous' broadcasting we refer to >2 same-indexed blocks that are being broadcasted
    # to the network and have been appended successfully to at least the chain of the origin/miner node.
    # (It is not certain that this will happen since the origin might have received a block for
    # the same index during mining.)

    block_dict = request.get_json()
    try:
        block = Block.from_dict(block_dict)
    except (KeyError, TypeError):
        response = dict(message='Invalid block JSON provided.')
        return jsonify(response), 400

    block_accepted = False
    if node.blockchain.add_block(block, block.hash):
        block_accepted = True
    else:
        node.blockchain = get_longest_blockchain()
        if block in node.blockchain or node.blockchain.add_block(block, block.hash):
            block_accepted = True

    # This will normally be used by the miner's client to broadcast the block he just mined.
    if block_accepted and request.args.get('broadcast', type=int, default=0):
        response = requests.post(
            request.host_url + '/broadcast_block',
            data=json.dumps(block.to_dict()),
            content_type='application/json'
        )
        if not response.status_code == 200:
            response = dict(message='Block rejected by the network.')
            return jsonify(response), 400

    if block_accepted:
        response = dict(message='Block added successfully.')
        status = 200
    else:
        response = dict(message='Block rejected by node.')
        status = 400

    return jsonify(response), status


@bp.route('/broadcast_block', methods=['POST'])
@required_fields('index', 'timestamp', 'transactions', 'nonce', 'previous_hash', 'hash')
def broadcast_block():
    block_dict = request.get_json()

    try:
        Block.from_dict(block_dict)
    except (KeyError, TypeError):
        response = dict(message='Invalid block JSON provided.')
        return jsonify(response), 400

    for address in node.network:
        response = requests.post(
            address + '/add_block?broadcast=0',  # Turn off broadcasting for recipients
            data=json.dumps(block_dict),
            content_type='application/json'
        )

        if not response.status_code == 200:
            response = {}
            return jsonify(response), 400

    response = {}
    return jsonify(response), 200
