-- Historical Charts Data Schema Extension
-- Additional tables for FMP Historical Charts API caching
-- Created: 2025-01-27

USE fmp_cache;

-- ============================================================================
-- HISTORICAL CHARTS DATA TABLES
-- ============================================================================

-- Historical price data (light version) - EOD data with basic OHLCV
CREATE TABLE historical_charts_light (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    `open` DECIMAL(20, 4),
    high DECIMAL(20, 4),
    low DECIMAL(20, 4),
    `close` DECIMAL(20, 4),
    volume BIGINT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_symbol_date_range (symbol, date),
    INDEX idx_expires_at (expires_at),
    INDEX idx_cached_at (cached_at)
) ENGINE=InnoDB;

-- Historical price data (full version) - EOD data with extended fields
CREATE TABLE historical_charts_full (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    `open` DECIMAL(20, 4),
    high DECIMAL(20, 4),
    low DECIMAL(20, 4),
    `close` DECIMAL(20, 4),
    adj_close DECIMAL(20, 4),
    volume BIGINT,
    unadjusted_volume BIGINT,
    `change` DECIMAL(20, 4),
    change_percent DECIMAL(10, 4),
    vwap DECIMAL(20, 4),
    label VARCHAR(50),
    change_over_time DECIMAL(10, 6),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_symbol_date_range (symbol, date),
    INDEX idx_expires_at (expires_at),
    INDEX idx_cached_at (cached_at)
) ENGINE=InnoDB;

-- Intraday price data - All supported intervals (1min, 5min, 15min, 30min, 1hour, 4hour)
CREATE TABLE historical_charts_intraday (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    datetime DATETIME NOT NULL,
    `interval` VARCHAR(10) NOT NULL, -- '1min', '5min', '15min', '30min', '1hour', '4hour'
    `open` DECIMAL(20, 4),
    high DECIMAL(20, 4),
    low DECIMAL(20, 4),
    `close` DECIMAL(20, 4),
    volume BIGINT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_datetime_interval (symbol, datetime, `interval`),
    INDEX idx_symbol (symbol),
    INDEX idx_datetime (datetime),
    INDEX idx_interval (`interval`),
    INDEX idx_symbol_datetime_range (symbol, datetime),
    INDEX idx_symbol_interval (symbol, `interval`),
    INDEX idx_expires_at (expires_at),
    INDEX idx_cached_at (cached_at)
) ENGINE=InnoDB;

-- Chart data cache metadata - Track specific chart data cache entries
CREATE TABLE historical_charts_cache_metadata (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cache_key VARCHAR(500) NOT NULL UNIQUE,
    endpoint_type VARCHAR(50) NOT NULL, -- 'light', 'full', 'intraday'
    symbol VARCHAR(20) NOT NULL,
    `interval` VARCHAR(10), -- For intraday data only
    date_from DATE,
    date_to DATE,
    params JSON,
    record_count INT DEFAULT 0,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    hit_count INT DEFAULT 0,
    last_hit_at TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    INDEX idx_cache_key (cache_key),
    INDEX idx_symbol (symbol),
    INDEX idx_endpoint_type (endpoint_type),
    INDEX idx_symbol_endpoint (symbol, endpoint_type),
    INDEX idx_expires_at (expires_at),
    INDEX idx_interval (`interval`)
) ENGINE=InnoDB;

-- ============================================================================
-- VIEWS FOR HISTORICAL CHARTS DATA
-- ============================================================================

-- Latest historical light data view
CREATE VIEW v_latest_historical_light AS
SELECT 
    symbol,
    date,
    `open`,
    high,
    low,
    `close`,
    volume,
    cached_at
FROM historical_charts_light hcl
WHERE hcl.expires_at > NOW()
ORDER BY symbol, date DESC;

-- Latest historical full data view
CREATE VIEW v_latest_historical_full AS
SELECT 
    symbol,
    date,
    `open`,
    high,
    low,
    `close`,
    adj_close,
    volume,
    unadjusted_volume,
    `change`,
    change_percent,
    vwap,
    label,
    change_over_time,
    cached_at
