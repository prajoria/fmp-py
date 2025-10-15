-- Simple S&P 500 Constituents Table Creation
-- Just the essential table without stored procedures

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