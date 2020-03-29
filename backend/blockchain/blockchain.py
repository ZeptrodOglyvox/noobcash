import time
from hashlib import sha256
import json


class Block:
    capacity = 100

    def __init__(self, index, previous_hash, transactions=None):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions or []
        self.nonce = None
        self.previous_hash = previous_hash
        self.hash = None

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        self.hash = sha256(block_string.encode()).hexdigest()


class Blockchain:
    def __init__(self, pow_difficulty=3):
        self.chain = []
        self.unconfirmed_transactions = []
        self.pow_difficulty = pow_difficulty
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
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    @staticmethod
    def is_valid_proof(block, test_hash, difficulty):
        return test_hash.startswith('0' * difficulty) and \
               test_hash == block.compute_hash()

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
