"""
Test module for FmpTechnicalIndicators class.

This module contains comprehensive tests for all technical indicators
including moving averages, momentum oscillators, trend indicators, and volatility measures.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock
from datetime import datetime, date

from fmp_py.fmp_technical_indicators import FmpTechnicalIndicators


@pytest.fixture
def fmp_technical_indicators():
    """Create FmpTechnicalIndicators instance for testing."""
    return FmpTechnicalIndicators(api_key='test_api_key')


@pytest.fixture
def sample_indicator_data():
    """Sample technical indicator response data."""
    return [
        {
            "date": "2025-02-04 00:00:00",
            "open": 227.2,
            "high": 233.13,
            "low": 226.65,
            "close": 232.8,
            "volume": 44489128,
            "sma": 231.215
        },
        {
            "date": "2025-02-03 00:00:00",
            "open": 225.5,
            "high": 230.0,
            "low": 224.0,
            "close": 228.5,
            "volume": 35000000,
            "sma": 230.0
        }
    ]


class TestFmpTechnicalIndicators:
    """Test class for FmpTechnicalIndicators."""

    def test_init(self, fmp_technical_indicators):
        """Test FmpTechnicalIndicators initialization."""
        assert isinstance(fmp_technical_indicators, FmpTechnicalIndicators)

    def test_validate_timeframe_valid(self, fmp_technical_indicators):
        """Test timeframe validation with valid values."""
        valid_timeframes = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day']
        for timeframe in valid_timeframes:
            # Should not raise exception
            fmp_technical_indicators._validate_timeframe(timeframe)

    def test_validate_timeframe_invalid(self, fmp_technical_indicators):
        """Test timeframe validation with invalid values."""
        invalid_timeframes = ['2min', '1week', '1month', '', None]
        for timeframe in invalid_timeframes:
            with pytest.raises(ValueError):
                fmp_technical_indicators._validate_timeframe(timeframe)

    def test_validate_symbol_valid(self, fmp_technical_indicators):
        """Test symbol validation with valid values."""
        valid_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        for symbol in valid_symbols:
            # Should not raise exception
            fmp_technical_indicators._validate_symbol(symbol)

    def test_validate_symbol_invalid(self, fmp_technical_indicators):
        """Test symbol validation with invalid values."""
        invalid_symbols = ['', None, 123, []]
        for symbol in invalid_symbols:
            with pytest.raises(ValueError):
                fmp_technical_indicators._validate_symbol(symbol)

    def test_validate_period_length_valid(self, fmp_technical_indicators):
        """Test period length validation with valid values."""
        valid_periods = [1, 10, 14, 20, 50, 100, 200]
        for period in valid_periods:
            # Should not raise exception
            fmp_technical_indicators._validate_period_length(period)

    def test_validate_period_length_invalid(self, fmp_technical_indicators):
        """Test period length validation with invalid values."""
        invalid_periods = [0, -1, 'string', None, 1.5]
        for period in invalid_periods:
            with pytest.raises(ValueError):
                fmp_technical_indicators._validate_period_length(period)

    def test_format_date(self, fmp_technical_indicators):
        """Test date formatting."""
        # String date
        assert fmp_technical_indicators._format_date('2025-01-01') == '2025-01-01'
        
        # Date object
        assert fmp_technical_indicators._format_date(date(2025, 1, 1)) == '2025-01-01'
        
        # Datetime object
        assert fmp_technical_indicators._format_date(datetime(2025, 1, 1, 12, 30)) == '2025-01-01'
        
        # Invalid date
        with pytest.raises(ValueError):
            fmp_technical_indicators._format_date(123)

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_simple_moving_average(self, mock_get_request, fmp_technical_indicators, sample_indicator_data):
        """Test simple moving average method."""
        mock_get_request.return_value = sample_indicator_data
        
        result = fmp_technical_indicators.simple_moving_average('AAPL', period_length=20)
        
        assert isinstance(result, pd.DataFrame)
        assert 'sma' in result.columns
        assert 'date' in result.columns
        assert len(result) == 2
        assert pd.api.types.is_datetime64_any_dtype(result['date'])
        
        # Verify API call
        mock_get_request.assert_called_once_with(
            'v3/technical_indicator/sma',
            {'symbol': 'AAPL', 'periodLength': 20, 'timeframe': '1day'}
        )

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_exponential_moving_average(self, mock_get_request, fmp_technical_indicators):
        """Test exponential moving average method."""
        sample_data = [
            {
                "date": "2025-02-04 00:00:00",
                "open": 227.2,
                "high": 233.13,
                "low": 226.65,
                "close": 232.8,
                "volume": 44489128,
                "ema": 232.84
            }
        ]
        mock_get_request.return_value = sample_data
        
        result = fmp_technical_indicators.exponential_moving_average('AAPL', period_length=12)
        
        assert isinstance(result, pd.DataFrame)
        assert 'ema' in result.columns
        assert len(result) == 1

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_relative_strength_index(self, mock_get_request, fmp_technical_indicators):
        """Test RSI method."""
        sample_data = [
            {
                "date": "2025-02-04 00:00:00",
                "open": 227.2,
                "high": 233.13,
                "low": 226.65,
                "close": 232.8,
                "volume": 44489128,
                "rsi": 47.65
            }
        ]
        mock_get_request.return_value = sample_data
        
        result = fmp_technical_indicators.relative_strength_index('AAPL', period_length=14)
        
        assert isinstance(result, pd.DataFrame)
        assert 'rsi' in result.columns
        assert len(result) == 1
        assert 0 <= result.iloc[0]['rsi'] <= 100

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_williams_percent_r(self, mock_get_request, fmp_technical_indicators):
        """Test Williams %R method."""
        sample_data = [
            {
                "date": "2025-02-04 00:00:00",
                "open": 227.2,
                "high": 233.13,
                "low": 226.65,
                "close": 232.8,
                "volume": 44489128,
                "williams": -52.52
            }
        ]
        mock_get_request.return_value = sample_data
        
        result = fmp_technical_indicators.williams_percent_r('AAPL', period_length=14)
        
        assert isinstance(result, pd.DataFrame)
        assert 'williams' in result.columns
        assert len(result) == 1
        assert -100 <= result.iloc[0]['williams'] <= 0

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_average_directional_index(self, mock_get_request, fmp_technical_indicators):
        """Test ADX method."""
        sample_data = [
            {
                "date": "2025-02-04 00:00:00",
                "open": 227.2,
                "high": 233.13,
                "low": 226.65,
                "close": 232.8,
                "volume": 44489128,
                "adx": 26.41
            }
        ]
        mock_get_request.return_value = sample_data
        
        result = fmp_technical_indicators.average_directional_index('AAPL', period_length=14)
        
        assert isinstance(result, pd.DataFrame)
        assert 'adx' in result.columns
        assert len(result) == 1
        assert 0 <= result.iloc[0]['adx'] <= 100

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_standard_deviation(self, mock_get_request, fmp_technical_indicators):
        """Test Standard Deviation method."""
        sample_data = [
            {
                "date": "2025-02-04 00:00:00",
                "open": 227.2,
                "high": 233.13,
                "low": 226.65,
                "close": 232.8,
                "volume": 44489128,
                "standardDeviation": 6.14
            }
        ]
        mock_get_request.return_value = sample_data
        
        result = fmp_technical_indicators.standard_deviation('AAPL', period_length=20)
        
        assert isinstance(result, pd.DataFrame)
        assert 'standardDeviation' in result.columns
        assert len(result) == 1
        assert result.iloc[0]['standardDeviation'] >= 0

    def test_with_date_parameters(self, fmp_technical_indicators):
        """Test methods with date parameters."""
        with patch.object(fmp_technical_indicators, 'get_request') as mock_get_request:
            mock_get_request.return_value = [
                {
                    "date": "2025-02-04 00:00:00",
                    "open": 227.2,
                    "high": 233.13,
                    "low": 226.65,
                    "close": 232.8,
                    "volume": 44489128,
                    "sma": 231.215
                }
            ]
            
            # Test with string dates
            fmp_technical_indicators.simple_moving_average(
                'AAPL', 
                period_length=20,
                from_date='2025-01-01',
                to_date='2025-02-01'
            )
            
            # Test with date objects
            fmp_technical_indicators.simple_moving_average(
                'AAPL', 
                period_length=20,
                from_date=date(2025, 1, 1),
                to_date=date(2025, 2, 1)
            )
            
            # Verify API calls include date parameters
            assert mock_get_request.call_count == 2
            for call in mock_get_request.call_args_list:
                params = call[0][1]  # Second argument (params)
                assert 'from' in params
                assert 'to' in params

    def test_invalid_symbol_raises_error(self, fmp_technical_indicators):
        """Test that invalid symbol raises ValueError."""
        with pytest.raises(ValueError):
            fmp_technical_indicators.simple_moving_average('', period_length=20)

    def test_invalid_period_length_raises_error(self, fmp_technical_indicators):
        """Test that invalid period length raises ValueError."""
        with pytest.raises(ValueError):
            fmp_technical_indicators.simple_moving_average('AAPL', period_length=0)

    def test_invalid_timeframe_raises_error(self, fmp_technical_indicators):
        """Test that invalid timeframe raises ValueError."""
        with pytest.raises(ValueError):
            fmp_technical_indicators.simple_moving_average('AAPL', period_length=20, timeframe='invalid')

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_empty_data_raises_error(self, mock_get_request, fmp_technical_indicators):
        """Test that empty data raises ValueError."""
        mock_get_request.return_value = []
        
        with pytest.raises(ValueError):
            fmp_technical_indicators.simple_moving_average('INVALID', period_length=20)

    @patch.object(FmpTechnicalIndicators, 'get_request')
    def test_get_multiple_indicators(self, mock_get_request, fmp_technical_indicators):
        """Test getting multiple indicators."""
        mock_get_request.return_value = [
            {
                "date": "2025-02-04 00:00:00",
                "open": 227.2,
                "high": 233.13,
                "low": 226.65,
                "close": 232.8,
                "volume": 44489128,
                "sma": 231.215
            }
        ]
        
        indicators = ['sma', 'rsi', 'adx']
        result = fmp_technical_indicators.get_multiple_indicators('AAPL', indicators, period_length=20)
        
        assert isinstance(result, dict)
        assert len(result) == 3
        assert all(indicator in result for indicator in indicators)
        assert all(isinstance(df, pd.DataFrame) for df in result.values())

    @patch.object(FmpTechnicalIndicators, 'relative_strength_index')
    @patch.object(FmpTechnicalIndicators, 'williams_percent_r')
    def test_get_trading_signals(self, mock_williams, mock_rsi, fmp_technical_indicators):
        """Test trading signals generation."""
        # Mock RSI data
        rsi_data = pd.DataFrame({
            'date': pd.to_datetime(['2025-02-04', '2025-02-03']),
            'close': [232.8, 228.5],
            'rsi': [25.0, 75.0]  # Oversold, then overbought
        })
        
        # Mock Williams %R data
        williams_data = pd.DataFrame({
            'date': pd.to_datetime(['2025-02-04', '2025-02-03']),
            'williams': [-85.0, -15.0]  # Oversold, then overbought
        })
        
        mock_rsi.return_value = rsi_data
        mock_williams.return_value = williams_data
        
        result = fmp_technical_indicators.get_trading_signals('AAPL')
        
        assert isinstance(result, pd.DataFrame)
        assert 'signal' in result.columns
        assert 'rsi' in result.columns
        assert 'williams' in result.columns
        assert len(result) == 2
        
        # Check signal generation
        assert result.iloc[0]['signal'] == 'STRONG_BUY'  # Both oversold
        assert result.iloc[1]['signal'] == 'STRONG_SELL'  # Both overbought

    @patch.object(FmpTechnicalIndicators, 'simple_moving_average')
    @patch.object(FmpTechnicalIndicators, 'exponential_moving_average')
    @patch.object(FmpTechnicalIndicators, 'average_directional_index')
    def test_get_trend_analysis(self, mock_adx, mock_ema, mock_sma, fmp_technical_indicators):
        """Test trend analysis generation."""
        # Mock SMA 20 data
        sma_20_data = pd.DataFrame({
            'date': pd.to_datetime(['2025-02-04']),
            'close': [232.8],
            'sma': [230.0]
        })
        
        # Mock SMA 50 data
        sma_50_data = pd.DataFrame({
            'date': pd.to_datetime(['2025-02-04']),
            'sma': [225.0]
        })
        
        # Mock EMA 12 data
        ema_12_data = pd.DataFrame({
            'date': pd.to_datetime(['2025-02-04']),
            'ema': [231.0]
        })
        
        # Mock ADX data
        adx_data = pd.DataFrame({
            'date': pd.to_datetime(['2025-02-04']),
            'adx': [30.0]
        })
        
        # Configure mocks to return different data based on period_length
        def sma_side_effect(symbol, period_length, *args, **kwargs):
            if period_length == 20:
                return sma_20_data
            elif period_length == 50:
                return sma_50_data
        
        mock_sma.side_effect = sma_side_effect
        mock_ema.return_value = ema_12_data
        mock_adx.return_value = adx_data
        
        result = fmp_technical_indicators.get_trend_analysis('AAPL')
        
        assert isinstance(result, pd.DataFrame)
        assert 'trend_direction' in result.columns
        assert 'trend_strength' in result.columns
        assert len(result) == 1
        
        # Check trend analysis (close > sma_20 > sma_50 and close > ema = STRONG_UPTREND)
        assert result.iloc[0]['trend_direction'] == 'STRONG_UPTREND'
        assert result.iloc[0]['trend_strength'] == 'STRONG'  # ADX > 25


class TestTechnicalIndicatorMethods:
    """Test individual technical indicator methods."""

    @pytest.fixture
    def fmp_ti(self):
        return FmpTechnicalIndicators(api_key='test_api_key')

    def test_all_moving_average_methods(self, fmp_ti):
        """Test that all moving average methods exist and are callable."""
        ma_methods = [
            'simple_moving_average',
            'exponential_moving_average',
            'weighted_moving_average',
            'double_exponential_moving_average',
            'triple_exponential_moving_average'
        ]
        
        for method_name in ma_methods:
            assert hasattr(fmp_ti, method_name)
            assert callable(getattr(fmp_ti, method_name))

    def test_all_oscillator_methods(self, fmp_ti):
        """Test that all oscillator methods exist and are callable."""
        oscillator_methods = [
            'relative_strength_index',
            'williams_percent_r'
        ]
        
        for method_name in oscillator_methods:
            assert hasattr(fmp_ti, method_name)
            assert callable(getattr(fmp_ti, method_name))

    def test_all_trend_methods(self, fmp_ti):
        """Test that all trend indicator methods exist and are callable."""
        trend_methods = [
            'average_directional_index'
        ]
        
        for method_name in trend_methods:
            assert hasattr(fmp_ti, method_name)
            assert callable(getattr(fmp_ti, method_name))

    def test_all_volatility_methods(self, fmp_ti):
        """Test that all volatility indicator methods exist and are callable."""
        volatility_methods = [
            'standard_deviation'
        ]
        
        for method_name in volatility_methods:
            assert hasattr(fmp_ti, method_name)
            assert callable(getattr(fmp_ti, method_name))


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def fmp_ti(self):
        return FmpTechnicalIndicators(api_key='test_api_key')

    def test_network_error_handling(self, fmp_ti):
        """Test handling of network errors."""
        with patch.object(fmp_ti, 'get_request', side_effect=Exception("Network error")):
            with pytest.raises(Exception):
                fmp_ti.simple_moving_average('AAPL', period_length=20)

    def test_malformed_data_handling(self, fmp_ti):
        """Test handling of malformed API response data."""
        with patch.object(fmp_ti, 'get_request', return_value=None):
            with pytest.raises(ValueError):
                fmp_ti.simple_moving_average('AAPL', period_length=20)

    def test_large_period_length(self, fmp_ti):
        """Test with very large period length."""
        with patch.object(fmp_ti, 'get_request') as mock_get_request:
            mock_get_request.return_value = [
                {
                    "date": "2025-02-04 00:00:00",
                    "open": 227.2,
                    "high": 233.13,
                    "low": 226.65,
                    "close": 232.8,
                    "volume": 44489128,
                    "sma": 231.215
                }
            ]
            
            # Should work with large period lengths
            result = fmp_ti.simple_moving_average('AAPL', period_length=200)
            assert isinstance(result, pd.DataFrame)

    def test_different_timeframes(self, fmp_ti):
        """Test with different timeframes."""
        timeframes = ['1min', '5min', '15min', '30min', '1hour', '4hour', '1day']
        
        with patch.object(fmp_ti, 'get_request') as mock_get_request:
            mock_get_request.return_value = [
                {
                    "date": "2025-02-04 00:00:00",
                    "open": 227.2,
                    "high": 233.13,
                    "low": 226.65,
                    "close": 232.8,
                    "volume": 44489128,
                    "sma": 231.215
                }
            ]
            
            for timeframe in timeframes:
                result = fmp_ti.simple_moving_average('AAPL', period_length=20, timeframe=timeframe)
                assert isinstance(result, pd.DataFrame)
                
                # Verify correct timeframe was passed to API
                call_args = mock_get_request.call_args[0][1]
                assert call_args['timeframe'] == timeframe


if __name__ == "__main__":
    pytest.main([__file__])