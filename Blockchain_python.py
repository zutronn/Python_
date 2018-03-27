# Blockchain class : Managing the chain
import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request

# this two for nodes : urllib.parse : break down url / requests : requests.get(url)
from urllib.parse import urlparse
import requests

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # create a set of nodes to join the network:
        self.nodes = set()

        # Create the gensis block (with prev_hash = 1 / proof = 100 manually set up first time)
        self.new_block(previous_hash=1,proof=100)


    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address : <str> Address of node to register eg. 'http://192.168.0.5:5000'
        :return : None

        """
        parsed_url = urlparse(address)
        # https://docs.python.org/2/library/urlparse.html
        # urlparse lib : break down the url to components

        # Add the parsed url to the nodes ((node1),(node2),(node3)....)
        self.nodes.add(parsed_url.netloc)
        # netloc = the core part (www.192.168.0.2:3000  (any other content excluded)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: <list> A blockchain
        :return:
        """
        # some node register to join the blockchain has its own blockchain. need verify
        last_block = chain[0]
        current_index = 1

        # verify loop each index (block) when smaller then the current chain height:
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of block is correct (prev hash != hash of last block)
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the POW is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            # Only if block hash & POW proof is correct, current index +1 check next block
            current_index += 1
            # until current_index = len(chain), while loop ends, verify completed.
        return True


    def resolve_conflict(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        We loop through all our neighbour nodes, download the chain,
        if their chain is valid + their chain longer than us.

        :return: <bool> True if our chain was replaced, False if not
        """

        # self.nodes set contains all the nodes (IP) joining us, our neighbours:
        neighbours = self.nodes
        # our chain:
        new_chain = None

        # We are only looking for chains longer than ours (let them sub us)
        # max_lenght is our own chain lenght
        max_lenght = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            # Get all nodes with url : IP address / chain (eg. 192.168.0.1:5600)
            response = requests.get(f'http://{node}/chain')

            # if respone is ok (200), create object = request content 'lenght / chain']
            if response.status_code == 200:
                lenght = response.json()['lenght']
                chain = response.json()['chain']

            # Check if the lenght is longer and the chain is valid:
            if lenght > max_lenght and self.valid_chain(chain):
                max_lenght = lenght
                new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            # our self.chain becomes the new_chain = chain from requests.get(neibour)
            self.chain = new_chain
            return True

        return False




    def new_block(self, proof, previous_hash=None):
        """
        Creates a new Block and adds it to the chain
        :param proof: <int> The proof given by the POW algorithm
        :param previous_hash: (Optional) <str> Hash of previous block
        :return: <dict> New Block

        """
        # Block structure Dict:
        block = {
            # block height = chain # + 1
            'index': len(self.chain) + 1,
            # Current time
            'timestamp' : time(),
            # transaction of this block = object : current_transaction (added new_transaction into this object)
            'transactions': self.current_transactions,
            'proof': proof,
            # previous hash = None or current hash - 1
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of tx in new_block
        self.current_transactions = []

        # The object chain add block info into it
        self.chain.append(block)
        return block

    # A new tx include sender / recipient / amount, will be added to the next block:
    def new_transaction(self,sender, recipient, amount):
        """
        Creates a new tx to go into the next mined Block:
        parameter sender : <str> Address of the sender
        parameter recipient : <str> Address of the Recipient
        parameter amount : <int> Amount
        return : <int> The index of the Block that will hold this tx

        """
        # Add this new tx into the class object : current_transaction
        # And this tx will be added to the next block to be mined:
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        # append a dict ({'x': x, 'y': y, 'z':z})

        # return the index / block height / number + 1 (next block)
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]
        # Chain = a list of block connect together

    @staticmethod
    def hash(block): #POW fucntion:
        # Hashes a Block
        """
        Creates a SHA-256 hash of a Block

        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure the Dictionary is Ordered, or inconsistent hash
        # hashlib sha256 of the block_string (answer) created.
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Simple POW Algorithm:
        - Find a number 'p' such that hash (pp') contains leading 4 zeros (0000), where
            p is the previous p.
        - p is the previous proof, and p' is the new proof

        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof : Does hash(last_proof, proof) contain 4 leading 0?

        :param last_proof: <int> Previous Proof
        :param proof:  <int> Current Proof
        :return: <bool> True if correct, False if not
        """
        # Guess = function of last proof * proof
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
        # return when pp' hash ends in "0000"
        # To increase difficulty, we can make it five, six zeros (00000) :x10 harder



# Instantiate our Node (Node = online server with IP)
app = Flask(__name__)

# Generate a globally unique address for this node (First node)
# uuid4 create a random str for you:
node_identifier = str(uuid4()).replace('-', '')

# Create the Blockchain class object:
blockchain = Blockchain()

# Create domain page (/mine, /transaction/new,  /chain)
# *** Remember each @app.route link needs a function with it (return jsonify) ***
# /mine : (GET REQUEST : an endpoint we get data from)
@app.route('/mine', methods=['GET'])
def mine():
    # Ask miners to mine & calculate the POW:
    # We run the POW to get the next proof..

    # Last block = our class object blockchain's last_block (=block-1)
    last_block = blockchain.last_block
    # Last proof = a number 'proof' on the last proof:
    last_proof = last_block['proof']
    # This new block proof (proof=1/0) = check if valid_proof is right, if yes return func
    proof = blockchain.proof_of_work(last_proof)

    # We must receieve a reward for finding the proof
    # The sender is "0" to signify that this node has mined a new coin (no prev sender):
    blockchain.new_transaction(
        sender="0",
        # node_identifier = ?
        recipient=node_identifier,
        amount=1
    )

    # Forge the new Block by adding it to the chain
    # Hash = encode the last block :
    previous_hash = blockchain.hash(last_block)
    # block = new block we create with the proof and previous_hash here:
    block = blockchain.new_block(proof, previous_hash)

    # New block created with index = len(chain), time = time(), tx = tx in here,
    # proof = POW of the last_proof, # previous hash = hash the last block
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    # show respone (new block msg) on the /mine
    return jsonify(response), 200


# /transaction/new (POST REQUEST : Since we will be sending tx data to it)
@app.route('/transaction/new', methods=['POST'])
def new_transaction():
#Example of tx: {
 #"sender": "my address",
 #"recipient": "someone else's address",
 #"amount": 5}

    # POST method collect json content from sender and put into object 'values':
    # *** Remember for POST method, we request.get_json from it and analyse / do something: ***
    values = request.get_json()

    # Check that the required firelds are in the POST'ed data
    # user send data : sender = sender, recipient = recipient, amount = amount:
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # If above checking is correct, we create a new tx using above def : new_transaction()
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    # object index = new_transaction format : values = user input a new tx

    respone = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(respone), 201


# /chain (GET REQUEST : returns the full blockchain data)
@app.route('/chain', methods=['GET'])
def full_chain():
    respone = {
        'chain': blockchain.chain,
        'lenght': len(blockchain.chain)
    }
    # method get the object respone : chain = our blockchain object.chain (chain)
    # Use flask function jsonify to return the object (print)
    return jsonify(respone), 200


# try to add my own stuff:
@app.route('/try', methods=['GET'])
def hello():
    display = "hello!"
    return jsonify(display), 200

# /nodes/register to register a node to the blockchain:
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    # Again, we request content in json format what a sender POST to us:
    values = request.get_json()

    # nodes are the set of all nodes in the blockchain:
    nodes = values.get('nodes')

    if nodes is None:
        return "Error : Please supply a valid list of nodes", 400

    for node in nodes:
        # when someone register a node, we add into the class object > register_node def
        blockchain.register_node(node)
        # where node values collect from what user POST

        respone = {
            'message': 'New nodes have been added',
            'total_nodes': list(blockchain.nodes)
        }
        return jsonify(respone), 201

#
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    # Called above def, which is the longest valid chain substitute us.
    replaced = blockchain.resolve_conflict()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }

    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response),200


# runs the server on 0.0.0.0:5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5600)


# reference:
# https://hackernoon.com/learn-blockchains-by-building-one-117428612f46