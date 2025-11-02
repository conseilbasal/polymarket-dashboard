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
import os
from sqlalchemy import text

# Import scheduler for background fetching
from scheduler import start_scheduler, stop_scheduler, get_scheduler_status

# Import database engine for copy trading
from database import engine

# Import copy trading engine
from copy_trading_engine import copy_trading_engine

# Import copy trading database initialization
from init_copy_trading_db import init_copy_trading_tables

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
    # Initialize Copy Trading database tables
    init_copy_trading_tables()

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

@app.get("/api/leaderboard/polymarket")
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
            pnl = float(trader.get("pnl", 0))
            volume = float(trader.get("vol", 0))

            # Calculate ROI: ROI = (PnL / Capital Invested) × 100
            # Capital Invested ≈ Volume - PnL (approximation)
            capital_invested = volume - pnl if volume > pnl else volume
            roi = round((pnl / capital_invested * 100), 1) if capital_invested > 0 else 0

            formatted_leaderboard.append({
                "rank": int(trader.get("rank", 0)),
                "address": trader.get("user_id", ""),
                "username": trader.get("user_name", ""),
                "volume": volume,
                "pnl": pnl,
                "profile_image": trader.get("profile_image", ""),
                "roi": roi,
                "total_trades": None  # Not available from leaderboard API
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

# ====================
# COPY TRADING ENDPOINTS
# ====================

@app.post("/api/copy-trading/enable", dependencies=[Depends(get_current_user)])
async def enable_copy_trading(
    target_trader: str,
    trader_name: str,
    copy_percentage: float
):
    """
    Activer copy trading pour un trader

    Args:
        target_trader: Adresse Ethereum du trader (0x...)
        trader_name: Nom friendly (ex: "25usdc")
        copy_percentage: Pourcentage à copier (0.1-100)

    Returns:
        {"status": "enabled", "config": {...}}
    """
    # Validation
    if not (0.1 <= copy_percentage <= 100):
        raise HTTPException(400, "Percentage must be between 0.1 and 100")

    try:
        # Insérer dans DB
        with engine.connect() as conn:
            # Check if PostgreSQL or SQLite
            is_postgres = str(engine.url).startswith('postgresql')

            if is_postgres:
                query = text("""
                    INSERT INTO copy_trading_config
                    (user_wallet_address, target_trader_address, target_trader_name, copy_percentage, enabled)
                    VALUES (:user_wallet, :target_trader, :trader_name, :percentage, true)
                    ON CONFLICT (user_wallet_address, target_trader_address)
                    DO UPDATE SET
                        copy_percentage = :percentage,
                        enabled = true,
                        updated_at = NOW()
                    RETURNING *
                """)
            else:  # SQLite
                query = text("""
                    INSERT INTO copy_trading_config
                    (user_wallet_address, target_trader_address, target_trader_name, copy_percentage, enabled)
                    VALUES (:user_wallet, :target_trader, :trader_name, :percentage, 1)
                    ON CONFLICT (user_wallet_address, target_trader_address)
                    DO UPDATE SET
                        copy_percentage = :percentage,
                        enabled = 1,
                        updated_at = CURRENT_TIMESTAMP
                """)

            result = conn.execute(query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
                "target_trader": target_trader,
                "trader_name": trader_name,
                "percentage": copy_percentage
            })

            conn.commit()

            # For SQLite, we need to fetch the inserted row separately
            if not is_postgres:
                select_query = text("""
                    SELECT * FROM copy_trading_config
                    WHERE user_wallet_address = :user_wallet
                    AND target_trader_address = :target_trader
                """)
                result = conn.execute(select_query, {
                    "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
                    "target_trader": target_trader
                })

            config = dict(result.fetchone()._mapping)

        return {"status": "enabled", "config": config}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enable copy trading: {str(e)}")


@app.post("/api/copy-trading/disable", dependencies=[Depends(get_current_user)])
async def disable_copy_trading(target_trader: str):
    """Désactiver copy trading pour un trader"""

    try:
        with engine.connect() as conn:
            is_postgres = str(engine.url).startswith('postgresql')

            # Désactiver dans config
            if is_postgres:
                query = text("""
                    UPDATE copy_trading_config
                    SET enabled = false, updated_at = NOW()
                    WHERE user_wallet_address = :user_wallet
                    AND target_trader_address = :target_trader
                """)
            else:  # SQLite
                query = text("""
                    UPDATE copy_trading_config
                    SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE user_wallet_address = :user_wallet
                    AND target_trader_address = :target_trader
                """)

            conn.execute(query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
                "target_trader": target_trader
            })

            # Annuler tous les ordres en attente
            if is_postgres:
                cancel_query = text("""
                    UPDATE pending_copy_orders
                    SET status = 'cancelled', last_updated = NOW()
                    WHERE user_wallet_address = :user_wallet
                    AND target_trader_address = :target_trader
                    AND status IN ('pending', 'partial')
                """)
            else:  # SQLite
                cancel_query = text("""
                    UPDATE pending_copy_orders
                    SET status = 'cancelled', last_updated = CURRENT_TIMESTAMP
                    WHERE user_wallet_address = :user_wallet
                    AND target_trader_address = :target_trader
                    AND status IN ('pending', 'partial')
                """)

            conn.execute(cancel_query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
                "target_trader": target_trader
            })

            conn.commit()

        return {"status": "disabled"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable copy trading: {str(e)}")


@app.get("/api/copy-trading/status", dependencies=[Depends(get_current_user)])
async def get_copy_trading_status():
    """
    Get copy trading status

    Returns:
        {
            "active_configs": [...],
            "pending_orders": [...],
            "total_pnl": float
        }
    """

    try:
        with engine.connect() as conn:
            is_postgres = str(engine.url).startswith('postgresql')

            # Active configs
            if is_postgres:
                configs_query = text("""
                    SELECT *
                    FROM copy_trading_config
                    WHERE user_wallet_address = :user_wallet
                    AND enabled = true
                """)
            else:  # SQLite
                configs_query = text("""
                    SELECT *
                    FROM copy_trading_config
                    WHERE user_wallet_address = :user_wallet
                    AND enabled = 1
                """)

            result = conn.execute(configs_query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
            })

            configs = [dict(row._mapping) for row in result.fetchall()]

            # Pending orders
            orders_query = text("""
                SELECT *
                FROM pending_copy_orders
                WHERE user_wallet_address = :user_wallet
                AND status IN ('pending', 'partial')
                ORDER BY created_at DESC
                LIMIT 100
            """)

            result = conn.execute(orders_query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
            })

            pending_orders = [dict(row._mapping) for row in result.fetchall()]

            # Total PnL from executed trades
            pnl_query = text("""
                SELECT SUM(pnl) as total_pnl
                FROM executed_copy_trades
                WHERE user_wallet_address = :user_wallet
            """)

            result = conn.execute(pnl_query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
            })

            row = result.fetchone()
            total_pnl = float(row[0]) if row and row[0] else 0.0

        return {
            "active_configs": configs,
            "pending_orders": pending_orders,
            "total_pnl": total_pnl
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get copy trading status: {str(e)}")


@app.get("/api/copy-trading/history", dependencies=[Depends(get_current_user)])
async def get_copy_trading_history(days: int = 30):
    """Get copy trading history"""

    try:
        with engine.connect() as conn:
            is_postgres = str(engine.url).startswith('postgresql')

            if is_postgres:
                query = text("""
                    SELECT *
                    FROM executed_copy_trades
                    WHERE user_wallet_address = :user_wallet
                    AND executed_at >= NOW() - INTERVAL ':days days'
                    ORDER BY executed_at DESC
                    LIMIT 1000
                """)
            else:  # SQLite
                query = text("""
                    SELECT *
                    FROM executed_copy_trades
                    WHERE user_wallet_address = :user_wallet
                    AND executed_at >= datetime('now', '-' || :days || ' days')
                    ORDER BY executed_at DESC
                    LIMIT 1000
                """)

            result = conn.execute(query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS"),
                "days": days
            })

            trades = [dict(row._mapping) for row in result.fetchall()]

        return {
            "trades": trades,
            "count": len(trades),
            "total_pnl": sum(float(t.get('pnl', 0) or 0) for t in trades)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get copy trading history: {str(e)}")


@app.get("/api/copy-trading/performance", dependencies=[Depends(get_current_user)])
async def get_copy_trading_performance():
    """Get detailed performance stats"""

    try:
        with engine.connect() as conn:
            is_postgres = str(engine.url).startswith('postgresql')

            # Stats par trader
            if is_postgres:
                query = text("""
                    SELECT
                        target_trader_address,
                        target_trader_name,
                        COUNT(*) as trade_count,
                        SUM(pnl) as total_pnl,
                        AVG(slippage) as avg_slippage,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::float / COUNT(*)::float as win_rate
                    FROM executed_copy_trades
                    WHERE user_wallet_address = :user_wallet
                    GROUP BY target_trader_address, target_trader_name
                """)
            else:  # SQLite
                query = text("""
                    SELECT
                        target_trader_address,
                        target_trader_name,
                        COUNT(*) as trade_count,
                        SUM(pnl) as total_pnl,
                        AVG(slippage) as avg_slippage,
                        CAST(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(*) AS FLOAT) as win_rate
                    FROM executed_copy_trades
                    WHERE user_wallet_address = :user_wallet
                    GROUP BY target_trader_address, target_trader_name
                """)

            result = conn.execute(query, {
                "user_wallet": os.getenv("POLYMARKET_WALLET_ADDRESS")
            })

            stats = [dict(row._mapping) for row in result.fetchall()]

        return {"trader_stats": stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get copy trading performance: {str(e)}")


# ====================
# MARKET EXPLORER ENDPOINTS (PolyDataExplore API)
# ====================

@app.get("/api/markets/explore")
async def get_all_markets():
    """
    Get all markets from PolyDataExplore API
    Includes volume, liquidity, open interest data
    """
    try:
        response = requests.get("https://polydataexplore.org/events", timeout=15)

        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="PolyDataExplore API unavailable")

        events = response.json()

        return {
            "markets": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch markets: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MarketFilterRequest(BaseModel):
    category_exact: str | None = None
    volume24hr_gt: float | None = None
    volume1wk_gt: float | None = None
    volume1mo_gt: float | None = None
    liquidity_gt: float | None = None
    openInterest_gt: float | None = None
    closed: bool | None = None
    featured: bool | None = None


@app.post("/api/markets/filter")
async def filter_markets(filters: MarketFilterRequest):
    """
    Filter markets with advanced criteria
    Returns markets matching all specified filters
    """
    try:
        # Build filter payload
        filter_payload = {}

        if filters.category_exact:
            filter_payload["category_exact"] = filters.category_exact
        if filters.volume24hr_gt is not None:
            filter_payload["volume24hr_gt"] = filters.volume24hr_gt
        if filters.volume1wk_gt is not None:
            filter_payload["volume1wk_gt"] = filters.volume1wk_gt
        if filters.volume1mo_gt is not None:
            filter_payload["volume1mo_gt"] = filters.volume1mo_gt
        if filters.liquidity_gt is not None:
            filter_payload["liquidity_gt"] = filters.liquidity_gt
        if filters.openInterest_gt is not None:
            filter_payload["openInterest_gt"] = filters.openInterest_gt
        if filters.closed is not None:
            filter_payload["closed"] = filters.closed
        if filters.featured is not None:
            filter_payload["featured"] = filters.featured

        response = requests.post(
            "https://polydataexplore.org/events/filter",
            json=filter_payload,
            timeout=15
        )

        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="PolyDataExplore API unavailable")

        markets = response.json()

        return {
            "markets": markets,
            "count": len(markets),
            "filters_applied": filter_payload,
            "timestamp": datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to filter markets: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PriceHistoryRequest(BaseModel):
    ids: list[int]


@app.post("/api/markets/price-history")
async def get_price_history(request: PriceHistoryRequest):
    """
    Get price history for specific market IDs
    Returns historical price data with timestamps
    """
    try:
        response = requests.post(
            "https://polydataexplore.org/price-history/filter_id",
            json={"ids": request.ids},
            timeout=15
        )

        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="PolyDataExplore API unavailable")

        price_history = response.json()

        return {
            "price_history": price_history,
            "market_count": len(price_history),
            "timestamp": datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch price history: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test-order", dependencies=[Depends(get_current_user)])
async def test_limit_order(
    token_id: str,
    price: float = 0.05,  # Default: 5 cents per share
    amount_usd: float = 2.0  # Default: 2 EUR (~2.2 USD)
):
    """
    TEST ENDPOINT: Place a limit order for testing

    Args:
        token_id: Market token ID (YES or NO token)
        price: Price per share (0-1 range, e.g., 0.05 for 5 cents)
        amount_usd: Amount in USD to spend (default: 2.0)

    Returns:
        Order details and status
    """
    try:
        from clob_client import PolymarketCLOBClient
        from py_clob_client.clob_types import OrderType

        # Initialize CLOB client
        clob_client = PolymarketCLOBClient()

        # Calculate number of shares for the given amount
        size = amount_usd / price

        # Create limit order
        order_data = clob_client.create_limit_order(
            token_id=token_id,
            side='YES',  # Assuming YES for test
            order_side='BUY',
            size=size,
            price=price
        )

        # Post the order (pass the full dict, not just order_data['order'])
        result = clob_client.post_order(order_data, OrderType.GTC)

        return {
            "success": True,
            "message": f"Test order placed: BUY {size:.2f} shares @ ${price:.4f}",
            "order_details": {
                "token_id": token_id,
                "size": size,
                "price": price,
                "amount_usd": amount_usd,
                "order_id": result.get('orderID'),
                "status": result.get('status')
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place test order: {str(e)}")


if __name__ == "__main__":
    print("[INFO] Starting Polymarket Copy Trading API Server...")
    print("[INFO] API will be available at http://localhost:8000")
    print("[INFO] Docs at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
