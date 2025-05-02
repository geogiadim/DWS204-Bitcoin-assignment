from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, P2pkhAddress, P2shAddress
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.script import Script
import argparse
import requests
import os
from dotenv import load_dotenv
from generate_p2sh import create_absolute_timelock_redeem_script, check_locktime


def fetch_fee_rate_per_kilobyte(speed='fast'):
    """
    Fetch current Bitcoin fee rate in satoshis per kilobyte from Tatum API.
    speed: 'slow', 'medium', or 'fast'
    """
    try:
        headers = {
            'x-api-key': os.getenv('TATUM_API_KEY')
        }
        response = requests.get("https://api.tatum.io/v3/blockchain/fee/BTC", headers=headers)
        response.raise_for_status()
        data = response.json()

        fee_rate_per_kilobyte = float(data[speed]) * 1000 # fee rate (satoshis) per kilobyte
        print(f"[INFO] Current {speed} fee rate: {fee_rate_per_kilobyte} satoshis per kilobyte")

        return fee_rate_per_kilobyte
    except Exception as e:
        print(f"Error fetching fee from Tatum API: {e}")
    

def validate_and_get_args(args):
    # Check locktime type using the same function as in generate_p2sh.py
    check_locktime(args.locktime)

    # Validate addresses
    try:
        p2sh_addr = P2shAddress(args.p2sh_addr)
        p2pkh_addr = P2pkhAddress(args.p2pkh_addr)
    except Exception as e:
        print(f"Invalid given address: {e}")
        return

    try:
        # Get the public key
        private_key = PrivateKey(args.privkey)
        pub_key = private_key.get_public_key()
    except Exception as e:
        print(f"Error getting public key: {e}")
        return

    return pub_key, private_key, p2sh_addr, p2pkh_addr


def get_utxos(p2sh_addr, rpc):
    """Query local regtest to retrieve UTXOs for the given P2SH address."""
    try:
        unspent = rpc.listunspent(0, 9999999, [p2sh_addr])
        for utxo in unspent:
            utxo['amount'] = to_satoshis(utxo['amount'])
        return unspent
    except Exception as e:
        print(f"Error fetching UTXOs: {e}")
        return []
    

def calculate_transaction_fee(tx_size, fee_rate=1):
    """Calculate the transaction fee based on the size and fee rate."""
    return tx_size * fee_rate


def create_raw_transaction(utxos, p2pkh_address):
    """Create raw transaction."""
    inputs = []
    outputs = []
    total_input = 0

    for utxo in utxos:
        inputs.append(TxInput(utxo['txid'], utxo['vout']))
        total_input += utxo['amount']
    
    # Formula: (len(inputs) * 148) + (len(outputs) * 34) + 10
    # Assume 1 outputs: 1 to P2PKH recipient, no change output since we are spending all UTXOs
    input_count = len(inputs)
    output_count = 1
    tx_size_kilo_bytes = ((input_count * 148) + (output_count * 34) + 10) / 1000
    total_fee = int(fetch_fee_rate_per_kilobyte() * tx_size_kilo_bytes)

    print(f"[INFO] Estimated transaction size: {tx_size_kilo_bytes} kilobytes")
    print(f"[INFO] Estimated fee: {total_fee} satoshis")

    amount_to_send = total_input - total_fee
    if amount_to_send <= 0:
        raise Exception("Fee exceeds total input amount.")
    outputs.append(TxOutput(amount_to_send, p2pkh_address.to_script_pub_key()))

    # Create transaction
    tx = Transaction(inputs, outputs)

    return tx


def sign_transaction(tx, private_key, redeem_script):
    """Sign the transaction."""
    for i in range(len(tx.inputs)):
        sig = private_key.sign_input(tx, i, redeem_script)
        tx.inputs[i].script_sig = Script([sig, redeem_script.to_hex()])
    return tx


# def send_transaction(tx):
#     """Send the signed transaction to the blockchain."""
#     raw_tx = tx.serialize()
#     txid = Network().broadcast_transaction(raw_tx)
#     return txid
    

def main():
    # Load environment variables from .env
    load_dotenv()
    # Set up regtest network
    setup('regtest')
    # Connect to local regtest node
    rpc = NodeProxy(os.getenv('RPCUSER'), os.getenv('RPCPASSWORD'), port=os.getenv('RPCPORT')).get_proxy()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Spend from a P2SH timelock address")
    parser.add_argument('--privkey', required=True, help="Private key in WIF format for P2PKH")
    parser.add_argument('--locktime', required=True, type=int, help="Locktime (block height or UNIX timestamp)")
    parser.add_argument('--p2sh-addr', required=True, help="P2SH address to spend from")
    parser.add_argument('--p2pkh-addr', required=True, help="P2PKH address to send funds to")
    args = parser.parse_args()
    
    # Validate and get arguments
    pub_key, private_key, p2sh_addr, p2pkh_addr = validate_and_get_args(args)
    
    # create the redeem script using the same function as in generate_p2sh.py
    redeem_script = create_absolute_timelock_redeem_script(pub_key, args.locktime)

    # Check if there are any UTXOs in the P2SH address and get them
    utxos = get_utxos(args.p2sh_addr, rpc)

    # Create the raw transaction
    tx = create_raw_transaction(utxos, p2pkh_addr)
    print(f"\n### Raw Unsigned Transaction: {tx.serialize()}")

    # Sign the transaction
    signed_tx = sign_transaction(tx, private_key, redeem_script)
    print(f"\n### Signed Raw Transaction: {signed_tx.serialize()}")
    print(f"\n### Transaction ID (txid): {signed_tx.get_txid()}")
    
    # Verify the transaction
    try:
        rpc.testmempoolaccept([signed_tx.serialize()])
        print("[INFO] Transaction is valid and ready to be sent.")
    except Exception as e:
        print(f"[ERROR] Transaction verification failed: {e}")
        return

    # Send transaction
    try:
        txid = rpc.sendrawtransaction(signed_tx.serialize())
        print(f"Transaction ID: {txid}")
    except Exception as e:
        print(f"Failed to broadcast transaction: {e}")

if __name__ == "__main__":
    main()