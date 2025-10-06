# FMP Cache System Documentation

## Overview

The FMP Cache System is a comprehensive framework for intelligent financial data caching with FMP (Financial Modeling Prep) API integration. It provides:

- **Smart Cache Management**: Intelligent cache validation to minimize API calls
- **Batch Processing**: Handle single stocks or lists of stocks efficiently
- **FMP-Compatible API**: Local API interface that mimics FMP endpoints
- **Date Range Support**: Flexible date filtering and validation
- **Performance Monitoring**: Comprehensive statistics and health monitoring

## Quick Start

### 1. Setup Environment

```bash
# Set your FMP API key
export FMP_API_KEY="your_fmp_api_key_here"

# Ensure MySQL database is running and configured
# Database credentials should be in .env file
```

### 2. Basic Usage

```python
from StockAnalysis import StockDataFetcher, FMPCacheAPI
from datetime import datetime, timedelta

# Initialize fetcher
fetcher = StockDataFetcher()

# Fetch data for Apple (last 365 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=365)
results = fetcher.fetch_batch("AAPL", start_date, end_date)

# Query cached data using FMP-compatible API
api = FMPCacheAPI()
profile = api.profile("AAPL")
quote = api.quote("AAPL")
historical = api.historical_price_full("AAPL", from_date="2024-01-01", to_date="2024-12-31")
```

### 3. Command Line Interface

```bash
# Fetch single stock
python fmp_cache_cli.py fetch AAPL --days 365

# Fetch multiple stocks from file
echo -e "AAPL\nMSFT\nGOOGL" > stocks.txt
python fmp_cache_cli.py fetch stocks.txt --start-date 2023-01-01 --end-date 2024-01-01

# Query cached data
python fmp_cache_cli.py query AAPL profile
python fmp_cache_cli.py query AAPL quote
python fmp_cache_cli.py query AAPL historical --from 2024-01-01 --to 2024-12-31

# Cache management
python fmp_cache_cli.py status
python fmp_cache_cli.py stats AAPL
python fmp_cache_cli.py cleanup --dry-run
```

## Architecture

### Core Components

1. **StockDataFetcher** (`cache/stock_data_fetcher.py`)
   - Handles data fetching from FMP API
   - Implements intelligent cache checking
   - Supports batch processing
   - Rate limiting and error handling

2. **CacheManager** (`cache/cache_manager.py`)
   - Cache validation and expiration policies
   - Freshness checking by data type
   - Cache statistics and monitoring
   - Cleanup operations

3. **FMPCacheAPI** (`api/fmp_cache_api.py`)
   - FMP-compatible API interface
   - Serves cached data through familiar endpoints
   - Identical interface to FMP API

4. **Database Layer** (`database/`)
   - MySQL connection management
   - Query execution and result handling
   - Transaction support

5. **Utilities** (`utils/`)
   - Date parsing and formatting
   - Helper functions
   - Configuration management

### Data Flow

```
Input (Symbols + Date Range)
    ↓
Cache Validation
    ↓
Smart Fetching (API calls only if needed)
    ↓
Data Storage (MySQL)
    ↓
FMP-Compatible API Access
    ↓
Analysis & Reporting
```

## Features

### Intelligent Caching

The system automatically checks cache freshness before making API calls:

- **Quotes**: 5-minute expiration for real-time data
- **Company Profiles**: 1-week expiration for static data  
- **Financial Statements**: 1-year expiration for annual data
- **Historical Prices**: 1-day expiration for price data
- **News**: 3-day expiration for news articles

### Batch Processing

```python
# Single symbol
results = fetcher.fetch_batch("AAPL", start_date, end_date)

# Multiple symbols
results = fetcher.fetch_batch(["AAPL", "MSFT", "GOOGL"], start_date, end_date)

# From file
results = fetcher.fetch_batch("stocks.txt", start_date, end_date)
```

### Date Range Support

```python
from utils.date_utils import parse_date_range

# Parse various date formats
start, end = parse_date_range("2024-01-01", "2024-12-31")
start, end = parse_date_range(None, None, days_back=365)
```

### FMP-Compatible API

The local API provides identical interfaces to FMP endpoints:

```python
api = FMPCacheAPI()

# Company profile (matches /api/v3/profile/{symbol})
profile = api.profile("AAPL")

# Quote data (matches /api/v3/quote/{symbol})
quote = api.quote("AAPL")

# Historical prices (matches /api/v3/historical-price-full/{symbol})
historical = api.historical_price_full("AAPL", from_date="2024-01-01")

# Financial statements
income = api.income_statement("AAPL", limit=5)
balance = api.balance_sheet_statement("AAPL", limit=5)
cashflow = api.cash_flow_statement("AAPL", limit=5)

# Ratios and metrics
ratios = api.ratios("AAPL", limit=5)
metrics = api.key_metrics("AAPL", limit=5)

# News
news = api.stock_news(tickers="AAPL", limit=50)
```

