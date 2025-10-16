-- FMP Cache Database Schema (Clean Version)
-- This schema contains only the tables that are actually used in the current system
-- Updated: 2025-10-15

-- Drop existing database and create fresh
DROP DATABASE IF EXISTS fmp_cache;
CREATE DATABASE fmp_cache CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fmp_cache;

-- ============================================================================
-- CORE ENTITIES
-- ============================================================================

-- Companies/Stocks table - Master list of symbols
CREATE TABLE companies (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50),
    exchange_short_name VARCHAR(20),
    type VARCHAR(50),
    currency VARCHAR(10),
    country VARCHAR(100),
    is_etf BOOLEAN DEFAULT FALSE,
    is_actively_trading BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_exchange (exchange),
    INDEX idx_type (type),
    INDEX idx_is_etf (is_etf),
    INDEX idx_name (name)
) ENGINE=InnoDB;

-- Company executives table - Executive information
CREATE TABLE company_executives (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    title VARCHAR(255),
    pay BIGINT,
    currency_pay VARCHAR(10),
    gender VARCHAR(10),
    year_born INT,
    title_since DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    INDEX idx_symbol (symbol),
    INDEX idx_title (title)
) ENGINE=InnoDB;

-- ============================================================================
-- HISTORICAL PRICE DATA
-- ============================================================================

