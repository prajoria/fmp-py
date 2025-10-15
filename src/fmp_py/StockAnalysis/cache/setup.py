#!/usr/bin/env python3
"""
Setup script for FMP Historical Chart Fetcher
Initializes database schema and verifies configuration
"""

import os
import sys
import argparse
from pathlib import Path

# Add path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from StockAnalysis.database.connection import get_db


def check_environment():
    """Check required environment variables"""
    required_vars = ['FMP_API_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    print("🔍 Checking environment variables...")
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            display_value = value if var not in ['FMP_API_KEY', 'DB_PASSWORD'] else '*' * len(value)
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these variables in your .env file or environment:")
        for var in missing_vars:
            print(f"  export {var}=your_value_here")
        return False
    
    print("✅ All environment variables are set")
    return True


def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        db = get_db()
        if db.test_connection():
            print("✅ Database connection successful")
            
            # Test basic query
            result = db.execute_query("SELECT VERSION() as version", fetch='one')
            if result:
                print(f"  📊 MySQL Version: {result['version']}")
            
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def create_database_schema():
    """Create database schema"""
    print("\n🔧 Creating database schema...")
    
    # Get script directory
    script_dir = Path(__file__).parent.parent / 'database'
    
    schema_files = [
        script_dir / 'schema.sql',
        script_dir / 'historical_chart_fetcher_schema.sql'
    ]
    
    db = get_db()
    
    for schema_file in schema_files:
        if not schema_file.exists():
            print(f"  ⚠️  Schema file not found: {schema_file}")
            continue
        
        print(f"  📜 Executing: {schema_file.name}")
        
        try:
            with open(schema_file, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        db.execute_update(statement)
                    except Exception as e:
                        # Some statements might fail if objects already exist
                        if 'already exists' not in str(e).lower():
                            print(f"    ⚠️  Statement {i+1} warning: {e}")
            
            print(f"  ✅ {schema_file.name} executed successfully")
            
        except Exception as e:
            print(f"  ❌ Error executing {schema_file.name}: {e}")
            return False
    
    return True


def verify_tables():
    """Verify that required tables exist"""
    print("\n🔍 Verifying database tables...")
    
    required_tables = [
        'companies',
        'historical_price_full_daily',
        'fetch_watermarks',
        'fetch_sessions',
        'popular_stocks'
    ]
    
    db = get_db()
    
    try:
        result = db.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
        """)
        
        existing_tables = [row['table_name'] for row in result] if result else []
        
        missing_tables = []
        for table in required_tables:
            if table in existing_tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - Missing")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
            return False
        
        print("✅ All required tables exist")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False


def test_fmp_api():
    """Test FMP API connection"""
    print("\n🔍 Testing FMP API connection...")
    
    try:
        from fmp_py.fmp_historical_charts import FmpHistoricalCharts
        
        client = FmpHistoricalCharts()
        
        # Test with a simple request
        data = client.get_historical_price_light('AAPL', 
            from_date='2024-01-01', to_date='2024-01-01')
        
        if data:
            print("✅ FMP API connection successful")
            print(f"  📊 Test data: {len(data)} records for AAPL")
            return True
        else:
            print("❌ FMP API returned no data")
            return False
            
    except Exception as e:
        print(f"❌ FMP API connection error: {e}")
        return False


def check_popular_stocks():
    """Check popular stocks in database"""
    print("\n🔍 Checking popular stocks...")
    
    try:
        db = get_db()
        result = db.execute_query("""
            SELECT COUNT(*) as count FROM popular_stocks WHERE is_active = TRUE
        """, fetch='one')
        
        count = result['count'] if result else 0
        
        if count > 0:
            print(f"✅ {count} popular stocks configured")
            
            # Show first few
            stocks = db.execute_query("""
                SELECT symbol, company_name FROM popular_stocks 
                WHERE is_active = TRUE 
                ORDER BY priority 
                LIMIT 5
            """)
            
            if stocks:
                print("  📈 Sample stocks:")
                for stock in stocks:
                    print(f"    - {stock['symbol']}: {stock['company_name']}")
            
            return True
        else:
            print("❌ No popular stocks found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking popular stocks: {e}")
        return False


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup FMP Historical Chart Fetcher")
    parser.add_argument('--skip-schema', action='store_true', help='Skip schema creation')
    parser.add_argument('--skip-api-test', action='store_true', help='Skip API test')
    
    args = parser.parse_args()
    
    print("🚀 FMP Historical Chart Fetcher Setup")
    print("=" * 50)
    
    success = True
    
    # Check environment
    if not check_environment():
        success = False
    
    # Test database connection
    if success and not test_database_connection():
        success = False
    
    # Create schema
    if success and not args.skip_schema:
        if not create_database_schema():
            success = False
    
    # Verify tables
    if success and not verify_tables():
        success = False
    
    # Test FMP API
    if success and not args.skip_api_test:
        if not test_fmp_api():
            success = False
    
    # Check popular stocks
    if success and not check_popular_stocks():
        success = False
    
    # Final result
    print("\n" + "=" * 50)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the fetcher with: python fmp_historical_chart_fetcher.py --popular-stocks")
        print("2. Check progress with: python fmp_historical_chart_fetcher.py --progress-report")
        print("3. View the README for more usage examples")
    else:
        print("❌ Setup failed. Please fix the issues above and try again.")
    print("=" * 50)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())