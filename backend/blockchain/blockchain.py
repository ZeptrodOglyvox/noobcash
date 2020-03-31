import time
from copy import deepcopy
from hashlib import sha256
import json

from .transaction import Transaction, TransactionOutput


class Block:
    capacity = 100

    def __init__(self, index, previous_hash, timestamp=None, transactions=None, nonce=None, hash=None):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions or []
        self.nonce = nonce
        self.previous_hash = previous_hash
        self.hash = hash

    def compute_hash(self):
        dict_ = self.to_dict()
        del dict_['hash']  # exclude self.hash so that the hashing is consistent if repeated
        block_string = json.dumps(dict_, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    @classmethod
    def from_dict(cls, block_dict):
        block_dict['transactions'] = [Transaction.from_dict(t) for t in block_dict['transactions']]
        return cls(**block_dict)

    def to_dict(self):
        ret = deepcopy(self.__dict__)
        ret['transactions'] = [t.to_dict() for t in ret['transactions']]
        return ret

    def __eq__(self, other):
        return other.__dict__ == self.__dict__


class Blockchain:
    def __init__(self, create_genesis=True, pow_difficulty=3):
        self.chain = []
        self.unconfirmed_transactions = []  # TODO: Should this be a set?
        self.pow_difficulty = pow_difficulty
        self.utxos = {}
        if create_genesis:
            self.create_genesis_block()
            self.last_block.hash = self.last_block.compute_hash()

    def create_genesis_block(self):
        genesis_block = Block(index=0, previous_hash='0')
        genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def mine_block(block, difficulty):
        block.nonce = 0
        proof = block.compute_hash()
        while not proof.startswith('0' * difficulty):
            block.nonce += 1
            proof = block.compute_hash()

        return proof

    @staticmethod
    def is_valid_proof(block, proof, difficulty):
        return proof.startswith('0' * difficulty) and proof == block.compute_hash()

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False
        elif not Blockchain.is_valid_proof(block, proof, self.pow_difficulty):
            return False
        else:
            block.hash = proof
            self.chain.append(block)
            return True

    def add_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def transaction_unconfirmed(self, transaction):
        unconfirmed_ids = [tx.transaction_id for tx in self.unconfirmed_transactions]
        return transaction.id in unconfirmed_ids

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions[:Block.capacity],
            previous_hash=last_block.hash
        )

        proof = self.mine_block(new_block, self.pow_difficulty)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = self.unconfirmed_transactions[Block.capacity:]
        return new_block.index

    def to_dict(self):
        ret = dict(
            length=len(self),
            chain=[b.to_dict() for b in self.chain],
            unconfirmed_transactions=[t.to_dict() for t in self.unconfirmed_transactions],
            utxos=[t.to_dict() for t in self.utxos]
        )
        return ret

    @classmethod
    def from_dict(cls, dict_):
        """
        Secure way of creating a BC from a loaded JSON dump.
        :param dict_list: An iterable of python dictionaries or dict-like objects.
        :return: Either a Blockchain or a str error message.
        """
        ret = cls(create_genesis=False)
        for block_dict in dict_['chain']:
            block = Block.from_dict(block_dict)
            if not block.index == 0:
                block_added = ret.add_block(block, block.hash)
                if not block_added:
                    return 'The chain dump is invalid or has been tampered with.'
            else:
                ret.chain.append(block)  # Add genesis block.

        ret.unconfirmed_transactions = [Transaction.from_dict(d) for d in dict_['unconfirmed_transactions']]
        ret.utxos = [TransactionOutput.from_dict(d) for d in dict_['utxos']]
        return ret

    def __contains__(self, item):
        return self.chain[item.index] == item

    def __eq__(self, other):
        return self.chain == other.chain

    def __len__(self):
        return len(self.chain)