-- Historical prices daily - Daily OHLCV data
CREATE TABLE historical_prices_daily (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_symbol_date_range (symbol, date),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- S&P 500 DATA
-- ============================================================================

-- S&P 500 constituents table
CREATE TABLE sp500_constituents (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    sub_industry VARCHAR(255),
    headquarters_location VARCHAR(255),
    date_first_added DATE,
    cik VARCHAR(20),
    founded INT,
    weight DECIMAL(8, 4),
    market_cap BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sector (sector),
    INDEX idx_sub_industry (sub_industry),
    INDEX idx_weight (weight),
    INDEX idx_market_cap (market_cap),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- OPERATIONAL TABLES
-- ============================================================================

-- API request logging
CREATE TABLE api_request_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    endpoint VARCHAR(500) NOT NULL,
    symbol VARCHAR(20),
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time_ms INT,
    status_code INT,
    error_message TEXT,
    request_size INT,
    response_size INT,
    INDEX idx_endpoint (endpoint(100)),
    INDEX idx_symbol (symbol),
    INDEX idx_request_time (request_time),
    INDEX idx_status_code (status_code)
) ENGINE=InnoDB;

-- Fetch session tracking
CREATE TABLE fetch_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    fetch_type VARCHAR(50) NOT NULL,
    symbols_requested TEXT, -- JSON array of symbols requested
    symbols_processed INT DEFAULT 0,
    symbols_successful INT DEFAULT 0,
    symbols_failed INT DEFAULT 0,
    total_api_calls INT DEFAULT 0,
    total_records_fetched INT DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    status ENUM('running', 'completed', 'failed', 'interrupted') DEFAULT 'running',
    error_message TEXT,
    notes TEXT,
    INDEX idx_session_id (session_id),
    INDEX idx_fetch_type (fetch_type),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB;

-- Fetch watermark tracking
CREATE TABLE fetch_watermarks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    fetch_type VARCHAR(50) NOT NULL, -- 'historical_full', 'historical_light', etc.
    earliest_date DATE NOT NULL, -- Earliest date we have data for
    latest_date DATE NOT NULL, -- Latest date we have data for
    last_fetch_date DATE NOT NULL, -- Last date we attempted to fetch
    last_successful_fetch TIMESTAMP NOT NULL, -- When the last successful fetch occurred
    total_records INT DEFAULT 0, -- Total number of records fetched for this symbol
    fetch_status ENUM('active', 'complete', 'failed', 'paused') DEFAULT 'active',
    error_count INT DEFAULT 0, -- Number of consecutive errors
    last_error_message TEXT, -- Last error encountered
    notes TEXT, -- Any additional notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_symbol_type (symbol, fetch_type),
    INDEX idx_symbol (symbol),
    INDEX idx_fetch_type (fetch_type),
    INDEX idx_last_fetch_date (last_fetch_date),
    INDEX idx_fetch_status (fetch_status),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Latest company data view
CREATE VIEW v_latest_company_data AS
SELECT 
    c.symbol,
    c.name,
    c.exchange,
    c.type,
    c.is_etf,
    c.is_actively_trading,
    sp.sector,
    sp.sub_industry,
    sp.weight as sp500_weight,
    sp.market_cap,
    sp.is_active as in_sp500
FROM companies c
LEFT JOIN sp500_constituents sp ON c.symbol = sp.symbol
WHERE c.is_actively_trading = TRUE
ORDER BY c.symbol;

-- Latest financial metrics view (basic)
CREATE VIEW v_latest_financial_metrics AS
SELECT 
    hpd.symbol,
    hpd.date as last_trading_date,
    hpd.close as last_price,
    hpd.volume as last_volume,
    hpd.change as daily_change,
    hpd.change_percent as daily_change_percent,
    c.name as company_name,
    c.exchange
FROM historical_prices_daily hpd
JOIN companies c ON hpd.symbol = c.symbol
WHERE hpd.date = (
    SELECT MAX(date) 
    FROM historical_prices_daily hpd2 
    WHERE hpd2.symbol = hpd.symbol
)
ORDER BY hpd.symbol;

-- Recent earnings view (placeholder - no earnings data yet)
CREATE VIEW v_recent_earnings AS
SELECT 
    c.symbol,
    c.name,
    'No earnings data available' as status
FROM companies c
WHERE c.is_actively_trading = TRUE
ORDER BY c.symbol;

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

DELIMITER //

-- Get or create watermark for a symbol
CREATE PROCEDURE GetOrCreateWatermark(
    IN p_symbol VARCHAR(20),
    IN p_fetch_type VARCHAR(50)
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    
    -- Check if watermark exists
    SELECT COUNT(*) INTO v_count 
    FROM fetch_watermarks 
    WHERE symbol = p_symbol AND fetch_type = p_fetch_type;
    
    -- Create if doesn't exist
    IF v_count = 0 THEN
        INSERT INTO fetch_watermarks (
            symbol, 
            fetch_type, 
            earliest_date, 
            latest_date, 
            last_fetch_date,
            last_successful_fetch,
            total_records,
            fetch_status
        ) VALUES (
            p_symbol,
            p_fetch_type,
            DATE_SUB(CURDATE(), INTERVAL 5 YEAR), -- Start from 5 years ago
            DATE_SUB(CURDATE(), INTERVAL 5 YEAR),
            DATE_SUB(CURDATE(), INTERVAL 5 YEAR),
            NOW(),
            0,
            'active'
        );
    END IF;
    
    -- Return the watermark
    SELECT * FROM fetch_watermarks 
    WHERE symbol = p_symbol AND fetch_type = p_fetch_type;
    
END //

-- Update watermark after successful fetch
CREATE PROCEDURE UpdateWatermark(
    IN p_symbol VARCHAR(20),
    IN p_fetch_type VARCHAR(50),
    IN p_latest_date DATE,
    IN p_records_count INT
)
BEGIN
    UPDATE fetch_watermarks 
    SET 
        latest_date = p_latest_date,
        last_fetch_date = p_latest_date,
        last_successful_fetch = NOW(),
        total_records = total_records + p_records_count,
        fetch_status = CASE 
            WHEN p_latest_date >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) THEN 'complete'
            ELSE 'active'
        END,
        error_count = 0,
        last_error_message = NULL,
        updated_at = NOW()
    WHERE symbol = p_symbol AND fetch_type = p_fetch_type;
END //

-- Record fetch error
CREATE PROCEDURE RecordFetchError(
    IN p_symbol VARCHAR(20),
    IN p_fetch_type VARCHAR(50),
    IN p_error_message TEXT
)
BEGIN
    UPDATE fetch_watermarks 
    SET 
        error_count = error_count + 1,
        last_error_message = p_error_message,
        fetch_status = CASE 
            WHEN error_count >= 5 THEN 'failed'
            ELSE 'active'
        END,
        updated_at = NOW()
    WHERE symbol = p_symbol AND fetch_type = p_fetch_type;
END //

DELIMITER ;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- This file only creates the schema. 
-- Use separate SQL files or setup scripts to populate initial data.