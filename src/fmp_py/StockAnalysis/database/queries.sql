-- Useful queries for FMP cache database (Clean Version)
-- Use these queries to monitor and maintain your cache
-- Updated: 2025-10-15 - Only includes tables that actually exist

-- ============================================================================
-- CACHE STATISTICS
-- ============================================================================

-- Overall cache statistics
SELECT 
    'Total Companies' as metric,
    COUNT(*) as value
FROM companies
UNION ALL
SELECT 
    'S&P 500 Constituents' as metric,
    COUNT(*) as value
FROM sp500_constituents
UNION ALL
SELECT 
    'Company Executives' as metric,
    COUNT(*) as value
FROM company_executives
UNION ALL
SELECT 
    'Historical Daily Records' as metric,
    COUNT(*) as value
FROM historical_prices_daily
UNION ALL
SELECT 
    'API Request Logs' as metric,
    COUNT(*) as value
FROM api_request_log
UNION ALL
SELECT 
    'Fetch Sessions' as metric,
    COUNT(*) as value
FROM fetch_sessions
UNION ALL
SELECT 
    'Fetch Watermarks' as metric,
    COUNT(*) as value
FROM fetch_watermarks;

-- API request statistics
SELECT 
    endpoint,
    COUNT(*) as total_requests,
    ROUND(AVG(response_time_ms), 2) as avg_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,
    MIN(response_time_ms) as min_response_time_ms
FROM api_request_log
WHERE response_time_ms IS NOT NULL
GROUP BY endpoint
ORDER BY total_requests DESC;

-- ============================================================================
-- DATA FRESHNESS
-- ============================================================================

-- Historical price data freshness
SELECT 
    symbol,
    MAX(date) as latest_date,
    COUNT(*) as total_records,
    DATEDIFF(CURDATE(), MAX(date)) as days_old
FROM historical_prices_daily
GROUP BY symbol
ORDER BY days_old DESC, symbol;

-- Fetch watermark status
SELECT 
    symbol,
    fetch_type,
    latest_date,
    fetch_status,
    total_records,
    error_count,
    DATEDIFF(CURDATE(), latest_date) as days_behind
FROM fetch_watermarks
ORDER BY days_behind DESC, symbol;

-- ============================================================================
-- TOP PERFORMERS
-- ============================================================================

-- Latest prices for S&P 500 stocks
SELECT 
    sp.symbol,
    sp.name,
    sp.sector,
    hpd.close as latest_price,
    hpd.change as daily_change,
    hpd.change_percent as daily_change_percent,
    hpd.volume as daily_volume,
    hpd.date as price_date
FROM sp500_constituents sp
JOIN historical_prices_daily hpd ON sp.symbol = hpd.symbol
WHERE hpd.date = (
    SELECT MAX(date) 
    FROM historical_prices_daily hpd2 
    WHERE hpd2.symbol = sp.symbol
)
ORDER BY hpd.change_percent DESC
LIMIT 20;

-- Biggest movers (S&P 500)
SELECT 
    sp.symbol,
    sp.name,
    sp.sector,
    hpd.close as latest_price,
    hpd.change_percent as daily_change_percent,
    hpd.volume as daily_volume,
    hpd.date as price_date
FROM sp500_constituents sp
JOIN historical_prices_daily hpd ON sp.symbol = hpd.symbol
WHERE hpd.date = (
    SELECT MAX(date) 
    FROM historical_prices_daily hpd2 
    WHERE hpd2.symbol = sp.symbol
)
ORDER BY ABS(hpd.change_percent) DESC
LIMIT 20;

-- ============================================================================
-- SECTOR ANALYSIS
-- ============================================================================

-- Average performance by sector (S&P 500)
SELECT 
    sp.sector,
    COUNT(*) as num_stocks,
    ROUND(AVG(hpd.change_percent), 2) as avg_daily_change_percent,
    ROUND(MIN(hpd.change_percent), 2) as min_change_percent,
    ROUND(MAX(hpd.change_percent), 2) as max_change_percent,
    SUM(hpd.volume) as total_volume
