import base58
import yaml
import requests  # Added to make HTTP requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import blake3
import time
import argparse
import uuid
from flask import Flask, jsonify, request

app = Flask(__name__)

class Wallet:
    def __init__(self, config_file="dsc-config.yaml", key_file="dsc-key.yaml"):
        self.config_file = config_file
        self.key_file = key_file
        config = self.read_config()
        if config:
            self.blockchain_server_url = f"http://{config['blockchain']['server']}:{config['blockchain']['port']}"
            self.pool_server_url = f"http://{config['pool']['server']}:{config['pool']['port']}"
        else:
            self.blockchain_server_url = 'http://localhost:5002'
            self.pool_server_url = 'http://localhost:5000'
    
    def read_config(self):
        try:
            with open(self.config_file, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print("Error reading configuration file.")
            return None

    def get_balance(self, address):
        # Connect to blockchain Server to retrieve balance
        response = requests.get(f"{self.blockchain_server_url}/get_balance", params={'address': address})
        if response.status_code == 200:
            balance = response.json().get('balance', 0)
        else:
            balance = 0
        return balance

    def run(self):
        parser = argparse.ArgumentParser(description="Wallet operations", prog="./dsc wallet")
        parser.add_argument("operation", nargs="?", default="create", help="Supported operations: create, key, balance, send, transaction, transactions, help")
        args = parser.parse_args()

        if args.operation == "create":
            self.create_wallet()
        elif args.operation == "key":
            self.display_keys()
        elif args.operation == "balance":
            address = self.read_config()['wallet']['public_key']
            balance = self.get_balance(address)
            print(f"DSC Wallet balance: {balance} coins")
        elif args.operation == "send":
            amount = input("Enter the amount to send: ")
            recipient_address = input("Enter the recipient address: ")
            self.send_transaction(amount, recipient_address)
        elif args.operation == "transaction":
            transaction_id = input("Enter the transaction ID: ")
            self.check_transaction_status(transaction_id)
        elif args.operation == "transactions":
            self.list_transactions()
        elif args.operation == "help":
            self.print_help()
        else:
            print("Invalid operation. Use './dsc wallet help' for supported operations.")

    def create_wallet(self):
        # Check if wallet already exists
        if self.wallet_exists():
           print("Wallet already exists.")
           return

        # Generate key pair
        private_key, public_key = self.generate_key_pair()

        # Save keys to files
        self.save_keys(public_key, private_key)

        print("Wallet created successfully.")
    

    def wallet_exists(self):
        try:
         with open(self.key_file, "r") as file:
            keys = yaml.safe_load(file)
            print("Content of keys:", keys)  # Add this line for debugging
            return keys is not None
        except FileNotFoundError:
         return False

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

    def display_keys(self):
     try:
        with open(self.key_file, "r") as file:
            keys = yaml.safe_load(file)
            if keys and 'public_key' in keys:
                print(f"DSC Public Address: {keys['public_key']}")
                print(f"DSC Private Address: {keys['private_key']}")
            else:
                print("Error in finding key information.")
     except FileNotFoundError:
        print("Error in finding key information. Run `./dsc wallet create` to create a wallet.")

    def hash_data(self, data):
        # Hash data using Blake3
        h = blake3.blake3()
        h.update(data)
        return h.hexdigest()

    def send_transaction(self, amount, recipient_address):
        transaction_id = self.create_transaction_id()
        print(f"Created transaction {transaction_id}, Sending {amount} coins to {recipient_address}")

        # Construct the transaction data
        transaction_data = {
            'transaction_id': transaction_id,
            'amount': amount,
            'recipient_address': recipient_address
        }

        # URL of the pool's transaction submission endpoint
        pool_url = f"{self.pool_server_url}/submit_transaction"

        # Send the transaction to the pool
        try:
            response = requests.post(pool_url, json=transaction_data)
            if response.status_code == 200:
                print(f"Transaction {transaction_id} submitted to the pool.")
                status = 'unconfirmed'
            else:
                print(f"Failed to submit transaction {transaction_id} to the pool.")
                return
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to the pool: {e}")
            return

        # Wait for confirmation (this is a simplified example)
        while status != 'confirmed':
            print(f"Transaction {transaction_id} status [{status}]")
            # In a real application, you would check the transaction status with the pool here
            time.sleep(1)  # Waiting for a fixed time before checking again
            status = 'confirmed'  # Simulate receiving confirmation

        print(f"Transaction {transaction_id} status [confirmed]")

    def check_transaction_status(self, transaction_id):
        # Should work on contacting the pool server and get the status 
        status = self.contact_pool_for_transaction_status(transaction_id)

        if status == 'unknown':
            # Follow up query to the blockchain
            status = self.contact_blockchain_for_transaction_status(transaction_id)

        print(f"Transaction {transaction_id} status: {status}")

    def list_transactions(self):
        # Should work on connection with pool server and get list of transcations 
        transactions = self.contact_pool_for_transactions()
        print("DSC Wallet transactions:")
        for transaction in transactions:
            print(transaction)

    def contact_blockchain_server_for_balance(self, address):
        # Should connect to blockchain server to get balance and replace the default
        balance = 0.0  # assume the balance is 0.0
        return balance

    def contact_pool_for_transaction_status(self, transaction_id):
        # Simulate contacting the pool server to get the transaction status
        # Replace this with actual communication with the pool component
        return 'confirmed'  # For now, assume the status becomes confirmed after some time

    def contact_blockchain_for_transaction_status(self, transaction_id):
        # Simulate contacting the blockchain server to get the transaction status
        # Replace this with actual communication with the blockchain component
        return 'confirmed'  # For now, assume the status becomes confirmed after some time

    def contact_pool_for_transactions(self):
        # Simulate contacting the pool server to get the list of transactions
        # Replace this with actual communication with the pool component
        transactions = ['Transaction 1', 'Transaction 2', 'Transaction 3']
        return transactions

    def create_transaction_id(self):
        # creating a transaction ID using uuid 
    
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
    Wallet().run()