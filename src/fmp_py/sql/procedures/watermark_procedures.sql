-- Simple stored procedures for watermark management
-- Compatible with existing fetch_watermarks table structure

USE fmp_cache;

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
            last_fetch_date,
            records_count
        ) VALUES (
            p_symbol,
            p_fetch_type,
            DATE_SUB(CURDATE(), INTERVAL 5 YEAR), -- Start from 5 years ago
            0
        );
    END IF;
    
    -- Return the watermark with expected column names
    SELECT 
        symbol,
        fetch_type,
        DATE_SUB(CURDATE(), INTERVAL 5 YEAR) as earliest_date,
        COALESCE(last_fetch_date, DATE_SUB(CURDATE(), INTERVAL 5 YEAR)) as latest_date,
        COALESCE(last_fetch_date, DATE_SUB(CURDATE(), INTERVAL 5 YEAR)) as last_fetch_date,
        COALESCE(records_count, 0) as total_records,
        'active' as fetch_status,
        0 as error_count,
        NULL as last_error_message
    FROM fetch_watermarks 
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
        last_fetch_date = p_latest_date,
        records_count = COALESCE(records_count, 0) + p_records_count,
        updated_at = NOW()
    WHERE symbol = p_symbol AND fetch_type = p_fetch_type;
    
    -- Insert if it doesn't exist (shouldn't happen, but safety net)
    INSERT IGNORE INTO fetch_watermarks (
        symbol, 
        fetch_type, 
        last_fetch_date,
        records_count
    ) VALUES (
        p_symbol,
        p_fetch_type,
        p_latest_date,
        p_records_count
    );
END //

-- Record fetch error (simple version)
CREATE PROCEDURE RecordFetchError(
    IN p_symbol VARCHAR(20),
    IN p_fetch_type VARCHAR(50),
    IN p_error_message TEXT
)
BEGIN
    -- For now, just update the record timestamp
    -- Can be enhanced later when we add error tracking columns
    UPDATE fetch_watermarks 
    SET updated_at = NOW()
    WHERE symbol = p_symbol AND fetch_type = p_fetch_type;
END //

DELIMITER ;