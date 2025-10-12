import numpy as np
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from fmp_py.fmp_historical_charts import FmpHistoricalCharts
from fmp_py.models.historical_charts import (
    HistoricalPriceLight,
    HistoricalPriceFull,
    IntradayPrice,
)


@pytest.fixture
def fmp_charts():
    return FmpHistoricalCharts(api_key="test_api_key")


@pytest.fixture
def mock_light_response():
    return [
        {"date": "2024-01-01", "close": 150.0, "volume": 1000000},
        {"date": "2024-01-02", "close": 152.5, "volume": 1200000},
    ]


@pytest.fixture
def mock_full_response():
    return [
        {
            "date": "2024-01-01",
            "open": 148.0,
            "high": 155.0,
            "low": 147.0,
            "close": 150.0,
            "adjClose": 150.0,
            "volume": 1000000,
            "unadjustedVolume": 1000000,
            "change": 2.0,
            "changePercent": 1.35,
            "vwap": 150.5,
            "label": "January 01, 24",
            "changeOverTime": 0.0135,
        },
        {
            "date": "2024-01-02",
            "open": 150.0,
            "high": 156.0,
            "low": 149.0,
            "close": 152.5,
            "adjClose": 152.5,
            "volume": 1200000,
            "unadjustedVolume": 1200000,
            "change": 2.5,
            "changePercent": 1.67,
            "vwap": 152.0,
            "label": "January 02, 24",
            "changeOverTime": 0.0302,
        },
    ]


@pytest.fixture
def mock_intraday_response():
    return [
        {
            "date": "2024-01-01 09:30:00",
            "open": 148.0,
            "high": 149.0,
            "low": 147.5,
            "close": 148.5,
            "volume": 50000,
        },
        {
            "date": "2024-01-01 09:31:00",
            "open": 148.5,
            "high": 149.5,
            "low": 148.0,
            "close": 149.0,
            "volume": 45000,
        },
    ]


def test_fmp_historical_charts_init(fmp_charts):
    assert isinstance(fmp_charts, FmpHistoricalCharts)
    assert fmp_charts.api_key == "test_api_key"


