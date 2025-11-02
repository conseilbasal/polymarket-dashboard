import requests

# Fetch current positions from API
url = "https://data-api.polymarket.com/positions?user=0x75e765216a57942d738d880ffcda854d9f869080"
response = requests.get(url, timeout=10)

if response.status_code == 200:
    positions = response.json()
    print(f"Total positions from API: {len(positions)}")

    # Find Israel/Gaza position
    for pos in positions:
        slug = pos.get('slug', '').lower()
        if 'israel' in slug and 'gaza' in slug and 'withdraw' in slug:
            print(f"\nIsrael/Gaza position from API:")
            print(f"  Title: {pos.get('title', 'N/A')}")
            print(f"  Slug: {pos.get('slug', 'N/A')}")
            print(f"  Side: {pos.get('outcome', 'N/A')}")
            print(f"  Size: {pos.get('size', 0)} shares")
            print(f"  Avg Price: ${pos.get('avgPrice', 0):.4f}")
            print(f"  Current Value: ${pos.get('currentValue', 0):.2f}")
            print(f"\n  Expected if +79.8 shares added: {5249.248317 + 79.8:.2f} shares")
            break
else:
    print(f"API Error: {response.status_code}")
