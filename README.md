# Bitcoin Timelock Assignment Instructions

# Requirements
- Python 3.10+
- Bitcoin Core (configured for regtest)
- Python library: bitcoinutils

Setup
-----
1. Install Bitcoin Core and configure for regtest:
   - Create ~/.bitcoin/bitcoin.conf with:
     ```
     regtest=1
     rpcuser=test
     rpcpassword=test
     rpcport=18443
     ```
   - Start regtest node:
     ```
     bitcoind -regtest -daemon
     ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Generate a keypair for testing:
   ```
   bitcoin-cli -regtest getnewaddress
   bitcoin-cli -regtest dumpprivkey <address>
   ```

Running generate_p2sh.py
-----------------------
Generates a P2SH address with an absolute timelock.

Usage:
```
python3 generate_p2sh.py --pubkey <pubkey> --locktime <locktime>
```
- `--pubkey`: Public key.
- `--privkey`: Private key (optional).
- `--locktime`: Block height or UNIX timestamp.


Running spend_p2sh.py
---------------------
Spends funds from the P2SH address to a P2PKH address.

Usage:
```
python spend_p2sh.py --pubkey <pubkey_hex> --privkey <privkey_wif> --locktime <locktime> [--block-height] --p2sh-addr <p2sh_addr> --dest-addr <p2pkh_addr>
```
- `--pubkey`: Public key.
- `--privkey`: Private key in WIF format.
- `--locktime`: Same locktime used in generate_p2sh.py.
- `--p2sh-addr`: P2SH address from generate_p2sh.py.
- `--p2pkh-addr`: P2PKH address to send funds to.


Testing
-------
1. Run generate_p2sh.py to get a P2SH address.
2. Send funds to the P2SH address:
   ```
   bitcoin-cli -regtest sendtoaddress <p2sh_addr> 1.0
   ```
3. If using block height, mine blocks:
   ```
   bitcoin-cli -regtest generate 101
   ```
4. Run spend_p2sh.py to spend the funds.

Notes
-----
- Fee calculation assumes 10 sat/byte for simplicity.
- Ensure the regtest node is running before executing scripts.
- Scripts handle multiple UTXOs.