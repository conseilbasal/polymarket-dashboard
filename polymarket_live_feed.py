import requests
import time
import csv
import json
import os
from datetime import datetime
from random import uniform

BASE_DATA = "https://gamma-api.polymarket.com"
BASE_CLOB = "https://clob.polymarket.com"
CACHE_FILE = "market_cache.json"
CSV_FILE = "polymarket_prices.csv"

# ---------- Utils ----------
def safe_get(url, retries=3, timeout=10):
    """GET avec retry et gestion d'erreur simple"""
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[!] Erreur {type(e).__name__} sur {url}")
        time.sleep(1.5 * (attempt + 1))
    return None

# ---------- Etape 1 : recuperer les marches ----------
def get_markets():
    print("Recuperation des marches actifs...")
    markets = safe_get(f"{BASE_DATA}/markets?limit=500")
    if not markets:
        raise Exception("Impossible de recuperer la liste des marches.")
    return [m for m in markets if not m.get("closed")]

# ---------- Etape 2 : cache local des token_ids ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def update_cache():
    cache = load_cache()
    markets = get_markets()

    for m in markets:
        q = m["question"]
        for o in m["outcomes"]:
            token = o["token_id"]
            name = o["name"]
            cache[token] = {"market": q, "outcome": name}
    save_cache(cache)
    print(f"Cache mis a jour avec {len(cache)} tokens.")
    return cache

# ---------- Etape 3 : lecture du carnet d'ordres ----------
def get_orderbook(token_id):
    ob = safe_get(f"{BASE_CLOB}/orderbook?token_id={token_id}")
    if not ob:
        return None, None
    best_bid = ob["bids"][0]["price"] if ob["bids"] else None
    best_ask = ob["asks"][0]["price"] if ob["asks"] else None
    return best_bid, best_ask

# ---------- Etape 4 : exporter vers CSV ----------
def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "market", "outcome", "bid", "ask"])

def append_csv(row):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

# ---------- Boucle principale ----------
def main_loop():
    cache = update_cache()
    init_csv()

    while True:
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - mise a jour des prix...")
        for token_id, info in cache.items():
            bid, ask = get_orderbook(token_id)
            if bid or ask:
                append_csv([
                    datetime.utcnow().isoformat(),
                    info["market"],
                    info["outcome"],
                    bid,
                    ask
                ])
                print(f"   {info['market'][:40]:40s} | {info['outcome']:5s} | bid={bid} | ask={ask}")
            time.sleep(uniform(0.2, 0.4))  # eviter le spam API
        print("Cycle termine. Attente avant prochaine mise a jour...\n")
        time.sleep(10)  # toutes les 10 secondes

# ---------- Execution ----------
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nArret manuel.")
