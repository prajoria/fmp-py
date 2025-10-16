#!/usr/bin/env python3
"""Debug script to check which base URL is being used."""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import and check
try:
    from fmp_py.fmp_base import FMP_BASE_URL, FmpBase
    from fmp_py.fmp_statement_analysis import FmpStatementAnalysis
    
    print(f"Imported FMP_BASE_URL: {FMP_BASE_URL}")
    print(f"FmpBase module path: {FmpBase.__module__}")
    print(f"FmpBase file: {FmpBase.__module__.__file__ if hasattr(FmpBase.__module__, '__file__') else 'N/A'}")
    
    # Check what file the class is actually loaded from
    import inspect
    base_file = inspect.getfile(FmpBase)
    statement_file = inspect.getfile(FmpStatementAnalysis)
    
    print(f"FmpBase loaded from: {base_file}")
    print(f"FmpStatementAnalysis loaded from: {statement_file}")
    
    # Create instance and check
    api_key = os.getenv("FMP_API_KEY", "test_key")
    if api_key != "test_key":
        client = FmpStatementAnalysis(api_key=api_key)
        
        # Test URL construction 
        test_url = "v3/test"
        full_url = f"{FMP_BASE_URL}{test_url}"
        print(f"Constructed URL: {full_url}")
        
        # Check if there's any hardcoded URL override
        print(f"Client base attributes: {[attr for attr in dir(client) if 'url' in attr.lower() or 'base' in attr.lower()]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()