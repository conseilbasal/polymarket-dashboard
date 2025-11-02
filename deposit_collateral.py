"""
Deposit USDC as collateral in Polymarket CTF system
"""
from dotenv import load_dotenv
from clob_client import PolymarketCLOBClient

load_dotenv()

try:
    print("Initializing CLOB client...")
    client = PolymarketCLOBClient()

    print("\nDepositing $2 USDC as collateral...")

    # The py-clob-client should handle depositing collateral
    # Let's check the current collateral balance first
    try:
        balance_info = client.client.get_balance_allowance(client.wallet_address)
        print(f"\nCurrent collateral balance: {balance_info}")
    except Exception as e:
        print(f"Could not fetch balance: {e}")

    # Try to get collateral address and check balance
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))

    # CTF Collateral contract (wrapped USDC for Polymarket)
    CTF_COLLATERAL = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"  # Polymarket CTF collateral

    CTF_ABI = [
        {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': 'balance', 'type': 'uint256'}], 'type': 'function'}
    ]

    ctf_contract = w3.eth.contract(address=CTF_COLLATERAL, abi=CTF_ABI)
    ctf_balance = ctf_contract.functions.balanceOf(client.wallet_address).call()

    print(f"\nCTF Collateral balance: ${ctf_balance / 1e6:.2f}")

    if ctf_balance < 2e6:  # Less than $2
        print("\nYou need to deposit USDC as collateral on Polymarket.")
        print("Go to https://polymarket.com and make a small trade to automatically wrap your USDC.")
        print("Or you need to call the deposit function on the CTF contract.")
    else:
        print("\nYou have sufficient CTF collateral!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
