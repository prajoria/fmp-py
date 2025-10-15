"""
Utility modules for FMP Stock Analysis
"""

from .config import Config, get_config, set_config, reset_config
from .helpers import (
    format_currency, format_percentage, format_number,
    calculate_ytd_performance, calculate_returns, calculate_volatility,
    calculate_sharpe_ratio, calculate_beta, clean_financial_data,
    parse_symbol, validate_date_string, get_trading_days_between,
    aggregate_financial_data, detect_outliers
)

# Import new date utilities
try:
    from .date_utils import (
        parse_date_range, format_date, get_trading_days,
        is_market_hours, get_last_trading_day, get_quarter_dates,
        parse_fiscal_year
    )
    DATE_UTILS_AVAILABLE = True
except ImportError:
    DATE_UTILS_AVAILABLE = False

# Import SP500 constituents fetcher
try:
    from .sp500_constituents_fetcher import SP500ConstituentsFetcher
    SP500_FETCHER_AVAILABLE = True
except ImportError:
    SP500_FETCHER_AVAILABLE = False

# Build the __all__ list
__all__ = [
    'Config', 'get_config', 'set_config', 'reset_config',
    'format_currency', 'format_percentage', 'format_number',
    'calculate_ytd_performance', 'calculate_returns', 'calculate_volatility',
    'calculate_sharpe_ratio', 'calculate_beta', 'clean_financial_data',
    'parse_symbol', 'validate_date_string', 'get_trading_days_between',
    'aggregate_financial_data', 'detect_outliers'
]

if DATE_UTILS_AVAILABLE:
    __all__.extend([
        'parse_date_range', 'format_date', 'get_trading_days',
        'is_market_hours', 'get_last_trading_day', 'get_quarter_dates',
        'parse_fiscal_year'
    ])

if SP500_FETCHER_AVAILABLE:
    __all__.append('SP500ConstituentsFetcher')