## Database Schema

The system uses a comprehensive MySQL schema with 22+ tables:

### Core Tables

- `companies`: Basic company information
- `company_profiles`: Detailed company profiles
- `quotes`: Real-time quote data
- `historical_prices_daily`: Daily price history

### Financial Statements

- `income_statements`: Income statement data
- `balance_sheets`: Balance sheet data  
- `cash_flow_statements`: Cash flow data

### Analysis Data

- `financial_ratios`: Financial ratio calculations
- `key_metrics`: Key performance metrics
- `stock_news`: News and sentiment data

### Monitoring

- `api_request_log`: API call monitoring
- Cache metadata with expiration tracking

## Configuration

### Environment Variables

```bash
# Required
FMP_API_KEY=your_fmp_api_key

# Database (MySQL)
FMP_DB_HOST=localhost
FMP_DB_PORT=3306
FMP_DB_NAME=fmp_cache
FMP_DB_USER=fmp_user
FMP_DB_PASSWORD=fmp_password
```

### Expiration Policies

Customize cache expiration in `CacheManager.EXPIRATION_POLICIES`:

```python
EXPIRATION_POLICIES = {
    'quotes': 0.08,  # 5 minutes
    'company_profiles': 168,  # 1 week
    'historical_prices_daily': 24,  # 1 day
    'stock_news': 72,  # 3 days
    # ... more policies
}
```

## Performance

### Cache Efficiency

The system tracks cache performance:

```python
cache_manager = CacheManager()
stats = cache_manager.get_cache_statistics()

print(f"Cache hits: {stats['cache_hits']}")
print(f"API calls: {stats['api_calls']}")
print(f"Efficiency: {cache_efficiency:.1f}%")
```

### Rate Limiting

Built-in rate limiting respects FMP API limits:

- 300 requests per minute (configurable)
- Automatic request spacing
- Request retry logic

### Bulk Operations

Optimized for large datasets:

- Batch SQL operations
- Connection pooling
- Parallel processing capabilities

## Error Handling

### Graceful Degradation

- API failures don't break the system
- Cached data served when API unavailable
- Comprehensive error logging

### Validation

- Input validation for symbols and dates
- Data integrity checks
- Schema validation

## Monitoring & Maintenance

### Health Checks

```python
api = FMPCacheAPI()
health = api.health_check()
print(f"Status: {health['status']}")
```

### Cache Cleanup

```python
cache_manager = CacheManager()

# Dry run to see what would be deleted
deleted = cache_manager.cleanup_expired_data(dry_run=True)

# Actually delete expired data
deleted = cache_manager.cleanup_expired_data(dry_run=False)
```

### Statistics

```python
# Overall statistics
stats = cache_manager.get_cache_statistics()

# Symbol-specific statistics  
stats = cache_manager.get_cache_statistics("AAPL")
```

## Integration Examples

### With FinRobot

```python
from StockAnalysis import FMPCacheAPI

# Use cached data in FinRobot analysis
api = FMPCacheAPI()
profile = api.profile("AAPL")
historical = api.historical_price_full("AAPL", from_date="2023-01-01")

# Pass to FinRobot agents for analysis
# ... FinRobot integration code
```

### Custom Analytics

```python
from StockAnalysis import FMPCacheAPI
import pandas as pd

api = FMPCacheAPI()

# Get multiple years of income statements
income_data = api.income_statement("AAPL", limit=10)

# Convert to DataFrame for analysis
df = pd.DataFrame(income_data)
df['revenue_growth'] = df['revenue'].pct_change()

# Perform custom analysis...
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `FMP_API_KEY` is set correctly
2. **Database Connection**: Check MySQL credentials in `.env`
3. **Cache Misses**: Verify date ranges and symbol formats
4. **Performance**: Monitor API rate limits and cache efficiency

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all cache operations will be logged
fetcher = StockDataFetcher()
```

### Validation

```python
# Check cache coverage
cache_manager = CacheManager()
coverage = cache_manager.check_data_freshness("AAPL", "historical_prices_daily", start_date, end_date)
print(f"Fresh: {coverage['is_fresh']}")
print(f"Complete: {coverage['is_complete']}")
```

## Best Practices

### 1. Cache Management

- Run cleanup regularly to manage storage
- Monitor cache efficiency metrics
- Set appropriate expiration policies

### 2. API Usage

- Use batch operations for multiple symbols
- Respect rate limits
- Handle API errors gracefully

### 3. Data Quality

- Validate input symbols and dates
- Check data completeness
- Monitor for data anomalies

### 4. Performance

- Use connection pooling for database
- Implement parallel processing for large datasets
- Monitor memory usage with large result sets

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review error logs
3. Validate configuration
4. Check database connectivity
5. Verify API key permissions

The FMP Cache System provides a robust foundation for financial data analysis with intelligent caching, comprehensive coverage, and seamless integration capabilities.