#!/usr/bin/env python3
"""Simple test to debug URL construction."""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from fmp_py.fmp_statement_analysis import FmpStatementAnalysis

def debug_request():
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        print("No API key found")
        return
    
    client = FmpStatementAnalysis(api_key=api_key)
    
    # Let's try to intercept the URL construction
    symbol = "AAPL"
    url = f"v3/ratios-ttm/{symbol}"
    params = {"apikey": api_key}
    
    # Import base class to check URL construction
    from fmp_py.fmp_base import FMP_BASE_URL
    full_url = f"{FMP_BASE_URL}{url}"
    
    print(f"Base URL: {FMP_BASE_URL}")
    print(f"Endpoint: {url}")
    print(f"Full URL: {full_url}")
    print(f"Params: {params}")
    
    # Now let's see what happens in the actual request
    try:
        # Monkey patch to see the actual request
        original_get = client.session.get
        
        def debug_get(url, **kwargs):
            print(f"ACTUAL REQUEST URL: {url}")
            print(f"ACTUAL PARAMS: {kwargs.get('params', {})}")
            return original_get(url, **kwargs)
        
        client.session.get = debug_get
        
        # Try the actual API call
        result = client.ratios_ttm(symbol)
        print(f"Success: {type(result)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_request()