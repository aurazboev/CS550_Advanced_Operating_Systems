# Metronome.py
import threading
import time
import requests
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

class Metronome:
    def __init__(self, config):
        self.config = config
        self.blockchain_server = config['blockchain']['server_address']
        self.pool_server = config['pool']['server_address']
        self.validator_server = config['validator']['blockchain_server']
        self.block_generation_interval = config['metronome']['block_generation_interval']
        self.metronome_thread = threading.Thread(target=self._metronome_loop, daemon=True)
        self.is_running = False

    @app.route('/start_metronome', methods=['POST'])
    def start_metronome_route(self):
        self.start()
        return {"message": "Metronome started."}

    @app.route('/stop_metronome', methods=['POST'])
    def stop_metronome_route(self):
        self.stop()
        return {"message": "Metronome stopped."}

    def _metronome_loop(self):
        while self.is_running:
            self.generate_and_process_block()
            time.sleep(self.block_generation_interval)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.metronome_thread.start()
            print("Metronome started.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            print("Metronome stopped.")

    def generate_and_process_block(self):
        # Fetch transactions from the pool
        transactions = self.fetch_transactions_from_pool()

        # Determine if the block is empty or contains transactions
        block_type = "empty block" if not transactions else "block with transactions"

        print(f"Attempting to mine a {block_type}.")

        # Request to mine a block
        block_data = {"transactions": transactions}
        mine_response = requests.post(f"{self.blockchain_server}/mine_block", json=block_data)
        if mine_response.status_code == 200:
            print(f"{block_type} mined, sending for validation.")

            # Send block to validator for validation
            validate_response = requests.post(f"{self.validator_server}/validate_block", json=mine_response.json())
            if validate_response.status_code == 200:
                print(f"{block_type} validated, adding to blockchain.")
            else:
                print(f"{block_type} validation failed.")
        else:
            print(f"{block_type} mining failed.")

    def fetch_transactions_from_pool(self):
        try:
            response = requests.get(f"{self.pool_server}/get_transactions")
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            print(f"Failed to fetch transactions from pool: {e}")
            return []

def load_config():
    with open('config.yaml', 'r') as config_file:
        return yaml.safe_load(config_file)

if __name__ == "__main__":
    config = load_config()
    metronome = Metronome(config)
    app.run(port=5003)
