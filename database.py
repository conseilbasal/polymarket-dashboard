"""
Database module using SQLAlchemy for flexibility between SQLite and PostgreSQL
"""
import os
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from pathlib import Path

# Get DATABASE_URL from environment variable, or default to SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).parent / 'data' / 'positions_history.db'}"
)

# Fix for Railway PostgreSQL URL (psycopg2 driver)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debug logs
    pool_pre_ping=True,  # Verify connections before using them
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Define models
class PositionHistory(Base):
    __tablename__ = "positions_history"

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    market = Column(Text)
    side = Column(String)
    size = Column(Float)
    avg_price = Column(Float)
    current_price = Column(Float)
    pnl = Column(Float)
    updated_at = Column(DateTime, index=True)


class CapitalHistory(Base):
    __tablename__ = "capital_history"

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    total_capital = Column(Float)
    exposure = Column(Float)
    pnl = Column(Float)
    positions_count = Column(Integer)
    timestamp = Column(DateTime, index=True)


def init_db():
    """Initialize database tables"""
    # Create data directory if using SQLite
    if "sqlite" in DATABASE_URL:
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"[OK] Database initialized: {DATABASE_URL}")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper functions for backwards compatibility with existing code
def save_snapshot(df):
    """Save positions snapshot to database (pandas DataFrame)"""
    if df.empty:
        print("[WARNING] No data to save")
        return

    db = SessionLocal()
    try:
        for _, row in df.iterrows():
            position = PositionHistory(
                user=row['user'],
                market=row['market'],
                side=row['side'],
                size=row['size'],
                avg_price=row['avg_price'],
                current_price=row['current_price'],
                pnl=row['pnl'],
                updated_at=datetime.fromisoformat(row['updated_at']) if isinstance(row['updated_at'], str) else row['updated_at']
            )
            db.add(position)

        db.commit()
        print(f"[OK] Saved {len(df)} positions to database")
    except Exception as e:
        print(f"[ERROR] Failed to save snapshot: {e}")
        db.rollback()
    finally:
        db.close()


def save_capital_snapshot(df, timestamp):
    """Save capital snapshot to database"""
    if df.empty:
        print("[WARNING] No data to calculate capital")
        return

    db = SessionLocal()
    try:
        # Calculate capital for each trader
        for user in df['user'].unique():
            user_df = df[df['user'] == user]
            exposure = (user_df['size'] * user_df['avg_price']).sum()
            pnl = user_df['pnl'].sum()
            total_capital = exposure + pnl
            positions_count = len(user_df)

            # Convert numpy types to Python native types for PostgreSQL compatibility
            capital = CapitalHistory(
                user=str(user),
                total_capital=float(total_capital),
                exposure=float(exposure),
                pnl=float(pnl),
                positions_count=int(positions_count),
                timestamp=datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
            )
            db.add(capital)

        db.commit()
        print(f"[OK] Saved capital snapshot for {len(df['user'].unique())} traders")
    except Exception as e:
        print(f"[ERROR] Failed to save capital snapshot: {e}")
        db.rollback()
    finally:
        db.close()


def get_latest_snapshot_dict():
    """Get latest positions snapshot as list of dicts (for API)"""
    db = SessionLocal()
    try:
        # Get the latest timestamp
        latest = db.query(PositionHistory).order_by(PositionHistory.updated_at.desc()).first()
        if not latest:
            return []

        latest_time = latest.updated_at

        # Get all positions from that timestamp
        positions = db.query(PositionHistory).filter(
            PositionHistory.updated_at == latest_time
        ).all()

        return [
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
    finally:
        db.close()


def get_capital_history_dict(days=30):
    """Get capital history as dict (for API)"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

        positions = db.query(CapitalHistory).filter(
            CapitalHistory.timestamp >= cutoff
        ).order_by(CapitalHistory.timestamp.asc()).all()

        # Group by user
        result = {}
        for p in positions:
            if p.user not in result:
                result[p.user] = []
            result[p.user].append({
                'total_capital': p.total_capital,
                'exposure': p.exposure,
                'pnl': p.pnl,
                'positions_count': p.positions_count,
                'timestamp': p.timestamp.isoformat()
            })

        return result
    finally:
        db.close()


if __name__ == "__main__":
    # Test database initialization
    init_db()
    print("Database tables created successfully!")
