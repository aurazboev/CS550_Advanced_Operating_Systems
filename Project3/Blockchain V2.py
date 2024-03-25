import time
import datetime
import yaml
import uuid
from blake3 import blake3
from flask import Flask, request, jsonify

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
        self.public_key = None

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
            'validator': self.validator,
            'public_key': self.public_key
        }

class Blockchain:
    def __init__(self, difficulty):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        version = 1
        prev_block_hash = "0" * 32
        block_id = 1
        timestamp = int(time.time())
        difficulty_target = self.difficulty
        nonce = self.proof_of_work(prev_block_hash, difficulty_target)
        timestmp = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
        transactions = [Transaction("root", "15f5f7cd634857432751e21364b6906bb556405bc3d1a7a36e12160b3e9ef9a4", 1024, timestmp, str(uuid.uuid4()), "confirmed")]
        genesis_block = Block(version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, transactions, "Genesis Validator")
        public_key = "a4608433b5edf55040f4fd89b3ae2dabf6bedc4282251209a7bf3c69b6f2e1b6"  # Public key from the wallet
        genesis_block.public_key = public_key

        self.chain.append(genesis_block)

    def create_block(self, validator, public_key):
        version = 1
        prev_block_hash = self.hash_block(self.chain[-1]) if self.chain else "0" * 32
        block_id = len(self.chain) + 1
        timestamp = int(time.time())
        difficulty_target = self.difficulty
        nonce = self.proof_of_work(prev_block_hash, difficulty_target)

        new_block = Block(version, prev_block_hash, block_id, timestamp, difficulty_target, nonce, validator)
        new_block.transactions = self.pending_transactions
        new_block.public_key = public_key

        return new_block

    def add_transaction_to_pending(self, transaction):
        self.pending_transactions.append(transaction)
    
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

    def mine_block_with_validator(self, validator):
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

    def add_block(self, block):
        if self.is_valid_block(block):
            self.chain.append(block)
            return True
        else:
            return False

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

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.get_json()
    transaction = Transaction(
        data['sender'],
        data['recipient'],
        data['value'],
        int(time.time()),
        data['tx_id'],
        data['signature']
    )
    blockchain.add_transaction_to_pending(transaction)
    return jsonify({"message": "Transaction added to pending transactions"}), 200

@app.route('/mine_block', methods=['POST'])
def mine_block():
    data = request.get_json()
    validator = data['validator']
    blockchain.mine_block_with_validator(validator)
    return jsonify({"message": "Block mined"}), 200

@app.route('/get_latest_block_hash', methods=['GET'])
def get_latest_block_hash():
    if blockchain.chain:
        latest_block = blockchain.chain[-1]
        latest_block_hash = blockchain.hash_block(latest_block)
        return {"latest_block_hash": latest_block_hash}
    else:
        return {"message": "Blockchain is empty."}

if __name__ == "__main__":
    blockchain = Blockchain(difficulty=2)
    app.run(port=5002)
