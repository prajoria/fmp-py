# FMP MySQL Cache Database

A comprehensive MySQL database caching system for Financial Modeling Prep (FMP) API responses. This system significantly reduces API calls, improves response times, and enables complex queries across cached financial data.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Maintenance](#maintenance)
- [Examples](#examples)

## Features

- **Intelligent Caching**: Automatic cache-first strategy with configurable TTL per data type
- **Complete FMP Coverage**: Tables for quotes, profiles, financial statements, historical prices, news, and more
- **Connection Pooling**: Efficient MySQL connection management
- **Cache Statistics**: Built-in monitoring and analytics
- **Automatic Cleanup**: Expired cache removal and log rotation
- **Join Capabilities**: Combine cached data without hitting the API
- **Type Safety**: Strongly typed DAL with proper error handling

## Architecture

```
┌─────────────────┐
│   FMP Client    │
│  (Your Code)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CachedFMPClient │ ◄── Cache-first logic
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌─────────┐
│  Cache │ │ FMP API │
│ (MySQL)│ │         │
└────────┘ └─────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- FMP API key

### Python Dependencies

```bash
# Install required packages
pip install mysql-connector-python python-dotenv pandas requests
```

### MySQL Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mysql-server mysql-client
sudo systemctl start mysql
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

**Windows:**
Download and install from [MySQL Downloads](https://dev.mysql.com/downloads/)

## Database Setup

### Quick Setup

1. **Run the setup script:**

```bash
cd /home/daaji/masterswork/git/fmp-py/src/fmp_py/StockAnalysis/database
chmod +x setup.sh

# Set MySQL root password (optional)
export MYSQL_ROOT_PASSWORD="your_root_password"

# Run setup
./setup.sh
```

2. **Update environment variables:**

Edit `.env` file in the StockAnalysis directory:

```bash
# FMP API Configuration
FMP_API_KEY=your_actual_api_key_here

# Database Configuration
FMP_DB_HOST=localhost
FMP_DB_PORT=3306
FMP_DB_NAME=fmp_cache
FMP_DB_USER=fmp_user
FMP_DB_PASSWORD=fmp_password

# Cache Configuration
FMP_CACHE_ENABLED=true
FMP_CACHE_TTL_QUOTE=300
FMP_CACHE_TTL_PROFILE=86400
FMP_CACHE_TTL_HISTORICAL=3600
FMP_CACHE_TTL_FINANCIALS=86400
FMP_CACHE_TTL_NEWS=1800
```

### Manual Setup

If you prefer manual setup:

```bash
# Create database and user
mysql -u root -p << EOF
CREATE DATABASE fmp_cache CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fmp_user'@'localhost' IDENTIFIED BY 'fmp_password';
GRANT ALL PRIVILEGES ON fmp_cache.* TO 'fmp_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Import schema
mysql -u root -p fmp_cache < schema.sql
```

## Usage

### Basic Usage

```python
from fmp_py.StockAnalysis.client.cached_fmp_client import create_cached_client

# Create cached client
client = create_cached_client(api_key="your_api_key", enable_cache=True)

# Use like normal FMP client - caching is transparent
quote = client.get_quote("AAPL")
profile = client.get_company_profile("AAPL")
historical = client.get_historical_prices("AAPL", from_date="2024-01-01")

# Get cache statistics
stats = client.get_cache_stats()
print(f"Cache enabled: {stats['cache_enabled']}")
print(f"Cached companies: {stats['companies']}")
print(f"Cache hit rate: {stats['cache_hit_rate_24h']}")

# Force refresh cached data
client.force_refresh("AAPL", "quote")

# Cleanup expired cache
deleted = client.cleanup_expired_cache()
print(f"Deleted {deleted} expired records")
```

### Direct Database Access

```python
from fmp_py.StockAnalysis.database import (
    company_dal, 
    quote_dal, 
    historical_price_dal,
    execute_query
)

# Get company profile from cache
profile = company_dal.get_company_profile("AAPL")

# Get latest quote
quote = quote_dal.get_quote("AAPL")

# Get historical prices
prices = historical_price_dal.get_daily_prices(
    "AAPL", 
    from_date="2024-01-01",
    to_date="2024-12-31"
)

# Custom query
results = execute_query("""
    SELECT c.symbol, c.name, cp.sector, q.price, q.market_cap
    FROM companies c
    JOIN company_profiles cp ON c.symbol = cp.symbol
    JOIN quotes q ON c.symbol = q.symbol
    WHERE cp.sector = 'Technology'
    ORDER BY q.market_cap DESC
    LIMIT 10
""")
```

### Advanced Queries

```python
from fmp_py.StockAnalysis.database import execute_query

# Get top companies by sector with financial metrics
top_by_sector = execute_query("""
    SELECT 
        cp.sector,
        c.symbol,
        c.name,
        q.price,
        q.market_cap,
        km.pe_ratio,
        km.roe,
        fr.debt_to_equity
    FROM companies c
    JOIN company_profiles cp ON c.symbol = cp.symbol
    JOIN quotes q ON c.symbol = q.symbol
    LEFT JOIN key_metrics km ON c.symbol = km.symbol
        AND km.id = (SELECT MAX(id) FROM key_metrics WHERE symbol = c.symbol)
    LEFT JOIN financial_ratios fr ON c.symbol = fr.symbol
        AND fr.id = (SELECT MAX(id) FROM financial_ratios WHERE symbol = c.symbol)
    WHERE cp.sector IS NOT NULL
    ORDER BY cp.sector, q.market_cap DESC
""")

# Analyze earnings surprises
earnings_analysis = execute_query("""
    SELECT 
        ec.symbol,
        c.name,
        ec.date,
        ec.eps,
        ec.eps_estimated,
        (ec.eps - ec.eps_estimated) as surprise,
        ROUND((ec.eps - ec.eps_estimated) / ec.eps_estimated * 100, 2) as surprise_pct
    FROM earnings_calendar ec
    JOIN companies c ON ec.symbol = c.symbol
    WHERE ec.date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
        AND ec.eps IS NOT NULL
        AND ec.eps_estimated IS NOT NULL
    ORDER BY ABS(ec.eps - ec.eps_estimated) DESC
    LIMIT 50
""")
```

## Database Schema

### Core Tables

- **companies**: Master list of stock symbols and basic info
- **company_profiles**: Detailed company information
- **company_executives**: Executive team data

### Market Data Tables

- **quotes**: Real-time quotes (5-minute TTL)
- **historical_prices_daily**: Daily OHLCV data
- **historical_prices_intraday**: Intraday price data

### Financial Statement Tables

- **income_statements**: Income statement data
- **balance_sheets**: Balance sheet data
- **cash_flow_statements**: Cash flow data

### Metrics Tables

- **financial_ratios**: Financial ratios
- **key_metrics**: Key financial metrics
- **financial_growth**: Growth metrics

### News and Calendar Tables

- **stock_news**: News articles
- **earnings_calendar**: Earnings announcements
- **dividend_calendar**: Dividend information

### Market Data Tables

- **market_movers**: Gainers, losers, most active
- **sector_performance**: Sector performance data

### Metadata Tables

- **cache_metadata**: Cache tracking and expiration
- **api_request_log**: API request monitoring

See `schema.sql` for complete table definitions.

## Configuration

### Cache TTL Configuration

Default TTL values (in seconds):

- **Quotes**: 300 (5 minutes)
- **Company Profiles**: 86400 (24 hours)
- **Historical Prices**: 3600 (1 hour)
- **Financial Statements**: 86400 (24 hours)
- **News**: 1800 (30 minutes)
- **Calendar Events**: 3600 (1 hour)
- **Metrics/Ratios**: 86400 (24 hours)

Customize in `.env`:

```bash
FMP_CACHE_TTL_QUOTE=300
FMP_CACHE_TTL_PROFILE=86400
FMP_CACHE_TTL_HISTORICAL=3600
```

### Connection Pool Settings

```bash
FMP_DB_POOL_SIZE=5  # Number of connections in pool
FMP_DB_POOL_NAME=fmp_pool
```

## Maintenance

### Regular Maintenance Tasks

```python
from fmp_py.StockAnalysis.client.cached_fmp_client import create_cached_client

client = create_cached_client()

# Cleanup expired cache (run daily)
deleted = client.cleanup_expired_cache()

# Cleanup old logs (run weekly)
deleted = client.cleanup_old_logs(days=30)
```

### SQL Maintenance Queries

See `queries.sql` for useful maintenance and analysis queries:

```bash
# Run from command line
mysql -u fmp_user -p fmp_cache < queries.sql
```

### Database Optimization

```sql
-- Optimize tables (run monthly)
OPTIMIZE TABLE quotes;
OPTIMIZE TABLE historical_prices_daily;
OPTIMIZE TABLE company_profiles;
OPTIMIZE TABLE api_request_log;

-- Check database size
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) as 'Size (MB)',
    table_rows as 'Rows'
FROM information_schema.tables
WHERE table_schema = 'fmp_cache'
ORDER BY (data_length + index_length) DESC;
```

## Examples

### Example 1: Portfolio Analysis

```python
from fmp_py.StockAnalysis.database import execute_query

# Get data for portfolio symbols
portfolio = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

query = """
SELECT 
    c.symbol,
    c.name,
    q.price,
    q.change,
    q.changes_percentage,
    cp.sector,
    km.pe_ratio,
    km.dividend_yield
FROM companies c
JOIN quotes q ON c.symbol = q.symbol
LEFT JOIN company_profiles cp ON c.symbol = cp.symbol
LEFT JOIN key_metrics km ON c.symbol = km.symbol
WHERE c.symbol IN (%s)
    AND q.expires_at > NOW()
""" % ','.join(['%s'] * len(portfolio))

results = execute_query(query, tuple(portfolio))
```

### Example 2: Sector Screening

```python
# Find undervalued tech stocks
undervalued_tech = execute_query("""
    SELECT 
        c.symbol,
        c.name,
        q.price,
        km.pe_ratio,
        km.pb_ratio,
        km.roe,
        fr.debt_to_equity,
        fr.current_ratio
    FROM companies c
    JOIN company_profiles cp ON c.symbol = cp.symbol
    JOIN quotes q ON c.symbol = q.symbol
    LEFT JOIN key_metrics km ON c.symbol = km.symbol
        AND km.id = (SELECT MAX(id) FROM key_metrics WHERE symbol = c.symbol)
    LEFT JOIN financial_ratios fr ON c.symbol = fr.symbol
        AND fr.id = (SELECT MAX(id) FROM financial_ratios WHERE symbol = c.symbol)
    WHERE cp.sector = 'Technology'
        AND km.pe_ratio < 20
        AND km.roe > 0.15
        AND fr.debt_to_equity < 1.0
        AND q.market_cap > 1000000000
    ORDER BY km.pe_ratio ASC
""")
```

### Example 3: Historical Analysis

```python
from fmp_py.StockAnalysis.database import historical_price_dal

# Get 1 year of daily prices
prices = historical_price_dal.get_daily_prices(
    "AAPL",
    from_date="2024-01-01",
    to_date="2024-12-31"
)

# Calculate returns
import pandas as pd
df = pd.DataFrame(prices)
df['return'] = df['close'].pct_change()
df['cumulative_return'] = (1 + df['return']).cumprod() - 1

print(f"Total return: {df['cumulative_return'].iloc[-1] * 100:.2f}%")
```

## Troubleshooting

### Connection Issues

```python
from fmp_py.StockAnalysis.database import get_db

db = get_db()
if db.test_connection():
    print("Database connection OK")
else:
    print("Database connection failed")
```

### Check Logs

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Reset Database

```bash
# WARNING: This will delete all cached data
mysql -u root -p fmp_cache < schema.sql
```

## Performance Tips

1. **Use batch operations** for inserting multiple records
2. **Create indexes** on frequently queried columns
3. **Run cleanup regularly** to remove expired data
4. **Monitor cache hit rate** and adjust TTL values
5. **Use connection pooling** for concurrent access

## License

This caching system is part of the fmp-py project.

## Support

For issues and questions, please refer to the main fmp-py documentation or open an issue on GitHub.
