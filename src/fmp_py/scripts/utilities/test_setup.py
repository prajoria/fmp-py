#!/usr/bin/env python3
"""
Test script to verify VS Code test setup is working correctly.
"""

import sys
import os
from pathlib import Path

# Use proper module imports instead of path manipulation
def test_imports():
    """Test that we can import the fmp_py modules."""
    try:
        from ....fmp_base import FmpBase
        print("✅ Successfully imported FmpBase")
        
        from fmp_py.fmp_chart_data import FmpChartData
        print("✅ Successfully imported FmpChartData")
        
        from fmp_py.fmp_company_information import FmpCompanyInformation
        print("✅ Successfully imported FmpCompanyInformation")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_environment():
    """Test environment setup."""
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("✅ .env file found")
        return True
    else:
        print("❌ .env file not found")
        return False

if __name__ == "__main__":
    print("=== FMP-PY Test Setup Verification ===")
    print()
    
    print("1. Testing environment...")
    env_ok = test_environment()
    print()
    
    print("2. Testing imports...")
    imports_ok = test_imports()
    print()
    
    if env_ok and imports_ok:
        print("🎉 Setup verification PASSED! VS Code testing should work.")
    else:
        print("❌ Setup verification FAILED. Check the issues above.")
    
    sys.exit(0 if (env_ok and imports_ok) else 1)