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
    utxos = node.utxos[transaction.sender_address]
    utxo_ids = [u.id for u in utxos]

    checks = dict(
        correct_sender=all(transaction.sender_address == input_.recipient_address for input_ in tx_inputs),
        valid_in_amount=sum(input_.amount for input_ in tx_inputs) >= transaction.amount,
        valid_out_amount=transaction.amount == sum(output.amount for output in transaction.transaction_outputs),
        unspent_inputs=all(input_.previous_output_id in utxo_ids for input_ in transaction.transaction_inputs)
    )

    error_message = dict(
        correct_sender='Input recipient does not match transaction sender.',
        valid_in_amount='Insufficent input amount.',
        valid_out_amount='Incorrect output sum.',
        unspent_inputs='Invalid UTXOs referenced as inputs.'
    )

    for check in checks:
        if checks[check] is False:
            return error_message[check]

    return True
