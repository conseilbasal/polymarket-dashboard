"""
Approve CTF (Conditional Token Framework) contract for Polymarket trading
This is REQUIRED in addition to USDC approval for CLOB API trading
"""
from dotenv import load_dotenv
import os
from web3 import Web3

load_dotenv()

private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
wallet_address = os.getenv("POLYMARKET_WALLET_ADDRESS")

# Polygon mainnet RPC
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))

# CTF Contract (ERC1155) - Conditional Tokens
CTF_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"

# Exchange contracts to approve
EXCHANGES = {
    "CTF Exchange": "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
    "Neg Risk CTF Exchange": "0xC5d563A36AE78145C45a50134d48A1215220f80a",
    "Neg Risk Adapter": "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"
}

# ERC1155 ABI for setApprovalForAll
CTF_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "operator", "type": "address"},
            {"name": "approved", "type": "bool"}
        ],
        "name": "setApprovalForAll",
        "outputs": [],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "operator", "type": "address"}
        ],
        "name": "isApprovedForAll",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

print("Approving CTF contract for Polymarket exchanges...")
print("=" * 80)
print(f"Wallet: {wallet_address}")
print(f"CTF Contract: {CTF_ADDRESS}")
print()

ctf_contract = w3.eth.contract(address=CTF_ADDRESS, abi=CTF_ABI)

for name, exchange_address in EXCHANGES.items():
    print(f"\n{name}: {exchange_address}")

    # Check if already approved
    is_approved = ctf_contract.functions.isApprovedForAll(wallet_address, exchange_address).call()

    if is_approved:
        print(f"  [OK] Already approved!")
        continue

    print(f"  -> Setting approval...")

    # Build transaction
    nonce = w3.eth.get_transaction_count(wallet_address)

    tx = ctf_contract.functions.setApprovalForAll(
        exchange_address,
        True  # Approve
    ).build_transaction({
        'from': wallet_address,
        'nonce': nonce,
        'gas': 100000,
        'maxFeePerGas': w3.eth.gas_price,
        'maxPriorityFeePerGas': w3.to_wei(30, 'gwei'),
        'chainId': 137
    })

    # Sign transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)

    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"  -> Transaction sent: {tx_hash.hex()}")
    print(f"  -> Waiting for confirmation...")

    # Wait for transaction receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt['status'] == 1:
        print(f"  [SUCCESS] CTF approved for {name}")
        print(f"  -> View on PolygonScan: https://polygonscan.com/tx/{tx_hash.hex()}")
    else:
        print(f"  [FAILED] Transaction reverted.")

print("\n" + "=" * 80)
print("Done! CTF approvals configured. You can now place orders via CLOB API.")
