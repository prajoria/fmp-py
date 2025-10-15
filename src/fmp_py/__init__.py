"""
FMP-PY: Python wrapper for Financial Modeling Prep API

This package provides a comprehensive Python interface to the Financial Modeling Prep API,
offering access to financial data, market information, and technical indicators.
"""

from .fmp_base import FmpBase
from .fmp_chart_data import FmpChartData
from .fmp_company_information import FmpCompanyInformation
from .fmp_company_search import FmpCompanySearch
from .fmp_crypto import FmpCrypto
from .fmp_dividends import FmpDividends
from .fmp_earnings import FmpEarnings
from .fmp_financial_statements import FmpFinancialStatements
from .fmp_forex import FmpForex
from .fmp_historical_charts import FmpHistoricalCharts

# Import cached client if available
try:
    from .StockAnalysis.client.cached_fmp_historical_charts import CachedFmpHistoricalCharts
    _CACHED_AVAILABLE = True
except ImportError:
    _CACHED_AVAILABLE = False
from .fmp_historical_data import FmpHistoricalData
from .fmp_ipo_calendar import FmpIpoCalendar
from .fmp_mergers_and_aquisitions import FmpMergersAndAquisitions
from .fmp_price_targets import FmpPriceTargets
from .fmp_quote import FmpQuote
from .fmp_splits import FmpSplits
from .fmp_statement_analysis import FmpStatementAnalysis
from .fmp_stock_list import FmpStockList
from .fmp_technical_indicators import FmpTechnicalIndicators
from .fmp_upgrades_downgrades import FmpUpgradesDowngrades
from .fmp_valuation import FmpValuation

__version__ = "0.0.20.3"
__author__ = "FMP-PY Team"

__all__ = [
    "FmpBase",
    "FmpChartData",
    "FmpCompanyInformation",
    "FmpCompanySearch",
    "FmpCrypto",
    "FmpDividends",
    "FmpEarnings",
    "FmpFinancialStatements",
    "FmpForex",
    "FmpHistoricalCharts",
    "FmpHistoricalData",
    "FmpIpoCalendar",
    "FmpMergersAndAquisitions",
    "FmpPriceTargets",
    "FmpQuote",
    "FmpSplits",
    "FmpStatementAnalysis",
    "FmpStockList",
    "FmpTechnicalIndicators",
    "FmpUpgradesDowngrades",
    "FmpValuation",
]