"""
FMP Client Package

This module provides the FMP API client for financial data access.
"""

from .fmp_client import FMPClient, FMPAPIError, create_client

__all__ = ['FMPClient', 'FMPAPIError', 'create_client']