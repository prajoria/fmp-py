"""
Stock Analysis Framework with FMP Cache Integration
===================================================

A comprehensive framework for financial data analysis with intelligent caching,
FMP API integration, and local high-performance data access.

Package Structure:
- api/: FMP-compatible API interface for cached data
- cache/: Intelligent cache management and data fetching
- client/: FMP API client for data retrieval
- database/: Database connection and data access layer
- utils/: Common utilities for date handling, formatting, etc.
- examples/: Usage examples and tutorials
- notebooks/: Jupyter notebooks for interactive analysis
- docs/: Comprehensive documentation and guides

Features:
---------
- Smart cache validation to minimize API calls
- FMP-compatible local API for seamless integration
- Batch processing for multiple stocks
- Date range filtering and validation
- Comprehensive financial data coverage
- Performance monitoring and statistics

For detailed analysis guidance, see docs/STOCK_ANALYSIS_GUIDE.md
"""

__version__ = "1.0.0"
__author__ = "Stock Analysis Team"

# Import existing components
from .client.fmp_client import FMPClient
from .utils.config import Config

# Import new cache components
try:
    from .api.fmp_cache_api import FMPCacheAPI
    from .cache.stock_data_fetcher import StockDataFetcher
    from .cache.cache_manager import CacheManager
    from .database.connection import get_db
    
    __all__ = [
        'FMPClient', 'Config',
        'FMPCacheAPI', 'StockDataFetcher', 
        'CacheManager', 'get_db'
    ]
except ImportError:
    # Fallback if cache components not available
    __all__ = ['FMPClient', 'Config']