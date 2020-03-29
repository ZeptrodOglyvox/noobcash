from uuid import uuid4

from flask import Blueprint, make_response, jsonify, request
import backend as bck
from backend import blockchain

from blockchain.transaction import Transaction, TransactionInput, TransactionOutput
from blockchain.utils import verify_signature, required_fields
from blockchain.wallet import Wallet

import binascii
import Crypto
from Crypto.PublicKey import RSA


bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.route('/generate_wallet', methods=['GET'])
def generate_wallet():
    bck.wallet = Wallet()
    private_key, public_key = bck.wallet.private_key, bck.wallet.public_key

    response = {
        'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
        'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    }

    return make_response(jsonify(response)), 200


@bp.route('/create', methods=['POST'])
@required_fields(['sender_address', 'sender_private_key', 'recipient_address', 'amount'])
def create_transaction():
    data = request.get_json()
    response = {}
    status_code = None

    if bck.wallet.balance() < data['amount']:
        response = dict(message='Your balance is not enough to complete transaction')
        status_code = 400

        return make_response(jsonify(response)), status_code

    # TODO: What if recipient doesn't exist, amount is negative etc.?

    transaction_id = str(uuid4())

    # Use as many utxos as necessary to create the new transaction inputs
    sum_ = 0
    tx_inputs = []
    while sum_ < data['amount']:
        utxo = bck.wallet.utxos.pop()
        sum_ += utxo.amount()
        tx_inputs.append(TransactionInput(previous_output_id=utxo.id, amount=utxo.amount))

    # Create 2 transaction outputs, one for the transfer and one for the sender's change
    tx_outputs = [
        TransactionOutput(
            transaction_id=transaction_id,
            recipient_address=data['recipient_address'],
            amount=data['amount']
        ),
        TransactionOutput(
            transaction_id=transaction_id,
            recipient_address=data['sender_address'],
            amount=sum_ - data['amount']
        )
    ]

    # Actual transaction object:
    tx = Transaction(
        sender_address=data['sender_address'],
        recipient_address=data['recipient_address'],
        amount=data['amount'],
        transaction_inputs=tx_inputs,
        transaction_outputs=tx_outputs,
        id=transaction_id
    )

    response = tx.to_dict()
    return make_response(jsonify(response)), 200


@bp.route('/sign', methods=['POST'])
def sign_transaction():
    data = request.get_json()
    try:
        tx = Transaction.from_dict(data['transaction'])
    except TypeError:
        response = dict(message='Improper transaction json provided.')
        status_code = 400
        return make_response(jsonify(response)), status_code
    signature = tx.sign()

    response = dict(signature=signature)
    return make_response(jsonify(response)), 200


@bp.route('/submit', methods=['POST'])
@required_fields(['transaction', 'signature'])
def submit_transaction():
    data = request.get_json()

    try:
        tx = Transaction.from_dict(data['transaction'])
    except TypeError:
        response = dict(message='Improper transaction json provided.')
        status_code = 400
        return make_response(jsonify(response)), status_code

    ver_result = verify_signature(tx, data['signature'])
    if isinstance(ver_result, str):
        response = dict(message=ver_result)
        status_code = 400
        return make_response(jsonify(response)), status_code
    else:
        blockchain.add_transaction(tx)

    # TODO: broadcast transaction
    response = dict(message='Transaction added.')
    return make_response(jsonify(response)), 200
