import threading
import time
import requests
import os
import yaml
from blake3 import blake3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from flask import Flask, request, jsonify
import argparse

app = Flask(__name__)

class Validator:
    def __init__(self, config):
        self.fingerprint = config["validator"]["fingerprint"]
        self.public_key = config["validator"]["public_key"]
        self.proof_config = config["validator"]["proof_config"]
        self.blockchain_server = config["blockchain"]["server_address"]
        self.metronome_server = config["metronome"]["server_address"]
        self.validator_thread = threading.Thread(target=self._validator_loop, daemon=True)
        self.is_running = False
        self.config = config

        self.pos_file_path = os.path.expanduser('~/dsc-pos.vault')
        self.pos_check_mode = False

        if not self.fingerprint or not self.public_key:
            self._generate_and_save_validator_keys()

    def _generate_and_save_validator_keys(self):
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Get public key in OpenSSH format
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        ).decode('utf-8')

        # Calculate fingerprint using Blake3
        fingerprint = blake3(public_key.encode()).hexdigest()

        # Save keys to config file
        self.config["validator"]["fingerprint"] = fingerprint
        self.config["validator"]["public_key"] = public_key

        with open("config.yaml", "w") as config_file:
            yaml.dump(self.config, config_file)

        self.fingerprint = fingerprint
        self.public_key = public_key

    def _validator_loop(self):
        while self.is_running:
            latest_block_hash = self._get_latest_block_hash()
            current_difficulty = self._get_current_difficulty()

            if self.proof_config.get("enable"):
                if self.proof_config["algorithm"] == "pow":
                    proof_result = self._perform_pow(latest_block_hash, current_difficulty)
                elif self.proof_config["algorithm"] == "pom":
                    proof_result = self._perform_pom(latest_block_hash, current_difficulty)
                elif self.proof_config["algorithm"] == "pos":
                    proof_result = self._perform_pos(latest_block_hash, current_difficulty)
                else:
                    print(f"Invalid proof algorithm: {self.proof_config['algorithm']}")
                    break

                if proof_result:
                    print("Proof successful! Block accepted.")
                else:
                    print("Proof failed. Block rejected.")
                
            time.sleep(6)  # Adjust this based on your block time



    def _get_latest_block_hash(self):
        response = requests.get(f"{self.blockchain_server}/get_latest_block_hash")
        return response.text if response.status_code == 200 else None

    def _get_current_difficulty(self):
    # Assuming your config structure is similar to the provided example
      try:
        difficulty = int(config["blockchain"]["difficulty"])
        print(f"Current Difficulty: {difficulty}")
        return difficulty
      except Exception as e:
        print(f"Error getting current difficulty from config.yaml.")
        print(f"Exception: {e}")
        return None
    
    def _perform_pow(self, block_hash, difficulty):
         print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} DSC v1.0")
         print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Proof of Work ({self.proof_config['threads']} threads)")
         print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Fingerprint: {self.fingerprint}")
         print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block X, diff {difficulty}, hash {block_hash}")

         start_time = time.time()
         nonce = self._find_nonce_pow(block_hash, difficulty)
         end_time = time.time()

         if nonce != -1:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block X, NONCE {nonce} ({self._calculate_hash_rate_pow(start_time, end_time)} MH/s)")
            return True
         else:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block X, NONCE -1 ({self._calculate_hash_rate_pow(start_time, end_time)} MH/s)")
            return False

    def _find_nonce_pow(self, block_hash, difficulty):
        start_time = time.time()
        end_time = start_time + 6  # Block time is 6 seconds
        nonce = 0

        while time.time() < end_time:
          nonce = self._calculate_nonce_pow(block_hash, difficulty, nonce, nonce + 2**22)
        if nonce != -1:
            return nonce

        return -1

    def _calculate_nonce_pow(self, block_hash, difficulty, start_nonce, end_nonce):
        for nonce in range(start_nonce, end_nonce + 1):
            data_to_hash = f"{block_hash}{difficulty}{nonce}{self.public_key}"
            hashed_data = blake3(data_to_hash.encode()).hexdigest()
            if hashed_data.startswith('0' * difficulty):
                return nonce

        return -1

    def _calculate_hash_rate_pow(self, start_time, end_time):
        elapsed_time = end_time - start_time
        hash_rate = (2**22) / (1024**2) / elapsed_time  # Hash rate in MH/s
        return round(hash_rate, 2)

    def _perform_pom(self, block_hash, difficulty):
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} DSC v1.0")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Proof of Memory ({self.proof_config['threads']} threads, {self.proof_config['memory']} RAM)")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Fingerprint: {self.fingerprint}")

        start_time = time.time()
        hashes = self._generate_and_organize_hashes_pom()
        end_time = time.time()

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} gen/org {self.proof_config['memory']} hashes ({round(end_time - start_time, 1)} sec ~ {round(self.proof_config['memory'] / (1024**2) / (end_time - start_time), 1)} MB/s)")

        latest_block_hash = self._get_latest_block_hash()
        current_difficulty = self._get_current_difficulty()

        while self.is_running:
            start_time = time.time()
            nonce = self._lookup_prefix_pom(latest_block_hash, current_difficulty, hashes)
            end_time = time.time()

            if nonce != -1:
                print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block X, NONCE {nonce} (lookup {round(end_time - start_time, 3)} sec with {len(hashes)} accesses)")
            else:
                print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block X, NONCE -1 (lookup {round(end_time - start_time, 3)} sec with {len(hashes)} accesses)")

            time.sleep(6)  # Adjust this based on your block time

    def _generate_and_organize_hashes_pom(self):
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} generating hashes [Thread #1]")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} generating hashes [Thread #2]")

        hashes_thread_1 = self._generate_hashes_pom(0, 2**21)
        hashes_thread_2 = self._generate_hashes_pom(2**21 + 1, 2**22)

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} finished generating hashes [Thread #1]")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} finished generating hashes [Thread #2]")

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} sorting hashes")
        start_time = time.time()
        sorted_hashes = sorted(hashes_thread_1 + hashes_thread_2)
        end_time = time.time()

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} finished sorting hashes")

        return sorted_hashes
    
    def _generate_hashes_pom(self, start_nonce, end_nonce):
        hashes = []
        for nonce in range(start_nonce, end_nonce + 1):
            data_to_hash = f"{nonce}{self.public_key}"
            hashed_data = blake3(data_to_hash.encode()).hexdigest()
            hashes.append(hashed_data)
        return hashes


    def _lookup_prefix_pom(self, block_hash, difficulty, hashes):
        prefix = block_hash[:difficulty]
        start_index = 0
        end_index = len(hashes) - 1

        while start_index <= end_index:
            mid_index = (start_index + end_index) // 2
            mid_value = hashes[mid_index][:difficulty]

            if mid_value == prefix:
                return mid_index

            if mid_value < prefix:
                start_index = mid_index + 1
            else:
                end_index = mid_index - 1

        return -1

    def _perform_pos(self, latest_block_hash, current_difficulty):
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Performing Proof of Space Check")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} DSC Validator v1.0 -- Proof of Space ({self.proof_config['threads']} threads, {self.proof_config['storage']} Storage, {self.proof_config['buckets']} buckets, {self.proof_config['bucket_size']} per bucket, {self.proof_config['write_size']} write, {self.proof_config['ram']} RAM)")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Fingerprint: {self.fingerprint}")

        start_time = time.time()
        hashes = self._generate_and_organize_hashes_pos()
        end_time = time.time()

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} gen/org {self.proof_config['storage']} hashes ({round(end_time - start_time, 1)} sec ~ {round(self.proof_config['storage'] / (1024**2) / (end_time - start_time), 1)} MB/s)")

        while self.is_running:
            start_time = time.time()
            nonce = self._lookup_prefix_pos(latest_block_hash, current_difficulty, hashes)
            end_time = time.time()

            if nonce != -1:
                print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block X, NONCE {nonce} (lookup {round(end_time - start_time, 3)} sec with {len(hashes)} accesses)")
                return True  # Assuming Proof of Space check is successful
            else:
                print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block X, NONCE -1 (lookup {round(end_time - start_time, 3)} sec with {len(hashes)} accesses)")

            time.sleep(6)  # Adjust this based on your block time

        return False


    def _generate_and_organize_hashes_pos(self):
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} generating hashes [Thread #1]")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} generating hashes [Thread #2]")

        hashes_thread_1 = self._generate_hashes_pos(0, 2**31)
        hashes_thread_2 = self._generate_hashes_pos(2**31 + 1, 2**32)

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} finished generating hashes [Thread #1]")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} finished generating hashes [Thread #2]")

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} sorting hashes")
        start_time = time.time()
        sorted_hashes = sorted(hashes_thread_1 + hashes_thread_2)
        end_time = time.time()

        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} finished sorting hashes")

        return sorted_hashes

    def _generate_hashes_pos(self, start_nonce, end_nonce):
        hashes = []
        for nonce in range(start_nonce, end_nonce + 1):
            data_to_hash = f"{nonce}{self.public_key}"
            hashed_data = blake3(data_to_hash.encode()).hexdigest()
            hashes.append(hashed_data)
        return hashes
    
    def _lookup_prefix_pos(self, block_hash, difficulty, hashes):
        prefix = block_hash[:difficulty]
        bucket_index = int(prefix, 2)
        start_index = bucket_index * self.proof_config['bucket_size']
        end_index = (bucket_index + 1) * self.proof_config['bucket_size'] - 1

        while start_index <= end_index:
            mid_index = (start_index + end_index) // 2
            mid_value = hashes[mid_index][:difficulty]

            if mid_value == prefix:
                return mid_index

            if mid_value < prefix:
                start_index = mid_index + 1
            else:
                end_index = mid_index - 1

        return -1

