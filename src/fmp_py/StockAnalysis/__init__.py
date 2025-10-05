"""
Financial Modeling Prep Stock Analysis Package

This package provides tools for financial analysis using the Financial Modeling Prep API.

Package Structure:
- client/: FMP API client for data retrieval
- utils/: Helper functions and configuration management
- examples/: Practical usage examples and demonstrations
- notebooks/: Jupyter notebooks for interactive analysis
- docs/: Comprehensive documentation and guides

For detailed analysis guidance, see docs/STOCK_ANALYSIS_GUIDE.md
"""

__version__ = "1.0.0"
__author__ = "Stock Analysis Team"

from .client.fmp_client import FMPClient
from .utils.config import Config

__all__ = ['FMPClient', 'Config']