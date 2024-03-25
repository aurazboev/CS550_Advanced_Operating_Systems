import threading
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

class MiningPool:
    def __init__(self, config):
        self.blockchain_address = (config['blockchain']['server'], config['blockchain']['port'])
        self.transactions = []
        self.lock = threading.Lock()

    @app.route('/submit_transaction', methods=['POST'])
    def submit_transaction():
        transaction_data = request.json
        print(f"Received transaction: {transaction_data}")

        

        return jsonify({'status': 'Transaction received and confirmed', 'transaction_id': transaction_data.get('transaction_id')}), 200



def run_flask_app(pool_config):
    app.run(host=pool_config['server'], port=pool_config['port'], use_reloader=False, threaded=True)

def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

if __name__ == "__main__":
    config = load_config('dsc-config.yaml')
    pool_config = config['pool']
    blockchain_config = config['blockchain']  
    metronome_config = config['metronome']  

    mining_pool = MiningPool(config)
    
    
    run_flask_app(pool_config)
