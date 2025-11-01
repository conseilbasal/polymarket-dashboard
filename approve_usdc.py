"""
Approve USDC spending for Polymarket CTF Exchange
"""
from dotenv import load_dotenv
import os
from web3 import Web3

load_dotenv()

private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
wallet_address = os.getenv("POLYMARKET_WALLET_ADDRESS")

# Polygon mainnet RPC
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))

# USDC contracts on Polygon (both old and new)
USDC_ADDRESSES = {
    "USDC (native)": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "USDC.e (bridged)": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
}

# CTF Exchange contract (CLOB)
CTF_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

# USDC ABI (minimal)
USDC_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

print("Approving USDC for Polymarket CTF Exchange...")
print("=" * 80)
print(f"Wallet: {wallet_address}")
print(f"CTF Exchange: {CTF_EXCHANGE}")
print()

# Check which USDC you have
for name, usdc_address in USDC_ADDRESSES.items():
    usdc_contract = w3.eth.contract(address=usdc_address, abi=USDC_ABI)
    balance = usdc_contract.functions.balanceOf(wallet_address).call()
    balance_usdc = balance / 1e6

    print(f"{name}: ${balance_usdc:.2f}")

    if balance_usdc > 0:
        print(f"  -> Approving unlimited USDC spending...")

        # Approve unlimited (max uint256)
        max_approval = 2**256 - 1

        # Build transaction
        nonce = w3.eth.get_transaction_count(wallet_address)

        tx = usdc_contract.functions.approve(
            CTF_EXCHANGE,
            max_approval
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
            print(f"  -> SUCCESS! USDC approved.")
            print(f"  -> View on PolygonScan: https://polygonscan.com/tx/{tx_hash.hex()}")
        else:
            print(f"  -> FAILED! Transaction reverted.")

        print()

print("=" * 80)
print("Done! You can now place orders on Polymarket.")
