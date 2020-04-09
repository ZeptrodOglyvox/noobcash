import time
from copy import deepcopy
from hashlib import sha256
import json
from threading import RLock
from .transaction import Transaction, TransactionOutput


class Block:
    capacity = 5

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
        safe_dict = {}

        for k in block_dict:
            if k == 'transactions':
                safe_dict[k] = []
            else:
                safe_dict[k] = block_dict[k]

        safe_dict['transactions'] = [Transaction.from_dict(t) for t in block_dict['transactions']]
        return cls(**safe_dict)

    def to_dict(self):
        ret = deepcopy(self.__dict__)
        ret['transactions'] = [t.to_dict() for t in ret['transactions']]
        return ret

    def __eq__(self, other):
        return other.__dict__ == self.__dict__


class Blockchain:
    def __init__(self, create_genesis=True, initial_transaction=None, pow_difficulty=3):
        self.chain = []
        self.unconfirmed_transactions = []
        self.pow_difficulty = pow_difficulty
        self.lock = RLock()
        self.utxos = {}  # An index of unspent transaction outputs for each public key: {pk1:[utxo1, ...], pk2:[], ...}
        if create_genesis:
            self.create_genesis_block(initial_transaction)

    def create_genesis_block(self, initial_transaction=None):
        genesis_block = Block(index=0, previous_hash='0')
        if initial_transaction is not None:
            genesis_block.transactions.append(initial_transaction)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        with self.lock:
            ret = self.chain[-1]
        return ret

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

    def add_block(self, block, proof=None):
        """
        Add a Block to the chain.
        :param block: Block to be added.
        :param proof: (opt) Proof-of-work suggested for block, if not provided block.hash will be used as proof.
        :return: True if block is added, False if deemed invalid.
        """
        proof_ = proof or block.hash
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return 'Previous hash incorrect.'
        elif not Blockchain.is_valid_proof(block, proof_, self.pow_difficulty):
            return 'Proof invalid.'
        else:
            with self.lock:
                block.hash = proof_
                self.chain.append(block)

                for tx in block.transactions:
                    if tx in self.unconfirmed_transactions:
                        self.unconfirmed_transactions.remove(tx)

            return True

    def add_transaction(self, transaction):
        """
        Adds transaction to unconfirmed transactions, manages UTXOs as well.
        :param transaction:
        :return:
        """
        with self.lock:
            self.unconfirmed_transactions.append(transaction)

            for ti in transaction.transaction_inputs:
                for utxo in self.utxos[transaction.sender_address]:
                    if utxo.id == ti.previous_output_id:
                        self.utxos[transaction.sender_address].remove(utxo)

            for to in transaction.transaction_outputs:
                self.utxos[to.recipient_address].append(to)

    def transaction_unconfirmed(self, transaction):
        with self.lock:
            unconfirmed_ids = [tx.transaction_id for tx in self.unconfirmed_transactions]
        return transaction.transaction_id in unconfirmed_ids

    def mine(self):
        with self.lock:
            if not self.unconfirmed_transactions or \
                    len(self.unconfirmed_transactions) < Block.capacity:
                return None

        last_block = self.last_block
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions[:Block.capacity],
            previous_hash=last_block.hash
        )

        proof = self.mine_block(new_block, self.pow_difficulty)
        new_block.hash = proof
        with self.lock:
            self.unconfirmed_transactions = self.unconfirmed_transactions[Block.capacity:]
        return new_block

    def to_dict(self):
        with self.lock:
            ret = dict(
                length=len(self),
                chain=[b.to_dict() for b in self.chain],
                unconfirmed_transactions=[t.to_dict() for t in self.unconfirmed_transactions],
                utxos={
                    address: [utxo.to_dict() for utxo in utxo_list]
                    for address, utxo_list in self.utxos.items()
                }
            )
        return ret

    @classmethod
    def from_dict(cls, dict_):
        ret = cls(create_genesis=False)
        for block_dict in dict_['chain']:
            block = Block.from_dict(block_dict)
            if not block.index == 0:
                block_added = ret.add_block(block)
                if isinstance(block_added, str):
                    return 'The chain dump is invalid or has been tampered with.'
            else:
                ret.chain.append(block)  # Add genesis block.

        ret.unconfirmed_transactions = [Transaction.from_dict(d) for d in dict_['unconfirmed_transactions']]
        ret.utxos = {
            address: [TransactionOutput.from_dict(utxo) for utxo in utxo_list]
            for address, utxo_list in dict_['utxos'].items()
        }
        return ret

    def replace(self, other):
        with self.lock:
            self.chain = other.chain
            self.utxos = other.utxos
            self.unconfirmed_transactions = other.unconfirmed_transactions
            self.pow_difficulty = other.pow_difficulty

    def __contains__(self, item):
        return self.chain[item.index] == item

    def __eq__(self, other):
        return self.chain == other.chain and \
               self.unconfirmed_transactions == other.unconfirmed_transactions and \
               self.utxos == other.utxos

    def __len__(self):
        return len(self.chain)
