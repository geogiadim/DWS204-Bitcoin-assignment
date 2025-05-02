# Bitcoin Timelock Assignment
This project consists of two Python scripts that implement a Bitcoin time-locked P2SH address mechanism using a local Regtest network:

1. **Lock Script**: Generates a Pay-to-Script-Hash (P2SH) Bitcoin address with an **absolute time-locking redeem script**. Funds sent to this address are locked until a specific block height or UNIX timestamp.

2. **Spend Script**: Spends **all funds received by the time-locked P2SH address** and sends them to a specified **P2PKH address**, once the time-lock condition is met.


Both scripts were built using the [`bitcoin-utils`](https://github.com/karask/python-bitcoin-utils) library.

# Table of Contents

- [Overview](#bitcoin-timelock-assignment)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Running generate_p2sh.py](#running-generate_p2shpy)
- [Running spend_p2sh.py](#running-spend_p2shpy)
- [Testing](#testing)
- [Fee Calculation for Bitcoin Transactions](#fee-calculation-for-bitcoin-transactions)

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
      ```sh
      bitcoind -regtest -daemon
      ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Environment Variables

For efficiency and configurability, the scripts rely on environment variables defined in a `.env` file. Below is an explanation of each variable:

- **`TATUM_API_KEY`**: Sets the API key used to interact with the [Tatum API](https://docs.tatum.io/docs/btc-fee-estimate) for Bitcoin fee estimation. You can keep the provided key or use your own.

- **`FEE_SPEED`**: Declares the desired transaction fee category from the Tatum API. Available options are:
  - `fast` (default)
  - `medium`
  - `slow`

   The selected fee speed determines the estimated fee per kilobyte applied during transaction creation and broadcast.

- **`RPCUSER`, `RPCPASSWORD`, `RPCPORT`**: Configuration values for connecting to your local Bitcoin Regtest node. These should match the corresponding fields in your `bitcoin.conf` file.

**Note**: All environment variables are utilized only in `spend_p2sh.py` script. 

To set the `.env` file run the following command.
```
cp example.env .env
```

# Running generate_p2sh.py
Generates a P2SH address with an absolute timelock.

Usage:
```sh
python3 generate_p2sh.py --pubkey <pubkey> --locktime <locktime>
```
or
```sh
python3 generate_p2sh.py --privkey <privkey> --locktime <locktime>
```
- `--pubkey`: Public key.
- `--privkey`: Private key (optional).
- `--locktime`: Block height or UNIX timestamp.

**Note**: You can specify either the `--pubkey` or the `--privkey` option, but not both. They are mutually exclusive, and you must define only one of them.

# Running spend_p2sh.py
Spends all funds from the P2SH address to a P2PKH address.

Usage:
```sh
python3 spend_p2sh.py --privkey <privkey> --locktime <locktime> --p2sh-addr <p2sh_addr> --p2pkh-addr <p2pkh_addr>
```
- `--privkey`: Private key associated with the P2SH address.
- `--locktime`: The same locktime used in generate_p2sh.py.
- `--p2sh-addr`: P2SH address generated from generate_p2sh.py.
- `--p2pkh-addr`: The destination P2PKH address to receive the funds. In **regtest**, this should be a **legacy address** starting with `m` or `n`. You can generate one using:

   ```sh
   bitcoin-cli -regtest getnewaddress "" legacy
   ```

**Note**:  
The `spend_p2sh.py` script uses the `create_absolute_timelock_redeem_script` function from `generate_p2sh.py` to reconstruct the redeem script. Therefore, **both scripts must be located in the same folder** to ensure proper execution.

# Testing
1. **Generate a P2PKH address and its private key:**
   ```sh
   bitcoin-cli getnewaddress
   bitcoin-cli dumpprivkey <address>
   ```
2. **Run `generate_p2sh.py` to create a P2SH address with an absolute timelock.**
3. **Send funds to the generated P2SH address:**
   ```
   bitcoin-cli sendtoaddress <p2sh_addr> 10.0
   ```

   **Note**: Repeat this step with different amounts if you want to create multiple UTXOs.
4. **Make the funds spendable:**

   - If you're using block height as the locktime, mine enough blocks:
      ```
      bitcoin-cli generatetoaddress <num_blocks> <p2pkh_addr>
      ```
   - If you're using a UNIX timestamp, wait until the specified time has passed.
5. **Run `spend_p2sh.py` to spend the funds to a P2PKH address.**
   
   **Note**: Get the transaction id (txid) from the output of the script.
6. **Check the transaction in the mempool:**
   ```sh
   bitcoin-cli getrawtransaction <txid> true
   ```
7. **Mine a block to confirm the transaction:**
   ```sh
   bitcoin-cli generatetoaddress 1 <miner_address>
   ```



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

