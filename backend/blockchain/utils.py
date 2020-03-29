import binascii
import functools

from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from flask import request, make_response, jsonify


def verify_signature(transaction, signature):
    h = SHA1.new(str(transaction.to_dict()).encode('utf8'))
    try:
        public_key = RSA.import_key(binascii.unhexlify(transaction.sender_address))
        cipher = PKCS1_v1_5.new(public_key)
        cipher.verify(h, signature)
        return True
    except (ValueError, TypeError):
        return 'Invalid Signature.'
