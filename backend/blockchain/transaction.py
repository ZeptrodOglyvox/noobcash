import binascii
from collections import OrderedDict
from uuid import uuid4

from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


# Doubt these 2 classes are needed, this isn't Java
class TransactionInput:
    def __init__(self, previous_output_id, amount):
        self.previous_output_id = previous_output_id
        self.amount = amount

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @classmethod
    def from_output(cls, transaction_output):
        return cls(previous_output_id=transaction_output.id, amount=transaction_output.amount)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class TransactionOutput:
    def __init__(self, transaction_id, recipient_address, amount, id=None):
        self.id = id or str(uuid4())
        self.transaction_id = transaction_id
        self.recipient_address = recipient_address
        self.amount = amount

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Transaction:
    def __init__(self, sender_address, recipient_address, amount,
                 transaction_inputs=None, transaction_outputs=None, id=None):
        self.id = id or str(uuid4())
        self.sender_address = sender_address
        self.recipient_address = recipient_address
        self.amount = amount
        self.transaction_inputs = transaction_inputs or []
        self.transaction_outputs = transaction_outputs or []

    def sign(self, private_key):
        signer = PKCS1_v1_5.new(private_key)
        h = SHA1.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    def to_dict(self):
        """
        Flattens inputs and outputs to dicts as well
        """
        return OrderedDict(
            id=self.id,
            sender_address=self.sender_address,
            recipient_address=self.recipient_address,
            amount=self.amount,
            transaction_inputs=[ti.to_dict() for ti in self.transaction_inputs],
            transaction_outputs=[to.to_dict() for to in self.transaction_outputs],
        )

    @classmethod
    def from_dict(cls, tx_dict):
        """
        Constructs inputs and outputs from dicts as well.
        """
        for idx, ti in enumerate(tx_dict['transaction_inputs']):
            tx_dict['transaction_inputs'][idx] = TransactionInput.from_dict(ti)

        for idx, to in enumerate(tx_dict['transaction_outputs']):
            tx_dict['transaction_outputs'][idx] = TransactionOutput.from_dict(to)

        return cls(**tx_dict)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__
