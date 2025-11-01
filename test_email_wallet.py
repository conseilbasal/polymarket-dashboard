"""
Test order placement with signature_type=1 (Email/Magic wallet)
"""
from dotenv import load_dotenv
import os
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderType

load_dotenv()

private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
wallet_address = os.getenv("POLYMARKET_WALLET_ADDRESS")

# Test token_id (SpaceX launches market)
token_id = "92192167045106446736607423165653335341855022557438632399181825277019301702561"
price = 0.10  # 10 cents
amount_usd = 2.00  # 2.00 USD
size = amount_usd / price

print("=" * 80)
print("TEST: Email/Magic Wallet with signature_type=1")
print("=" * 80)

try:
    print("\n1. Initializing CLOB client with signature_type=1...")

    # Initialize with signature_type=1 (Email/Magic wallet)
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137,
        signature_type=1,  # Email/Magic wallet
        funder=wallet_address  # The proxy wallet that holds funds
    )

    print("   Client initialized!")

    print("\n2. Deriving API credentials...")
    api_creds = client.create_or_derive_api_creds()
    print("   API credentials derived!")

    print("\n3. Setting API credentials...")
    client.set_api_creds(api_creds)
    print("   API credentials set!")

    print("\n4. Creating limit order...")
    from py_clob_client.order_builder.constants import BUY
    from py_clob_client.clob_types import OrderArgs

    order_args = OrderArgs(
        token_id=token_id,
        price=price,
        size=size,
        side=BUY
    )

    signed_order = client.create_order(order_args)
    print(f"   Order created: BUY {size:.2f} shares @ ${price:.4f}")

    print("\n5. Posting order to Polymarket...")
    result = client.post_order(signed_order, OrderType.GTC)

    print("\n[SUCCESS]!")
    print(f"   Order ID: {result.get('orderID')}")
    print(f"   Status: {result.get('status')}")

except Exception as e:
    print(f"\n[ERROR]: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
