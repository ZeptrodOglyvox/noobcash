import functools

import requests

import backend as node
from flask import request, jsonify

from backend.blockchain import Blockchain


def required_fields(*fields):
    def wrapper(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            if not request.content_type == 'application/json' or \
                    not request.method == 'POST':
                response = dict(message='Please submit data as JSON using a POST request.')
                status_code = 400
                return jsonify(response), status_code

            data = request.get_json()

            if data is None or not all(k in data for k in fields):
                response = dict(message='Required fields missing.')
                status_code = 400
                return jsonify(response), status_code
            else:
                return view(*args, **kwargs)

        return wrapped_view
    return wrapper


def bootstrap_endpoint(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if not node.node_id == 0:
            response = dict(message='This endpoint is only meant to be used by the bootstrap node.')
            status_code = 400
            return jsonify(response), status_code
        else:
            return view(*args, **kwargs)
    return wrapped_view


def validate_transaction_document(transaction):
    tx_inputs = transaction.transaction_inputs
    tx_ouputs = transaction.transaction_outputs
    utxos = node.blockchain.utxos[transaction.sender_address]
    utxo_ids = [u.id for u in utxos]

    checks = dict(
        valid_in_amount=sum(ti.amount for ti in tx_inputs) >= transaction.amount,
        valid_out_amount=sum(ti.amount for ti in tx_inputs) == sum(to.amount for to in tx_ouputs),
        unspent_inputs=all(ti.previous_output_id in utxo_ids for ti in tx_inputs)
    )

    error_message = dict(
        valid_in_amount='Insufficient input amount.',
        valid_out_amount='Incorrect output sum.',
        unspent_inputs='Invalid UTXOs referenced as inputs.'
    )

    for check in checks:
        if checks[check] is False:
            return error_message[check]

    return True


def get_longest_blockchain():
    cur_length = len(node.blockchain)
    cur_last_hash = node.blockchain.last_block.hash
    ret = node.blockchain
    for node_ in node.network:
        if not node_['id'] == node.node_id:
            response = requests.get(node_['ip'] + '/blockchain/get_chain')
            dump = response.json()
            chain_length = dump['length']
            chain_last_hash = dump['chain'][-1]['hash']

            # Imply stricter ordering using last block hash to ensure the same chain will always prevail.
            if cur_length < chain_length or (cur_length == chain_length and cur_last_hash < chain_last_hash):
                bc = Blockchain.from_dict(dump)  # Parse the chain to ensure validity
                if isinstance(bc, Blockchain):
                    ret = bc
                    cur_length = dump['length']

    return ret


def balance():
    """
    :return: The sum of all UTXOs with this node as the recipient that aren't referencing unconfirmed transactions.
    """
    public_key = node.wallet.public_key
    utxos = node.blockchain.utxos[public_key]
    return sum(utxo.amount for utxo in utxos if not node.blockchain.transaction_unconfirmed(utxo))
