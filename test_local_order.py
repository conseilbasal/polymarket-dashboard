"""
Test order placement locally (not through Railway API)
"""
import os
from dotenv import load_dotenv
from clob_client import PolymarketCLOBClient

# Load environment variables from .env
load_dotenv()

# Test token_id (SpaceX launches market - valid token from active market)
token_id = "92192167045106446736607423165653335341855022557438632399181825277019301702561"
market_name = "Will SpaceX have between 180-199 launches in 2025?"
price = 0.10  # 10 cents
amount_usd = 2.00  # 2.00 USD

print("=" * 80)
print("TEST: Place order locally")
print("=" * 80)

# Check if credentials are set
if not os.getenv("POLYMARKET_PRIVATE_KEY"):
    print("\nERROR: POLYMARKET_PRIVATE_KEY not set in .env")
    print("Please add your private key to .env file")
    exit(1)

if not os.getenv("POLYMARKET_WALLET_ADDRESS"):
    print("\nERROR: POLYMARKET_WALLET_ADDRESS not set in .env")
    print("Please add your wallet address to .env file")
    exit(1)

try:
    print("\n1. Initializing CLOB client...")
    clob_client = PolymarketCLOBClient()
    print("   Client initialized!")

    print("\n2. Creating limit order...")
    size = amount_usd / price
    order_data = clob_client.create_limit_order(
        token_id=token_id,
        side='YES',
        order_side='BUY',
        size=size,
        price=price
    )
    print(f"   Order created: BUY {size:.2f} shares @ ${price:.4f}")

    print("\n3. Posting order to Polymarket...")
    from py_clob_client.clob_types import OrderType
    result = clob_client.post_order(order_data, OrderType.GTC)

    print("\n✅ SUCCESS!")
    print(f"   Order ID: {result.get('orderID')}")
    print(f"   Status: {result.get('status')}")

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
