"""
Utility functions for FMP Stock Analysis

This module provides common utility functions for data processing,
formatting, and analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
from datetime import datetime, timedelta
import re


def format_currency(value: float, symbol: str = "$", decimal_places: int = 2) -> str:
    """
    Format a number as currency
    
    Args:
        value (float): Numeric value to format
        symbol (str): Currency symbol
        decimal_places (int): Number of decimal places
        
    Returns:
        str: Formatted currency string
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    if abs(value) >= 1e12:
        return f"{symbol}{value/1e12:.{decimal_places}f}T"
    elif abs(value) >= 1e9:
        return f"{symbol}{value/1e9:.{decimal_places}f}B"
    elif abs(value) >= 1e6:
        return f"{symbol}{value/1e6:.{decimal_places}f}M"
    elif abs(value) >= 1e3:
        return f"{symbol}{value/1e3:.{decimal_places}f}K"
    else:
        return f"{symbol}{value:,.{decimal_places}f}"


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format a number as percentage
    
    Args:
        value (float): Numeric value (0.05 = 5%)
        decimal_places (int): Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    return f"{value*100:.{decimal_places}f}%"


def format_number(value: float, decimal_places: int = 2) -> str:
    """
    Format a number with thousands separators
    
    Args:
        value (float): Numeric value to format
        decimal_places (int): Number of decimal places
        
    Returns:
        str: Formatted number string
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    return f"{value:,.{decimal_places}f}"


def calculate_ytd_performance(current_price: float, year_start_price: float) -> float:
    """
    Calculate year-to-date performance
    
    Args:
        current_price (float): Current stock price
        year_start_price (float): Price at start of year
        
    Returns:
        float: YTD performance as decimal (0.05 = 5%)
    """
    if not year_start_price or year_start_price == 0:
        return 0.0
    
    return (current_price - year_start_price) / year_start_price


def calculate_returns(prices: List[float]) -> List[float]:
    """
    Calculate daily returns from price series
    
    Args:
        prices (List[float]): List of prices
        
    Returns:
        List[float]: Daily returns
    """
    if len(prices) < 2:
        return []
    
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] != 0:
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        else:
            returns.append(0.0)
    
    return returns


def calculate_volatility(returns: List[float], annualize: bool = True) -> float:
    """
    Calculate volatility from returns
    
    Args:
        returns (List[float]): List of returns
        annualize (bool): Whether to annualize the volatility
        
    Returns:
        float: Volatility (standard deviation of returns)
    """
    if len(returns) < 2:
        return 0.0
    
    vol = np.std(returns)
    
    if annualize:
        vol *= np.sqrt(252)  # Assuming 252 trading days per year
    
    return vol


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio
    
    Args:
        returns (List[float]): List of returns
        risk_free_rate (float): Risk-free rate (annual)
        
    Returns:
        float: Sharpe ratio
    """
    if len(returns) < 2:
        return 0.0
    
    excess_returns = [r - risk_free_rate/252 for r in returns]  # Daily risk-free rate
    
    mean_excess_return = np.mean(excess_returns)
    vol = np.std(returns)
    
    if vol == 0:
        return 0.0
    
    return (mean_excess_return / vol) * np.sqrt(252)  # Annualized


def calculate_beta(stock_returns: List[float], market_returns: List[float]) -> float:
    """
    Calculate beta coefficient
    
    Args:
        stock_returns (List[float]): Stock returns
        market_returns (List[float]): Market returns
        
    Returns:
        float: Beta coefficient
    """
    if len(stock_returns) != len(market_returns) or len(stock_returns) < 2:
        return 1.0
    
    covariance = np.cov(stock_returns, market_returns)[0][1]
    market_variance = np.var(market_returns)
    
    if market_variance == 0:
        return 1.0
    
    return covariance / market_variance


def clean_financial_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean financial data DataFrame
    
    Args:
        df (pd.DataFrame): Raw financial data
        
    Returns:
        pd.DataFrame: Cleaned data
    """
    # Make a copy
    cleaned_df = df.copy()
    
    # Convert date columns
    date_columns = ['date', 'fillingDate', 'acceptedDate', 'calendarYear']
    for col in date_columns:
        if col in cleaned_df.columns:
            cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
    
    # Convert numeric columns
    numeric_columns = cleaned_df.select_dtypes(include=['object']).columns
    for col in numeric_columns:
        if col not in date_columns and col not in ['symbol', 'reportedCurrency', 'cik', 'link', 'finalLink']:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
    
    return cleaned_df


def parse_symbol(symbol: str) -> str:
    """
    Parse and validate stock symbol
    
    Args:
        symbol (str): Stock symbol
        
    Returns:
        str: Cleaned symbol
    """
    if not symbol:
        raise ValueError("Symbol cannot be empty")
    
    # Remove whitespace and convert to uppercase
    symbol = symbol.strip().upper()
    
    # Basic validation - alphanumeric and some special characters
    if not re.match(r'^[A-Z0-9.-]+$', symbol):
        raise ValueError(f"Invalid symbol format: {symbol}")
    
    return symbol


def validate_date_string(date_str: str) -> bool:
    """
    Validate date string format (YYYY-MM-DD)
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid format
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def get_trading_days_between(start_date: str, end_date: str) -> int:
    """
    Calculate number of trading days between two dates
    
    Args:
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        
    Returns:
        int: Number of trading days
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Simple approximation: assume 5 trading days per week
    total_days = (end - start).days
    weeks = total_days // 7
    remaining_days = total_days % 7
    
    # Count remaining weekdays
    weekdays = 0
    current = start + timedelta(days=weeks * 7)
    for i in range(remaining_days):
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            weekdays += 1
        current += timedelta(days=1)
    
    return weeks * 5 + weekdays


def aggregate_financial_data(df: pd.DataFrame, period: str = 'annual') -> pd.DataFrame:
    """
    Aggregate financial data by period
    
    Args:
        df (pd.DataFrame): Financial data
        period (str): Aggregation period ('annual', 'quarter')
        
    Returns:
        pd.DataFrame: Aggregated data
    """
    if 'date' not in df.columns:
        return df
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    if period == 'annual':
        df['year'] = df['date'].dt.year
        group_col = 'year'
    elif period == 'quarter':
        df['year_quarter'] = df['date'].dt.to_period('Q')
        group_col = 'year_quarter'
    else:
        return df
    
    # Aggregate numeric columns (sum for most financial metrics)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    agg_dict = {}
    for col in numeric_cols:
        agg_dict[col] = 'sum' if col != 'date' else 'first'
    
    # Add non-numeric columns (take first value)
    for col in df.columns:
        if col not in numeric_cols and col != group_col:
            agg_dict[col] = 'first'
    
    return df.groupby(group_col).agg(agg_dict).reset_index()


def detect_outliers(data: List[float], method: str = 'iqr') -> List[int]:
    """
    Detect outliers in data
    
    Args:
        data (List[float]): Data to analyze
        method (str): Method to use ('iqr', 'zscore')
        
    Returns:
        List[int]: Indices of outliers
    """
    if len(data) < 4:
        return []
    
    outlier_indices = []
    
    if method == 'iqr':
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
    
    elif method == 'zscore':
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        if std_val == 0:
            return []
        
        for i, value in enumerate(data):
            z_score = abs((value - mean_val) / std_val)
            if z_score > 3:  # 3 standard deviations
                outlier_indices.append(i)
    
    return outlier_indices