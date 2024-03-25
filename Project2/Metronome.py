import threading
import time
import requests
from Blockchain import Blockchain
from Wallet import Wallet
from flask import Flask, request

app = Flask(__name__)

class Metronome:
    def __init__(self, validators, netspace, block_generation_interval=10):
        self.validators = validators
        self.netspace = netspace
        self.block_generation_interval = block_generation_interval
        self.metronome_thread = threading.Thread(target=self._metronome_loop, daemon=True)
        self.is_running = False
        self.blockchain = Blockchain(difficulty=2)
        self.wallet = Wallet()
        self.start()

    def _metronome_loop(self):
        while self.is_running:
            self.generate_blocks()
            time.sleep(self.block_generation_interval)

    def start(self):
        if not self.is_running:
            self.is_running = True
            print("Metronome started.")
            self.metronome_thread.start()
        else:
            print("Metronome is already running.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            print("Metronome stopped.")
        else:
            print("Metronome is not running.")

    def generate_blocks(self):
        for validator in self.validators:
            self.wallet.run()

            # Create a new block for each validator
            new_block = self.blockchain.create_block(validator)
            print(f"Created new block with {self.blockchain.hash_block(new_block)}.")

            # Send the block to the validator for validation
            validation_result = self.validate_block_with_validator(new_block, validator)

            if validation_result:
                # Validator approved, add the block to the blockchain
                self.blockchain.add_block(new_block)
                print(f"Block added to the blockchain. Validator: {validator}, Netspace: {self.netspace}")
            else:
                print(f"Block rejected by the validator. Validator: {validator}, Netspace: {self.netspace}")

    def validate_block_with_validator(self, block, validator):
        # Make an HTTP request to the validator for validation
        validation_url = f"{validator}/validate_block"
        response = requests.post(validation_url, json=block.to_dict())

        # Print debug information
        print(f"Validation request sent to {validator}. Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        # Check if the validator approved the block
        if response.status_code == 200 and response.json().get('validation_result'):
            return True
        else:
            return False

# Move route definitions outside of the class
@app.route('/start_metronome', methods=['POST'])
def start_metronome_route():
    metronome.start()
    return {"message": "Metronome started."}

@app.route('/stop_metronome', methods=['POST'])
def stop_metronome_route():
    metronome.stop()
    return {"message": "Metronome stopped."}

if __name__ == "__main__":
    validators = ["http://localhost:5007"]
    netspace = 1000
    metronome = Metronome(validators, netspace, block_generation_interval=15)
    threading.Thread(target=app.run, kwargs={"port": 5003}).start()
