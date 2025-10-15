# FMP Historical Chart Fetcher

A comprehensive historical price data fetcher with watermark tracking and crash recovery capabilities.

## Features

- **Robust Data Fetching**: Uses `FmpHistoricalCharts.get_historical_price_full()` to fetch comprehensive historical data
- **Watermark Tracking**: Maintains fetch progress to resume from interruptions  
- **Crash Recovery**: Automatically resumes from last successful fetch date
- **API Rate Limiting**: Respects FMP API rate limits (configurable)
- **Batch Processing**: Supports single stock or batch processing from lists/files
- **Popular Stocks**: Includes curated list of popular stocks
- **Progress Monitoring**: Track fetch progress and statistics
- **Database Storage**: Stores data in `historical_price_full_daily` table

## Database Schema

The fetcher creates and uses these tables:

- **`historical_price_full_daily`**: Stores comprehensive historical price data
- **`fetch_watermarks`**: Tracks fetch progress for each symbol
- **`fetch_sessions`**: Records batch processing sessions
- **`popular_stocks`**: Maintains list of popular stocks

## Installation & Setup

1. **Database Setup**:
```bash
mysql -u root -p < src/fmp_py/StockAnalysis/database/schema.sql
mysql -u root -p < src/fmp_py/StockAnalysis/database/historical_chart_fetcher_schema.sql
```

2. **Environment Variables**:
```bash
export FMP_API_KEY="your_fmp_api_key_here"
export DB_HOST="localhost"
export DB_USER="your_db_user"
export DB_PASSWORD="your_db_password"
export DB_NAME="fmp_cache"
```

## Usage Examples

### Command Line Interface

```bash
# Fetch popular stocks (uses watermarks for resume)
python fmp_historical_chart_fetcher.py --popular-stocks

# Fetch specific symbols
python fmp_historical_chart_fetcher.py --symbols AAPL,MSFT,GOOGL

# Fetch from file
python fmp_historical_chart_fetcher.py --symbols-file examples/sample_stocks.txt

# Fetch with specific date range
python fmp_historical_chart_fetcher.py --symbols AAPL --start-date 2020-01-01 --end-date 2023-12-31

# Force refresh (ignore watermarks, fetch all data)
python fmp_historical_chart_fetcher.py --symbols AAPL --force-refresh

# Show progress report
python fmp_historical_chart_fetcher.py --progress-report

# Fetch with custom rate limiting
python fmp_historical_chart_fetcher.py --popular-stocks --rate-limit 200

# Verbose logging
python fmp_historical_chart_fetcher.py --symbols AAPL --verbose
```

### Python API

```python
from fmp_py.StockAnalysis.cache.fmp_historical_chart_fetcher import FmpHistoricalChartFetcher

# Initialize fetcher
fetcher = FmpHistoricalChartFetcher()

# Fetch single stock
success = fetcher.fetch_symbol_data('AAPL')

# Fetch multiple stocks
results = fetcher.fetch_batch(['AAPL', 'MSFT', 'GOOGL'])

# Get progress report
fetcher.print_progress_report(['AAPL', 'MSFT'])

# Check watermark
watermark = fetcher.get_or_create_watermark('AAPL')
print(f"Latest data: {watermark.latest_date}")
```

## Popular Stocks List

The fetcher includes a curated list of popular stocks across different sectors:

### Large Cap Tech Giants
- AAPL (Apple), MSFT (Microsoft), GOOGL (Alphabet), AMZN (Amazon)
- META (Meta), TSLA (Tesla), NVDA (NVIDIA)

### Financial Sector  
- JPM (JPMorgan), BAC (Bank of America), WFC (Wells Fargo), GS (Goldman Sachs)

### Healthcare & Pharma
- JNJ (Johnson & Johnson), PFE (Pfizer), UNH (UnitedHealth), ABBV (AbbVie)

### Popular ETFs
- SPY (S&P 500), QQQ (NASDAQ 100), IWM (Russell 2000), VTI (Total Market)

*Total: 30+ carefully selected symbols*

## Watermark System

The watermark system enables crash recovery and efficient incremental updates:

```sql
-- Check fetch progress
SELECT symbol, latest_date, total_records, fetch_status 
FROM fetch_watermarks 
WHERE symbol = 'AAPL';

-- View progress for all symbols
SELECT * FROM v_fetch_progress;
```

### Watermark States
- **`active`**: Currently fetching data
- **`complete`**: Up to date (within 1 day)
- **`failed`**: Too many consecutive errors (>= 5)
- **`paused`**: Manually paused

## API Rate Limiting

The fetcher implements intelligent rate limiting:

