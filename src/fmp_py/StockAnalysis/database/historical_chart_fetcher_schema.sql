-- Additional schema for FMP Historical Chart Fetcher
-- Created: 2025-10-14

USE fmp_cache;

-- ============================================================================
-- HISTORICAL PRICE FULL DAILY TABLE
-- ============================================================================

-- Table for storing comprehensive historical price data (full version)
CREATE TABLE IF NOT EXISTS historical_price_full_daily (
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
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- ============================================================================
-- FETCH WATERMARK TABLE
-- ============================================================================

-- Table for tracking fetch progress and watermarks
CREATE TABLE IF NOT EXISTS fetch_watermarks (
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
-- FETCH SESSIONS TABLE
-- ============================================================================

-- Table for tracking individual fetch sessions
CREATE TABLE IF NOT EXISTS fetch_sessions (
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

-- ============================================================================
-- POPULAR STOCKS REFERENCE TABLE
-- ============================================================================

-- Table for maintaining list of popular stocks to fetch
CREATE TABLE IF NOT EXISTS popular_stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    market_cap_category ENUM('large', 'mid', 'small') DEFAULT 'large',
    exchange VARCHAR(50),
    priority INT DEFAULT 100, -- Lower number = higher priority
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol),
    INDEX idx_priority (priority),
    INDEX idx_is_active (is_active),
    INDEX idx_sector (sector)
) ENGINE=InnoDB;

-- ============================================================================
-- VIEWS FOR MONITORING
-- ============================================================================

-- View for fetch progress monitoring
CREATE VIEW v_fetch_progress AS
SELECT 
    fw.symbol,
    fw.fetch_type,
    fw.earliest_date,
    fw.latest_date,
    fw.last_fetch_date,
    fw.total_records,
    fw.fetch_status,
    fw.error_count,
    fw.last_successful_fetch,
    DATEDIFF(CURDATE(), fw.latest_date) as days_behind,
    CASE 
        WHEN fw.fetch_status = 'complete' THEN '✅ Complete'
        WHEN fw.fetch_status = 'failed' THEN '❌ Failed'
        WHEN fw.fetch_status = 'paused' THEN '⏸️ Paused'
        WHEN DATEDIFF(CURDATE(), fw.latest_date) > 7 THEN '⚠️ Behind'
        ELSE '🟢 Active'
    END as status_display
FROM fetch_watermarks fw
ORDER BY fw.symbol, fw.fetch_type;

-- View for session statistics
CREATE VIEW v_fetch_session_stats AS
SELECT 
    fs.session_id,
    fs.fetch_type,
    fs.status,
    fs.symbols_processed,
    fs.symbols_successful,
    fs.symbols_failed,
    fs.total_api_calls,
    fs.total_records_fetched,
    TIMESTAMPDIFF(MINUTE, fs.start_time, COALESCE(fs.end_time, NOW())) as duration_minutes,
    CASE 
        WHEN fs.symbols_processed > 0 
        THEN ROUND((fs.symbols_successful / fs.symbols_processed) * 100, 2)
        ELSE 0 
    END as success_rate_percent
FROM fetch_sessions fs
ORDER BY fs.start_time DESC;

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
-- INSERT POPULAR STOCKS
-- ============================================================================

-- Insert popular stocks data
INSERT INTO popular_stocks (symbol, company_name, sector, market_cap_category, exchange, priority, notes) VALUES
-- Large Cap Tech Giants
('AAPL', 'Apple Inc.', 'Technology', 'large', 'NASDAQ', 1, 'Top tech stock'),
('MSFT', 'Microsoft Corporation', 'Technology', 'large', 'NASDAQ', 2, 'Cloud leader'),
('GOOGL', 'Alphabet Inc.', 'Technology', 'large', 'NASDAQ', 3, 'Search & AI'),
('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 'large', 'NASDAQ', 4, 'E-commerce giant'),
('META', 'Meta Platforms Inc.', 'Technology', 'large', 'NASDAQ', 5, 'Social media'),
('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 'large', 'NASDAQ', 6, 'EV leader'),
('NVDA', 'NVIDIA Corporation', 'Technology', 'large', 'NASDAQ', 7, 'AI & GPU leader'),

-- Other Large Cap Stocks
('BRK.B', 'Berkshire Hathaway Inc.', 'Financial Services', 'large', 'NYSE', 10, 'Buffett holding'),
('JNJ', 'Johnson & Johnson', 'Healthcare', 'large', 'NYSE', 11, 'Healthcare giant'),
('V', 'Visa Inc.', 'Financial Services', 'large', 'NYSE', 12, 'Payment processor'),
('WMT', 'Walmart Inc.', 'Consumer Staples', 'large', 'NYSE', 13, 'Retail giant'),
('PG', 'Procter & Gamble Co.', 'Consumer Staples', 'large', 'NYSE', 14, 'Consumer goods'),
('UNH', 'UnitedHealth Group Inc.', 'Healthcare', 'large', 'NYSE', 15, 'Health insurance'),
('HD', 'Home Depot Inc.', 'Consumer Discretionary', 'large', 'NYSE', 16, 'Home improvement'),
('MA', 'Mastercard Inc.', 'Financial Services', 'large', 'NYSE', 17, 'Payment processor'),

-- Financial Sector
('JPM', 'JPMorgan Chase & Co.', 'Financial Services', 'large', 'NYSE', 20, 'Banking leader'),
('BAC', 'Bank of America Corp.', 'Financial Services', 'large', 'NYSE', 21, 'Major bank'),
('WFC', 'Wells Fargo & Co.', 'Financial Services', 'large', 'NYSE', 22, 'Regional bank'),
('GS', 'Goldman Sachs Group Inc.', 'Financial Services', 'large', 'NYSE', 23, 'Investment bank'),

-- Energy & Materials
('XOM', 'Exxon Mobil Corporation', 'Energy', 'large', 'NYSE', 30, 'Oil & gas'),
('CVX', 'Chevron Corporation', 'Energy', 'large', 'NYSE', 31, 'Oil & gas'),

-- Healthcare & Pharma
('PFE', 'Pfizer Inc.', 'Healthcare', 'large', 'NYSE', 40, 'Pharmaceutical'),
('ABBV', 'AbbVie Inc.', 'Healthcare', 'large', 'NYSE', 41, 'Biotech'),
('MRK', 'Merck & Co. Inc.', 'Healthcare', 'large', 'NYSE', 42, 'Pharmaceutical'),

-- Popular Growth Stocks
('NFLX', 'Netflix Inc.', 'Communication Services', 'large', 'NASDAQ', 50, 'Streaming leader'),
('CRM', 'Salesforce Inc.', 'Technology', 'large', 'NYSE', 51, 'CRM software'),
('AMD', 'Advanced Micro Devices', 'Technology', 'large', 'NASDAQ', 52, 'Semiconductor'),
('INTC', 'Intel Corporation', 'Technology', 'large', 'NASDAQ', 53, 'Semiconductor'),
('ORCL', 'Oracle Corporation', 'Technology', 'large', 'NYSE', 54, 'Database software'),

-- Popular ETFs
('SPY', 'SPDR S&P 500 ETF', 'ETF', 'large', 'NYSE', 100, 'S&P 500 ETF'),
('QQQ', 'Invesco QQQ Trust', 'ETF', 'large', 'NASDAQ', 101, 'NASDAQ 100 ETF'),
('IWM', 'iShares Russell 2000 ETF', 'ETF', 'large', 'NYSE', 102, 'Small cap ETF'),
('VTI', 'Vanguard Total Stock Market ETF', 'ETF', 'large', 'NYSE', 103, 'Total market ETF')

ON DUPLICATE KEY UPDATE 
    company_name = VALUES(company_name),
    sector = VALUES(sector),
    market_cap_category = VALUES(market_cap_category),
    exchange = VALUES(exchange),
    updated_at = NOW();