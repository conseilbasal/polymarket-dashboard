"""
API Server FastAPI simple pour le dashboard Copy Trading
Lit les CSV et expose les données via API
Lance avec: python api_server.py ou uvicorn api_server:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import json
import uvicorn
from pydantic import BaseModel
import subprocess
import sys
import sqlite3
import requests

# Import scheduler for background fetching
from scheduler import start_scheduler, stop_scheduler, get_scheduler_status

# Import authentication
from auth import (
    LoginRequest,
    Token,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="Polymarket Copy Trading API", version="1.0.0")

# Startup event - start background scheduler
@app.on_event("startup")
async def startup_event():
    """Start the background scheduler on application startup"""
    print("[SCHEDULER] Starting background data fetcher...")
    start_scheduler()
    print("[SCHEDULER] Background scheduler started successfully")

# Shutdown event - stop scheduler gracefully
@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background scheduler on application shutdown"""
    print("[SCHEDULER] Stopping background scheduler...")
    stop_scheduler()
    print("[SCHEDULER] Scheduler stopped")

# CORS - Autoriser le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production: mettre l'URL exacte
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemins
BASE_DIR = Path(__file__).parent
SNAPSHOTS_DIR = BASE_DIR / "data" / "snapshots"
CONFIG_DIR = BASE_DIR / "config"
TRADERS_FILE = CONFIG_DIR / "traders.json"
FETCH_SCRIPT = BASE_DIR / "scripts" / "fetch_positions.py"
DB_PATH = BASE_DIR / "data" / "positions_history.db"

