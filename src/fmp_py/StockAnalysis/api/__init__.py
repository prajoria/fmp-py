# API module initialization
"""
API Module
==========

Provides FMP-compatible API interface for cached data.
Serves cached financial data through the same interface as FMP API.
"""

from .fmp_cache_api import FMPCacheAPI

__all__ = ['FMPCacheAPI']