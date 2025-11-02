"""
Check that the wallet address matches the private key
"""
from dotenv import load_dotenv
import os
from eth_account import Account

load_dotenv()

private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
wallet_address = os.getenv("POLYMARKET_WALLET_ADDRESS")

print("Checking wallet credentials...")
print("=" * 80)

if not private_key:
    print("ERROR: POLYMARKET_PRIVATE_KEY not found in .env")
    exit(1)

if not wallet_address:
    print("ERROR: POLYMARKET_WALLET_ADDRESS not found in .env")
    exit(1)

# Derive address from private key
try:
    # Remove '0x' if present
    pk = private_key if not private_key.startswith('0x') else private_key[2:]
    account = Account.from_key('0x' + pk)
    derived_address = account.address

    print(f"\nConfigured wallet address: {wallet_address}")
    print(f"Address derived from private key: {derived_address}")

    if wallet_address.lower() == derived_address.lower():
        print("\nSUCCESS! Wallet address matches private key.")
    else:
        print("\nERROR! Wallet address does NOT match private key!")
        print("Please check your .env file and ensure POLYMARKET_WALLET_ADDRESS")
        print("matches the address derived from your POLYMARKET_PRIVATE_KEY.")

except Exception as e:
    print(f"\nError checking credentials: {e}")
    import traceback
    traceback.print_exc()