- **Default**: 250 calls/minute (within FMP limits)
- **Configurable**: Adjust with `--rate-limit` parameter
- **Automatic spacing**: Calculates optimal delays between requests
- **Burst protection**: Prevents exceeding API quotas

## Error Handling & Recovery

### Automatic Recovery
- **Watermark resume**: Continues from last successful fetch
- **Error tracking**: Records consecutive failures per symbol
- **Skip failed symbols**: Automatically skips symbols with > 5 errors
- **Session logging**: Tracks batch processing progress

### Manual Recovery
```bash
# Reset watermark for symbol (force refetch)
UPDATE fetch_watermarks SET latest_date = DATE_SUB(CURDATE(), INTERVAL 5 YEAR) WHERE symbol = 'AAPL';

# Reset error count
UPDATE fetch_watermarks SET error_count = 0, fetch_status = 'active' WHERE symbol = 'AAPL';
```

## Monitoring & Statistics

### Progress Reports
```bash
# Show progress for all symbols
python fmp_historical_chart_fetcher.py --progress-report

# Database queries
SELECT * FROM v_fetch_progress;
SELECT * FROM v_fetch_session_stats;
```

### Key Metrics
- **Coverage**: Days of data available vs requested
- **Freshness**: Days behind current date
- **Success rate**: Percentage of successful fetches
- **API efficiency**: Calls per minute, records per call

## Performance Considerations

### Optimal Usage Patterns
1. **Initial Load**: Fetch 5 years of data for all symbols
2. **Daily Updates**: Run with watermarks to get latest data
3. **Maintenance**: Periodic progress reports and error cleanup

### Storage Requirements
- **Per symbol**: ~1,825 records (5 years daily data)
- **Per record**: ~150 bytes (all fields)
- **Total estimate**: ~275 KB per symbol for 5 years

### API Usage
- **Initial fetch**: ~1 API call per symbol per 5 years
- **Daily updates**: ~1 API call per symbol per day
- **Popular stocks (30)**: ~30 calls for daily updates

## Troubleshooting

### Common Issues

1. **Database Connection**:
```bash
# Test connection
python -c "from src.fmp_py.StockAnalysis.database.connection import get_db; print('✅ Connected' if get_db().test_connection() else '❌ Failed')"
```

2. **API Key Issues**:
```bash
# Verify API key
echo $FMP_API_KEY
python -c "from fmp_py.fmp_historical_charts import FmpHistoricalCharts; print(FmpHistoricalCharts().get_historical_price_light('AAPL')[:1])"
```

3. **Watermark Issues**:
```sql
-- Reset all watermarks
UPDATE fetch_watermarks SET fetch_status = 'active', error_count = 0;

-- Check failed symbols
SELECT symbol, error_count, last_error_message FROM fetch_watermarks WHERE fetch_status = 'failed';
```

## Configuration Options

### Environment Variables
```bash
FMP_API_KEY=your_api_key           # Required: FMP API key
DB_HOST=localhost                  # Database host
DB_PORT=3306                       # Database port
DB_USER=root                       # Database user
DB_PASSWORD=password               # Database password
DB_NAME=fmp_cache                  # Database name
```

### Command Line Options
```bash
--rate-limit 250                   # API calls per minute
--force-refresh                    # Ignore watermarks
--start-date 2020-01-01           # Custom start date
--end-date 2023-12-31             # Custom end date
--verbose                         # Debug logging
--quiet                           # Minimal output
```

## Integration Examples

### Cron Job Setup
```bash
# Daily updates at 7 AM
0 7 * * * cd /path/to/fmp-py && python src/fmp_py/StockAnalysis/cache/fmp_historical_chart_fetcher.py --popular-stocks

# Weekly full refresh on Sunday
0 2 * * 0 cd /path/to/fmp-py && python src/fmp_py/StockAnalysis/cache/fmp_historical_chart_fetcher.py --popular-stocks --force-refresh
```

### Python Integration
```python
import schedule
import time
from fmp_py.StockAnalysis.cache.fmp_historical_chart_fetcher import FmpHistoricalChartFetcher

def daily_update():
    fetcher = FmpHistoricalChartFetcher()
    fetcher.fetch_batch(fetcher.POPULAR_STOCKS)

# Schedule daily updates
schedule.every().day.at("07:00").do(daily_update)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## Contributing

To extend the fetcher:

1. **Add new symbols**: Update `popular_stocks` table or `POPULAR_STOCKS` list
2. **Custom data types**: Extend `fetch_symbol_data()` for light/intraday data
3. **New storage formats**: Add methods for different database schemas
4. **Enhanced monitoring**: Add custom views and reporting functions

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review database logs and watermark status
3. Enable verbose logging for detailed error information
4. Check FMP API status and quotas