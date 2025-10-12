# Chart APIs Documentation

This document provides comprehensive documentation for Financial Modeling Prep's Chart APIs, which offer various types of stock price and volume data.

## Table of Contents

1. [Stock Chart Light API](#stock-chart-light-api)
2. [Stock Price and Volume Data API](#stock-price-and-volume-data-api)
3. [Unadjusted Stock Price API](#unadjusted-stock-price-api)
4. [Dividend Adjusted Price Chart API](#dividend-adjusted-price-chart-api)
5. [Intraday Chart APIs](#intraday-chart-apis)
   - [1 Min Interval](#1-min-interval-stock-chart-api)
   - [5 Min Interval](#5-min-interval-stock-chart-api)
   - [15 Min Interval](#15-min-interval-stock-chart-api)
   - [30 Min Interval](#30-min-interval-stock-chart-api)
   - [1 Hour Interval](#1-hour-interval-stock-chart-api)
   - [4 Hour Interval](#4-hour-interval-stock-chart-api)

## Stock Chart Light API

**Availability:** 🌍 Available for companies worldwide

Access simplified stock chart data using the FMP Basic Stock Chart API. This API provides essential charting information, including date, price, and trading volume, making it ideal for tracking stock performance with minimal data and creating basic price and volume charts.

### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-price-eod/light?symbol={symbol}
```

### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2025-06-10 | Start date |
| to | date | | 2025-09-10 | End date |

*Required | Maximum 5000 records per request

### Example Request
```
GET https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=AAPL&from=2025-06-10&to=2025-09-10&apikey=YOUR_API_KEY
```

---

## Stock Price and Volume Data API

**Availability:** 🌍 Available for companies worldwide

Access full price and volume data for any stock symbol using the FMP Comprehensive Stock Price and Volume Data API. Get detailed insights, including open, high, low, close prices, trading volume, price changes, percentage changes, and volume-weighted average price (VWAP).

### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={symbol}
```

### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2025-06-10 | Start date |
| to | date | | 2025-09-10 | End date |

*Required | Maximum 5000 records per request

### Example Request
```
GET https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=AAPL&from=2025-06-10&to=2025-09-10&apikey=YOUR_API_KEY
```

---

## Unadjusted Stock Price API

**Availability:** 🌍 Available for companies worldwide

Access stock price and volume data without adjustments for stock splits with the FMP Unadjusted Stock Price Chart API. Get accurate insights into stock performance, including open, high, low, and close prices, along with trading volume, without split-related changes.

### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-price-eod/non-split-adjusted?symbol={symbol}
```

### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2025-06-10 | Start date |
| to | date | | 2025-09-10 | End date |

*Required | Maximum 5000 records per request

### Example Request
```
GET https://financialmodelingprep.com/stable/historical-price-eod/non-split-adjusted?symbol=AAPL&from=2025-06-10&to=2025-09-10&apikey=YOUR_API_KEY
```

---

## Dividend Adjusted Price Chart API

**Availability:** 🌍 Available for companies worldwide

Analyze stock performance with dividend adjustments using the FMP Dividend-Adjusted Price Chart API. Access end-of-day price and volume data that accounts for dividend payouts, offering a more comprehensive view of stock trends over time.

### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol={symbol}
```

### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2025-06-10 | Start date |
| to | date | | 2025-09-10 | End date |

*Required | Maximum 5000 records per request

### Example Request
```
GET https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol=AAPL&from=2025-06-10&to=2025-09-10&apikey=YOUR_API_KEY
```

---

## Intraday Chart APIs

### 1 Min Interval Stock Chart API

**Availability:** 🌍 Available for companies worldwide

Access precise intraday stock price and volume data with the FMP 1-Minute Interval Stock Chart API. Retrieve real-time or historical stock data in 1-minute intervals, including key information such as open, high, low, and close prices, and trading volume for each minute.

#### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-chart/1min?symbol={symbol}
```

#### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2024-01-01 | Start date |
| to | date | | 2024-03-01 | End date |
| nonadjusted | boolean | | false | Include non-adjusted data |

*Required

#### Example Request
```
GET https://financialmodelingprep.com/stable/historical-chart/1min?symbol=AAPL&from=2024-01-01&to=2024-03-01&apikey=YOUR_API_KEY
```

---

### 5 Min Interval Stock Chart API

**Availability:** 🌍 Available for companies worldwide

Access stock price and volume data with the FMP 5-Minute Interval Stock Chart API. Retrieve detailed stock data in 5-minute intervals, including open, high, low, and close prices, along with trading volume for each 5-minute period. This API is perfect for short-term trading analysis and building intraday charts.

#### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-chart/5min?symbol={symbol}
```

#### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2024-01-01 | Start date |
| to | date | | 2024-03-01 | End date |
| nonadjusted | boolean | | false | Include non-adjusted data |

*Required

#### Example Request
```
GET https://financialmodelingprep.com/stable/historical-chart/5min?symbol=AAPL&from=2024-01-01&to=2024-03-01&apikey=YOUR_API_KEY
```

---

### 15 Min Interval Stock Chart API

**Availability:** 🌍 Available for companies worldwide

Access stock price and volume data with the FMP 15-Minute Interval Stock Chart API. Retrieve detailed stock data in 15-minute intervals, including open, high, low, close prices, and trading volume. This API is ideal for creating intraday charts and analyzing medium-term price trends during the trading day.

#### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-chart/15min?symbol={symbol}
```

#### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2024-01-01 | Start date |
| to | date | | 2024-03-01 | End date |
| nonadjusted | boolean | | false | Include non-adjusted data |

*Required

#### Example Request
```
GET https://financialmodelingprep.com/stable/historical-chart/15min?symbol=AAPL&from=2024-01-01&to=2024-03-01&apikey=YOUR_API_KEY
```

---

### 30 Min Interval Stock Chart API

**Availability:** 🌍 Available for companies worldwide

Access stock price and volume data with the FMP 30-Minute Interval Stock Chart API. Retrieve essential stock data in 30-minute intervals, including open, high, low, close prices, and trading volume. This API is perfect for creating intraday charts and tracking medium-term price movements for more strategic trading decisions.

#### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-chart/30min?symbol={symbol}
```

#### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2024-01-01 | Start date |
| to | date | | 2024-03-01 | End date |
| nonadjusted | boolean | | false | Include non-adjusted data |

*Required

#### Example Request
```
GET https://financialmodelingprep.com/stable/historical-chart/30min?symbol=AAPL&from=2024-01-01&to=2024-03-01&apikey=YOUR_API_KEY
```

---

### 1 Hour Interval Stock Chart API

**Availability:** 🌍 Available for companies worldwide

Track stock price movements over hourly intervals with the FMP 1-Hour Interval Stock Chart API. Access essential stock price and volume data, including open, high, low, and close prices for each hour, to analyze broader intraday trends with precision.

#### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-chart/1hour?symbol={symbol}
```

#### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2024-01-01 | Start date |
| to | date | | 2024-03-01 | End date |
| nonadjusted | boolean | | false | Include non-adjusted data |

*Required

#### Example Request
```
GET https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=AAPL&from=2024-01-01&to=2024-03-01&apikey=YOUR_API_KEY
```

---

### 4 Hour Interval Stock Chart API

**Availability:** 🌍 Available for companies worldwide

Analyze stock price movements over extended intraday periods with the FMP 4-Hour Interval Stock Chart API. Access key stock price and volume data in 4-hour intervals, perfect for tracking longer intraday trends and understanding broader market movements.

#### Endpoint
```
GET https://financialmodelingprep.com/stable/historical-chart/4hour?symbol={symbol}
```

#### Parameters

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| symbol* | string | ✓ | AAPL | Stock symbol |
| from | date | | 2024-01-01 | Start date |
| to | date | | 2024-03-01 | End date |
| nonadjusted | boolean | | false | Include non-adjusted data |

*Required

#### Example Request
```
GET https://financialmodelingprep.com/stable/historical-chart/4hour?symbol=AAPL&from=2024-01-01&to=2024-03-01&apikey=YOUR_API_KEY
```

---

## General Notes

- **Authentication**: Add `?apikey=YOUR_API_KEY` at the end of every request
- **Query Parameters**: Use `&apikey=YOUR_API_KEY` if other query parameters already exist
- **Rate Limits**: Please refer to your subscription plan for rate limit details
- **Data Format**: All APIs return data in JSON format
- **Timestamps**: All timestamps are in UTC format
- **Market Coverage**: Different APIs have different market coverage (worldwide vs US-only)

## Support

For questions about these APIs or pricing information, please [contact Financial Modeling Prep](https://site.financialmodelingprep.com/contact).