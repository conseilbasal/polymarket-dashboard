"""
Find a valid token_id from an active Polymarket market
"""
from dotenv import load_dotenv
from clob_client import PolymarketCLOBClient

load_dotenv()

try:
    print("Initializing CLOB client...")
    client = PolymarketCLOBClient()

    print("\nFetching market data...")
    # Get sampling of markets
    markets_data = client.client.get_sampling_markets()

    # Check if it's a dict or list
    if isinstance(markets_data, dict):
        # If dict, might have a 'data' key or similar
        markets = markets_data.get('data', [markets_data])
    else:
        markets = markets_data if isinstance(markets_data, list) else [markets_data]

    print(f"\nFound {len(markets)} markets\n")
    print("=" * 80)

    # Find first market with valid tokens
    for i, market in enumerate(markets[:5] if len(markets) > 5 else markets):
        print(f"\nMarket {i+1}:")
        print(f"  Question: {market.get('question', 'N/A')[:60]}...")
        print(f"  Condition ID: {market.get('condition_id', 'N/A')}")

        # Get tokens
        tokens = market.get('tokens', [])
        if tokens:
            for token in tokens:
                outcome = token.get('outcome', 'N/A')
                token_id = token.get('token_id', 'N/A')
                print(f"  Token ({outcome}): {token_id}")

            # Save first valid token for testing
            if i == 0 and len(tokens) > 0:
                test_token = tokens[0]['token_id']
                test_market = market.get('question', 'Unknown')
                print(f"\n\nPREMIER TOKEN VALIDE POUR TEST:")
                print(f"  Market: {test_market}")
                print(f"  Token ID: {test_token}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
