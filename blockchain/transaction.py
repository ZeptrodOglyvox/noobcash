import binascii
import Crypto
import Crypto.Random
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


# Doubt these 2 classes are needed, this isn't Java
class TransactionInput:
    def __init__(self, previous_output_id):
        self.previous_output_id = previous_output_id

    def __getattr__(self, item):
        return self.data[item]


class TransactionOutput:
    def __init__(self, id, origin_id, recipient_address, amount):
        self.id = id
        self.origin_id = origin_id
        self.recipient_address = recipient_address
        self.amount = amount

    def __getattr__(self, item):
        return self.data[item]


class Transaction:
    def __init__(self, id, sender_address, sender_private_key, recipient_address, value):
        self.id = id
        self.sender_address = sender_address
        self.sender_private_key = sender_private_key
        self.recipient_address = recipient_address
        self.value = value
        self.signature = None
        self.transaction_inputs = []
        self.transaction_outputs = []

    def to_dict(self):
        return dict(
            sender_address=self.sender_address,
            recipient_address=self.recipient_address,
            value=self.value
        )

    def sign(self):
        private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA1.new(str(self.to_dict()).encode('utf8'))
        self.signature = binascii.hexlify(signer.sign(h)).decode('ascii')
        # return binascii.hexlify(signer.sign(h)).decode('ascii')

