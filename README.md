# Bitcoin Timelock Assignment Instructions

# Requirements
- Python 3.10+
- Bitcoin Core (configured for regtest)
- Python library: bitcoinutils

# Setup
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

# Running generate_p2sh.py
Generates a P2SH address with an absolute timelock.

Usage:
```
python3 generate_p2sh.py --pubkey <pubkey> --locktime <locktime>
```
- `--pubkey`: Public key.
- `--privkey`: Private key (optional).
- `--locktime`: Block height or UNIX timestamp.


# Running spend_p2sh.py
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


# Testing
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


# Fee calculation for Bitcoin transactions
To estimate the fee for a Bitcoin transaction, the following formula is used:

```
Estimated total Fee = approximate fee per kilobyte × transaction size in kilobytes
```

## Transaction size calculation
The transaction size in bytes is estimated using the following formula:

- **`len(inputs) * 148`**: Each input (spending a UTXO) typically occupies 148 bytes.
- **`+ len(outputs) * 34`**: Each output (sending Bitcoin to a recipient) typically occupies 34 bytes.
- **`+ 10`**: This accounts for fixed transaction overhead, including fields such as the version number, locktime, and other constant data.

For example, for a transaction with 1 input and 1 output:
- **Input size**: `1 * 148 = 148 bytes`
- **Output size**: `1 * 34 = 34 bytes`
- **Overhead**: `+ 10 bytes`

Thus, the estimated transaction size would be:

`148 bytes (input) + 34 bytes (output) + 10 bytes (overhead) = 192 bytes = 0.192 kilobytes`

## Fee per kilobyte estimation

The **approximate fee per kilobyte** is obtained from the Tatum API, which provides up-to-date fee rates for Bitcoin transactions. You can reference the Tatum API [here](https://docs.tatum.io/docs/btc-fee-estimate).

The script provides three fee options:

- **fast**: A higher fee for faster transaction confirmation.
- **medium**: A moderate fee for balanced confirmation time.
- **low**: A lower fee for slower confirmation times.

The **default** option in the current script is **fast**, however, you can change it to any other option by modifying the `FEE_SPEED` field in the `.env` file.

Once the fee rate and transaction size are determined, the estimated fee can be calculated and applied when broadcasting the transaction.

