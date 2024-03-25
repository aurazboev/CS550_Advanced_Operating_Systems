import threading
import time
import requests
import yaml

# Function to load configuration from YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

class Metronome:
    def __init__(self, config, block_generation_interval=6, difficulty=30):
        self.block_generation_interval = block_generation_interval
        self.difficulty = difficulty
        self.metronome_thread = threading.Thread(target=self._metronome_loop, daemon=True)
        self.is_running = False
        self.blockchain_server_url = f"http://{config['blockchain']['server']}:{config['blockchain']['port']}"

    def _metronome_loop(self):
        while self.is_running:
            self.submit_block()
            time.sleep(self.block_generation_interval)

    def submit_block(self):
        # For now, we're just sending the difficulty level to the blockchain server
        block_data = {'difficulty': self.difficulty}
        try:
            response = requests.post(f"{self.blockchain_server_url}/submit_block", json=block_data)
            if response.status_code == 200:
                print("Block submitted successfully.")
            else:
                print("Failed to submit block.")
        except requests.exceptions.RequestException as e:
            print(f"Error submitting block: {e}")

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

if __name__ == "__main__":
    config = load_config('dsc-config.yaml')
    metronome = Metronome(config)
    metronome.start()

    try:
        # Keep the program running to allow the Metronome to function
        while True:
            time.sleep(1)
    finally:
        metronome.stop()
