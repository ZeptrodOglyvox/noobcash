import time
from copy import deepcopy
from hashlib import sha256
import json

from .transaction import Transaction


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
        self.unconfirmed_transactions = []
        self.pow_difficulty = pow_difficulty
        if create_genesis:
            self.create_genesis_block()

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

    def json_dump(self):
        return json.dumps([block.to_dict() for block in self.chain])

    @classmethod
    def from_dump(cls, dump):
        ret = cls(create_genesis=False)
        chain = [Block.from_dict(b_dict) for b_dict in json.loads(dump)]
        for block in chain:
            # TODO: Should genesis block be added like this?
            if block.previous_hash == '0':
                ret.chain.append(block)
            elif not ret.add_block(block, block.hash):
                return 'The chain dump is invalid or has been tampered with.'

        return ret