# Pydantic models
class TraderAdd(BaseModel):
    name: str
    address: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/auth/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Login endpoint - returns JWT token for authentication
    """
    if not verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"authenticated": True},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/scheduler/status")
async def get_scheduler_status_endpoint():
    """Get status of background scheduler"""
    return get_scheduler_status()

@app.post("/api/refresh", dependencies=[Depends(get_current_user)])
async def refresh_positions():
    """Déclenche la récupération des positions depuis Polymarket"""
    try:
        print(f"[REFRESH] Lancement du script de récupération des positions...")

        # Lancer le script fetch_positions.py
        result = subprocess.run(
            [sys.executable, str(FETCH_SCRIPT)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes max
        )

        if result.returncode != 0:
            print(f"[ERROR] Script failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch positions: {result.stderr}"
            )

        print(f"[REFRESH] Script terminé avec succès")

        # Récupérer le dernier snapshot après le fetch
        snapshots = sorted(SNAPSHOTS_DIR.glob("positions_*.csv"))
        if not snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found after refresh")

        # Charger les nouvelles données
        df = pd.read_csv(snapshots[-1])

        # Compter par trader
        trader_counts = df.groupby('user').size().to_dict()

        return {
            "status": "success",
            "message": "Positions refreshed successfully",
            "timestamp": datetime.now().isoformat(),
            "snapshot": snapshots[-1].name,
            "total_positions": len(df),
            "traders": trader_counts,
            "output": result.stdout
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Refresh timeout - took more than 2 minutes")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions/latest", dependencies=[Depends(get_current_user)])
async def get_latest_positions():
    """Get latest positions from last snapshot"""
    try:
        snapshots = sorted(SNAPSHOTS_DIR.glob("positions_*.csv"))

        if not snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found")

        # Charger le dernier snapshot
        df = pd.read_csv(snapshots[-1])

        return {
            "timestamp": snapshots[-1].stem.split('_', 1)[1],
            "positions": df.to_dict(orient="records"),
            "count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/copy-trading/comparison", dependencies=[Depends(get_current_user)])
async def get_copy_trading_comparison(
    target_trader: str = "25usdc",
    user_trader: str = "Shunky",
    copy_percentage: float = 10.0
):
    """Get copy trading comparison and actions needed"""
    try:
        snapshots = sorted(SNAPSHOTS_DIR.glob("positions_*.csv"))

        if not snapshots:
            raise HTTPException(status_code=404, detail="No snapshots found")

        # Charger le dernier snapshot
        df = pd.read_csv(snapshots[-1])

        # Filtrer par traders
        df_target = df[df['user'] == target_trader].copy()
        df_user = df[df['user'] == user_trader].copy()

        if df_target.empty:
            raise HTTPException(status_code=404, detail=f"Trader {target_trader} not found")
        if df_user.empty:
            raise HTTPException(status_code=404, detail=f"Trader {user_trader} not found")

        # Merger et calculer la comparaison
        comparison = df_target[['market', 'side', 'size', 'avg_price', 'current_price', 'pnl']].merge(
            df_user[['market', 'side', 'size', 'avg_price', 'current_price', 'pnl']],
            on=['market', 'side'],
            how='outer',
            suffixes=('_target', '_user')
        )

        # Remplir les NaN
        comparison = comparison.fillna(0)

        # Appliquer le pourcentage de copy trading
        comparison['target_size'] = comparison['size_target'] * (copy_percentage / 100)
        comparison['target_avg_price'] = comparison['avg_price_target']

        # Calculer les montants investis
        comparison['invested_target'] = comparison['target_size'] * comparison['target_avg_price']
        comparison['invested_user'] = comparison['size_user'] * comparison['avg_price_user']

        # Calculer les deltas
        comparison['delta_shares'] = comparison['target_size'] - comparison['size_user']
        comparison['delta_invested'] = comparison['invested_target'] - comparison['invested_user']

        # Déterminer les actions
        def get_action(delta):
            if delta > 0.01:
                return "BUY"
            elif delta < -0.01:
                return "SELL"
            return "HOLD"

        comparison['action'] = comparison['delta_shares'].apply(get_action)

        # Filtrer les actions nécessaires
        actions_needed = comparison[comparison['action'].isin(['BUY', 'SELL'])].copy()
        actions_needed = actions_needed.sort_values('delta_shares', key=lambda x: x.abs(), ascending=False)

        # Calculer les métriques
        exposure_target = (df_target['size'] * df_target['avg_price']).sum()
        exposure_user = (df_user['size'] * df_user['avg_price']).sum()

        # Préparer les résultats
        result = {
            "timestamp": datetime.now().isoformat(),
            "target_trader": target_trader,
            "user_trader": user_trader,
            "copy_percentage": copy_percentage,
            "metrics_target": {
                "positions": int(len(df_target)),
                "exposure": float(exposure_target),
                "pnl": float(df_target['pnl'].sum())
            },
            "metrics_user": {
                "positions": int(len(df_user)),
                "exposure": float(exposure_user),
                "pnl": float(df_user['pnl'].sum())
            },
            "metrics_delta": {
                "positions": int(len(df_target) - len(df_user)),
                "exposure": float(exposure_target - exposure_user),
                "pnl": float(df_target['pnl'].sum() - df_user['pnl'].sum())
            },
            "actions": [
                {
                    "market": str(row['market']),
                    "side": str(row['side']),
                    "action": str(row['action']),
                    "delta_shares": float(row['delta_shares']),
                    "delta_invested": float(row['delta_invested']),
                    "avg_price_25usdc": float(row['avg_price_target']),
                    "avg_price_shunky": float(row['avg_price_user']),
                    "current_price": float(row['current_price_target']) if row['current_price_target'] > 0 else float(row['current_price_user']),
                    "pnl_25usdc": float(row['pnl_target']) if row['pnl_target'] != 0 else 0.0,
                    "pnl_shunky": float(row['pnl_user']) if row['pnl_user'] != 0 else 0.0,
                    "target_size": float(row['target_size']),
                    "size_shunky": float(row['size_user'])
                }
                for _, row in actions_needed.iterrows()
            ],
            "actions_count": {
                "buy": int(len(actions_needed[actions_needed['action'] == 'BUY'])),
                "sell": int(len(actions_needed[actions_needed['action'] == 'SELL']))
            }
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")  # Debug
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/traders", dependencies=[Depends(get_current_user)])
async def get_traders():
    """Get list of all traders from config"""
    try:
        with open(TRADERS_FILE, 'r') as f:
            config = json.load(f)

        traders = config.get("TRADERS", [])

        # Get latest snapshot for stats
        snapshots = sorted(SNAPSHOTS_DIR.glob("positions_*.csv"))
        if snapshots:
            df = pd.read_csv(snapshots[-1])

            # Add stats for each trader
            for trader in traders:
                trader_df = df[df['user'] == trader['name']]
                if not trader_df.empty:
                    trader['stats'] = {
                        'positions': int(len(trader_df)),
                        'exposure': float((trader_df['size'] * trader_df['avg_price']).sum()),
                        'pnl': float(trader_df['pnl'].sum())
                    }
                else:
                    trader['stats'] = {
                        'positions': 0,
                        'exposure': 0,
                        'pnl': 0
                    }

        return {"traders": traders}
    except FileNotFoundError:
        return {"traders": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/traders", dependencies=[Depends(get_current_user)])
async def add_trader(trader: TraderAdd):
    """Add a new trader to config"""
    try:
        # Load existing config
        try:
            with open(TRADERS_FILE, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {"TRADERS": []}

        traders = config.get("TRADERS", [])

        # Check if trader already exists
        if any(t['address'].lower() == trader.address.lower() for t in traders):
            raise HTTPException(status_code=400, detail="Trader already exists")

        # Add new trader
        traders.append({
            "name": trader.name,
            "address": trader.address.lower()
        })

        config["TRADERS"] = traders

        # Save config
        with open(TRADERS_FILE, 'w') as f:
            json.dump(config, f, indent=4)

        return {"message": "Trader added successfully", "trader": trader}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/traders/{address}", dependencies=[Depends(get_current_user)])
async def delete_trader(address: str):
    """Delete a trader from config"""
    try:
        with open(TRADERS_FILE, 'r') as f:
            config = json.load(f)

        traders = config.get("TRADERS", [])

        # Filter out the trader
        new_traders = [t for t in traders if t['address'].lower() != address.lower()]

        if len(new_traders) == len(traders):
            raise HTTPException(status_code=404, detail="Trader not found")

        config["TRADERS"] = new_traders

        with open(TRADERS_FILE, 'w') as f:
            json.dump(config, f, indent=4)

        return {"message": "Trader deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/traders/{address}/stats", dependencies=[Depends(get_current_user)])
async def get_trader_stats(address: str):
    """Get detailed stats for a specific trader"""
    try:
        # Find trader name from address
        with open(TRADERS_FILE, 'r') as f:
            config = json.load(f)

        traders = config.get("TRADERS", [])
        trader = next((t for t in traders if t['address'].lower() == address.lower()), None)

        if not trader:
            raise HTTPException(status_code=404, detail="Trader not found")

        # Get latest snapshot
        snapshots = sorted(SNAPSHOTS_DIR.glob("positions_*.csv"))
        if not snapshots:
            raise HTTPException(status_code=404, detail="No data available")

        df = pd.read_csv(snapshots[-1])
        trader_df = df[df['user'] == trader['name']]

        if trader_df.empty:
            return {
                "name": trader['name'],
                "address": trader['address'],
                "stats": {
                    "positions": 0,
                    "exposure": 0,
                    "pnl": 0
                },
                "positions": []
            }

        return {
            "name": trader['name'],
            "address": trader['address'],
            "stats": {
                "positions": int(len(trader_df)),
                "exposure": float((trader_df['size'] * trader_df['avg_price']).sum()),
                "pnl": float(trader_df['pnl'].sum())
            },
            "positions": trader_df.to_dict(orient="records")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/capital-history", dependencies=[Depends(get_current_user)])
async def get_capital_history_endpoint(trader: str = None, days: int = 30):
    """Get capital evolution history for traders"""
    try:
        if not DB_PATH.exists():
            raise HTTPException(status_code=404, detail="Database not found")

        conn = sqlite3.connect(DB_PATH)

        if trader:
            query = f"""
                SELECT * FROM capital_history
                WHERE user = ?
                AND datetime(timestamp) >= datetime('now', '-{days} days')
                ORDER BY timestamp ASC
            """
            df = pd.read_sql(query, conn, params=(trader,))
        else:
            query = f"""
                SELECT * FROM capital_history
                WHERE datetime(timestamp) >= datetime('now', '-{days} days')
                ORDER BY timestamp ASC
            """
            df = pd.read_sql(query, conn)

        conn.close()

        if df.empty:
            return {"history": [], "traders": []}

        # Group by trader
        result = {}
        for user in df['user'].unique():
            user_df = df[df['user'] == user].sort_values('timestamp')
            result[user] = user_df.to_dict(orient="records")

        return {
            "history": result,
            "traders": list(df['user'].unique())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leaderboard/polymarket", dependencies=[Depends(get_current_user)])
async def get_polymarket_leaderboard(limit: int = 100):
    """
    Get Polymarket leaderboard (top traders by PnL)
    Fetches real-time data from Polymarket API

    Args:
        limit: Number of traders to return (default: 100)
    """
    try:
        # Fetch leaderboard from Polymarket API
        response = requests.get("https://data-api.polymarket.com/leaderboard", timeout=10)

        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="Polymarket API unavailable")

        leaderboard = response.json()

        # Limit results
        if limit and limit > 0:
            leaderboard = leaderboard[:limit]

        # Format for frontend
        formatted_leaderboard = []
        for trader in leaderboard:
            formatted_leaderboard.append({
                "rank": int(trader.get("rank", 0)),
                "address": trader.get("user_id", ""),
                "username": trader.get("user_name", ""),
                "volume": float(trader.get("vol", 0)),
                "pnl": float(trader.get("pnl", 0)),
                "profile_image": trader.get("profile_image", "")
            })

        return {
            "traders": formatted_leaderboard,
            "count": len(formatted_leaderboard),
            "timestamp": datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch leaderboard: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("[INFO] Starting Polymarket Copy Trading API Server...")
    print("[INFO] API will be available at http://localhost:8000")
    print("[INFO] Docs at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
