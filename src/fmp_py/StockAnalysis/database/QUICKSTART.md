# Quick Start Guide - FMP MySQL Cache

Get up and running with FMP database caching in 5 minutes!

## Prerequisites

- Python 3.8+
- MySQL 8.0+
- FMP API key ([Get one here](https://site.financialmodelingprep.com/developer/docs))

## Step 1: Install MySQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mysql-server
sudo systemctl start mysql
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

## Step 2: Install Python Dependencies

```bash
cd /home/daaji/masterswork/git/fmp-py/src/fmp_py/StockAnalysis/database
pip install -r requirements.txt
```

## Step 3: Setup Database

```bash
# Set your MySQL root password (if needed)
export MYSQL_ROOT_PASSWORD="your_mysql_root_password"

# Run setup script
chmod +x setup.sh
./setup.sh
```

The script will:
- Create `fmp_cache` database
- Create `fmp_user` with appropriate permissions
- Import all tables and indexes
- Create a `.env` file template

## Step 4: Configure API Key

Edit the `.env` file created in the parent directory:

```bash
cd /home/daaji/masterswork/git/fmp-py/src/fmp_py/StockAnalysis
nano .env
```

Update your FMP API key:
```bash
FMP_API_KEY=your_actual_api_key_here
```

## Step 5: Test It!

```python
from fmp_py.StockAnalysis.client.cached_fmp_client import create_cached_client

# Create cached client
client = create_cached_client(enable_cache=True)

# Fetch data (will cache automatically)
quote = client.get_quote("AAPL")
print(f"AAPL Price: ${quote['price']}")

# Second call uses cache (instant!)
quote = client.get_quote("AAPL")
print(f"AAPL Price: ${quote['price']} (from cache)")

# View cache stats
stats = client.get_cache_stats()
print(f"Cache hit rate: {stats.get('cache_hit_rate_24h', {}).get('hit_rate_percent', 0)}%")
```

Or run the examples:

```bash
cd /home/daaji/masterswork/git/fmp-py/src/fmp_py/StockAnalysis/database
python examples.py
```

## What's Cached?

Everything is cached automatically with intelligent TTL:

- ✅ **Quotes** (5 min TTL) - Real-time stock prices
- ✅ **Company Profiles** (24 hr TTL) - Company information
- ✅ **Historical Prices** (1 hr TTL) - OHLCV data
- ✅ **Financial Statements** (24 hr TTL) - Income, balance sheet, cash flow
- ✅ **Financial Metrics** (24 hr TTL) - Ratios, KPIs, growth
- ✅ **News** (30 min TTL) - Financial news articles
- ✅ **Calendars** (1 hr TTL) - Earnings, dividends

## Common Commands

### View cache statistics:
```bash
mysql -u fmp_user -p fmp_cache -e "
SELECT 
    'Companies' as item, COUNT(*) as count FROM companies
UNION ALL
    SELECT 'Quotes', COUNT(*) FROM quotes
UNION ALL
    SELECT 'Historical Prices', COUNT(*) FROM historical_prices_daily
UNION ALL
    SELECT 'Profiles', COUNT(*) FROM company_profiles;
"
```

### Clean up expired cache:
```python
from fmp_py.StockAnalysis.client.cached_fmp_client import create_cached_client
client = create_cached_client()
deleted = client.cleanup_expired_cache()
print(f"Deleted {deleted} expired records")
```

### Force refresh data:
```python
client.force_refresh("AAPL", "quote")  # Clear cached quote
quote = client.get_quote("AAPL")  # Fetch fresh data
```

## Benefits

- 🚀 **10-100x faster** - No API latency for cached data
- 💰 **Reduced API costs** - Fewer API calls = lower costs
- 📊 **Complex queries** - JOIN across cached data
- 🔍 **Historical analysis** - Query all cached data at once
- ⚡ **Offline capable** - Work with cached data offline

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore [examples.py](examples.py) for usage patterns
- Check [queries.sql](queries.sql) for useful SQL queries
- Review [schema.sql](schema.sql) to understand the database structure

## Troubleshooting

**Database connection fails:**
```python
from fmp_py.StockAnalysis.database import get_db
db = get_db()
print("Connection OK" if db.test_connection() else "Connection Failed")
```

**Check MySQL is running:**
```bash
sudo systemctl status mysql  # Linux
brew services list | grep mysql  # macOS
```

**Reset database:**
```bash
mysql -u root -p fmp_cache < schema.sql
```

## Support

For issues or questions:
1. Check the [README.md](README.md) for detailed docs
2. Review error logs in the console
3. Verify `.env` configuration
4. Check MySQL permissions

Happy coding! 🎉
