-- Useful queries for FMP cache database
-- Use these queries to monitor and maintain your cache

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
    'Companies with Profiles' as metric,
    COUNT(*) as value
FROM company_profiles
UNION ALL
SELECT 
    'Cached Quotes' as metric,
    COUNT(*) as value
FROM quotes
UNION ALL
SELECT 
    'Historical Daily Records' as metric,
    COUNT(*) as value
FROM historical_prices_daily
UNION ALL
SELECT 
    'Income Statements' as metric,
    COUNT(*) as value
FROM income_statements
UNION ALL
SELECT 
    'Balance Sheets' as metric,
    COUNT(*) as value
FROM balance_sheets
UNION ALL
SELECT 
    'Cash Flow Statements' as metric,
    COUNT(*) as value
FROM cash_flow_statements;

-- Cache hit rate
SELECT 
    endpoint,
    COUNT(*) as total_requests,
    SUM(from_cache) as cache_hits,
    ROUND(SUM(from_cache) / COUNT(*) * 100, 2) as hit_rate_percent,
    ROUND(AVG(response_time_ms), 2) as avg_response_time_ms
FROM api_request_log
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY endpoint
ORDER BY total_requests DESC;

-- ============================================================================
-- DATA FRESHNESS
-- ============================================================================

-- Check expired cache entries
SELECT 
    'Expired Quotes' as cache_type,
    COUNT(*) as count
FROM quotes
WHERE expires_at < NOW()
UNION ALL
SELECT 
    'Expired Company Profiles' as cache_type,
    COUNT(*) as count
FROM company_profiles
WHERE expires_at < NOW()
UNION ALL
SELECT 
    'Expired Cache Metadata' as cache_type,
    COUNT(*) as count
FROM cache_metadata
WHERE expires_at < NOW();

-- Recently cached data
SELECT 
    'Quotes' as data_type,
    COUNT(*) as records,
    MAX(cached_at) as last_cached
FROM quotes
WHERE cached_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
UNION ALL
SELECT 
    'Historical Prices' as data_type,
    COUNT(*) as records,
    MAX(cached_at) as last_cached
FROM historical_prices_daily
WHERE cached_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
UNION ALL
SELECT 
    'Company Profiles' as data_type,
    COUNT(*) as records,
    MAX(cached_at) as last_cached
FROM company_profiles
WHERE cached_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- ============================================================================
-- TOP COMPANIES BY DATA
-- ============================================================================

-- Companies with most complete data
SELECT 
    c.symbol,
    c.name,
    c.sector,
    COUNT(DISTINCT hpd.date) as daily_prices_count,
    COUNT(DISTINCT is_t.date) as income_stmt_count,
    COUNT(DISTINCT bs.date) as balance_sheet_count,
    COUNT(DISTINCT cf.date) as cashflow_count,
    (cp.symbol IS NOT NULL) as has_profile
FROM companies c
LEFT JOIN historical_prices_daily hpd ON c.symbol = hpd.symbol
LEFT JOIN income_statements is_t ON c.symbol = is_t.symbol
LEFT JOIN balance_sheets bs ON c.symbol = bs.symbol
LEFT JOIN cash_flow_statements cf ON c.symbol = cf.symbol
LEFT JOIN company_profiles cp ON c.symbol = cp.symbol
GROUP BY c.symbol, c.name, c.sector, has_profile
ORDER BY 
    (COUNT(DISTINCT hpd.date) + 
     COUNT(DISTINCT is_t.date) + 
     COUNT(DISTINCT bs.date) + 
     COUNT(DISTINCT cf.date)) DESC
LIMIT 20;

-- Most queried symbols
SELECT 
    symbol,
    COUNT(*) as request_count,
    MAX(created_at) as last_requested
FROM api_request_log
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND symbol IS NOT NULL
GROUP BY symbol
ORDER BY request_count DESC
LIMIT 20;

-- ============================================================================
-- FINANCIAL DATA ANALYSIS
-- ============================================================================

-- Latest financial metrics for top companies by market cap
SELECT 
    cp.symbol,
    cp.company_name,
    cp.sector,
    cp.mkt_cap,
    km.pe_ratio,
    km.pb_ratio,
    km.roe,
    fr.debt_to_equity,
    fr.current_ratio,
    km.dividend_yield
FROM company_profiles cp
LEFT JOIN key_metrics km ON cp.symbol = km.symbol
    AND km.id = (SELECT MAX(id) FROM key_metrics WHERE symbol = cp.symbol)
LEFT JOIN financial_ratios fr ON cp.symbol = fr.symbol
    AND fr.id = (SELECT MAX(id) FROM financial_ratios WHERE symbol = cp.symbol)
WHERE cp.mkt_cap IS NOT NULL
ORDER BY cp.mkt_cap DESC
LIMIT 50;

-- Companies with recent earnings
SELECT 
    ec.symbol,
    c.name,
    ec.date as earnings_date,
    ec.eps,
    ec.eps_estimated,
    (ec.eps - ec.eps_estimated) as eps_surprise,
    ROUND((ec.eps - ec.eps_estimated) / ec.eps_estimated * 100, 2) as surprise_percent
FROM earnings_calendar ec
JOIN companies c ON ec.symbol = c.symbol
WHERE ec.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    AND ec.eps IS NOT NULL
    AND ec.eps_estimated IS NOT NULL
ORDER BY ec.date DESC
LIMIT 30;

-- ============================================================================
-- SECTOR ANALYSIS
-- ============================================================================

-- Average metrics by sector
SELECT 
    cp.sector,
    COUNT(DISTINCT cp.symbol) as company_count,
    ROUND(AVG(km.pe_ratio), 2) as avg_pe,
    ROUND(AVG(km.pb_ratio), 2) as avg_pb,
    ROUND(AVG(km.roe), 4) as avg_roe,
    ROUND(AVG(fr.debt_to_equity), 2) as avg_debt_to_equity,
    ROUND(AVG(km.dividend_yield), 4) as avg_dividend_yield
FROM company_profiles cp
LEFT JOIN key_metrics km ON cp.symbol = km.symbol
    AND km.id = (SELECT MAX(id) FROM key_metrics WHERE symbol = cp.symbol)
LEFT JOIN financial_ratios fr ON cp.symbol = fr.symbol
    AND fr.id = (SELECT MAX(id) FROM financial_ratios WHERE symbol = cp.symbol)
WHERE cp.sector IS NOT NULL
GROUP BY cp.sector
ORDER BY company_count DESC;

-- Recent sector performance
SELECT 
    sector,
    changes_percentage,
    date
FROM sector_performance
WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
ORDER BY date DESC, changes_percentage DESC;

-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Delete expired cache entries
-- DELETE FROM quotes WHERE expires_at < NOW();
-- DELETE FROM company_profiles WHERE expires_at < NOW();
-- DELETE FROM cache_metadata WHERE expires_at < NOW();

-- Delete old API request logs (keep last 30 days)
-- DELETE FROM api_request_log WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Optimize tables
-- OPTIMIZE TABLE quotes;
-- OPTIMIZE TABLE historical_prices_daily;
-- OPTIMIZE TABLE company_profiles;
-- OPTIMIZE TABLE api_request_log;

-- Get database size
SELECT 
    table_schema as 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'fmp_cache'
GROUP BY table_schema;

-- Table sizes
SELECT 
    table_name as 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) as 'Size (MB)',
    table_rows as 'Rows'
FROM information_schema.tables
WHERE table_schema = 'fmp_cache'
ORDER BY (data_length + index_length) DESC;