FROM sp500_constituents sp
JOIN historical_prices_daily hpd ON sp.symbol = hpd.symbol
WHERE hpd.date = (
    SELECT MAX(date) 
    FROM historical_prices_daily hpd2 
    WHERE hpd2.symbol = sp.symbol
)
GROUP BY sp.sector
ORDER BY avg_daily_change_percent DESC;

-- ============================================================================
-- DATA QUALITY CHECKS
-- ============================================================================

-- Missing data check
SELECT 
    'Symbols in companies but not in historical_prices_daily' as check_type,
    COUNT(*) as count
FROM companies c
LEFT JOIN historical_prices_daily hpd ON c.symbol = hpd.symbol
WHERE hpd.symbol IS NULL
UNION ALL
SELECT 
    'Symbols in sp500_constituents but not in companies' as check_type,
    COUNT(*) as count
FROM sp500_constituents sp
LEFT JOIN companies c ON sp.symbol = c.symbol
WHERE c.symbol IS NULL
UNION ALL
SELECT 
    'Symbols in historical_prices_daily but not in companies' as check_type,
    COUNT(*) as count
FROM (
    SELECT DISTINCT symbol FROM historical_prices_daily
) hpd
LEFT JOIN companies c ON hpd.symbol = c.symbol
WHERE c.symbol IS NULL;

-- Duplicate data check
SELECT 
    'Duplicate historical_prices_daily records' as check_type,
    COUNT(*) - COUNT(DISTINCT symbol, date) as duplicates
FROM historical_prices_daily;

-- Volume anomalies (volume = 0 or extremely high)
SELECT 
    symbol,
    date,
    volume,
    'Zero volume' as anomaly_type
FROM historical_prices_daily
WHERE volume = 0
UNION ALL
SELECT 
    symbol,
    date,
    volume,
    'Extremely high volume' as anomaly_type
FROM historical_prices_daily
WHERE volume > (
    SELECT AVG(volume) * 100 
    FROM historical_prices_daily 
    WHERE volume > 0
)
ORDER BY symbol, date;

-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Clean old API request logs (older than 30 days)
-- DELETE FROM api_request_log WHERE request_time < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Clean old fetch sessions (older than 30 days)
-- DELETE FROM fetch_sessions WHERE start_time < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Update table statistics
-- ANALYZE TABLE companies;
-- ANALYZE TABLE historical_prices_daily;
-- ANALYZE TABLE sp500_constituents;

-- Optimize tables
-- OPTIMIZE TABLE companies;
-- OPTIMIZE TABLE historical_prices_daily;
-- OPTIMIZE TABLE sp500_constituents;

-- ============================================================================
-- USEFUL AGGREGATIONS
-- ============================================================================

-- Daily trading summary
SELECT 
    date,
    COUNT(*) as stocks_traded,
    ROUND(AVG(change_percent), 2) as avg_change_percent,
    ROUND(MIN(change_percent), 2) as min_change_percent,
    ROUND(MAX(change_percent), 2) as max_change_percent,
    SUM(volume) as total_volume
FROM historical_prices_daily
WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date DESC;

-- Symbol coverage summary
SELECT 
    'Total symbols in companies' as metric,
    COUNT(*) as value
FROM companies
UNION ALL
SELECT 
    'Symbols with historical data' as metric,
    COUNT(DISTINCT symbol) as value
FROM historical_prices_daily
UNION ALL
SELECT 
    'S&P 500 symbols' as metric,
    COUNT(*) as value
FROM sp500_constituents
UNION ALL
SELECT 
    'S&P 500 symbols with historical data' as metric,
    COUNT(DISTINCT hpd.symbol) as value
FROM sp500_constituents sp
JOIN historical_prices_daily hpd ON sp.symbol = hpd.symbol;