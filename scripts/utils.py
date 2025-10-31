"""
Utility functions for database operations
Now uses the new database.py module for SQLite/PostgreSQL flexibility
"""
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path to import database module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from new database module
from database import (
    init_db as _init_db,
    save_snapshot as _save_snapshot,
    save_capital_snapshot as _save_capital_snapshot,
    SessionLocal,
    PositionHistory,
    CapitalHistory
)
from datetime import datetime, timedelta
from sqlalchemy import func

# Keep DB_PATH for backward compatibility
DB_PATH = Path(__file__).parent.parent / "data" / "positions_history.db"


def init_db():
    """Initialize database - wrapper for backward compatibility"""
    return _init_db()


def save_snapshot(df):
    """Save positions snapshot - wrapper for backward compatibility"""
    return _save_snapshot(df)


def save_capital_snapshot(df, timestamp):
    """Save capital snapshot - wrapper for backward compatibility"""
    return _save_capital_snapshot(df, timestamp)


def get_latest_snapshot():
    """Get latest positions snapshot as DataFrame"""
    db = SessionLocal()
    try:
        # Get the latest timestamp
        latest = db.query(PositionHistory).order_by(
            PositionHistory.updated_at.desc()
        ).first()

        if not latest:
            return pd.DataFrame()

        latest_time = latest.updated_at

        # Get all positions from that timestamp
        positions = db.query(PositionHistory).filter(
            PositionHistory.updated_at == latest_time
        ).all()

        # Convert to DataFrame
        data = [
            {
                'user': p.user,
                'market': p.market,
                'side': p.side,
                'size': p.size,
                'avg_price': p.avg_price,
                'current_price': p.current_price,
                'pnl': p.pnl,
                'updated_at': p.updated_at.isoformat()
            }
            for p in positions
        ]

        return pd.DataFrame(data)
    finally:
        db.close()


def get_trader_history(trader_name, days=7):
    """Get trader history for the last N days"""
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=days)

        positions = db.query(PositionHistory).filter(
            PositionHistory.user == trader_name,
            PositionHistory.updated_at >= cutoff
        ).order_by(PositionHistory.updated_at.desc()).all()

        # Convert to DataFrame
        data = [
            {
                'user': p.user,
                'market': p.market,
                'side': p.side,
                'size': p.size,
                'avg_price': p.avg_price,
                'current_price': p.current_price,
                'pnl': p.pnl,
                'updated_at': p.updated_at.isoformat()
            }
            for p in positions
        ]

        return pd.DataFrame(data)
    finally:
        db.close()


def get_capital_history(trader_name=None, days=30):
    """Get capital history for all traders or a specific trader"""
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=days)

        query = db.query(CapitalHistory).filter(
            CapitalHistory.timestamp >= cutoff
        )

        if trader_name:
            query = query.filter(CapitalHistory.user == trader_name)

        positions = query.order_by(CapitalHistory.timestamp.asc()).all()

        # Convert to DataFrame
        data = [
            {
                'user': p.user,
                'total_capital': p.total_capital,
                'exposure': p.exposure,
                'pnl': p.pnl,
                'positions_count': p.positions_count,
                'timestamp': p.timestamp.isoformat()
            }
            for p in positions
        ]

        return pd.DataFrame(data)
    finally:
        db.close()
