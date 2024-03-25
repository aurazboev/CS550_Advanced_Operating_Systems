# Blockchain.py
import time
import yaml
import random
from blake3 import blake3
from flask import Flask, request, jsonify

# Function to load configuration from YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Load the configuration
config = load_config('dsc-config.yaml')
blockchain_config = config['blockchain']

app = Flask(__name__)

class Transaction:
    def __init__(self, sender, recipient, value, timestamp, tx_id, signature):
        self.sender = sender
        self.recipient = recipient
        self.value = value
        self.timestamp = timestamp
        self.tx_id = tx_id
        self.signature = signature

class Block:
    def __init__(self, version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, validator):
        self.version = version
        self.prev_block_hash = prev_block_hash
        self.block_id = block_id
        self.timestamp = timestamp
        self.difficulty_target = difficulty_target
        self.nonce = nonce
        self.transactions = []
        self.validator = validator

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

class Blockchain:
    def get_balance(self, address):
        print(f"Received getBalance request for address: {address}")
        return random.uniform(0, 100)

    def generate_random_hash(self):
        return bytes([random.randint(0, 255) for _ in range(24)])

blockchain = Blockchain()

@app.route('/get_balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    if address:
        balance = blockchain.get_balance(address)
        return jsonify({'balance': balance})
    else:
        return jsonify({'error': 'Address is required'}), 400

@app.route('/generate_random_hash', methods=['GET'])
def generate_random_hash():
    random_hash = blockchain.generate_random_hash()
    return jsonify({'random_hash': random_hash.hex()})

if __name__ == "__main__":
    # Use configuration to set the host and port for Flask app
    app.run(host='0.0.0.0', port=blockchain_config['port'])

