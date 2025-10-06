"""
Date Utilities
==============
Common date parsing and formatting utilities for stock analysis
"""

from datetime import datetime, timedelta
from typing import Tuple, Optional, Union


def parse_date_range(start: Union[str, datetime], end: Union[str, datetime] = None, 
                    days_back: int = None) -> Tuple[datetime, datetime]:
    """
    Parse date range from various input formats.
    
    Args:
        start: Start date as string (YYYY-MM-DD) or datetime
        end: End date as string (YYYY-MM-DD) or datetime (default: today)
        days_back: If provided, calculate start date as end - days_back
    
    Returns:
        Tuple of (start_date, end_date) as datetime objects
    """
    # Parse end date
    if end is None:
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif isinstance(end, str):
        end_date = datetime.strptime(end, '%Y-%m-%d')
    else:
        end_date = end
    
    # Parse start date
    if days_back is not None:
        start_date = end_date - timedelta(days=days_back)
    elif isinstance(start, str):
        start_date = datetime.strptime(start, '%Y-%m-%d')
    else:
        start_date = start
    
    # Ensure start is before end
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    return start_date, end_date


def format_date(date: datetime, format_str: str = '%Y-%m-%d') -> str:
    """Format datetime object to string"""
    return date.strftime(format_str)


def get_trading_days(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate approximate number of trading days between two dates.
    Assumes 5 trading days per week, doesn't account for holidays.
    """
    total_days = (end_date - start_date).days
    weeks = total_days // 7
    remaining_days = total_days % 7
    
    # Rough estimate: 5 trading days per week
    trading_days = weeks * 5
    
    # Add remaining days (max 5 for partial week)
    trading_days += min(remaining_days, 5)
    
    return trading_days


def is_market_hours() -> bool:
    """
    Check if current time is during market hours (9:30 AM - 4:00 PM ET).
    Simple implementation - doesn't account for holidays.
    """
    now = datetime.now()
    
    # Convert to market hours (assuming system is in correct timezone)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # Check if weekday and within market hours
    is_weekday = now.weekday() < 5  # Monday = 0, Sunday = 6
    is_market_time = market_open <= now <= market_close
    
    return is_weekday and is_market_time


def get_last_trading_day() -> datetime:
    """Get the last completed trading day"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # If it's weekend, go back to Friday
    if today.weekday() == 5:  # Saturday
        return today - timedelta(days=1)
    elif today.weekday() == 6:  # Sunday
        return today - timedelta(days=2)
    else:
        # If market is still open, use previous day
        if is_market_hours():
            return today
        else:
            return today - timedelta(days=1)


def get_quarter_dates(year: int, quarter: int) -> Tuple[datetime, datetime]:
    """
    Get start and end dates for a specific quarter.
    
    Args:
        year: Year (e.g., 2024)
        quarter: Quarter number (1, 2, 3, or 4)
    
    Returns:
        Tuple of (start_date, end_date) for the quarter
    """
    if quarter not in [1, 2, 3, 4]:
        raise ValueError("Quarter must be 1, 2, 3, or 4")
    
    quarter_starts = {
        1: (1, 1),    # Jan 1
        2: (4, 1),    # Apr 1
        3: (7, 1),    # Jul 1
        4: (10, 1)    # Oct 1
    }
    
    quarter_ends = {
        1: (3, 31),   # Mar 31
        2: (6, 30),   # Jun 30
        3: (9, 30),   # Sep 30
        4: (12, 31)   # Dec 31
    }
    
    start_month, start_day = quarter_starts[quarter]
    end_month, end_day = quarter_ends[quarter]
    
    start_date = datetime(year, start_month, start_day)
    end_date = datetime(year, end_month, end_day)
    
    return start_date, end_date


def parse_fiscal_year(fiscal_year_end: str) -> Tuple[datetime, datetime]:
    """
    Parse fiscal year end date and return fiscal year start and end.
    
    Args:
        fiscal_year_end: Date string in format 'YYYY-MM-DD'
    
    Returns:
        Tuple of (fiscal_year_start, fiscal_year_end)
    """
    end_date = datetime.strptime(fiscal_year_end, '%Y-%m-%d')
    start_date = datetime(end_date.year - 1, end_date.month, end_date.day) + timedelta(days=1)
    
    return start_date, end_date