from flask import Blueprint, make_response, jsonify

import binascii
import Crypto
from Crypto.PublicKey import RSA

bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.route('/generate_wallet', methods=['GET'])
def generate_wallet():
    random_gen = Crypto.Random.new().read
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()
    response = {
        'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
        'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    }

    return make_response(jsonify(response)), 200
