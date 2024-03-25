import yaml
import os
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from blake3 import blake3
import time
from flask import Flask, request, jsonify


app = Flask(__name__)



class PoW:
    def __init__(self, config):
        self.fingerprint = config["validator"]["fingerprint"]
        self.public_key = config["validator"]["public_key"]
        self.proof_config = config["validator"]["proof_pow"]
        self.threads = self.proof_config.get("threads", 2)

    def _hash_input(self, block_hash, difficulty, nonce):
        input_data = block_hash + str(difficulty) + str(nonce) + self.public_key
        return blake3(input_data.encode()).hexdigest()

    def perform_pow(self, block_hash, block_id, difficulty):
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} DSC v1.0")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Proof of Work ({self.proof_config['threads']} threads)")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Fingerprint: {self.fingerprint}")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block {block_id}, diff {difficulty}, hash {block_hash}")

        start_time = time.time()
        nonce = self.find_nonce(block_hash, difficulty)
        end_time = time.time()
        hash_rate = self.calculate_hash_rate(start_time, end_time)

        if nonce != -1:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block {block_id}, NONCE {nonce} ({hash_rate} MH/s)")
            return True,nonce, hash_rate
        else:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} block {block_id}, NONCE -1 ({hash_rate} MH/s)")
            return False

    def find_nonce(self, block_hash, difficulty):
        start_time = time.time()
        end_time = start_time + 6 # Block time is 6 seconds
        nonce = 0

        while time.time() < end_time:
            hash_output = self._hash_input(block_hash, difficulty, nonce)
            if hash_output.startswith('0' * difficulty):
                return nonce
            nonce += 1

        return -1

    def calculate_hash_rate(self, start_time, end_time):
        elapsed_time = end_time - start_time
        hash_rate = (2**22) / (1024**2) / elapsed_time  # Hash rate in MH/s
        return round(hash_rate, 2)


class PoM:
    def __init__(self, config):
        self.fingerprint = config["validator"]["fingerprint"]
        self.public_key = config["validator"]["public_key"]
        self.proof_config = config["validator"]["proof_pom"]

    def _convert_memory_to_bytes(self, memory_string):
        # Converts memory string like '1G' to bytes
        units = {"K": 1024, "M": 1024**2, "G": 1024**3}
        unit = memory_string[-1]  # Last character for unit
        num = int(memory_string[:-1])  # All but the last character for number
        return num * units.get(unit.upper(), 1)  # Default to bytes if no unit

    def _hash_input(self, nonce):
        input_data = self.fingerprint + self.public_key + str(nonce)
        return blake3(input_data.encode()).hexdigest()

    def calculate_hash_rate(self, start_time, end_time, total_hashes):
        elapsed_time = end_time - start_time
        hash_rate = total_hashes / elapsed_time  # Hashes per second
        return round(hash_rate, 2)

    
    def perform_pom(self, block_hash,  difficulty):
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} DSC v1.0")
        memory_bytes = self._convert_memory_to_bytes(self.proof_config['memory'])
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Proof of Memory ({self.proof_config['threads']} threads, {self.proof_config['memory']} RAM)")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Fingerprint: {self.fingerprint}")

        start_time = time.time()
        hashes = self.generate_and_organize_hashes()
        end_time = time.time()

        hash_rate = self.calculate_hash_rate(start_time, end_time, len(hashes))
        nonce = self.lookup_prefix(block_hash, difficulty, hashes)
        if nonce != -1:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Block hash found, NONCE: {nonce}, Hash Rate: {hash_rate} H/s")
            return True, nonce, hash_rate
        else:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Block hash not found, NONCE: -1, Hash Rate: {hash_rate} H/s")
            return False

    def generate_and_organize_hashes(self):
        # Hash generation logic
        hashes = []
        for nonce in range(0, 2**22):
            hashes.append(self._hash_input(nonce))
        print("Hash generation complete.")

        # Sorting logic
        print("Sorting hashes.")
        return sorted(hashes)

    def lookup_prefix(self, block_hash, difficulty, hashes):
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
    

