import functools
import backend as node
from flask import request, make_response, jsonify


def required_fields(*fields):
    def wrapper(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            data = request.get_json()

            if data is None or not all(k in data for k in fields):
                response = dict(message='Required fields missing.')
                status_code = 400
                return make_response(jsonify(response)), status_code
            else:
                return view(*args, **kwargs)

        return wrapped_view
    return wrapper


def validate_transaction_document(transaction):
    tx_inputs = transaction.transaction_inputs
    tx_ouputs = transaction.transaction_outputs
    utxos = node.utxos[transaction.sender_address]
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
