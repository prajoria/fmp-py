#!/usr/bin/env python3
"""
FMP Historical Charts API Example

This script demonstrates how to use the FmpHistoricalCharts class to fetch
various types of historical and intraday chart data from Financial Modeling Prep.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add the src directory to Python path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fmp_py.fmp_historical_charts import FmpHistoricalCharts


def main():
    """Main example function demonstrating FmpHistoricalCharts usage."""
    
    # Initialize the client (requires FMP_API_KEY environment variable)
    try:
        charts_client = FmpHistoricalCharts()
        print("✅ FmpHistoricalCharts client initialized successfully")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Please set your FMP_API_KEY environment variable")
        return

    symbol = "AAPL"
    print(f"\n📊 Fetching historical chart data for {symbol}\n")

    # Calculate date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")

    print(f"📅 Date range: {from_date} to {to_date}\n")

    # Example 1: Light Historical Data
    print("1️⃣ Light Historical Data (simplified)")
    print("-" * 40)
    try:
        light_data_df = charts_client.get_historical_price_light_df(
            symbol, from_date, to_date
        )
        print(f"📈 Retrieved {len(light_data_df)} light historical records")
        print(f"Columns: {list(light_data_df.columns)}")
        print(f"Latest close price: ${light_data_df.iloc[-1]['close']:.2f}")
        print(f"Latest volume: {light_data_df.iloc[-1]['volume']:,}")
        print()
    except Exception as e:
        print(f"❌ Error fetching light data: {e}\n")

    # Example 2: Full Historical Data
    print("2️⃣ Full Historical Data (comprehensive)")
    print("-" * 45)
    try:
        full_data_df = charts_client.get_historical_price_full_df(
            symbol, from_date, to_date
        )
        print(f"📈 Retrieved {len(full_data_df)} full historical records")
        print(f"Columns: {list(full_data_df.columns)}")
        
        latest = full_data_df.iloc[-1]
        print(f"Latest OHLC: O=${latest['open']:.2f}, H=${latest['high']:.2f}, "
              f"L=${latest['low']:.2f}, C=${latest['close']:.2f}")
        print(f"VWAP: ${latest['vwap']:.2f}")
        print(f"Change: {latest['change_percent']:.2f}%")
        print()
    except Exception as e:
        print(f"❌ Error fetching full data: {e}\n")

    # Example 3: Unadjusted Historical Data
    print("3️⃣ Unadjusted Historical Data (no split adjustments)")
    print("-" * 55)
    try:
        unadjusted_df = charts_client.get_historical_price_unadjusted(
            symbol, from_date, to_date
        )
        print(f"📈 Retrieved {len(unadjusted_df)} unadjusted records")
        print(f"Latest unadjusted close: ${unadjusted_df.iloc[-1]['close']:.2f}")
        print()
    except Exception as e:
        print(f"❌ Error fetching unadjusted data: {e}\n")

    # Example 4: Dividend Adjusted Data
    print("4️⃣ Dividend Adjusted Historical Data")
    print("-" * 40)
    try:
        div_adjusted_df = charts_client.get_historical_price_dividend_adjusted(
            symbol, from_date, to_date
        )
        print(f"📈 Retrieved {len(div_adjusted_df)} dividend-adjusted records")
        print(f"Latest dividend-adjusted close: ${div_adjusted_df.iloc[-1]['close']:.2f}")
        print()
    except Exception as e:
        print(f"❌ Error fetching dividend-adjusted data: {e}\n")

    # Example 5: Intraday Data (1-minute intervals)
    print("5️⃣ Intraday Data - 1 Minute Intervals")
    print("-" * 40)
    try:
        # Get intraday data for the most recent trading day
        intraday_1min_df = charts_client.get_intraday_1min_df(
            symbol, to_date, to_date
        )
        print(f"📈 Retrieved {len(intraday_1min_df)} 1-minute intraday records")
        if len(intraday_1min_df) > 0:
            print(f"First record time: {intraday_1min_df.iloc[0]['date']}")
            print(f"Last record time: {intraday_1min_df.iloc[-1]['date']}")
            print(f"Last price: ${intraday_1min_df.iloc[-1]['close']:.2f}")
        print()
    except Exception as e:
        print(f"❌ Error fetching 1-minute intraday data: {e}\n")

    # Example 6: Intraday Data (5-minute intervals)
    print("6️⃣ Intraday Data - 5 Minute Intervals")
    print("-" * 40)
    try:
        intraday_5min_df = charts_client.get_intraday_5min_df(
            symbol, to_date, to_date
        )
        print(f"📈 Retrieved {len(intraday_5min_df)} 5-minute intraday records")
        if len(intraday_5min_df) > 0:
            print(f"Price range: ${intraday_5min_df['low'].min():.2f} - ${intraday_5min_df['high'].max():.2f}")
            print(f"Total volume: {intraday_5min_df['volume'].sum():,}")
        print()
    except Exception as e:
        print(f"❌ Error fetching 5-minute intraday data: {e}\n")

    # Example 7: Intraday Data (1-hour intervals)
    print("7️⃣ Intraday Data - 1 Hour Intervals")
    print("-" * 38)
    try:
        intraday_1hour_df = charts_client.get_intraday_1hour_df(
            symbol, to_date, to_date
        )
        print(f"📈 Retrieved {len(intraday_1hour_df)} 1-hour intraday records")
        if len(intraday_1hour_df) > 0:
            avg_volume = intraday_1hour_df['volume'].mean()
            print(f"Average hourly volume: {avg_volume:,.0f}")
        print()
    except Exception as e:
        print(f"❌ Error fetching 1-hour intraday data: {e}\n")

    # Example 8: Using Object-Oriented Results
    print("8️⃣ Object-Oriented Data Access")
    print("-" * 35)
    try:
        light_data_objects = charts_client.get_historical_price_light(
            symbol, from_date, to_date
        )
        print(f"📈 Retrieved {len(light_data_objects)} light data objects")
        
        if light_data_objects:
            latest_record = light_data_objects[-1]
            print(f"Latest record:")
            print(f"  Date: {latest_record.date}")
            print(f"  Close: ${latest_record.close:.2f}")
            print(f"  Volume: {latest_record.volume:,}")
        print()
    except Exception as e:
        print(f"❌ Error fetching object-oriented data: {e}\n")

    print("🎉 Historical Charts API examples completed!")
    print("\n💡 Tips:")
    print("- Use light data for basic charting needs")
    print("- Use full data for comprehensive analysis")
    print("- Use intraday data for short-term trading strategies")
    print("- Adjust date ranges based on your analysis requirements")


if __name__ == "__main__":
    main()