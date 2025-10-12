#!/usr/bin/env python3
"""
Example script demonstrating the usage of FmpTechnicalIndicators class.

This script shows how to:
1. Initialize the technical indicators client
2. Get various technical indicators for a stock
3. Use convenience methods for multiple indicators
4. Generate trading signals and trend analysis

Prerequisites:
- Set FMP_API_KEY environment variable with your Financial Modeling Prep API key
- Install required dependencies: pip install pandas numpy python-dotenv

Usage:
    python examples/technical_indicators_example.py
"""

import os
from datetime import datetime, timedelta
from fmp_py.fmp_technical_indicators import FmpTechnicalIndicators

def main():
    """Main function demonstrating technical indicators usage."""
    
    # Initialize the technical indicators client
    # Make sure you have FMP_API_KEY set in your environment
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("Warning: FMP_API_KEY not found in environment variables.")
        print("Please set your API key: export FMP_API_KEY='your_api_key_here'")
        return
    
    ti = FmpTechnicalIndicators(api_key=api_key)
    symbol = 'AAPL'  # Apple Inc.
    
    print(f"=== Technical Indicators Example for {symbol} ===\n")
    
    try:
        # 1. Simple Moving Average (20-period)
        print("1. Simple Moving Average (20-period)")
        sma_data = ti.simple_moving_average(symbol, period_length=20, timeframe='1day')
        print(f"Latest SMA (20): {sma_data.iloc[-1]['sma']:.2f}")
        print(f"Current Price: {sma_data.iloc[-1]['close']:.2f}")
        print()
        
        # 2. Exponential Moving Average (12-period)
        print("2. Exponential Moving Average (12-period)")
        ema_data = ti.exponential_moving_average(symbol, period_length=12, timeframe='1day')
        print(f"Latest EMA (12): {ema_data.iloc[-1]['ema']:.2f}")
        print()
        
        # 3. Relative Strength Index (14-period)
        print("3. Relative Strength Index (14-period)")
        rsi_data = ti.relative_strength_index(symbol, period_length=14, timeframe='1day')
        latest_rsi = rsi_data.iloc[-1]['rsi']
        print(f"Latest RSI (14): {latest_rsi:.2f}")
        
        # Interpret RSI levels
        if latest_rsi > 70:
            rsi_signal = "Overbought (>70)"
        elif latest_rsi < 30:
            rsi_signal = "Oversold (<30)"
        else:
            rsi_signal = "Neutral (30-70)"
        print(f"RSI Signal: {rsi_signal}")
        print()
        
        # 4. Williams %R (14-period)
        print("4. Williams %R (14-period)")
        williams_data = ti.williams_percent_r(symbol, period_length=14, timeframe='1day')
        latest_williams = williams_data.iloc[-1]['williams']
        print(f"Latest Williams %R (14): {latest_williams:.2f}")
        
        # Interpret Williams %R levels
        if latest_williams > -20:
            williams_signal = "Overbought (>-20)"
        elif latest_williams < -80:
            williams_signal = "Oversold (<-80)"
        else:
            williams_signal = "Neutral (-20 to -80)"
        print(f"Williams %R Signal: {williams_signal}")
        print()
        
        # 5. Average Directional Index (14-period)
        print("5. Average Directional Index (14-period)")
        adx_data = ti.average_directional_index(symbol, period_length=14, timeframe='1day')
        latest_adx = adx_data.iloc[-1]['adx']
        print(f"Latest ADX (14): {latest_adx:.2f}")
        
        # Interpret ADX levels
        if latest_adx > 25:
            adx_signal = "Strong Trend (>25)"
        elif latest_adx > 20:
            adx_signal = "Moderate Trend (20-25)"
        else:
            adx_signal = "Weak Trend (<20)"
        print(f"ADX Signal: {adx_signal}")
        print()
        
        # 6. Standard Deviation (20-period)
        print("6. Standard Deviation (20-period)")
        std_data = ti.standard_deviation(symbol, period_length=20, timeframe='1day')
        latest_std = std_data.iloc[-1]['standardDeviation']
        print(f"Latest Standard Deviation (20): {latest_std:.2f}")
        print()
        
        # 7. Multiple Indicators at once
        print("7. Multiple Indicators (SMA, RSI, ADX)")
        indicators = ['sma', 'rsi', 'adx']
        multiple_data = ti.get_multiple_indicators(symbol, indicators, period_length=14)
        
        for indicator, data in multiple_data.items():
            latest_value = data.iloc[-1][indicator]
            print(f"Latest {indicator.upper()}: {latest_value:.2f}")
        print()
        
        # 8. Trading Signals
        print("8. Trading Signals (RSI + Williams %R)")
        signals = ti.get_trading_signals(symbol, period_length=14)
        latest_signal = signals.iloc[-1]
        print(f"Signal: {latest_signal['signal']}")
        print(f"RSI: {latest_signal['rsi']:.2f}")
        print(f"Williams %R: {latest_signal['williams']:.2f}")
        print()
        
        # 9. Trend Analysis
        print("9. Trend Analysis (SMA 20/50 + EMA 12 + ADX)")
        trend_analysis = ti.get_trend_analysis(symbol)
        latest_trend = trend_analysis.iloc[-1]
        print(f"Trend Direction: {latest_trend['trend_direction']}")
        print(f"Trend Strength: {latest_trend['trend_strength']}")
        print(f"Close: {latest_trend['close']:.2f}")
        print(f"SMA 20: {latest_trend['sma_20']:.2f}")
        print(f"SMA 50: {latest_trend['sma_50']:.2f}")
        print(f"EMA 12: {latest_trend['ema_12']:.2f}")
        print(f"ADX: {latest_trend['adx']:.2f}")
        print()
        
        # 10. Historical data with date range
        print("10. Historical SMA with Date Range (last 30 days)")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        historical_sma = ti.simple_moving_average(
            symbol, 
            period_length=20, 
            timeframe='1day',
            from_date=start_date,
            to_date=end_date
        )
        print(f"Retrieved {len(historical_sma)} data points")
        print(f"Date range: {historical_sma.iloc[0]['date'].date()} to {historical_sma.iloc[-1]['date'].date()}")
        print()
        
        print("=== Technical Indicators Example Complete ===")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a valid FMP API key and internet connection.")

if __name__ == "__main__":
    main()