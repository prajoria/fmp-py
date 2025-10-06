#!/usr/bin/env python3
"""
FMP Cache System - Quick Test
=============================

A quick test script to verify the FMP Cache System is working correctly.
This script performs basic functionality tests and reports results.
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from api.fmp_cache_api import FMPCacheAPI
        print("  ✅ FMPCacheAPI imported successfully")
    except ImportError as e:
        print(f"  ❌ FMPCacheAPI import failed: {e}")
        return False
    
    try:
        from cache.stock_data_fetcher import StockDataFetcher
        print("  ✅ StockDataFetcher imported successfully")
    except ImportError as e:
        print(f"  ❌ StockDataFetcher import failed: {e}")
        return False
    
    try:
        from cache.cache_manager import CacheManager
        print("  ✅ CacheManager imported successfully")
    except ImportError as e:
        print(f"  ❌ CacheManager import failed: {e}")
        return False
    
    try:
        from utils.date_utils import parse_date_range
        print("  ✅ Date utilities imported successfully")
    except ImportError as e:
        print(f"  ❌ Date utilities import failed: {e}")
        return False
    
    return True


def test_api_key():
    """Test API key configuration"""
    print("\n🔑 Testing API key configuration...")
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("  ❌ FMP_API_KEY environment variable not set")
        return False
    
    if len(api_key) < 10:
        print("  ⚠️  API key seems too short")
        return False
    
    print(f"  ✅ API key configured: {api_key[:10]}...")
    return True


def test_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing database connection...")
    
    try:
        from api.fmp_cache_api import FMPCacheAPI
        api = FMPCacheAPI()
        
        # Try to get health check
        health = api.health_check()
        if health.get('status') == 'healthy':
            print("  ✅ Database connection successful")
            print(f"  📊 Cache contains {health.get('cache_stats', {}).get('total_symbols', 0)} symbols")
            return True
        else:
            print(f"  ❌ Database health check failed: {health}")
            return False
            
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False


def test_basic_functionality():
    """Test basic system functionality"""
    print("\n⚙️  Testing basic functionality...")
    
    try:
        from api.fmp_cache_api import FMPCacheAPI
        api = FMPCacheAPI()
        
        # Test getting available symbols
        symbols = api.get_available_symbols()
        if symbols:
            print(f"  ✅ Found {len(symbols)} symbols in cache")
            test_symbol = symbols[0]
            print(f"  🔍 Testing with symbol: {test_symbol}")
            
            # Test profile query
            profile = api.profile(test_symbol)
            if profile:
                print("  ✅ Profile query successful")
            else:
                print("  ⚠️  Profile query returned no data")
            
            # Test quote query
            quote = api.quote(test_symbol)
            if quote:
                print("  ✅ Quote query successful")
            else:
                print("  ⚠️  Quote query returned no data")
            
            return True
        else:
            print("  ⚠️  No symbols found in cache (database might be empty)")
            return False
            
    except Exception as e:
        print(f"  ❌ Basic functionality test failed: {e}")
        return False


def test_date_utilities():
    """Test date utility functions"""
    print("\n📅 Testing date utilities...")
    
    try:
        from utils.date_utils import parse_date_range
        
        # Test various date formats
        test_cases = [
            "30",
            "2024-01-01,2024-12-31",
            "365",
            "2023-01-01 to 2023-12-31"
        ]
        
        for test_case in test_cases:
            try:
                start, end = parse_date_range(test_case)
                print(f"  ✅ Parsed '{test_case}' -> {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
            except Exception as e:
                print(f"  ❌ Failed to parse '{test_case}': {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Date utilities test failed: {e}")
        return False


def test_cache_manager():
    """Test cache manager functionality"""
    print("\n🗂️  Testing cache manager...")
    
    try:
        from cache.cache_manager import CacheManager
        cache_manager = CacheManager()
        
        # Get cache statistics
        stats = cache_manager.get_cache_statistics()
        print(f"  ✅ Cache statistics retrieved")
        print(f"  📊 Total symbols: {stats.get('total_symbols', 0)}")
        print(f"  📊 Total records: {stats.get('total_records', 0)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Cache manager test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("="*60)
    print("🚀 FMP CACHE SYSTEM - QUICK TEST")
    print("="*60)
    
    tests = [
        ("Import Test", test_imports),
        ("API Key Test", test_api_key),
        ("Database Test", test_database_connection),
        ("Functionality Test", test_basic_functionality),
        ("Date Utils Test", test_date_utilities),
        ("Cache Manager Test", test_cache_manager)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The FMP Cache System is ready to use.")
        print("\n🚀 Next steps:")
        print("  1. Run examples/getting_started.py")
        print("  2. Try the CLI: python fmp_cache_cli.py --help")
        print("  3. Run complete demo: python examples/complete_demo.py")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        print("\n🔧 Troubleshooting:")
        print("  1. Ensure FMP_API_KEY is set")
        print("  2. Check database connection settings")
        print("  3. Verify MySQL database is running")
        print("  4. Check docs/README.md for setup instructions")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())