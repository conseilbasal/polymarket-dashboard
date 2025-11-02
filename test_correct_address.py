"""
Test with the CORRECT address from traders.json
"""

import requests
import json

# Address from traders.json
CORRECT_ADDRESS = "0x75e765216a57942d738d880ffcda854d9f869080"
# Address I was using (WRONG)
WRONG_ADDRESS = "0x00ce0682efd980b2caa0e8d7f7e5290fe4f9df0f"

print("=" * 80)
print("Testing both addresses")
print("=" * 80)

for name, address in [("CORRECT (from traders.json)", CORRECT_ADDRESS), ("WRONG (from my tests)", WRONG_ADDRESS)]:
    print(f"\n{name}:")
    print(f"Address: {address}")

    url = f"https://data-api.polymarket.com/positions?user={address}"
    response = requests.get(url, timeout=10)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        positions = response.json()
        print(f"Positions found: {len(positions)}")

        if positions:
            print("\nRecent positions:")
            for i, pos in enumerate(positions[:5]):
                print(f"\n  Position #{i+1}:")
                print(f"    Market: {pos.get('title', pos.get('market_slug', 'N/A'))}")
                print(f"    Side: {pos.get('outcome', 'N/A')}")
                print(f"    Size: {pos.get('size', 0)} shares")
                print(f"    Value: ${pos.get('value', 0):.2f}")

            # Save for debugging
            with open(f"positions_{name.split()[0]}.json", "w") as f:
                json.dump(positions, f, indent=2)
    else:
        print(f"ERROR: {response.text[:200]}")

print("\n" + "=" * 80)
