# Technical Indicators API Documentation

## Overview

The Financial Modeling Prep (FMP) Technical Indicators API provides access to various technical analysis indicators for stocks and other financial instruments. These indicators help analyze price movements, trends, and market momentum.

## Base URL

```
https://financialmodelingprep.com/stable/technical-indicators/
```

## Authentication

All requests require an API key parameter:
```
?apikey=YOUR_API_KEY
```

## Common Parameters

All technical indicator endpoints share these common parameters:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `symbol` | string | Yes | Stock symbol or ticker | `AAPL` |
| `periodLength` | number | Yes | Number of periods for calculation | `10`, `14`, `20` |
| `timeframe` | string | Yes | Time interval for data | `1day`, `1hour`, `5min` |
| `from` | date | No | Start date (YYYY-MM-DD) | `2025-04-24` |
| `to` | date | No | End date (YYYY-MM-DD) | `2025-07-24` |

### Supported Timeframes

- `1min` - 1-minute intervals
- `5min` - 5-minute intervals  
- `15min` - 15-minute intervals
- `30min` - 30-minute intervals
- `1hour` - 1-hour intervals
- `4hour` - 4-hour intervals
- `1day` - Daily intervals

## Available Technical Indicators

### Moving Averages

#### Simple Moving Average (SMA)

Calculates the average price over a specified number of periods.

**Endpoint:**
```
GET /technical-indicators/sma
```

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/sma?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY
```

**Example Response:**
```json
[
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
```

#### Exponential Moving Average (EMA)

Gives more weight to recent prices, making it more responsive to new information.

**Endpoint:**
```
GET /technical-indicators/ema
```

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/ema?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY
```

**Example Response:**
```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "ema": 232.8406611792779
  }
]
```

#### Weighted Moving Average (WMA)

Assigns different weights to each data point, with more recent data having higher weights.

**Endpoint:**
```
GET /technical-indicators/wma
```

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/wma?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY
```

#### Double Exponential Moving Average (DEMA)

A smoothed EMA that reduces lag while maintaining sensitivity to price changes.

**Endpoint:**
```
GET /technical-indicators/dema
```

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/dema?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY
```

#### Triple Exponential Moving Average (TEMA)

Further reduces lag compared to DEMA while maintaining responsiveness.

**Endpoint:**
```
GET /technical-indicators/tema
```

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/tema?symbol=AAPL&periodLength=10&timeframe=1day&apikey=YOUR_API_KEY
```

### Momentum Oscillators

#### Relative Strength Index (RSI)

Measures the speed and change of price movements, ranging from 0 to 100.

**Endpoint:**
```
GET /technical-indicators/rsi
```

**Common Period Lengths:** 14 (default), 21

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/rsi?symbol=AAPL&periodLength=14&timeframe=1day&apikey=YOUR_API_KEY
```

**Example Response:**
```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "rsi": 47.64507340768903
  }
]
```

**Interpretation:**
- RSI > 70: Potentially overbought (sell signal)
- RSI < 30: Potentially oversold (buy signal)
- RSI around 50: Neutral momentum

#### Williams %R

Momentum oscillator that measures overbought and oversold levels.

**Endpoint:**
```
GET /technical-indicators/williams
```

**Common Period Lengths:** 14, 20

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/williams?symbol=AAPL&periodLength=14&timeframe=1day&apikey=YOUR_API_KEY
```

**Example Response:**
```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "williams": -52.51824817518242
  }
]
```

**Interpretation:**
- Williams %R > -20: Overbought condition
- Williams %R < -80: Oversold condition

### Trend Indicators

#### Average Directional Index (ADX)

Measures the strength of a trend regardless of direction.

**Endpoint:**
```
GET /technical-indicators/adx
```

**Common Period Lengths:** 14, 20

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/adx?symbol=AAPL&periodLength=14&timeframe=1day&apikey=YOUR_API_KEY
```

**Example Response:**
```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "adx": 26.414065772772613
  }
]
```

**Interpretation:**
- ADX > 25: Strong trend
- ADX < 20: Weak trend or sideways movement
- ADX between 20-25: Moderate trend

### Volatility Indicators