class TestHistoricalPriceLight:
    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_light(self, mock_get_request, fmp_charts, mock_light_response):
        mock_get_request.return_value = mock_light_response
        
        result = fmp_charts.get_historical_price_light("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, HistoricalPriceLight) for item in result)
        assert result[0].date == "2024-01-01"
        assert result[0].close == 150.0
        assert result[0].volume == 1000000
        
        mock_get_request.assert_called_once_with("v3/historical-price-eod/light/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_light_with_dates(self, mock_get_request, fmp_charts, mock_light_response):
        mock_get_request.return_value = mock_light_response
        
        result = fmp_charts.get_historical_price_light("AAPL", "2024-01-01", "2024-01-02")
        
        expected_params = {"from": "2024-01-01", "to": "2024-01-02"}
        mock_get_request.assert_called_once_with("v3/historical-price-eod/light/AAPL", expected_params)
        assert len(result) == 2

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_light_df(self, mock_get_request, fmp_charts, mock_light_response):
        mock_get_request.return_value = mock_light_response
        
        result = fmp_charts.get_historical_price_light_df("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["date", "close", "volume"]
        assert result["date"].dtype == "datetime64[ns]"
        assert result["close"].dtype == "float64"
        assert result["volume"].dtype == "int64"

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_light_no_data(self, mock_get_request, fmp_charts):
        mock_get_request.return_value = []
        
        with pytest.raises(ValueError, match="No data found for symbol: INVALID"):
            fmp_charts.get_historical_price_light("INVALID")


class TestHistoricalPriceFull:
    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_full(self, mock_get_request, fmp_charts, mock_full_response):
        mock_get_request.return_value = mock_full_response
        
        result = fmp_charts.get_historical_price_full("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, HistoricalPriceFull) for item in result)
        assert result[0].date == "2024-01-01"
        assert result[0].open == 148.0
        assert result[0].high == 155.0
        assert result[0].low == 147.0
        assert result[0].close == 150.0
        assert result[0].adj_close == 150.0
        assert result[0].volume == 1000000
        assert result[0].vwap == 150.5
        
        mock_get_request.assert_called_once_with("v3/historical-price-eod/full/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_full_df(self, mock_get_request, fmp_charts, mock_full_response):
        mock_get_request.return_value = mock_full_response
        
        result = fmp_charts.get_historical_price_full_df("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        expected_columns = [
            "date", "open", "high", "low", "close", "adj_close", "volume",
            "unadjusted_volume", "change", "change_percent", "vwap", "label", "change_over_time"
        ]
        assert list(result.columns) == expected_columns
        assert result["date"].dtype == "datetime64[ns]"
        assert result["open"].dtype == "float64"
        assert result["volume"].dtype == "int64"

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_full_with_dates(self, mock_get_request, fmp_charts, mock_full_response):
        mock_get_request.return_value = mock_full_response
        
        result = fmp_charts.get_historical_price_full("AAPL", "2024-01-01", "2024-01-02")
        
        expected_params = {"from": "2024-01-01", "to": "2024-01-02"}
        mock_get_request.assert_called_once_with("v3/historical-price-eod/full/AAPL", expected_params)
        assert len(result) == 2


class TestUnadjustedHistoricalData:
    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_unadjusted(self, mock_get_request, fmp_charts):
        mock_response = [
            {"date": "2024-01-01", "open": 148.0, "high": 155.0, "low": 147.0, "close": 150.0, "volume": 1000000},
            {"date": "2024-01-02", "open": 150.0, "high": 156.0, "low": 149.0, "close": 152.5, "volume": 1200000},
        ]
        mock_get_request.return_value = mock_response
        
        result = fmp_charts.get_historical_price_unadjusted("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        expected_columns = ["date", "open", "high", "low", "close", "volume"]
        assert list(result.columns) == expected_columns
        
        mock_get_request.assert_called_once_with("v3/historical-price-eod/non-split-adjusted/AAPL", {})


class TestDividendAdjustedHistoricalData:
    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_historical_price_dividend_adjusted(self, mock_get_request, fmp_charts):
        mock_response = [
            {"date": "2024-01-01", "open": 148.0, "high": 155.0, "low": 147.0, "close": 150.0, "volume": 1000000},
            {"date": "2024-01-02", "open": 150.0, "high": 156.0, "low": 149.0, "close": 152.5, "volume": 1200000},
        ]
        mock_get_request.return_value = mock_response
        
        result = fmp_charts.get_historical_price_dividend_adjusted("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        expected_columns = ["date", "open", "high", "low", "close", "volume"]
        assert list(result.columns) == expected_columns
        
        mock_get_request.assert_called_once_with("v3/historical-price-eod/dividend-adjusted/AAPL", {})


class TestIntradayData:
    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_1min(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_1min("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, IntradayPrice) for item in result)
        assert result[0].date == "2024-01-01 09:30:00"
        assert result[0].open == 148.0
        assert result[0].close == 148.5
        assert result[0].volume == 50000
        
        mock_get_request.assert_called_once_with("v3/historical-chart/1min/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_1min_df(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_1min_df("AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        expected_columns = ["date", "open", "high", "low", "close", "volume"]
        assert list(result.columns) == expected_columns
        assert result["date"].dtype == "datetime64[ns]"

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_5min(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_5min("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        mock_get_request.assert_called_once_with("v3/historical-chart/5min/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_15min(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_15min("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        mock_get_request.assert_called_once_with("v3/historical-chart/15min/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_30min(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_30min("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        mock_get_request.assert_called_once_with("v3/historical-chart/30min/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_1hour(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_1hour("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        mock_get_request.assert_called_once_with("v3/historical-chart/1hour/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_4hour(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_4hour("AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        mock_get_request.assert_called_once_with("v3/historical-chart/4hour/AAPL", {})

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_with_parameters(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts.get_intraday_1min("AAPL", "2024-01-01", "2024-01-02", nonadjusted=True)
        
        expected_params = {"from": "2024-01-01", "to": "2024-01-02", "nonadjusted": "true"}
        mock_get_request.assert_called_once_with("v3/historical-chart/1min/AAPL", expected_params)
        assert len(result) == 2

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_no_data(self, mock_get_request, fmp_charts):
        mock_get_request.return_value = []
        
        with pytest.raises(ValueError, match="No data found for symbol: INVALID"):
            fmp_charts.get_intraday_1min("INVALID")


class TestHelperMethods:
    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_data_helper(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts._get_intraday_data("1min", "AAPL")
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, IntradayPrice) for item in result)

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_get_intraday_data_df_helper(self, mock_get_request, fmp_charts, mock_intraday_response):
        mock_get_request.return_value = mock_intraday_response
        
        result = fmp_charts._get_intraday_data_df("1min", "AAPL")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        expected_columns = ["date", "open", "high", "low", "close", "volume"]
        assert list(result.columns) == expected_columns


class TestErrorHandling:
    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_api_error_handling(self, mock_get_request, fmp_charts):
        mock_get_request.side_effect = Exception("API Error")
        
        with pytest.raises(ValueError, match="Error retrieving historical price light data"):
            fmp_charts.get_historical_price_light("AAPL")

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_empty_response_handling(self, mock_get_request, fmp_charts):
        mock_get_request.return_value = None
        
        with pytest.raises(ValueError, match="No data found for symbol"):
            fmp_charts.get_historical_price_full("AAPL")

    @patch.object(FmpHistoricalCharts, 'get_request')
    def test_invalid_symbol_handling(self, mock_get_request, fmp_charts):
        mock_get_request.return_value = []
        
        with pytest.raises(ValueError, match="No data found for symbol"):
            fmp_charts.get_historical_price_dividend_adjusted("INVALID_SYMBOL")