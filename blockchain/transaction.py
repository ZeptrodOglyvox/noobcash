import binascii
from collections import OrderedDict
from uuid import uuid4

import Crypto
import Crypto.Random
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


# Doubt these 2 classes are needed, this isn't Java
class TransactionInput:
    def __init__(self, previous_output_id, amount):
        self.previous_output_id = previous_output_id
        self.amount = amount


class TransactionOutput:
    def __init__(self, transaction_id, recipient_address, amount, id=None):
        self.id = id or str(uuid4())
        self.transaction_id = transaction_id
        self.recipient_address = recipient_address
        self.amount = amount


class Transaction:
    def __init__(self, sender_address, recipient_address, amount,
                 transaction_inputs=None, transaction_outputs=None, id=None):
        self.id = id or str(uuid4())
        self.sender_address = sender_address
        self.recipient_address = recipient_address
        self.amount = amount
        self.transaction_inputs = transaction_inputs or []
        self.transaction_outputs = transaction_outputs or []

    def to_dict(self):
        return OrderedDict(
            transaction_id=self.id,
            sender_address=self.sender_address,
            recipient_address=self.recipient_address,
            amount=self.amount,
            transaction_inputs=self.transaction_inputs,
            transaction_outputs=self.transaction_outputs,
        )

    def sign(self, private_key):
        private_key = RSA.import_key(private_key)
        signer = PKCS1_v1_5.new(private_key)
        h = SHA1.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    @classmethod
    def from_dict(cls, tx_dict):
        return cls(**tx_dict)