@app.route('/start_validator', methods=['POST'])
def start_validator():
    global validator
    validator.start()
    return jsonify({"message": "Validator started."}), 200

@app.route('/stop_validator', methods=['POST'])
def stop_validator():
    global validator
    validator.stop()
    return jsonify({"message": "Validator stopped."}), 200

@app.route('/validate_block', methods=['POST'])
def validate_block():
    global validator
    block_data = request.json.get('block_data')
    is_valid = validator.validate_block(block_data)  # Implement this method
    return jsonify({"is_valid": is_valid}), 200

def load_config():
    with open('config.yaml', 'r') as config_file:
        return yaml.safe_load(config_file)

def pos_check(fingerprint, public_key, blockchain_server, metronome_server):
    parser = argparse.ArgumentParser(description='DSC Validator Proof of Space Checker')
    parser.add_argument('--path', type=str, help='Path to the PoS file')
    parser.add_argument('--disk', type=str, help='Disk size')
    parser.add_argument('--buckets', type=int, help='Number of buckets')
    parser.add_argument('--bucket_size', type=int, help='Bucket size')
    parser.add_argument('--storage', type=int, help='Storage size')  # Include "storage" key
    parser.add_argument('--write_size', type=int, help='Write size')  # Include "write_size" key
    parser.add_argument('--ram', type=int, help= 'ram')
    parser.add_argument('--start', type=int, default=0, help='Starting index for PoS check')
    parser.add_argument('--end', type=int, default=5, help='Ending index for PoS check')

    args = parser.parse_args()

    # Include the 'write_size' key in the proof_config dictionary
    proof_config = {
        "enable": True,
        "algorithm": "pos",
        "threads": 4,
        "storage": args.storage,
        "buckets": args.buckets,
        "bucket_size": args.bucket_size,
        "write_size": args.write_size,  # Include the 'write_size' key
        "ram": args.ram, 
    }

    validator = Validator(fingerprint, public_key, proof_config, blockchain_server, metronome_server)
    validator.pos_file_path = args.path
    validator.pos_check_mode = True

    latest_block_hash = validator._get_latest_block_hash()
    current_difficulty = validator._get_current_difficulty()

    validator._perform_pos(latest_block_hash, current_difficulty)


if __name__ == "__main__":
    config = load_config()
    validator = Validator(config)

    # Run the Flask app
    app.run(port=5007)
    
