"""
Background scheduler for automatic Polymarket data fetching
Runs as part of the FastAPI application
"""
import os
import requests
import pandas as pd
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import save_snapshot, save_capital_snapshot, init_db
from copy_trading_engine import copy_trading_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "traders.json"
SNAPSHOTS_DIR = BASE_DIR / "data" / "snapshots"

# Initialize
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Get fetch interval from environment (default: 5 minutes)
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "5"))


def fetch_polymarket_positions():
    """
    Fetch positions from Polymarket API and save to database
    This runs automatically in the background
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled Polymarket data fetch")

        # Load traders config
        if not CONFIG_PATH.exists():
            logger.error(f"Traders config not found: {CONFIG_PATH}")
            return

        with open(CONFIG_PATH) as f:
            traders_config = json.load(f)["TRADERS"]

        # Parse traders list
        traders_list = []
        for trader in traders_config:
            if isinstance(trader, dict):
                traders_list.append(trader)

        if not traders_list:
            logger.warning("No traders configured")
            return

        trader_names = [t['name'] for t in traders_list]
        logger.info(f"Tracking {len(traders_list)} traders: {', '.join(trader_names)}")

        records = []
        errors = []

        # Fetch positions for each trader
        for trader_config in traders_list:
            trader_name = trader_config['name']
            trader_address = trader_config['address']

            try:
                url = f"https://data-api.polymarket.com/positions?user={trader_address}"
                r = requests.get(url, timeout=10)

                if r.status_code == 200:
                    positions = r.json()

                    if positions:
                        logger.info(f"  ✓ {trader_name}: {len(positions)} positions")

                        for p in positions:
                            records.append({
                                'user': trader_name,
                                'market': p.get('title', 'Unknown'),
                                'side': p.get('outcome', 'Unknown'),
                                'size': float(p.get('size', 0)),
                                'avg_price': float(p.get('avgPrice', 0)),
                                'current_price': float(p.get('curPrice', 0)),
                                'pnl': float(p.get('cashPnl', 0)),
                                'updated_at': datetime.now().isoformat()
                            })
                    else:
                        logger.info(f"  ⚠ {trader_name}: No open positions")
                else:
                    logger.error(f"  ✗ {trader_name}: HTTP {r.status_code}")
                    errors.append(f"{trader_name}: HTTP {r.status_code}")

            except Exception as e:
                logger.error(f"  ✗ {trader_name}: {str(e)}")
                errors.append(f"{trader_name}: {str(e)}")

        # Save data
        if not records:
            logger.warning("No positions found in this fetch")
            return

        df = pd.DataFrame(records)

        # Save CSV snapshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = SNAPSHOTS_DIR / f"positions_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"CSV snapshot saved: {csv_path.name}")

        # Save to database
        save_snapshot(df)
        save_capital_snapshot(df, datetime.now().isoformat())

        # Summary
        logger.info(f"Summary: {len(df)} positions, {df['user'].nunique()} traders, {df['market'].nunique()} markets")
        logger.info(f"Total exposure: ${df['size'].sum():,.2f}, Total PnL: ${df['pnl'].sum():,.2f}")

        if errors:
            logger.warning(f"Errors encountered: {len(errors)}")
            for err in errors:
                logger.warning(f"  - {err}")

        logger.info("Scheduled fetch complete")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error in scheduled fetch: {str(e)}", exc_info=True)


# Global scheduler instance
scheduler = None


def start_scheduler():
    """Start the background scheduler"""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    # Initialize database
    init_db()

    # Create scheduler
    scheduler = BackgroundScheduler(
        timezone="UTC",
        daemon=True
    )

    # Add job to fetch positions every N minutes
    scheduler.add_job(
        func=fetch_polymarket_positions,
        trigger=IntervalTrigger(minutes=FETCH_INTERVAL_MINUTES),
        id='fetch_positions',
        name='Fetch Polymarket Positions',
        replace_existing=True
    )

    # Add Copy Trading jobs (every 5 minutes)
    scheduler.add_job(
        func=lambda: asyncio.run(copy_trading_engine.monitor_positions()),
        trigger=IntervalTrigger(minutes=5),
        id='copy_trading_monitor',
        name='Copy Trading - Position Monitor',
        replace_existing=True
    )

    scheduler.add_job(
        func=lambda: asyncio.run(copy_trading_engine.manage_pending_orders()),
        trigger=IntervalTrigger(minutes=5),
        id='copy_trading_orders',
        name='Copy Trading - Order Manager',
        replace_existing=True
    )

    # Start scheduler
    scheduler.start()
    logger.info(f"Scheduler started - will fetch every {FETCH_INTERVAL_MINUTES} minutes")
    logger.info("Copy Trading jobs added (5-minute intervals)")

    # Run once immediately on startup
    logger.info("Running initial fetch on startup...")
    fetch_polymarket_positions()


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped")


def get_scheduler_status():
    """Get scheduler status info"""
    if scheduler is None:
        return {"status": "stopped"}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        "status": "running",
        "fetch_interval_minutes": FETCH_INTERVAL_MINUTES,
        "jobs": jobs
    }
