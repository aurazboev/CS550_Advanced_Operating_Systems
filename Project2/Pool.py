import socket
import threading
import blake3
from collections import OrderedDict
from flask import Flask, request, jsonify
from multiprocessing import Process

app = Flask(__name__)
mining_pool = None  # Global variable to hold the mining pool instance



def run_flask_app(port):
    app.run(host='0.0.0.0', port=port)

class MiningPool:
    def __init__(self, blockchain_address, flask_port, socket_port):
        self.flask_port = flask_port  # Flask application port
        self.socket_port = socket_port  # Socket server port
        self.blockchain_address = blockchain_address
        self.validators = []
        self.submitted_transactions = OrderedDict()  # Transactions from wallets
        self.unconfirmed_transactions = OrderedDict() # Transactions requested by validators
        self.lock = threading.Lock()

    def connect_validator_route(self):
        client_socket, client_address = request.json['client_socket'], request.json['client_address']
        validator_thread = threading.Thread(target=self.handle_validator, args=(client_socket, client_address))
        validator_thread.start()
        return {"message": f"Validator {client_address} connected."}
    
    def add_transaction(self, transaction):
        """Add a new transaction to the submitted pile."""
        with self.lock:
            self.submitted_transactions[transaction['tx_id']] = transaction

    def start_pool(self):
        flask_process = Process(target=run_flask_app, args=(self.flask_port,))
        flask_process.start()

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', self.socket_port))
        server_socket.listen(5)

        print(f"Flask server running on port {self.flask_port}")
        print(f"Socket server listening on port {self.socket_port}")

        while True:
            client_socket, client_address = server_socket.accept()
            validator_thread = threading.Thread(target=self.handle_validator, args=(client_socket, client_address))
            validator_thread.start()

    def handle_validator(self, client_socket, client_address):
        with self.lock:
            print(f"Validator {client_address} connected.")
            self.validators.append(client_socket)

        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                # Process the validator's request, validate transactions, etc.
                # In a real-world scenario, you'd handle validator logic here.

                # Hash the data using Blake3
                hashed_data = blake3.blake3(data).hexdigest()

                # For simplicity, let's just broadcast the hashed data to other validators
                with self.lock:
                    for validator in self.validators:
                        if validator != client_socket:
                            validator.sendall(hashed_data.encode())

                # Forward hashed data to the blockchain component
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blockchain_socket:
                    blockchain_socket.connect(self.blockchain_address)
                    blockchain_socket.sendall(hashed_data.encode())

            except Exception as e:
                print(f"Error handling validator {client_address}: {e}")
                break

        with self.lock:
            print(f"Validator {client_address} disconnected.")
            self.validators.remove(client_socket)
            client_socket.close()

# Global mining pool instance
blockchain_address = ('localhost', 5002)
flask_port = 5005
socket_port = 8000
mining_pool = MiningPool(blockchain_address, flask_port, socket_port)

@staticmethod
@app.route('/submit_transaction', methods=['POST'])
def submit_transaction():
    global mining_pool
    transaction = request.json
    mining_pool.add_transaction(transaction)
    return {"message": "Transaction added to the pool"}, 200

@staticmethod
@app.route('/transaction_status', methods=['GET'])
def transaction_status():
    global mining_pool
    tx_id = request.args.get('id')
    # Check for transaction in both submitted and unconfirmed transactions
    with mining_pool.lock:
        if tx_id in mining_pool.submitted_transactions:
            return {"status": "submitted"}, 200
        elif tx_id in mining_pool.unconfirmed_transactions:
            return {"status": "unconfirmed"}, 200
        else:
            return {"status": "unknown"}, 404

@staticmethod        
@app.route('/list_transactions', methods=['GET'])
def list_transactions():
    global mining_pool
    public_key = request.args.get('public_key')
    if not public_key:
        return jsonify({"error": "Public key is required"}), 400

    with mining_pool.lock:
        # Convert odict_values to lists and concatenate them
        all_transactions = list(mining_pool.submitted_transactions.values()) + \
                           list(mining_pool.unconfirmed_transactions.values())

        # Filter transactions by the provided public key
        filtered_transactions = [txn for txn in all_transactions if txn.get('sender') == public_key]

        return jsonify(filtered_transactions), 200


if __name__ == "__main__":
    # Specify the address of the blockchain component
    blockchain_address = ('localhost', 5002)
    flask_port = 5005  # Specify Flask port
    socket_port = 8000  # Specify Socket server port

    mining_pool = MiningPool(blockchain_address, flask_port, socket_port)
    mining_pool.start_pool()