FROM historical_charts_full hcf
WHERE hcf.expires_at > NOW()
ORDER BY symbol, date DESC;

-- Latest intraday data view
CREATE VIEW v_latest_intraday_data AS
SELECT 
    symbol,
    datetime,
    `interval`,
    `open`,
    high,
    low,
    `close`,
    volume,
    cached_at
FROM historical_charts_intraday hci
WHERE hci.expires_at > NOW()
ORDER BY symbol, `interval`, datetime DESC;

-- Historical charts cache statistics view
CREATE VIEW v_historical_charts_cache_stats AS
SELECT 
    endpoint_type,
    COUNT(*) as total_entries,
    COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as valid_entries,
    COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_entries,
    SUM(record_count) as total_records,
    SUM(hit_count) as total_hits,
    AVG(hit_count) as avg_hits_per_entry,
    MIN(cached_at) as oldest_cache,
    MAX(cached_at) as newest_cache
FROM historical_charts_cache_metadata
GROUP BY endpoint_type;

-- ============================================================================
-- STORED PROCEDURES FOR MAINTENANCE
-- ============================================================================

DELIMITER //

-- Cleanup expired historical charts data
CREATE PROCEDURE CleanupExpiredHistoricalCharts()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Delete expired light data
    DELETE FROM historical_charts_light 
    WHERE expires_at <= NOW();
    
    -- Delete expired full data
    DELETE FROM historical_charts_full 
    WHERE expires_at <= NOW();
    
    -- Delete expired intraday data
    DELETE FROM historical_charts_intraday 
    WHERE expires_at <= NOW();
    
    -- Delete expired cache metadata
    DELETE FROM historical_charts_cache_metadata 
    WHERE expires_at <= NOW();
    
    COMMIT;
    
    -- Return cleanup statistics
    SELECT 
        'historical_charts_light' as table_name,
        COUNT(*) as remaining_records
    FROM historical_charts_light
    UNION ALL
    SELECT 
        'historical_charts_full' as table_name,
        COUNT(*) as remaining_records
    FROM historical_charts_full
    UNION ALL
    SELECT 
        'historical_charts_intraday' as table_name,
        COUNT(*) as remaining_records
    FROM historical_charts_intraday
    UNION ALL
    SELECT 
        'historical_charts_cache_metadata' as table_name,
        COUNT(*) as remaining_records
    FROM historical_charts_cache_metadata;
    
END //

-- Get cache statistics for historical charts
CREATE PROCEDURE GetHistoricalChartsCacheStats()
BEGIN
    SELECT 
        'Cache Statistics' as section,
        endpoint_type,
        total_entries,
        valid_entries,
        expired_entries,
        total_records,
        total_hits,
        avg_hits_per_entry,
        oldest_cache,
        newest_cache
    FROM v_historical_charts_cache_stats
    
    UNION ALL
    
    SELECT 
        'Data Volume' as section,
        'historical_charts_light' as endpoint_type,
        COUNT(*) as total_entries,
        COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as valid_entries,
        COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_entries,
        0 as total_records,
        0 as total_hits,
        0 as avg_hits_per_entry,
        MIN(cached_at) as oldest_cache,
        MAX(cached_at) as newest_cache
    FROM historical_charts_light
    
    UNION ALL
    
    SELECT 
        'Data Volume' as section,
        'historical_charts_full' as endpoint_type,
        COUNT(*) as total_entries,
        COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as valid_entries,
        COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_entries,
        0 as total_records,
        0 as total_hits,
        0 as avg_hits_per_entry,
        MIN(cached_at) as oldest_cache,
        MAX(cached_at) as newest_cache
    FROM historical_charts_full
    
    UNION ALL
    
    SELECT 
        'Data Volume' as section,
        'historical_charts_intraday' as endpoint_type,
        COUNT(*) as total_entries,
        COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as valid_entries,
        COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_entries,
        0 as total_records,
        0 as total_hits,
        0 as avg_hits_per_entry,
        MIN(cached_at) as oldest_cache,
        MAX(cached_at) as newest_cache
    FROM historical_charts_intraday;
    
END //

DELIMITER ;