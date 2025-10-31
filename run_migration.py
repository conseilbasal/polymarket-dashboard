"""
Script to run database migrations for copy trading
"""
import os
import psycopg2
from psycopg2 import sql
from pathlib import Path

def run_migration():
    """Execute the copy trading schema migration"""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Using SQLite fallback is not supported for copy trading")
        return False

    # Read migration file
    migration_file = Path(__file__).parent / "migrations" / "001_copy_trading_schema.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    try:
        # Connect to database
        print(f"📊 Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Execute migration
        print(f"🔧 Executing migration...")
        cursor.execute(migration_sql)
        conn.commit()

        # Verify tables were created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('copy_trading_config', 'position_snapshots', 'pending_copy_orders', 'executed_copy_trades')
            ORDER BY table_name
        """)

        tables = cursor.fetchall()

        print(f"\n✅ Migration completed successfully!")
        print(f"\n📋 Created tables:")
        for (table_name,) in tables:
            print(f"   ✓ {table_name}")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print(" 🚀 COPY TRADING DATABASE MIGRATION")
    print("=" * 70)
    print()

    success = run_migration()

    if success:
        print()
        print("=" * 70)
        print(" ✅ Migration completed! Copy trading tables are ready.")
        print("=" * 70)
    else:
        print()
        print("=" * 70)
        print(" ❌ Migration failed. Please check errors above.")
        print("=" * 70)
        exit(1)
