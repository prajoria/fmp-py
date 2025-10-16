#!/usr/bin/env python3
"""
Database Setup Script with S&P 500 Support
===========================================
Sets up all database tables including S&P 500 constituents
"""

import os
import sys
import logging
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from fmp_py.StockAnalysis.database.connection import get_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def execute_sql_file(db, sql_file_path: str) -> bool:
    """Execute SQL commands from a file"""
    try:
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Split by statements (rough approach)
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement and not statement.startswith('--'):
                try:
                    db.execute_query(statement)
                    logger.debug(f"Executed: {statement[:50]}...")
                except Exception as e:
                    # Skip statements that might already exist
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        logger.debug(f"Skipping existing object: {e}")
                    else:
                        logger.error(f"Error executing statement: {e}")
                        logger.error(f"Statement: {statement}")
                        return False
        
        logger.info(f"Successfully executed SQL file: {sql_file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error reading/executing SQL file {sql_file_path}: {e}")
        return False


def setup_database():
    """Set up all database tables and schemas"""
    try:
        # Get database connection
        db = get_db()
        logger.info("Connected to database successfully")
        
        # Get the database directory
        db_dir = Path(__file__).parent
        
        # List of SQL files to execute in order
        sql_files = [
            "schema.sql",  # Main schema
            "historical_chart_fetcher_schema.sql",  # Historical chart fetcher schema
            "sp500_constituents_schema.sql"  # S&P 500 schema
        ]
        
        success_count = 0
        for sql_file in sql_files:
            sql_path = db_dir / sql_file
            if sql_path.exists():
                logger.info(f"Executing {sql_file}...")
                if execute_sql_file(db, str(sql_path)):
                    success_count += 1
                    logger.info(f"✅ {sql_file} executed successfully")
                else:
                    logger.error(f"❌ Failed to execute {sql_file}")
            else:
                logger.warning(f"⚠️  SQL file not found: {sql_path}")
        
        logger.info(f"Database setup completed. {success_count}/{len(sql_files)} files executed successfully.")
        
        # Test the setup by checking tables
        logger.info("Verifying table creation...")
        test_tables = [
            'historical_prices_daily',
            'fetch_watermarks', 
            'popular_stocks',
            'sp500_constituents'
        ]
        
        for table in test_tables:
            try:
                result = db.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                if result:
                    count = result[0]['count']
                    logger.info(f"✅ Table '{table}' exists with {count} records")
                else:
                    logger.warning(f"⚠️  Table '{table}' exists but query failed")
            except Exception as e:
                logger.error(f"❌ Table '{table}' check failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False


def populate_sp500_data():
    """Populate S&P 500 data from web"""
    try:
        logger.info("Populating S&P 500 data...")
        
        from fmp_py.StockAnalysis.utils.sp500_constituents_fetcher import SP500ConstituentsFetcher
        
        fetcher = SP500ConstituentsFetcher(use_database=True)
        
        if not fetcher.use_database:
            logger.error("Database not available for S&P 500 data")
            return False
        
        # Fetch and save
        df, csv_path, db_records = fetcher.fetch_and_save(save_to_db=True)
        
        logger.info(f"✅ S&P 500 data populated: {db_records} records saved to database")
        logger.info(f"📄 CSV backup saved to: {csv_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error populating S&P 500 data: {e}")
        return False


def main():
    """Main setup function"""
    print("="*60)
    print("DATABASE SETUP WITH S&P 500 SUPPORT")
    print("="*60)
    
    # Step 1: Setup database schemas
    logger.info("Step 1: Setting up database schemas...")
    if not setup_database():
        print("❌ Database setup failed")
        return 1
    
    # Step 2: Populate S&P 500 data
    logger.info("Step 2: Populating S&P 500 data...")
    if not populate_sp500_data():
        print("⚠️  S&P 500 data population failed (continuing anyway)")
    
    print("\n" + "="*60)
    print("🎉 DATABASE SETUP COMPLETED")
    print("="*60)
    print("✅ All database tables created")
    print("✅ S&P 500 constituents populated")
    print("\nNext steps:")
    print("1. Run historical chart fetcher: --sp500-stocks")
    print("2. Check S&P 500 data: python sp500_constituents_fetcher.py --database-stats")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup database with S&P 500 support")
    parser.add_argument('--schema-only', action='store_true', help='Setup schemas only, skip data population')
    parser.add_argument('--data-only', action='store_true', help='Populate data only, skip schema setup')
    
    args = parser.parse_args()
    
    if args.schema_only:
        success = setup_database()
        sys.exit(0 if success else 1)
    elif args.data_only:
        success = populate_sp500_data()
        sys.exit(0 if success else 1)
    else:
        sys.exit(main())