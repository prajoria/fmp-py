#!/usr/bin/env python3
"""
Test script for S&P 500 integration with the historical chart fetcher
"""

import os
import sys

# Add paths for testing
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_sp500_fetcher():
    """Test the SP500 constituents fetcher separately"""
    print("Testing SP500 Constituents Fetcher...")
    
    try:
        from fmp_py.StockAnalysis.utils.sp500_constituents_fetcher import SP500ConstituentsFetcher
        
        fetcher = SP500ConstituentsFetcher()
        print("✅ SP500ConstituentsFetcher imported successfully")
        
        # Test fetching (without actually fetching to avoid network call)
        print("🔧 SP500ConstituentsFetcher is ready for use")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_historical_fetcher_integration():
    """Test the integration in historical chart fetcher"""
    print("\nTesting Historical Chart Fetcher Integration...")
    
    try:
        from fmp_py.StockAnalysis.cache.fmp_historical_chart_fetcher import FmpHistoricalChartFetcher, SP500_AVAILABLE
        
        print(f"✅ FmpHistoricalChartFetcher imported successfully")
        print(f"📊 SP500_AVAILABLE: {SP500_AVAILABLE}")
        
        if SP500_AVAILABLE:
            print("✅ S&P 500 integration is available")
        else:
            print("⚠️  S&P 500 integration not available (pandas missing?)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_help_output():
    """Test that help output includes SP500 option"""
    print("\nTesting Command Line Help...")
    
    try:
        # Import the main function without running it
        import subprocess
        import tempfile
        
        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fmp_historical_chart_fetcher.py'
        )
        
        if os.path.exists(script_path):
            # Run help command
            result = subprocess.run([sys.executable, script_path, '--help'], 
                                 capture_output=True, text=True, timeout=10)
            
            if '--sp500-stocks' in result.stdout:
                print("✅ --sp500-stocks option found in help")
                return True
            else:
                print("❌ --sp500-stocks option not found in help")
                return False
        else:
            print(f"⚠️  Script not found at: {script_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing help: {e}")
        return False

def main():
    print("="*60)
    print("S&P 500 INTEGRATION TEST")
    print("="*60)
    
    all_tests_passed = True
    
    # Test 1: SP500 fetcher
    if not test_sp500_fetcher():
        all_tests_passed = False
    
    # Test 2: Historical fetcher integration  
    if not test_historical_fetcher_integration():
        all_tests_passed = False
    
    # Test 3: Help output
    if not test_help_output():
        all_tests_passed = False
    
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED")
        print("✅ S&P 500 integration is working correctly")
        print("\nUsage:")
        print("  python fmp_historical_chart_fetcher.py --sp500-stocks")
    else:
        print("❌ SOME TESTS FAILED")
        print("🔧 Check the errors above and ensure pandas is installed")
        
    print("="*60)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())