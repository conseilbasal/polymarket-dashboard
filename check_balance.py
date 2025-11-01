"""
Check USDC balance and allowance for the wallet
"""
from dotenv import load_dotenv
import os
from web3 import Web3

load_dotenv()

# Polygon mainnet RPC
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))

wallet_address = os.getenv("POLYMARKET_WALLET_ADDRESS")
print(f"Checking wallet: {wallet_address}")

# USDC contract on Polygon (native USDC)
USDC_ADDRESS = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
# CTF Exchange contract (CLOB)
CTF_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

# USDC ABI (minimal)
USDC_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

print("Checking wallet balance and allowances...")
print("=" * 80)
print(f"Wallet: {wallet_address}")
print()

# Get USDC contract
usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)

# Check balance (USDC has 6 decimals)
balance = usdc_contract.functions.balanceOf(wallet_address).call()
balance_usdc = balance / 1e6

print(f"USDC Balance: ${balance_usdc:.2f}")

# Check allowance for CTF Exchange
allowance = usdc_contract.functions.allowance(wallet_address, CTF_EXCHANGE).call()
allowance_usdc = allowance / 1e6

print(f"Allowance for CLOB: ${allowance_usdc:.2f}")

if balance_usdc < 2:
    print("\nERROR: Not enough USDC balance (need at least $2)")
elif allowance_usdc < 2:
    print("\nERROR: Not enough allowance!")
    print("You need to approve the CTF Exchange contract to spend your USDC.")
    print("Go to Polymarket.com and make a small trade to approve the contract,")
    print("or use the approve_usdc.py script.")
else:
    print("\nSUCCESS: Balance and allowance are sufficient!")
