"""
FMP Technical Indicators Module

This module provides access to Financial Modeling Prep's Technical Indicators API.
It includes various technical analysis indicators such as moving averages, momentum oscillators,
trend indicators, and volatility measures.

Author: FMP-PY Team
Date: October 2025
"""

import pandas as pd
from fmp_py.fmp_base import FmpBase
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date


class FmpTechnicalIndicators(FmpBase):
    """
    A class to interact with Financial Modeling Prep's Technical Indicators API.
    
    This class provides methods to fetch various technical indicators including:
    - Moving Averages (SMA, EMA, WMA, DEMA, TEMA)
    - Momentum Oscillators (RSI, Williams %R)
    - Trend Indicators (ADX)
    - Volatility Indicators (Standard Deviation)
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the FmpTechnicalIndicators class.

        Args:
            api_key (str, optional): API key for Financial Modeling Prep.
                                   If not provided, will use FMP_API_KEY environment variable.
        """
        super().__init__(api_key)

    def _validate_timeframe(self, timeframe: str) -> None:
        """
        Validate the timeframe parameter.

        Args:
            timeframe (str): The timeframe to validate.

        Raises:
            ValueError: If timeframe is not supported.
        """
        valid_timeframes = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day']
        if timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe '{timeframe}'. Must be one of: {valid_timeframes}")

    def _validate_symbol(self, symbol: str) -> None:
        """
        Validate the symbol parameter.

        Args:
            symbol (str): The symbol to validate.

        Raises:
            ValueError: If symbol is invalid.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")

    def _validate_period_length(self, period_length: int) -> None:
        """
        Validate the period length parameter.

        Args:
            period_length (int): The period length to validate.

        Raises:
            ValueError: If period length is invalid.
        """
        if not isinstance(period_length, int) or period_length <= 0:
            raise ValueError("Period length must be a positive integer")

    def _format_date(self, date_param: Union[str, date, datetime]) -> str:
        """
        Format date parameter to YYYY-MM-DD string.

        Args:
            date_param: Date parameter to format.

        Returns:
            str: Formatted date string.
        """
        if isinstance(date_param, str):
            return date_param
        elif isinstance(date_param, (date, datetime)):
            return date_param.strftime('%Y-%m-%d')
        else:
            raise ValueError("Date must be string, date, or datetime object")

    def _get_technical_indicator(
        self,
        indicator: str,
        symbol: str,
        period_length: int,
        timeframe: str,
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Generic method to fetch technical indicator data.

        Args:
            indicator (str): Technical indicator name.
            symbol (str): Stock symbol.
            period_length (int): Number of periods for calculation.
            timeframe (str): Time interval.
            from_date (optional): Start date.
            to_date (optional): End date.

        Returns:
            pd.DataFrame: Technical indicator data.

        Raises:
            ValueError: If parameters are invalid.
            Exception: If API request fails.
        """
        # Validate parameters
        self._validate_symbol(symbol)
        self._validate_period_length(period_length)
        self._validate_timeframe(timeframe)

        # Build parameters
        params = {
            'symbol': symbol.upper(),
            'periodLength': period_length,
            'timeframe': timeframe
        }

        if from_date:
            params['from'] = self._format_date(from_date)
        if to_date:
            params['to'] = self._format_date(to_date)

        # Make API request
        endpoint = f"v3/technical_indicator/{indicator}"
        data = self.get_request(endpoint, params)

        if not data:
            raise ValueError(f"No data returned for {symbol} with {indicator}")

        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

        return self.fill_na(df)

    # Moving Averages

    def simple_moving_average(
        self,
        symbol: str,
        period_length: int = 20,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Simple Moving Average (SMA) data.

        The Simple Moving Average calculates the average price over a specified number of periods.
        It's used to smooth out price fluctuations and identify trend direction.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 20.
                               Common values: 10, 20, 50, 100, 200.
            timeframe (str): Time interval. Default is '1day'.
                           Options: '1min', '5min', '15min', '30min', '1hour', '4hour', '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and SMA values.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> sma_data = fmp.simple_moving_average('AAPL', period_length=20)
            >>> print(sma_data.head())
        """
        return self._get_technical_indicator('sma', symbol, period_length, timeframe, from_date, to_date)

    def exponential_moving_average(
        self,
        symbol: str,
        period_length: int = 12,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Exponential Moving Average (EMA) data.

        The Exponential Moving Average gives more weight to recent prices, making it more
        responsive to new information compared to SMA.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 12.
                               Common values: 12, 26 (for MACD), 9, 21.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and EMA values.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> ema_data = fmp.exponential_moving_average('AAPL', period_length=12)
            >>> print(ema_data.head())
        """
        return self._get_technical_indicator('ema', symbol, period_length, timeframe, from_date, to_date)

    def weighted_moving_average(
        self,
        symbol: str,
        period_length: int = 20,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Weighted Moving Average (WMA) data.

        The Weighted Moving Average assigns different weights to each data point,
        with more recent data having higher weights.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 20.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and WMA values.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> wma_data = fmp.weighted_moving_average('AAPL', period_length=20)
            >>> print(wma_data.head())
        """
        return self._get_technical_indicator('wma', symbol, period_length, timeframe, from_date, to_date)

    def double_exponential_moving_average(
        self,
        symbol: str,
        period_length: int = 21,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Double Exponential Moving Average (DEMA) data.

        DEMA is a smoothed EMA that reduces lag while maintaining sensitivity to price changes.
        It's calculated by applying EMA to EMA.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 21.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and DEMA values.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> dema_data = fmp.double_exponential_moving_average('AAPL', period_length=21)
            >>> print(dema_data.head())
        """
        return self._get_technical_indicator('dema', symbol, period_length, timeframe, from_date, to_date)

    def triple_exponential_moving_average(
        self,
        symbol: str,
        period_length: int = 21,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Triple Exponential Moving Average (TEMA) data.

        TEMA further reduces lag compared to DEMA while maintaining responsiveness.
        It's calculated by applying EMA three times.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 21.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and TEMA values.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> tema_data = fmp.triple_exponential_moving_average('AAPL', period_length=21)
            >>> print(tema_data.head())
        """
        return self._get_technical_indicator('tema', symbol, period_length, timeframe, from_date, to_date)

    # Momentum Oscillators

    def relative_strength_index(
        self,
        symbol: str,
        period_length: int = 14,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Relative Strength Index (RSI) data.

        RSI measures the speed and change of price movements, ranging from 0 to 100.
        It's used to identify overbought (>70) and oversold (<30) conditions.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 14.
                               Common values: 14, 21.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and RSI values.

        Interpretation:
            - RSI > 70: Potentially overbought (sell signal)
            - RSI < 30: Potentially oversold (buy signal)
            - RSI around 50: Neutral momentum

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> rsi_data = fmp.relative_strength_index('AAPL', period_length=14)
            >>> print(rsi_data.head())
            >>> 
            >>> # Check for overbought/oversold conditions
            >>> overbought = rsi_data[rsi_data['rsi'] > 70]
            >>> oversold = rsi_data[rsi_data['rsi'] < 30]
        """
        return self._get_technical_indicator('rsi', symbol, period_length, timeframe, from_date, to_date)

    def williams_percent_r(
        self,
        symbol: str,
        period_length: int = 14,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Williams %R data.

        Williams %R is a momentum oscillator that measures overbought and oversold levels.
        It ranges from 0 to -100, with readings above -20 indicating overbought conditions
        and readings below -80 indicating oversold conditions.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 14.
                               Common values: 14, 20.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and Williams %R values.

        Interpretation:
            - Williams %R > -20: Overbought condition
            - Williams %R < -80: Oversold condition

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> williams_data = fmp.williams_percent_r('AAPL', period_length=14)
            >>> print(williams_data.head())
            >>> 
            >>> # Check for overbought/oversold conditions
            >>> overbought = williams_data[williams_data['williams'] > -20]
            >>> oversold = williams_data[williams_data['williams'] < -80]
        """
        return self._get_technical_indicator('williams', symbol, period_length, timeframe, from_date, to_date)

    # Trend Indicators

    def average_directional_index(
        self,
        symbol: str,
        period_length: int = 14,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Average Directional Index (ADX) data.

        ADX measures the strength of a trend regardless of direction. It ranges from 0 to 100,
        with higher values indicating stronger trends.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 14.
                               Common values: 14, 20.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and ADX values.

        Interpretation:
            - ADX > 25: Strong trend
            - ADX < 20: Weak trend or sideways movement
            - ADX between 20-25: Moderate trend

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> adx_data = fmp.average_directional_index('AAPL', period_length=14)
            >>> print(adx_data.head())
            >>> 
            >>> # Identify strong trends
            >>> strong_trends = adx_data[adx_data['adx'] > 25]
            >>> weak_trends = adx_data[adx_data['adx'] < 20]
        """
        return self._get_technical_indicator('adx', symbol, period_length, timeframe, from_date, to_date)

    # Volatility Indicators

    def standard_deviation(
        self,
        symbol: str,
        period_length: int = 20,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get Standard Deviation data.

        Standard Deviation measures the amount of variation or dispersion in price movements.
        Higher values indicate greater volatility.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT').
            period_length (int): Number of periods for calculation. Default is 20.
                               Common values: 10, 20, 30.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame containing OHLCV data and Standard Deviation values.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> std_data = fmp.standard_deviation('AAPL', period_length=20)
            >>> print(std_data.head())
            >>> 
            >>> # Identify high volatility periods
            >>> high_volatility = std_data[std_data['standardDeviation'] > std_data['standardDeviation'].mean()]
        """
        return self._get_technical_indicator('standarddeviation', symbol, period_length, timeframe, from_date, to_date)

    # Convenience Methods

    def get_multiple_indicators(
        self,
        symbol: str,
        indicators: List[str],
        period_length: int = 14,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Get multiple technical indicators for a symbol.

        Args:
            symbol (str): Stock symbol.
            indicators (List[str]): List of indicator names.
                                  Available: 'sma', 'ema', 'wma', 'dema', 'tema', 'rsi', 'williams', 'adx', 'standarddeviation'
            period_length (int): Number of periods for calculation. Default is 14.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            Dict[str, pd.DataFrame]: Dictionary with indicator names as keys and DataFrames as values.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> indicators = ['sma', 'rsi', 'adx']
            >>> data = fmp.get_multiple_indicators('AAPL', indicators, period_length=20)
            >>> for indicator, df in data.items():
            ...     print(f"{indicator}: {len(df)} rows")
        """
        indicator_methods = {
            'sma': self.simple_moving_average,
            'ema': self.exponential_moving_average,
            'wma': self.weighted_moving_average,
            'dema': self.double_exponential_moving_average,
            'tema': self.triple_exponential_moving_average,
            'rsi': self.relative_strength_index,
            'williams': self.williams_percent_r,
            'adx': self.average_directional_index,
            'standarddeviation': self.standard_deviation
        }

        results = {}
        for indicator in indicators:
            if indicator in indicator_methods:
                try:
                    results[indicator] = indicator_methods[indicator](
                        symbol, period_length, timeframe, from_date, to_date
                    )
                except Exception as e:
                    print(f"Error fetching {indicator} for {symbol}: {e}")
            else:
                print(f"Unknown indicator: {indicator}")

        return results

    def get_trading_signals(
        self,
        symbol: str,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get basic trading signals based on RSI and Williams %R.

        Args:
            symbol (str): Stock symbol.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame with RSI, Williams %R and basic trading signals.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> signals = fmp.get_trading_signals('AAPL')
            >>> buy_signals = signals[signals['signal'] == 'BUY']
            >>> sell_signals = signals[signals['signal'] == 'SELL']
        """
        try:
            # Get RSI and Williams %R data
            rsi_data = self.relative_strength_index(symbol, 14, timeframe, from_date, to_date)
            williams_data = self.williams_percent_r(symbol, 14, timeframe, from_date, to_date)

            # Merge data on date
            merged = pd.merge(rsi_data[['date', 'close', 'rsi']], 
                            williams_data[['date', 'williams']], 
                            on='date', how='inner')

            # Generate signals
            def get_signal(rsi, williams):
                if rsi < 30 and williams < -80:
                    return 'STRONG_BUY'
                elif rsi < 30 or williams < -80:
                    return 'BUY'
                elif rsi > 70 and williams > -20:
                    return 'STRONG_SELL'
                elif rsi > 70 or williams > -20:
                    return 'SELL'
                else:
                    return 'HOLD'

            merged['signal'] = merged.apply(lambda row: get_signal(row['rsi'], row['williams']), axis=1)

            return merged

        except Exception as e:
            raise Exception(f"Error generating trading signals for {symbol}: {e}")

    def get_trend_analysis(
        self,
        symbol: str,
        timeframe: str = '1day',
        from_date: Optional[Union[str, date, datetime]] = None,
        to_date: Optional[Union[str, date, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get trend analysis using SMA, EMA, and ADX.

        Args:
            symbol (str): Stock symbol.
            timeframe (str): Time interval. Default is '1day'.
            from_date (optional): Start date for data range.
            to_date (optional): End date for data range.

        Returns:
            pd.DataFrame: DataFrame with moving averages, ADX, and trend analysis.

        Example:
            >>> fmp = FmpTechnicalIndicators()
            >>> trend = fmp.get_trend_analysis('AAPL')
            >>> strong_uptrends = trend[(trend['trend_direction'] == 'UPTREND') & (trend['trend_strength'] == 'STRONG')]
        """
        try:
            # Get indicators
            sma_20 = self.simple_moving_average(symbol, 20, timeframe, from_date, to_date)
            sma_50 = self.simple_moving_average(symbol, 50, timeframe, from_date, to_date)
            ema_12 = self.exponential_moving_average(symbol, 12, timeframe, from_date, to_date)
            adx_data = self.average_directional_index(symbol, 14, timeframe, from_date, to_date)

            # Merge data
            merged = pd.merge(sma_20[['date', 'close', 'sma']], 
                            sma_50[['date', 'sma']], 
                            on='date', how='inner', suffixes=('_20', '_50'))
            merged = pd.merge(merged, 
                            ema_12[['date', 'ema']], 
                            on='date', how='inner')
            merged = pd.merge(merged, 
                            adx_data[['date', 'adx']], 
                            on='date', how='inner')

            # Determine trend direction
            def get_trend_direction(close, sma_20, sma_50, ema_12):
                if close > sma_20 > sma_50 and close > ema_12:
                    return 'STRONG_UPTREND'
                elif close > sma_20 and close > ema_12:
                    return 'UPTREND'
                elif close < sma_20 < sma_50 and close < ema_12:
                    return 'STRONG_DOWNTREND'
                elif close < sma_20 and close < ema_12:
                    return 'DOWNTREND'
                else:
                    return 'SIDEWAYS'

            # Determine trend strength based on ADX
            def get_trend_strength(adx):
                if adx > 25:
                    return 'STRONG'
                elif adx > 20:
                    return 'MODERATE'
                else:
                    return 'WEAK'

            merged['trend_direction'] = merged.apply(
                lambda row: get_trend_direction(row['close'], row['sma_20'], row['sma_50'], row['ema']), 
                axis=1
            )
            merged['trend_strength'] = merged['adx'].apply(get_trend_strength)

            return merged

        except Exception as e:
            raise Exception(f"Error generating trend analysis for {symbol}: {e}")