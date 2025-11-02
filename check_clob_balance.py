"""
Check balance via Polymarket CLOB API
"""
from dotenv import load_dotenv
from clob_client import PolymarketCLOBClient

load_dotenv()

try:
    print("Initializing CLOB client...")
    client = PolymarketCLOBClient()

    print(f"\nWallet: {client.wallet_address}")
    print("\nFetching balance from Polymarket CLOB API...")

    # Try to get balance via CLOB API
    try:
        # Get all balances
        balances = client.client.get_balance_allowance()
        print(f"\nBalance response: {balances}")
    except Exception as e:
        print(f"Error getting balance: {e}")

    # Try alternative method - check open orders
    try:
        orders = client.client.get_orders()
        print(f"\nOpen orders: {orders}")
    except Exception as e:
        print(f"Error getting orders: {e}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
