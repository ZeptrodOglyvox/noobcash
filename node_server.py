import time
from hashlib import sha256
import json

from flask import Flask, request
import requests

peers = set()

class Block:
    capacity = 10

    def __init__(self, index, previous_hash, transactions=None):
        """
        Constructor for the `Block` Class.
        :param index:           unique id of the block
        :param transactions:    list of transactions
        :param timestamp:       time of generation of the block
        :param previous_hash:   hash of the prev. block in the chain 
        :param hash:            hash of the current block
        """
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
    def is_valid_proof(block, test_hash, difficulty=3):
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

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def check_chain_validity(cls, chain):
        """
        A helper method to check if the entire blockchain is valid.
        """
        result = True
        previous_hash = "0"

        # Iterate through every block 
        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash
            # again using `compute hash` method
            delattr(block, "hash")
            if not cls.is_valid_proof(block, block.hash) or \
                previous_hash != block.previous_hash:
                result = False
                break
            block.hash, previous_hash = block_hash, block_hash
        
        return result


app = Flask(__name__)

# the node's copy of the blockchain
blockchain = Blockchain()


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)
    return "Success", 201


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data})


# @app.route('/mine', methods=['GET'])
# def mine_unconfirmed_transactions():
#     result = blockchain.mine()
#     if not result:
#         return "No transactions to mine"
#     else:
#         return "Block #{} is mined.".format(result)

@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)  

@app.route('/register_node', methods=['POST'])
def register_new_peers():
    # The host address to the peer node
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)
    # Return the blockchain to the newly registered 
    # node so that it can sync
    return get_chain()    

@app.route('/register_with', methods=['POST'])    
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to 
    register current node with the remote node specified in 
    the request, and sync the blockchain as well 
    with the remote node.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and
    # obtain information
    response = requests.post(node_address + "/register_node",
                data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers   
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to 
        # the API response
        return response.content, response.status_code

def create_chain_from_dump(chain_dump):
    blockchain = Blockchain()        
    for idx, block_data in enumerate(chain_dump):
        block = Block(index=block_data["index"],
            transactions=block_data["transactions"],
            previous_hash=block_data["previous_hash"])
        block.timestamp = block_data["timestamp"]
        proof = block_data['hash']
        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!")
        else:
            # The block is a genesis block, no verification needed
            blockchain.chain.append(block)
    return blockchain       

def consensus():
    """
    Our simple consenus algorithm. If a longer valid chain is 
    found, our chain is replaced with it.
    """
    global blockchain
    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and \
            blockchain.check_chain_validity(chain):
            # Longer valid chain found
            current_len = length
            longest_chain = chain
    if longest_chain:
        blockchain = longest_chain
        return True
    return False       


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(index=block_data["index"],
                previous_hash=block_data["previous_hash"],
                transactions=block_data["transactions"])
    block.timestamp = block_data["timestamp"]    
    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201

def announce_new_block(block):
    """
    A function to announce to the network once a block has been 
    mined. Other blocks can simply verify the proof of work and 
    add it to their respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))

@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        # Making sure we have the longest chain before 
        # announcing to the network
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the nework
            announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)     