class PoS:
    def __init__(self, config,validator_id):
        self.config = config
        self.validator_id = validator_id
        self.fingerprint = config["validator"]["fingerprint"]
        self.public_key = config["validator"]["public_key"]
        self.proof_config = config["validator"]["proof_pos"]
        self.vault_path = self.proof_config.get("vault", f"./default_vault_{self.validator_id}.yaml")
        self.buckets = self.proof_config["buckets"]
        self.cup_size = self.proof_config["cup_size"]
        self.cups_per_bucket = self.proof_config["cups_per_bucket"]

        # Check and generate vault file if not present
        self.check_and_generate_vault()

    def check_and_generate_vault(self):
        if not os.path.exists(self.vault_path):
            print(f"Vault file not found at {self.vault_path}. Generating new vault.")
            self.generate_to_file()
            # Update the path in the config
            self.config["validator"]["proof_pos"]["vault"] = self.vault_path
            self.save_config()

    def save_config(self):
        with open(self.config_path, 'w') as file:
            yaml.dump(self.config, file)

    def _hash_input(self, nonce):
        input_data = self.fingerprint + self.public_key + str(nonce)
        return blake3(input_data.encode()).hexdigest()

    def generate_to_file(self):
        # Calculate the total number of hashes to generate
        total_hashes = self.buckets * self.cup_size * self.cups_per_bucket

        with open(self.vault_path, 'wb') as file:
            for i in range(total_hashes):
                hash_output = self._hash_input(i)
                prefix = int(hash_output[0:2], 16)  # First byte as prefix
                # Write hash and nonce to the file
                data = f'{prefix:02x}:{hash_output}:{i}\n'
                file.write(data.encode())

    def calculate_hash_rate(self, start_time, end_time, total_hashes):
        elapsed_time = end_time - start_time
        hash_rate = total_hashes / elapsed_time  # Hashes per second
        return round(hash_rate, 2)
    
    def _perform_pos(self, latest_block_hash, current_difficulty):
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Performing Proof of Space Check")
        print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} DSC Validator v1.0 -- Proof of Space")

        start_time = time.time()
        nonce = self.lookup(latest_block_hash, current_difficulty)
        end_time = time.time()

        hash_rate = self.calculate_hash_rate(start_time, end_time, self.buckets * self.cup_size * self.cups_per_bucket)
        if nonce != -1:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Block hash found, NONCE: {nonce}, Hash Rate: {hash_rate} H/s")
            return True, nonce, hash_rate
        else:
            print(f"{time.strftime('%Y%m%d %H:%M:%S.%f')} Block hash not found, NONCE: -1, Hash Rate: {hash_rate} H/s")
            return False

    def lookup(self, target_hash, difficulty):
        target_prefix = int(target_hash[0:2], 16)

        with open(self.vault_path, 'rb') as file:
            for line in file:
                prefix, hash_output, nonce = line.decode().strip().split(':')
                if int(prefix, 16) == target_prefix:
                    if hash_output.startswith(target_hash[:difficulty]):
                        return int(nonce)
        return -1

    


