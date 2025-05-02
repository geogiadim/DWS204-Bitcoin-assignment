from bitcoinutils.setup import setup
from bitcoinutils.keys import PublicKey, PrivateKey, P2shAddress
from bitcoinutils.script import Script
import argparse
from datetime import datetime, timezone


def check_locktime(locktime):
    locktime = int(locktime)
    # Detect whether locktime is a block height or timestamp for logging
    if locktime < 500000000:
        print(f"[INFO] Using block height locktime: {locktime}")
    else:
        readable_time = datetime.fromtimestamp(locktime, tz=timezone.utc)
        print(f"[INFO] Using UNIX timestamp locktime: {locktime} ({readable_time} UTC)")


def create_absolute_timelock_redeem_script(pub_key, locktime):
    """Manually create a timelock redeem script with OP_CHECKLOCKTIMEVERIFY."""
    locktime = int(locktime)
    # Construct script: <locktime> CLTV DROP DUP HASH160 <pubKeyHash> EQUALVERIFY CHECKSIG
    redeem_script = Script([
        locktime,
        'OP_CHECKLOCKTIMEVERIFY',
        'OP_DROP',
        'OP_DUP',
        'OP_HASH160',
        pub_key.get_address().to_hash160(),
        'OP_EQUALVERIFY',
        'OP_CHECKSIG'
    ])
    return redeem_script

def generate_p2sh(pub_key, locktime):
    """Generate P2SH address from redeem script."""
    # Create reedem script
    redeem_script = create_absolute_timelock_redeem_script(pub_key, locktime)
    # Create P2SH address
    p2sh_addr = P2shAddress.from_script(redeem_script)

    return p2sh_addr, redeem_script

def main():
    # Set up regtest network
    setup('regtest')

    # Parse arguments
    parser = argparse.ArgumentParser(description="Generate a P2SH timelock address")
    # Create a mutually exclusive group to ensure either pubkey or privkey is provided
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pubkey', help="Public key for P2PKH")
    group.add_argument('--privkey', help='Private key (optional, get pubkey from it)')
    parser.add_argument('--locktime', required=True, type=int, help="Locktime (block height or UNIX timestamp)")
    args = parser.parse_args()

    # Check locktime type
    check_locktime(args.locktime)

    try:
        # Get the public key
        if args.privkey:
            private_key = PrivateKey(args.privkey)
            pub_key = private_key.get_public_key()
        else:
            pub_key = PublicKey(args.pubkey)
    except Exception as e:
        print(f"Error getting public key: {e}")
        return

    try:
        # Execute the process
        p2sh_addr, redeem_script = generate_p2sh(pub_key, args.locktime)
        print(f"[INFO] Redeem Script: {redeem_script}")
        print(f"[INFO] Redeem Script in Hex: {redeem_script.to_hex()}")

        print(f"\n### The generated P2SH Address: {p2sh_addr.to_string()}")

    except Exception as e:
        print(f"Error generating P2SH address: {e}")


if __name__ == "__main__":
    main()