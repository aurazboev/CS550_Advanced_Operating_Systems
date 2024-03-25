import base58
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import blake3
import socket
import time
import argparse
import uuid
import requests  # Add this import for making HTTP requests
from flask import Flask, request

app = Flask(__name__)

class Wallet:
    def __init__(self, config_file="config.yaml", key_file="dsc-key.yaml"):
        self.config_file = config_file
        self.key_file = key_file
        self.balance = 10  # Initialize the wallet with a balance of 10 coins

    @app.route('/wallet/<operation>', methods=['POST'])
    def run(self, operation):
        if operation == "create":
            return self.create_wallet()
        elif operation == "key":
            return self.display_keys()
        elif operation == "balance":
            return self.get_balance()
        elif operation == "send":
            data = request.json
            return self.send_transaction(data['amount'], data['recipient_address'])
        elif operation == "transaction":
            transaction_id = request.json['transaction_id']
            return self.check_transaction_status(transaction_id)
        elif operation == "transactions":
            return self.list_transactions()
        elif operation == "help":
            return self.print_help()
        else:
            return {"message": "Invalid operation."}, 400

    def create_wallet(self):
        # Check if wallet already exists
        if self.wallet_exists():
            return {"message": "Wallet already exists."}

        # Generate key pair
        private_key, public_key = self.generate_key_pair()

        # Save keys to files
        self.save_keys(public_key, private_key)

        return {"message": "Wallet created successfully."}

    def display_keys(self):
        try:
            with open(self.key_file, "r") as file:
                keys = yaml.safe_load(file)
                if keys:
                    return {"public_key": keys['public_key'], "private_key": keys['private_key']}
                else:
                    return {"message": "Error in finding key information."}, 404
        except FileNotFoundError:
            return {"message": "Wallet not found. Create a wallet first."}, 404

    def generate_key_pair(self):
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

        # Get private key in PEM format
        private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        return private_key, public_key

    def save_keys(self, public_key, private_key):
        # Hash keys using Blake3
        hashed_public_key = self.hash_data(public_key.encode())
        hashed_private_key = self.hash_data(private_key.encode())

        keys = {"public_key": hashed_public_key, "private_key": hashed_private_key}

        # Save keys to dsc-key.yaml
        with open(self.key_file, "w") as file:
            yaml.dump(keys, file)

        # Save public key to dsc-config.yaml
        config = {"wallet": {"public_key": hashed_public_key}}
        with open(self.config_file, "w") as file:
            yaml.dump(config, file)

    def wallet_exists(self):
        try:
            with open(self.key_file, "r") as file:
                keys = yaml.safe_load(file)
                print("Content of keys:", keys)  # Add this line for debugging
                return keys is not None
        except FileNotFoundError:
            return False

    def hash_data(self, data):
        # Hash data using Blake3
        h = blake3.blake3()
        h.update(data)
        return h.hexdigest()

    def get_balance(self):
        config = self.read_config()
        address = config['wallet']['public_key']
        balance = self.contact_blockchain_server_for_balance(address)
        return {"balance": balance, "message": f"DSC Wallet balance: {balance} coins"}

    def send_transaction(self, amount, recipient_address):
        config = self.read_config()
        transaction_id = str(uuid.uuid4())
        transaction = {
            "transaction_id": transaction_id,
            "amount": amount,
            "recipient_address": recipient_address,
            "sender_address": config['wallet']['public_key']
        }

        # Send the transaction to the mining pool
        pool_address = config['pool']['server_address']
        response = requests.post(f"{pool_address}/submit_transaction", json=transaction)

        if response.status_code == 200:
            return {"transaction_id": transaction_id, "message": "Transaction submitted successfully."}
        else:
            return {"message": "Failed to submit transaction."}, 500

    def check_transaction_status(self, transaction_id):
        # Simulate contacting the pool server to get the transaction status
        # Replace this with actual communication with the pool component
        status = self.contact_pool_for_transaction_status(transaction_id)

        if status == 'unknown':
            # Follow up query to the blockchain
            status = self.contact_blockchain_for_transaction_status(transaction_id)

        print(f"Transaction {transaction_id} status: {status}")

    def list_transactions(self):
        # Simulate contacting the pool server to get the list of transactions
        # Replace this with actual communication with the pool component
        transactions = self.contact_pool_for_transactions()
        print("DSC Wallet transactions:")
        for transaction in transactions:
            print(transaction)

    def contact_blockchain_server_for_balance(self, address):
        try:
            config = self.read_config()
            blockchain_address = config['blockchain']['server_address']

            # Simulate contacting the blockchain server to get the balance
            # Replace this with actual communication with the blockchain component
            response = requests.get(f"{blockchain_address}/get_balance/{address}")

            if response.status_code == 200:
                return float(response.text)  # Assuming the balance is returned as a float
            else:
                return 0.0  # Return 0.0 if there is an error or if the address has no balance
        except requests.RequestException as e:
            print(f"Error contacting blockchain server: {str(e)}")
            return 0.0  # Return 0.0 in case of an exception

    def contact_pool_for_transaction_status(self, transaction_id):
        try:
            config = self.read_config()
            pool_address = config['pool']['server_address']

            # Simulate contacting the pool server to get the transaction status
            # Replace this with actual communication with the pool component
            response = requests.get(f"{pool_address}/transaction_status/{transaction_id}")

            if response.status_code == 200:
                return response.text  # Assuming the status is returned as a string
            else:
                return 'unknown'  # Return 'unknown' if there is an error or if the status is not available
        except requests.RequestException as e:
            print(f"Error contacting mining pool: {str(e)}")
            return 'unknown'  # Return 'unknown' in case of an exception

    def contact_blockchain_for_transaction_status(self, transaction_id):
        try:
            config = self.read_config()
            blockchain_address = config['blockchain']['server_address']

            # Simulate contacting the blockchain server to get the transaction status
            # Replace this with actual communication with the blockchain component
            response = requests.get(f"{blockchain_address}/transaction_status/{transaction_id}")

            if response.status_code == 200:
                return response.text  # Assuming the status is returned as a string
            else:
                return 'unknown'  # Return 'unknown' if there is an error or if the status is not available
        except requests.RequestException as e:
            print(f"Error contacting blockchain server: {str(e)}")
            return 'unknown'  # Return 'unknown' in case of an exception

    def contact_pool_for_transactions(self):
        try:
            config = self.read_config()
            pool_address = config['pool']['server_address']

            # Simulate contacting the pool server to get the list of transactions
            # Replace this with actual communication with the pool component
            response = requests.get(f"{pool_address}/transactions")

            if response.status_code == 200:
                return response.json()  # Assuming transactions are returned in JSON format
            else:
                return []  # Return an empty list if there is an error or if no transactions are available
        except requests.RequestException as e:
            print(f"Error contacting mining pool: {str(e)}")
            return []  # Return an empty list in case of an exception

    def create_transaction_id(self):
        # Simulate creating a transaction ID
        
        return str(uuid.uuid4())

    def print_help(self):
        print("DSC: DataSys Coin Blockchain v1.0")
        print("Help menu for Wallet, supported operations:")
        print("./dsc wallet help")
        print("./dsc wallet create")
        print("./dsc wallet key")
        print("./dsc wallet balance")
        print("./dsc wallet send <amount> <address>")
        print("./dsc wallet transaction <ID>")
        print("./dsc wallet transactions")

if __name__ == "__main__":
    
    app.run(port=5001)
