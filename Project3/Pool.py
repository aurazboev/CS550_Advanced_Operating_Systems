import socket
import threading
import yaml
from flask import Flask, request, jsonify
from multiprocessing import Process
import time
import requests

app = Flask(__name__)

def start_flask_app(port):
    app.run(host='0.0.0.0', port=port)

class MiningPool:
    def __init__(self, config):
        self.pool_address = (config['pool']['server_address'].split('://')[1].split(':')[0],
                             int(config['pool']['server_address'].split(':')[2]))
        self.metronome_address = (config['metronome']['server_address'].split('://')[1].split(':')[0], 
                                  int(config['metronome']['server_address'].split(':')[2]))
        self.transactions = []  # Store pending transactions
        self.lock = threading.Lock()

    @app.route('/submit_transaction', methods=['POST'])
    def submit_transaction(self):
        transaction = request.json
        with self.lock:
            self.transactions.append(transaction)
        return jsonify({"message": "Transaction added to the pool."}), 200

    def start_pool(self):
        flask_process = Process(target=start_flask_app, args=(self.pool_address[1],))
        flask_process.start()

        print(f"Pool server listening on {self.pool_address[0]}:{self.pool_address[1]}")

        while True:
            with self.lock:
                if self.transactions:
                    self.forward_transactions_to_metronome()
            time.sleep(5)  # Check every 5 seconds

    def forward_transactions_to_metronome(self):
        data = {"transactions": self.transactions}
        response = requests.post(f"http://{self.metronome_address[0]}:{self.metronome_address[1]}/generate_block", json=data)
        if response.status_code == 200:
            print("Transactions forwarded to Metronome for block generation.")
            self.transactions.clear()
        else:
            print("Failed to forward transactions to Metronome.")

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

if __name__ == "__main__":
    config = load_config()
    mining_pool = MiningPool(config)
    mining_pool.start_pool()
