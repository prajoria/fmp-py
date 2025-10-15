# Historical Charts Database Cache Setup

This document explains how to set up and use the database cache manager for FMP Historical Charts API responses.

## Overview

The Historical Charts Database Cache Manager provides:

- **Automatic Caching**: All historical chart API responses are automatically cached in MySQL database
- **TTL Management**: Different cache durations for different data types (EOD vs intraday)
- **Performance Optimization**: Significant speed improvements for repeated requests
- **API Usage Reduction**: Reduces FMP API calls and associated costs
- **Offline Capability**: Access cached data even when API is unavailable
- **Cache Management**: Cleanup, statistics, and invalidation capabilities

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│                     │    │                      │    │                     │
│  FMP Historical     │────│  Cached FMP         │────│  Database Cache     │
│  Charts API         │    │  Historical Charts  │    │  Manager            │
│                     │    │                      │    │                     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────┐
                           │                      │
                           │  MySQL Database      │
                           │  ├ Light Historical  │
                           │  ├ Full Historical   │
                           │  ├ Intraday Data     │
                           │  └ Cache Metadata    │
                           │                      │
                           └──────────────────────┘
```

## Database Schema

### Core Tables

1. **historical_charts_light**: Basic EOD price data (OHLCV)
2. **historical_charts_full**: Comprehensive EOD data with additional metrics
3. **historical_charts_intraday**: Intraday data for all supported intervals
4. **historical_charts_cache_metadata**: Cache tracking and metadata

### Cache Management

- **TTL Configuration**: Different expiration times for different data types
- **Automatic Cleanup**: Stored procedures for removing expired data
- **Hit Tracking**: Monitor cache usage and performance
- **Statistics**: Views for cache analytics

## Setup Instructions

### 1. Database Installation

```bash
# Install MySQL (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install mysql-server

# Start MySQL service
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation
```

### 2. Database Schema Setup

```bash
# Connect to MySQL
mysql -u root -p

# Create database and tables
source src/fmp_py/StockAnalysis/database/schema.sql
source src/fmp_py/StockAnalysis/database/historical_charts_schema.sql
```

### 3. Python Dependencies

```bash
# Install required packages
pip install mysql-connector-python
pip install python-dotenv
```

### 4. Environment Configuration

Create a `.env` file with database credentials:

```env
# FMP API
FMP_API_KEY=your_fmp_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=fmp_cache
```

## Usage Examples

### Basic Usage

```python
from fmp_py.StockAnalysis.client.cached_fmp_historical_charts import CachedFmpHistoricalCharts

# Initialize cached client
client = CachedFmpHistoricalCharts(enable_cache=True)

# Get light historical data (cached automatically)
data = client.get_historical_price_light('AAPL', '2024-01-01', '2024-01-31')

# Second call will be served from cache
cached_data = client.get_historical_price_light('AAPL', '2024-01-01', '2024-01-31')
```

### Cache Management

```python
# Get cache statistics
stats = client.get_cache_statistics()
for stat in stats:
    print(f"{stat['endpoint_type']}: {stat['valid_entries']} entries")

# Clean up expired cache
cleanup_stats = client.cleanup_expired_cache()
print(f"Cleanup completed: {cleanup_stats}")

# Clear cache for specific symbol
success = client.clear_cache_for_symbol('AAPL')
print(f"Cache cleared: {success}")
```

## Cache TTL Configuration

Default cache durations:

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Light Historical | 1 hour | EOD data updates once daily |
| Full Historical | 1 hour | EOD data updates once daily |
| 1-minute Intraday | 5 minutes | High-frequency data |
| 5-minute Intraday | 10 minutes | Medium-frequency data |
| 15-minute Intraday | 15 minutes | Lower-frequency data |
| 30-minute Intraday | 30 minutes | Lower-frequency data |
| 1-hour Intraday | 1 hour | Low-frequency data |
| 4-hour Intraday | 2 hours | Very low-frequency data |

For complete documentation, see the full README in the database directory.