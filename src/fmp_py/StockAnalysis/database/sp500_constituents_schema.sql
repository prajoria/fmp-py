-- S&P 500 Constituents Database Schema
-- Table to store S&P 500 constituent stocks with their metadata

-- Create the S&P 500 constituents table
CREATE TABLE IF NOT EXISTS sp500_constituents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    security VARCHAR(200) NOT NULL,
    gics_sector VARCHAR(100),
    gics_sub_industry VARCHAR(150),
    headquarters_location VARCHAR(200),
    date_added DATE,
    cik VARCHAR(10),
    founded VARCHAR(50),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Indexes for performance
    UNIQUE KEY uk_sp500_symbol (symbol),
    INDEX idx_sp500_sector (gics_sector),
    INDEX idx_sp500_active (is_active),
    INDEX idx_sp500_fetched (fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create a view for active S&P 500 constituents
CREATE OR REPLACE VIEW sp500_active AS
SELECT 
    symbol,
    security,
    gics_sector,
    gics_sub_industry,
    headquarters_location,
    date_added,
    cik,
    founded,
    fetched_at,
    updated_at
FROM sp500_constituents 
WHERE is_active = TRUE
ORDER BY symbol;

-- Create a stored procedure to refresh S&P 500 data
DELIMITER //
CREATE OR REPLACE PROCEDURE RefreshSP500Data()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Mark all current records as inactive
    UPDATE sp500_constituents SET is_active = FALSE;
    
    -- The actual data insertion will be done by the Python script
    -- This procedure is mainly for cleanup and preparation
    
    COMMIT;
END//
DELIMITER ;

-- Create a function to get sector statistics
DELIMITER //
CREATE OR REPLACE FUNCTION GetSP500SectorCount(sector_name VARCHAR(100))
RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE count_result INT DEFAULT 0;
    
    SELECT COUNT(*) INTO count_result
    FROM sp500_constituents 
    WHERE gics_sector = sector_name AND is_active = TRUE;
    
    RETURN count_result;
END//
DELIMITER ;

-- Insert some metadata about the table
INSERT INTO table_metadata (table_name, description, last_updated, data_source) 
VALUES (
    'sp500_constituents',
    'S&P 500 constituent stocks with sector information and metadata',
    NOW(),
    'Wikipedia - List of S&P 500 companies'
) ON DUPLICATE KEY UPDATE 
    description = VALUES(description),
    last_updated = VALUES(last_updated),
    data_source = VALUES(data_source);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sp500_security ON sp500_constituents(security);
CREATE INDEX IF NOT EXISTS idx_sp500_date_added ON sp500_constituents(date_added);
CREATE INDEX IF NOT EXISTS idx_sp500_updated ON sp500_constituents(updated_at);

-- Sample query examples (commented out)
/*
-- Get all constituents by sector
SELECT gics_sector, COUNT(*) as count 
FROM sp500_active 
GROUP BY gics_sector 
ORDER BY count DESC;

-- Get recently added companies
SELECT symbol, security, date_added 
FROM sp500_active 
WHERE date_added >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
ORDER BY date_added DESC;

-- Get technology sector companies
SELECT symbol, security, gics_sub_industry 
FROM sp500_active 
WHERE gics_sector = 'Information Technology'
ORDER BY symbol;

-- Get companies by headquarters state
SELECT headquarters_location, COUNT(*) as count
FROM sp500_active 
WHERE headquarters_location IS NOT NULL
GROUP BY headquarters_location
ORDER BY count DESC
LIMIT 10;
*/