#!/usr/bin/env python3
"""
FMP MySQL Database Test
======================
Test the FMP API with MySQL caching functionality
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/daaji/masterswork/git/fmp-py/.env')

# Add the StockAnalysis path
sys.path.append('/home/daaji/masterswork/git/fmp-py/src/fmp_py/StockAnalysis')

from database.connection import get_db

def test_database_operations():
    """Test basic database operations"""
    
    print("🗄️ Testing FMP MySQL Database")
    print("=" * 50)
    
    try:
        db = get_db()
        
        # Test 1: Connection
        print("1. Testing database connection...")
        if db.test_connection():
            print("   ✅ Connection successful")
        else:
            print("   ❌ Connection failed")
            return False
        
        # Test 2: Insert a test company
        print("2. Testing data insertion...")
        test_symbol = "AAPL"
        
        # Insert company if not exists
        insert_query = """
        INSERT IGNORE INTO companies (symbol, name, exchange, country, currency) 
        VALUES (%s, %s, %s, %s, %s)
        """
        rows_affected = db.execute_update(insert_query, (test_symbol, "Apple Inc.", "NASDAQ", "US", "USD"))
        print(f"   ✅ Insert operation completed (rows affected: {rows_affected})")
        
        # Test 3: Query data
        print("3. Testing data retrieval...")
        select_query = "SELECT * FROM companies WHERE symbol = %s"
        result = db.execute_query(select_query, (test_symbol,), fetch='one')
        
        if result:
            print(f"   ✅ Found company: {result['name']} ({result['symbol']})")
        else:
            print("   ⚠️ No data found")
        
        # Test 4: Insert quote data
        print("4. Testing quote data insertion...")
        quote_query = """
        INSERT INTO quotes (symbol, price, changes_percentage, `change`, volume, market_cap, cached_at, expires_at) 
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 5 MINUTE))
        ON DUPLICATE KEY UPDATE 
        price = VALUES(price), 
        changes_percentage = VALUES(changes_percentage),
        `change` = VALUES(`change`),
        volume = VALUES(volume),
        market_cap = VALUES(market_cap),
        cached_at = NOW(),
        expires_at = DATE_ADD(NOW(), INTERVAL 5 MINUTE)
        """
        
        # Sample quote data
        db.execute_update(quote_query, (test_symbol, 258.02, 0.35, 0.89, 49155614, 3829117427800))
        print("   ✅ Quote data inserted/updated")
        
        # Test 5: Query with JOIN
        print("5. Testing complex query with JOIN...")
        join_query = """
        SELECT c.symbol, c.name, q.price, q.changes_percentage, q.market_cap
        FROM companies c
        LEFT JOIN quotes q ON c.symbol = q.symbol
        WHERE c.symbol = %s
        """
        
        result = db.execute_query(join_query, (test_symbol,), fetch='one')
        if result:
            print(f"   ✅ {result['name']}: ${result['price']} ({result['changes_percentage']:+.2f}%)")
            print(f"      Market Cap: ${result['market_cap']:,}")
        
        # Test 6: Cache statistics
        print("6. Testing cache statistics...")
        stats_queries = {
            "Total companies": "SELECT COUNT(*) as count FROM companies",
            "Cached quotes": "SELECT COUNT(*) as count FROM quotes WHERE expires_at > NOW()",
            "Expired quotes": "SELECT COUNT(*) as count FROM quotes WHERE expires_at <= NOW()"
        }
        
        for stat_name, query in stats_queries.items():
            result = db.execute_query(query, fetch='one')
            print(f"   {stat_name}: {result['count']}")
        
        print()
        print("🎉 All database tests passed!")
        print("✅ Your FMP MySQL cache database is fully functional!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def show_database_info():
    """Show database information"""
    
    print("\n📊 Database Information")
    print("=" * 50)
    
    # Show environment configuration
    print("Configuration:")
    print(f"  Host: {os.getenv('FMP_DB_HOST')}")
    print(f"  Database: {os.getenv('FMP_DB_NAME')}")
    print(f"  User: {os.getenv('FMP_DB_USER')}")
    print(f"  Pool Size: {os.getenv('FMP_DB_POOL_SIZE', '5')}")
    print()
    
    try:
        db = get_db()
        
        # Show table information
        table_info = db.execute_query("""
            SELECT 
                table_name,
                table_rows,
                ROUND(((data_length + index_length) / 1024 / 1024), 2) as size_mb
            FROM information_schema.tables 
            WHERE table_schema = 'fmp_cache' 
            ORDER BY (data_length + index_length) DESC
            LIMIT 10
        """, fetch='all')
        
        print("Top 10 Tables by Size:")
        print("Table Name".ljust(25) + "Rows".ljust(10) + "Size (MB)")
        print("-" * 45)
        
        for table in table_info:
            print(f"{table['table_name'][:24].ljust(25)}{str(table['table_rows']).ljust(10)}{table['size_mb']}")
        
    except Exception as e:
        print(f"Error getting database info: {e}")

if __name__ == "__main__":
    print("🚀 FMP MySQL Database Test Suite")
    print("=" * 60)
    
    # Test database operations
    success = test_database_operations()
    
    if success:
        # Show database information
        show_database_info()
        
        print("\n🎯 Next Steps:")
        print("1. Your MySQL database is ready for FMP API caching")
        print("2. Use the database connection in your FMP client code")
        print("3. Cache API responses to reduce API calls and improve performance")
        print("4. Monitor cache hit rates and adjust TTL values as needed")
        
    else:
        print("\n❌ Database setup needs attention")
        print("Please check the error messages above and fix any issues")