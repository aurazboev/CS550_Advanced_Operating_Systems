# Blockchain.py
import time
import datetime
import yaml
import uuid
from blake3 import blake3
from flask import Flask, request,jsonify
from Wallet import Wallet

app = Flask(__name__)


class Transaction:
    def __init__(self, sender, recipient, value, timestamp, tx_id, status):
        self.sender = sender
        self.recipient = recipient
        self.value = value
        self.timestamp = timestamp
        self.tx_id = tx_id
        self.status = status

        def to_dict(self):
            return {
                'sender': self.sender,
                'recipient': self.recipient,
                'value': self.value,
                'timestamp': self.timestamp,
                'tx_id': self.tx_id,
                'status': self.status
            }

class Block:
    def __init__(self, version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, transactions, validator):
        self.version = version
        self.prev_block_hash = prev_block_hash
        self.block_id = block_id
        self.timestamp = timestamp
        self.difficulty_target = difficulty_target
        self.nonce = nonce
        self.transactions = transactions
        self.validator = validator

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def to_dict(self):
        return {
            'version': self.version,
            'prev_block_hash': self.prev_block_hash,
            'block_id': self.block_id,
            'timestamp': self.timestamp,
            'difficulty_target': self.difficulty_target,
            'nonce': self.nonce,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'validator': self.validator
        }

class Blockchain:
    def __init__(self, difficulty):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        timestmp = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
        transactions = [Transaction("root", "15f5f7cd634857432751e21364b6906bb556405bc3d1a7a36e12160b3e9ef9a4", 1024, timestmp, str(uuid.uuid4()), "confirmed")]
        genesis_block = Block(1, "0" * 64, 0, time.time(), self.difficulty, 0, transactions, "Genesis")
        self.chain.append(genesis_block)
        print("Genesis block created")
        self.print_blockchain_info()

    def create_block(self, validator):
        version = 1
        prev_block_hash = self.hash_block(self.chain[-1]) if self.chain else "0" * 64
        block_id = len(self.chain) + 1
        timestamp = int(time.time())
        difficulty_target = self.difficulty
        nonce = self.proof_of_work(prev_block_hash, difficulty_target)
        transactions  = []
        new_block = Block(version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, transactions, validator)
        new_block.transactions = self.pending_transactions

        return new_block

    @app.route('/get_balance', methods=['GET'])
    def get_balance():
        wallet_address = request.args.get('wallet_address')
        if not wallet_address:
            return jsonify({"error": "Wallet address is required"}), 400
        balance = blockchain.calculate_balance(wallet_address)
        latest_block_number = blockchain.chain[-1].block_id if blockchain.chain else 0
        return jsonify({"balance": balance, "block_number": latest_block_number}), 200
    
    def calculate_balance(self, wallet_address):
        balance = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == wallet_address:
                    balance -= transaction.value
                elif transaction.recipient == wallet_address:
                    balance += transaction.value
        return balance

    def add_block(self, block):
        self.chain.append(block)
        print(f"New block added: Block ID {block.block_id}, Hash {self.hash_block(block)}")
        self.print_blockchain_info()

    def print_blockchain_info(self):
        print(f"Blockchain now contains {len(self.chain)} blocks:")
        for block in self.chain:
            print(f"  Block ID: {block.block_id}, Hash: {self.hash_block(block)}")

    def get_latest_block_hash(self):
        if len(self.chain) > 0:
            latest_block = self.chain[-1]
            return self.hash_block(latest_block)
        else:
            return None

    def add_transaction(self, sender, recipient, value, timestamp, tx_id, status):
        new_transaction = Transaction(sender, recipient, value, timestamp, tx_id, status)
        self.pending_transactions.append(new_transaction)
        print(f"20231110 12:10:00.120 Transaction id {tx_id} received from {sender}, ACK")

    @app.route('/mine_block', methods=['POST'])
    def mine_block(self):
        data = request.json
        validator = data.get('validator')

        version = 1
        prev_block_hash = self.hash_block(self.chain[-1]) if self.chain else "0" * 32
        block_id = len(self.chain) + 1
        timestamp = int(time.time())
        difficulty_target = self.difficulty
        nonce = self.proof_of_work(prev_block_hash, difficulty_target)

        new_block = Block(version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, validator)
        new_block.transactions = self.pending_transactions
        self.pending_transactions = []

        self.add_block(new_block)
        return jsonify({"message": f"Block {block_id} mined by {validator}"})

    def hash_block(self, block):
        block_str = (
            str(block.version) +
            block.prev_block_hash +
            str(block.block_id) +
            str(block.timestamp) +
            str(block.difficulty_target) +
            str(block.nonce) +
            ''.join([tx.tx_id for tx in block.transactions]) +
            str(block.validator)
        )
        return blake3(block_str.encode()).hexdigest()

    def proof_of_work(self, prev_block_hash, difficulty):
        nonce = 0
        while True:
            block_str = prev_block_hash + str(nonce)
            block_hash = blake3(block_str.encode()).hexdigest()
            if block_hash.startswith('0' * difficulty):
                return nonce
            nonce += 1

def load_config():
    with open('dsc-config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

def load_private_key():
    try:
        with open('dsc-key.yaml', 'r') as key_file:
            keys = yaml.safe_load(key_file)
            if 'wallet' in keys and 'private_key' in keys['wallet']:
                return keys['wallet']['private_key']
            else:
                print("Invalid format in dsc-key.yaml. Missing 'wallet' or 'private_key' key.")
                return None
    except FileNotFoundError:
        print("Key file not found.")
        return None


def main():
    config = load_config()
    private_key = load_private_key()

    if private_key is not None:
        blockchain = Blockchain(difficulty=2)
        wallet_address = config['wallet']['public_key']
        Wallet().run()  # Run wallet operations

        # Run your blockchain operations, transactions, mining, etc.

@app.route('/get_latest_block_hash', methods=['GET'])
def get_latest_block_hash():
    latest_block_hash = blockchain.get_latest_block_hash()
    if latest_block_hash:
        return jsonify({"latest_block_hash": latest_block_hash}), 200
    else:
        return jsonify({"error": "No blocks found in the chain"}), 404

if __name__ == "__main__":
    blockchain = Blockchain(difficulty=2)
    app.run(port=5002)