class Validator:
    def __init__(self, validator_id):
        self.validator_id = validator_id
        self.config_path = f'validator{validator_id}.yaml'  # Store the config file path
        self.config = self.load_config(self.config_path)
        self.ensure_fingerprint_and_key()
        self.blockchain_server = self.config['blockchain']['server_address']
        self.metronome_server = self.config['metronome']['server_address']
        self.pow = PoW(self.config)
        self.pom = PoM(self.config)
        self.pos = PoS(self.config, self.validator_id)
        self.is_running = False


    def run(self):
        while self.is_running:
            latest_block_hash, block_id = self.get_latest_block_info()
            if latest_block_hash:
                print(f"Latest Block Hash: {latest_block_hash}")
                difficulty = self.get_current_difficulty()
                proof_result = self.perform_proof(latest_block_hash, block_id, difficulty)
                if proof_result is not None:
                    proof_type, nonce, hash_rate = proof_result
                    self.notify_metronome_validator_win(proof_type, nonce, hash_rate)
            time.sleep(30)  # Sleep for the block interval

    
    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def ensure_fingerprint_and_key(self):
       # Check if 'fingerprint' or 'public_key' is not in the 'validator' section of the config
     if 'fingerprint' not in self.config['validator'] or 'public_key' not in self.config['validator']:
        # Generate a new private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Extract the public key in OpenSSH format
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        
        # Generate the fingerprint using blake3
        fingerprint = blake3(public_key).hexdigest()

        # Update the config dictionary under the 'validator' section
        self.config['validator']['fingerprint'] = fingerprint
        self.config['validator']['public_key'] = public_key.decode()

        # Save the updated config to the YAML file
        self.save_config()

    def save_config(self):
        with open(self.config_path, 'w') as file:
            yaml.dump(self.config, file)


    def start(self):
        if not self.is_running:
            self.is_running = True
            print("Validator started.")
        else:
            print("Validator is already running.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            print("Validator stopped.")
        else:
            print("Validator is not running.")
    
    
    
    def get_latest_block_info(self):
      response = requests.get(f"{self.blockchain_server}/get_latest_block_hash")
      if response.status_code == 200:
         data = response.json()
         return data["latest_block_hash"], data["block_id"]
      return None, None

    def get_current_difficulty(self):
        # Assuming difficulty is a fixed value for now
        return self.config.get('difficulty', 2)

    def perform_proof(self, latest_block_hash, block_id, difficulty):
        if self.config.get('validator', {}).get('proof_pow', {}).get('enable', False):
            proof_success, nonce, hash_rate = self.pow.perform_pow(latest_block_hash, block_id, difficulty)
            if proof_success:
                return "pow", nonce, hash_rate
        elif self.config.get('validator', {}).get('proof_pom', {}).get('enable', False):
            proof_success, nonce, hash_rate = self.pom.perform_pom(latest_block_hash, difficulty)
            if proof_success:
                return "pom", nonce, hash_rate
        elif self.config.get('validator', {}).get('proof_pos', {}).get('enable', False):
            proof_success, nonce, hash_rate = self.pos.perform_pos(latest_block_hash, difficulty)
            if proof_success:
                return "pos", nonce, hash_rate

        return None

    def register_with_metronome(self):
        data = {
            "validator_id": self.validator_id,
            "fingerprint": self.config["validator"]["fingerprint"]
        }
        response = requests.post(f"{self.metronome_server}/register_validator", json=data)
     

    
    def notify_metronome_validator_win(self, proof_type, nonce, hash_rate):
      data = {
          "validator_id": self.validator_id,
          "proof_type": proof_type,
          "nonce": nonce,
          "hash_rate": hash_rate
        }
      response = requests.post(f"{self.metronome_server}/report_statistics", json=data)


@app.route('/validate_and_mine', methods=['POST'])
def validate_and_mine():
    latest_block_hash, block_id = validator.get_latest_block_info()
    difficulty = validator.get_current_difficulty()
    proof_result = validator.perform_proof(latest_block_hash, block_id, difficulty)
    if proof_result is not None:
        proof_type, nonce, hash_rate = proof_result
        validator.notify_metronome_validator_win(proof_type, nonce, hash_rate)
        return jsonify({"message": "Validation successful"})
    else:
        return jsonify({"error": "Proof failed"}), 400

# Main execution
if __name__ == "__main__":
   if __name__ == "__main__":
    validator_id = 1  # Set this based on the specific validator instance
    validator = Validator(validator_id)
    validator.register_with_metronome()
    print("Validator Running")
    validator.start()
    try:
        validator.run()
    except KeyboardInterrupt:
        print("Stopping Validator")
        validator.stop()

    
    