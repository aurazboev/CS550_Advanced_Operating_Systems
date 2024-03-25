import threading
import time
import requests
import blake3
from flask import Flask, jsonify

app = Flask(__name__)

class Monitor:
    def __init__(self, blockchain_server, metronome_server, validator_server):
        self.blockchain_server = blockchain_server
        self.metronome_server = metronome_server
        self.validator_server = validator_server
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.is_running = False

    @app.route('/start_monitor', methods=['POST'])
    def start_monitor(self):
        if not self.is_running:
            self.is_running = True
            print("Monitor started.")
            self.monitor_thread.start()
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Monitor is already running."})

    @app.route('/stop_monitor', methods=['POST'])
    def stop_monitor(self):
        if self.is_running:
            self.is_running = False
            print("Monitor stopped.")
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Monitor is not running."})

    def _monitor_loop(self):
        while self.is_running:
            # Monitor blockchain health
            blockchain_health = self._get_blockchain_health()
            print(f"Blockchain Health: {blockchain_health}")

            # Monitor metronome metrics
            metronome_metrics = self._get_metronome_metrics()
            print(f"Metronome Metrics: {metronome_metrics}")

            # Monitor validator status
            validator_status = self._get_validator_status()
            print(f"Validator Status: {validator_status}")

            time.sleep(10)  # Adjust this based on your monitoring interval

    def _get_blockchain_health(self):
        try:
            response = requests.get(f"{self.blockchain_server}/get_health")
            if response.status_code == 200:
                # Use Blake3 to hash the response for added security
                return blake3.blake3(response.text.encode()).hexdigest()
            else:
                return "Error fetching blockchain health."
        except requests.RequestException as e:
            return f"Error fetching blockchain health: {str(e)}"

    def _get_metronome_metrics(self):
        try:
            response = requests.get(f"{self.metronome_server}/get_metrics")
            if response.status_code == 200:
                # Use Blake3 to hash the response for added security
                return blake3.blake3(response.text.encode()).hexdigest()
            else:
                return "Error fetching metronome metrics."
        except requests.RequestException as e:
            return f"Error fetching metronome metrics: {str(e)}"

    def _get_validator_status(self):
        try:
            response = requests.get(f"{self.validator_server}/get_status")
            if response.status_code == 200:
                # Use Blake3 to hash the response for added security
                return blake3.blake3(response.text.encode()).hexdigest()
            else:
                return "Error fetching validator status."
        except requests.RequestException as e:
            return f"Error fetching validator status: {str(e)}"


if __name__ == "__main__":
    blockchain_server = "http://localhost:5002"  # Replace with your blockchain server address
    metronome_server = "http://localhost:5003"  # Replace with your metronome server address
    validator_server = "http://localhost:5007"  # Replace with your validator server address

    monitor = Monitor(blockchain_server, metronome_server, validator_server)
    app.run(port=5008)
