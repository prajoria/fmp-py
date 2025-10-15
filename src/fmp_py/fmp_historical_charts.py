from typing import List, Optional
import pandas as pd
from fmp_py.fmp_base import FmpBase
import os
import pendulum
from dotenv import load_dotenv

from fmp_py.models.historical_charts import (
    HistoricalPriceLight,
    HistoricalPriceFull,
    IntradayPrice,
)

load_dotenv()


class FmpHistoricalCharts(FmpBase):
    """
    Financial Modeling Prep Historical Charts API client.
    
    This class provides access to various chart data endpoints including:
    - Light historical price data (basic charting)
    - Full historical price data (comprehensive OHLC with additional metrics)
    - Unadjusted price data (without stock split adjustments)
    - Dividend adjusted price data
    - Intraday data with multiple time intervals (1min, 5min, 15min, 30min, 1hour, 4hour)
    """

    def __init__(self, api_key: str = os.getenv("FMP_API_KEY")):
        """
        Initialize the FmpHistoricalCharts class.

        Args:
            api_key (str): The API key for Financial Modeling Prep.
        """
        super().__init__(api_key)

    ##########################
    # Light Historical Data
    ##########################

    def get_historical_price_light(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[HistoricalPriceLight]:
        """
        Get simplified historical price data for a stock symbol.
        
        This API provides essential charting information, including date, price, and trading
        volume, making it ideal for tracking stock performance with minimal data.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format

        Returns:
            List[HistoricalPriceLight]: List of light historical price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        url = f"v3/historical-price-eod/light/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        try:
            response = self.get_request(url, params)
            if not response:
                raise ValueError(f"No data found for symbol: {symbol}")

            historical_data = []
            for item in response:
                data_dict = {
                    "date": self.clean_value(item.get("date", ""), str),
                    "close": self.clean_value(item.get("close", 0.0), float),
                    "volume": self.clean_value(item.get("volume", 0), int),
                }
                historical_data.append(HistoricalPriceLight(**data_dict))

            return historical_data

        except Exception as e:
            raise ValueError(f"Error retrieving historical price light data: {e}")

    def get_historical_price_light_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get simplified historical price data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: DataFrame containing historical price light data
        """
        url = f"v3/historical-price-eod/light/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = self.get_request(url, params)
        if not response:
            raise ValueError(f"No data found for symbol: {symbol}")

        df = pd.DataFrame(response)
        df["date"] = pd.to_datetime(df["date"])
        
        return df.astype({
            "date": "datetime64[ns]",
            "close": "float",
            "volume": "int",
        }).sort_values(by="date").reset_index(drop=True)

    ##########################
    # Full Historical Data
    ##########################

    def get_historical_price_full(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[HistoricalPriceFull]:
        """
        Get comprehensive historical price and volume data for a stock symbol.
        
        Provides detailed insights including OHLC prices, trading volume, price changes,
        percentage changes, and volume-weighted average price (VWAP).

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format

        Returns:
            List[HistoricalPriceFull]: List of comprehensive historical price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        url = f"api/v3/historical-price-full/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        try:
            response = self.get_request(url, params)
            if not response or not response.get('historical'):
                raise ValueError(f"No data found for symbol: {symbol}")

            historical_data = []
            for item in response.get('historical', []):
                data_dict = {
                    "date": self.clean_value(item.get("date", ""), str),
                    "open": self.clean_value(item.get("open", 0.0), float),
                    "high": self.clean_value(item.get("high", 0.0), float),
                    "low": self.clean_value(item.get("low", 0.0), float),
                    "close": self.clean_value(item.get("close", 0.0), float),
                    "adj_close": self.clean_value(item.get("adjClose", 0.0), float),
                    "volume": self.clean_value(item.get("volume", 0), int),
                    "unadjusted_volume": self.clean_value(item.get("unadjustedVolume", 0), int),
                    "change": self.clean_value(item.get("change", 0.0), float),
                    "change_percent": self.clean_value(item.get("changePercent", 0.0), float),
                    "vwap": self.clean_value(item.get("vwap", 0.0), float),
                    "label": self.clean_value(item.get("label", ""), str),
                    "change_over_time": self.clean_value(item.get("changeOverTime", 0.0), float),
                }
                historical_data.append(HistoricalPriceFull(**data_dict))

            return historical_data

        except Exception as e:
            raise ValueError(f"Error retrieving historical price full data: {e}")

    def get_historical_price_full_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get comprehensive historical price data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: DataFrame containing comprehensive historical price data
        """
        url = f"api/v3/historical-price-full/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = self.get_request(url, params)
        if not response or not response.get('historical'):
            raise ValueError(f"No data found for symbol: {symbol}")

        df = pd.DataFrame(response.get('historical', []))
        df["date"] = pd.to_datetime(df["date"])
        
        # Rename columns to match our naming convention
        df = df.rename(columns={
            "adjClose": "adj_close",
            "unadjustedVolume": "unadjusted_volume",
            "changePercent": "change_percent",
            "changeOverTime": "change_over_time"
        })
        
        return df.astype({
            "date": "datetime64[ns]",
            "open": "float",
            "high": "float", 
            "low": "float",
            "close": "float",
            "adj_close": "float",
            "volume": "int",
            "unadjusted_volume": "int",
            "change": "float",
            "change_percent": "float",
            "vwap": "float",
            "label": "str",
            "change_over_time": "float",
        }).sort_values(by="date").reset_index(drop=True)

    ##########################
    # Unadjusted Historical Data
    ##########################

    def get_historical_price_unadjusted(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical price data without stock split adjustments.
        
        Provides accurate insights into stock performance with original pricing
        without split-related changes.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: DataFrame containing unadjusted historical price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        url = f"v3/historical-price-eod/non-split-adjusted/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = self.get_request(url, params)
        if not response:
            raise ValueError(f"No data found for symbol: {symbol}")

        df = pd.DataFrame(response)
        df["date"] = pd.to_datetime(df["date"])
        
        return df.astype({
            "date": "datetime64[ns]",
            "open": "float",
            "high": "float",
            "low": "float", 
            "close": "float",
            "volume": "int",
        }).sort_values(by="date").reset_index(drop=True)

    ##########################
    # Dividend Adjusted Historical Data
    ##########################

    def get_historical_price_dividend_adjusted(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical price data adjusted for dividend payouts.
        
        Provides comprehensive view of stock trends accounting for dividend distributions.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format

        Returns:
            pd.DataFrame: DataFrame containing dividend-adjusted historical price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        url = f"v3/historical-price-eod/dividend-adjusted/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = self.get_request(url, params)
        if not response:
            raise ValueError(f"No data found for symbol: {symbol}")

        df = pd.DataFrame(response)
        df["date"] = pd.to_datetime(df["date"])
        
        return df.astype({
            "date": "datetime64[ns]",
            "open": "float",
            "high": "float",
            "low": "float",
            "close": "float",
            "volume": "int",
        }).sort_values(by="date").reset_index(drop=True)

    ##########################
    # Intraday Data - 1 Minute
    ##########################

    def get_intraday_1min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> List[IntradayPrice]:
        """
        Get 1-minute interval intraday stock price and volume data.
        
        Provides precise tracking of stock performance with minute-by-minute data.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            List[IntradayPrice]: List of 1-minute intraday price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        return self._get_intraday_data("1min", symbol, from_date, to_date, nonadjusted)

    def get_intraday_1min_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> pd.DataFrame:
        """
        Get 1-minute interval intraday data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            pd.DataFrame: DataFrame containing 1-minute intraday data
        """
        return self._get_intraday_data_df("1min", symbol, from_date, to_date, nonadjusted)

    ##########################
    # Intraday Data - 5 Minutes
    ##########################

    def get_intraday_5min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> List[IntradayPrice]:
        """
        Get 5-minute interval intraday stock price and volume data.
        
        Perfect for short-term trading analysis and building intraday charts.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            List[IntradayPrice]: List of 5-minute intraday price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        return self._get_intraday_data("5min", symbol, from_date, to_date, nonadjusted)

    def get_intraday_5min_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> pd.DataFrame:
        """
        Get 5-minute interval intraday data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            pd.DataFrame: DataFrame containing 5-minute intraday data
        """
        return self._get_intraday_data_df("5min", symbol, from_date, to_date, nonadjusted)

    ##########################
    # Intraday Data - 15 Minutes
    ##########################

    def get_intraday_15min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> List[IntradayPrice]:
        """
        Get 15-minute interval intraday stock price and volume data.
        
        Ideal for analyzing medium-term price trends during the trading day.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            List[IntradayPrice]: List of 15-minute intraday price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        return self._get_intraday_data("15min", symbol, from_date, to_date, nonadjusted)

    def get_intraday_15min_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> pd.DataFrame:
        """
        Get 15-minute interval intraday data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            pd.DataFrame: DataFrame containing 15-minute intraday data
        """
        return self._get_intraday_data_df("15min", symbol, from_date, to_date, nonadjusted)

    ##########################
    # Intraday Data - 30 Minutes
    ##########################

    def get_intraday_30min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> List[IntradayPrice]:
        """
        Get 30-minute interval intraday stock price and volume data.
        
        Perfect for tracking medium-term price movements for strategic trading decisions.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            List[IntradayPrice]: List of 30-minute intraday price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        return self._get_intraday_data("30min", symbol, from_date, to_date, nonadjusted)

    def get_intraday_30min_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> pd.DataFrame:
        """
        Get 30-minute interval intraday data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            pd.DataFrame: DataFrame containing 30-minute intraday data
        """
        return self._get_intraday_data_df("30min", symbol, from_date, to_date, nonadjusted)

    ##########################
    # Intraday Data - 1 Hour
    ##########################

    def get_intraday_1hour(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> List[IntradayPrice]:
        """
        Get 1-hour interval intraday stock price and volume data.
        
        Provides analysis of broader intraday trends with precision.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            List[IntradayPrice]: List of 1-hour intraday price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        return self._get_intraday_data("1hour", symbol, from_date, to_date, nonadjusted)

    def get_intraday_1hour_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> pd.DataFrame:
        """
        Get 1-hour interval intraday data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            pd.DataFrame: DataFrame containing 1-hour intraday data
        """
        return self._get_intraday_data_df("1hour", symbol, from_date, to_date, nonadjusted)

    ##########################
    # Intraday Data - 4 Hours
    ##########################

    def get_intraday_4hour(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> List[IntradayPrice]:
        """
        Get 4-hour interval intraday stock price and volume data.
        
        Perfect for tracking longer intraday trends and broader market movements.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            List[IntradayPrice]: List of 4-hour intraday price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        return self._get_intraday_data("4hour", symbol, from_date, to_date, nonadjusted)

    def get_intraday_4hour_df(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> pd.DataFrame:
        """
        Get 4-hour interval intraday data as a DataFrame.

        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            nonadjusted (bool): Include non-adjusted data

        Returns:
            pd.DataFrame: DataFrame containing 4-hour intraday data
        """
        return self._get_intraday_data_df("4hour", symbol, from_date, to_date, nonadjusted)

    ##########################
    # Helper Methods
    ##########################

    def _get_intraday_data(
        self,
        interval: str,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> List[IntradayPrice]:
        """
        Helper method to get intraday data for various intervals.

        Args:
            interval (str): Time interval (1min, 5min, 15min, 30min, 1hour, 4hour)
            symbol (str): Stock symbol
            from_date (Optional[str]): Start date
            to_date (Optional[str]): End date
            nonadjusted (bool): Include non-adjusted data

        Returns:
            List[IntradayPrice]: List of intraday price data

        Raises:
            ValueError: If no data is found for the given symbol
        """
        url = f"v3/historical-chart/{interval}/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if nonadjusted:
            params["nonadjusted"] = str(nonadjusted).lower()

        try:
            response = self.get_request(url, params)
            if not response:
                raise ValueError(f"No data found for symbol: {symbol}")

            intraday_data = []
            for item in response:
                data_dict = {
                    "date": self.clean_value(item.get("date", ""), str),
                    "open": self.clean_value(item.get("open", 0.0), float),
                    "high": self.clean_value(item.get("high", 0.0), float),
                    "low": self.clean_value(item.get("low", 0.0), float),
                    "close": self.clean_value(item.get("close", 0.0), float),
                    "volume": self.clean_value(item.get("volume", 0), int),
                }
                intraday_data.append(IntradayPrice(**data_dict))

            return intraday_data

        except Exception as e:
            raise ValueError(f"Error retrieving {interval} intraday data: {e}")

    def _get_intraday_data_df(
        self,
        interval: str,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        nonadjusted: bool = False
    ) -> pd.DataFrame:
        """
        Helper method to get intraday data as DataFrame for various intervals.

        Args:
            interval (str): Time interval (1min, 5min, 15min, 30min, 1hour, 4hour)
            symbol (str): Stock symbol
            from_date (Optional[str]): Start date
            to_date (Optional[str]): End date
            nonadjusted (bool): Include non-adjusted data

        Returns:
            pd.DataFrame: DataFrame containing intraday data
        """
        url = f"v3/historical-chart/{interval}/{symbol}"
        params = {}
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if nonadjusted:
            params["nonadjusted"] = str(nonadjusted).lower()

        response = self.get_request(url, params)
        if not response:
            raise ValueError(f"No data found for symbol: {symbol}")

        df = pd.DataFrame(response)
        df["date"] = pd.to_datetime(df["date"])
        
        return df.astype({
            "date": "datetime64[ns]",
            "open": "float",
            "high": "float",
            "low": "float",
            "close": "float", 
            "volume": "int",
        }).sort_values(by="date").reset_index(drop=True)