#### Standard Deviation

Measures the amount of variation or dispersion in price movements.

**Endpoint:**
```
GET /technical-indicators/standarddeviation
```

**Example Request:**
```
https://financialmodelingprep.com/stable/technical-indicators/standarddeviation?symbol=AAPL&periodLength=20&timeframe=1day&apikey=YOUR_API_KEY
```

**Example Response:**
```json
[
  {
    "date": "2025-02-04 00:00:00",
    "open": 227.2,
    "high": 233.13,
    "low": 226.65,
    "close": 232.8,
    "volume": 44489128,
    "standardDeviation": 6.139182763202282
  }
]
```

## Rate Limits

- **Free Tier:** 250 requests per day
- **Starter Plan:** 1,000 requests per day
- **Professional Plan:** 10,000 requests per day
- **Enterprise Plan:** Unlimited requests

## Error Responses

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Rate limit exceeded |
| 404 | Not Found - Invalid symbol or endpoint |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "error": {
    "message": "Invalid symbol",
    "code": 404
  }
}
```

## Best Practices

### 1. Parameter Selection

- **Period Length:** Choose appropriate periods based on your analysis timeframe:
  - Short-term: 5, 10, 14 periods
  - Medium-term: 20, 50 periods
  - Long-term: 100, 200 periods

- **Timeframe:** Select based on trading strategy:
  - Day trading: 1min, 5min, 15min
  - Swing trading: 1hour, 4hour, 1day
  - Position trading: 1day

### 2. Data Management

- Cache responses to avoid unnecessary API calls
- Implement proper error handling for rate limits
- Use date ranges to limit data volume

### 3. Technical Analysis Tips

- Combine multiple indicators for better signals
- Consider market context (trending vs. ranging)
- Backtest indicator strategies before live trading
- Understand indicator limitations and false signals

## Code Examples

### Python Example using requests

```python
import requests
import pandas as pd

def get_rsi(symbol, period_length=14, timeframe='1day', api_key='YOUR_API_KEY'):
    """
    Fetch RSI data for a given symbol
    """
    url = f"https://financialmodelingprep.com/stable/technical-indicators/rsi"
    params = {
        'symbol': symbol,
        'periodLength': period_length,
        'timeframe': timeframe,
        'apikey': api_key
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data)
    else:
        print(f"Error: {response.status_code}")
        return None

# Usage
rsi_data = get_rsi('AAPL', period_length=14)
print(rsi_data.head())
```

### JavaScript Example

```javascript
async function getRSI(symbol, periodLength = 14, timeframe = '1day', apiKey = 'YOUR_API_KEY') {
    const url = `https://financialmodelingprep.com/stable/technical-indicators/rsi`;
    const params = new URLSearchParams({
        symbol: symbol,
        periodLength: periodLength,
        timeframe: timeframe,
        apikey: apiKey
    });

    try {
        const response = await fetch(`${url}?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching RSI data:', error);
        return null;
    }
}

// Usage
getRSI('AAPL', 14).then(data => {
    console.log(data);
});
```

## Supported Symbols

The Technical Indicators API supports:

- **US Stocks:** NYSE, NASDAQ listed companies
- **International Stocks:** Major global exchanges
- **ETFs:** Exchange-traded funds
- **Indices:** Major stock indices (^GSPC, ^DJI, ^IXIC)
- **Forex:** Currency pairs (EURUSD, GBPUSD, etc.)
- **Cryptocurrencies:** Major crypto pairs (BTCUSD, ETHUSD, etc.)
- **Commodities:** Gold, Silver, Oil, etc.

## Additional Resources

- [FMP API Documentation](https://site.financialmodelingprep.com/developer/docs)
- [Technical Analysis Basics](https://site.financialmodelingprep.com/developer/docs/technical-analysis)
- [API Rate Limits](https://site.financialmodelingprep.com/developer/docs/pricing)
- [Support Contact](https://site.financialmodelingprep.com/contact)

## Changelog

### Version 1.0.0 (Current)
- Initial release with 8 technical indicators
- Support for multiple timeframes
- Comprehensive parameter validation
- Rate limiting implementation

---

*Last updated: October 2025*