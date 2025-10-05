-- FMP Cache Database Schema
-- This schema is designed to cache Financial Modeling Prep API responses
-- Created: 2025-10-05

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

-- Company profiles - Detailed company information
CREATE TABLE company_profiles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),
    price DECIMAL(20, 4),
    beta DECIMAL(10, 4),
    vol_avg BIGINT,
    mkt_cap BIGINT,
    last_div DECIMAL(10, 4),
    `range` VARCHAR(50),
    changes DECIMAL(20, 4),
    cik VARCHAR(20),
    isin VARCHAR(20),
    cusip VARCHAR(20),
    industry VARCHAR(255),
    sector VARCHAR(255),
    website VARCHAR(500),
    description TEXT,
    ceo VARCHAR(255),
    full_time_employees INT,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    zip VARCHAR(20),
    country VARCHAR(100),
    phone VARCHAR(50),
    image VARCHAR(500),
    ipo_date DATE,
    default_image BOOLEAN DEFAULT FALSE,
    is_adr BOOLEAN DEFAULT FALSE,
    dcf DECIMAL(20, 4),
    dcf_diff DECIMAL(20, 4),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol (symbol),
    INDEX idx_sector (sector),
    INDEX idx_industry (industry),
    INDEX idx_cached_at (cached_at),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB;

-- Company executives
CREATE TABLE company_executives (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    title VARCHAR(255),
    name VARCHAR(255),
    pay BIGINT,
    currency_pay VARCHAR(10),
    gender VARCHAR(10),
    year_born INT,
    title_since DATE,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    INDEX idx_symbol (symbol),
    INDEX idx_title (title)
) ENGINE=InnoDB;

-- ============================================================================
-- MARKET DATA - QUOTES AND PRICES
-- ============================================================================

-- Real-time quotes cache (short-lived)
CREATE TABLE quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 4),
    changes_percentage DECIMAL(10, 4),
    `change` DECIMAL(20, 4),
    day_low DECIMAL(20, 4),
    day_high DECIMAL(20, 4),
    year_high DECIMAL(20, 4),
    year_low DECIMAL(20, 4),
    market_cap BIGINT,
    price_avg_50 DECIMAL(20, 4),
    price_avg_200 DECIMAL(20, 4),
    volume BIGINT,
    avg_volume BIGINT,
    `open` DECIMAL(20, 4),
    previous_close DECIMAL(20, 4),
    eps DECIMAL(20, 4),
    pe DECIMAL(20, 4),
    earnings_announcement DATETIME,
    shares_outstanding BIGINT,
    timestamp_unix BIGINT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    INDEX idx_symbol_cached (symbol, cached_at),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB;

-- Historical daily prices
CREATE TABLE historical_prices_daily (
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
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_symbol_date_range (symbol, date)
) ENGINE=InnoDB;

-- Historical intraday prices (5-minute, 1-hour, etc.)
CREATE TABLE historical_prices_intraday (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    datetime DATETIME NOT NULL,
    period VARCHAR(10) NOT NULL, -- '1min', '5min', '15min', '30min', '1hour'
    `open` DECIMAL(20, 4),
    high DECIMAL(20, 4),
    low DECIMAL(20, 4),
    `close` DECIMAL(20, 4),
    volume BIGINT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_datetime_period (symbol, datetime, period),
    INDEX idx_symbol (symbol),
    INDEX idx_datetime (datetime),
    INDEX idx_period (period),
    INDEX idx_symbol_datetime_range (symbol, datetime)
) ENGINE=InnoDB;

-- ============================================================================
-- FINANCIAL STATEMENTS
-- ============================================================================

-- Income statements
CREATE TABLE income_statements (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    calendar_year INT,
    period VARCHAR(10), -- 'FY', 'Q1', 'Q2', 'Q3', 'Q4'
    reported_currency VARCHAR(10),
    cik VARCHAR(20),
    filling_date DATE,
    accepted_date DATETIME,
    revenue BIGINT,
    cost_of_revenue BIGINT,
    gross_profit BIGINT,
    gross_profit_ratio DECIMAL(10, 4),
    research_and_development_expenses BIGINT,
    general_and_administrative_expenses BIGINT,
    selling_and_marketing_expenses BIGINT,
    selling_general_and_administrative_expenses BIGINT,
    other_expenses BIGINT,
    operating_expenses BIGINT,
    cost_and_expenses BIGINT,
    interest_income BIGINT,
    interest_expense BIGINT,
    depreciation_and_amortization BIGINT,
    ebitda BIGINT,
    ebitda_ratio DECIMAL(10, 4),
    operating_income BIGINT,
    operating_income_ratio DECIMAL(10, 4),
    total_other_income_expenses_net BIGINT,
    income_before_tax BIGINT,
    income_before_tax_ratio DECIMAL(10, 4),
    income_tax_expense BIGINT,
    net_income BIGINT,
    net_income_ratio DECIMAL(10, 4),
    eps DECIMAL(20, 4),
    eps_diluted DECIMAL(20, 4),
    weighted_average_shares_outstanding BIGINT,
    weighted_average_shares_outstanding_dil BIGINT,
    link VARCHAR(500),
    final_link VARCHAR(500),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date_period (symbol, date, period),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_calendar_year (calendar_year),
    INDEX idx_period (period)
) ENGINE=InnoDB;

-- Balance sheets
CREATE TABLE balance_sheets (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    calendar_year INT,
    period VARCHAR(10),
    reported_currency VARCHAR(10),
    cik VARCHAR(20),
    filling_date DATE,
    accepted_date DATETIME,
    cash_and_cash_equivalents BIGINT,
    short_term_investments BIGINT,
    cash_and_short_term_investments BIGINT,
    net_receivables BIGINT,
    inventory BIGINT,
    other_current_assets BIGINT,
    total_current_assets BIGINT,
    property_plant_equipment_net BIGINT,
    goodwill BIGINT,
    intangible_assets BIGINT,
    goodwill_and_intangible_assets BIGINT,
    long_term_investments BIGINT,
    tax_assets BIGINT,
    other_non_current_assets BIGINT,
    total_non_current_assets BIGINT,
    other_assets BIGINT,
    total_assets BIGINT,
    account_payables BIGINT,
    short_term_debt BIGINT,
    tax_payables BIGINT,
    deferred_revenue BIGINT,
    other_current_liabilities BIGINT,
    total_current_liabilities BIGINT,
    long_term_debt BIGINT,
    deferred_revenue_non_current BIGINT,
    deferred_tax_liabilities_non_current BIGINT,
    other_non_current_liabilities BIGINT,
    total_non_current_liabilities BIGINT,
    other_liabilities BIGINT,
    capital_lease_obligations BIGINT,
    total_liabilities BIGINT,
    preferred_stock BIGINT,
    common_stock BIGINT,
    retained_earnings BIGINT,
    accumulated_other_comprehensive_income_loss BIGINT,
    othertotal_stockholders_equity BIGINT,
    total_stockholders_equity BIGINT,
    total_equity BIGINT,
    total_liabilities_and_stockholders_equity BIGINT,
    minority_interest BIGINT,
    total_liabilities_and_total_equity BIGINT,
    total_investments BIGINT,
    total_debt BIGINT,
    net_debt BIGINT,
    link VARCHAR(500),
    final_link VARCHAR(500),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date_period (symbol, date, period),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_calendar_year (calendar_year),
    INDEX idx_period (period)
) ENGINE=InnoDB;

-- Cash flow statements
CREATE TABLE cash_flow_statements (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    calendar_year INT,
    period VARCHAR(10),
    reported_currency VARCHAR(10),
    cik VARCHAR(20),
    filling_date DATE,
    accepted_date DATETIME,
    net_income BIGINT,
    depreciation_and_amortization BIGINT,
    deferred_income_tax BIGINT,
    stock_based_compensation BIGINT,
    change_in_working_capital BIGINT,
    accounts_receivables BIGINT,
    inventory BIGINT,
    accounts_payables BIGINT,
    other_working_capital BIGINT,
    other_non_cash_items BIGINT,
    net_cash_provided_by_operating_activities BIGINT,
    investments_in_property_plant_and_equipment BIGINT,
    acquisitions_net BIGINT,
    purchases_of_investments BIGINT,
    sales_maturities_of_investments BIGINT,
    other_investing_activities BIGINT,
    net_cash_used_for_investing_activities BIGINT,
    debt_repayment BIGINT,
    common_stock_issued BIGINT,
    common_stock_repurchased BIGINT,
    dividends_paid BIGINT,
    other_financing_activities BIGINT,
    net_cash_used_provided_by_financing_activities BIGINT,
    effect_of_forex_changes_on_cash BIGINT,
    net_change_in_cash BIGINT,
    cash_at_end_of_period BIGINT,
    cash_at_beginning_of_period BIGINT,
    operating_cash_flow BIGINT,
    capital_expenditure BIGINT,
    free_cash_flow BIGINT,
    link VARCHAR(500),
    final_link VARCHAR(500),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date_period (symbol, date, period),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_calendar_year (calendar_year),
    INDEX idx_period (period)
) ENGINE=InnoDB;

-- ============================================================================
-- FINANCIAL METRICS AND RATIOS
-- ============================================================================

-- Financial ratios
CREATE TABLE financial_ratios (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    calendar_year INT,
    period VARCHAR(10),
    current_ratio DECIMAL(10, 4),
    quick_ratio DECIMAL(10, 4),
    cash_ratio DECIMAL(10, 4),
    days_of_sales_outstanding DECIMAL(10, 4),
    days_of_inventory_outstanding DECIMAL(10, 4),
    operating_cycle DECIMAL(10, 4),
    days_of_payables_outstanding DECIMAL(10, 4),
    cash_conversion_cycle DECIMAL(10, 4),
    gross_profit_margin DECIMAL(10, 4),
    operating_profit_margin DECIMAL(10, 4),
    pretax_profit_margin DECIMAL(10, 4),
    net_profit_margin DECIMAL(10, 4),
    effective_tax_rate DECIMAL(10, 4),
    return_on_assets DECIMAL(10, 4),
    return_on_equity DECIMAL(10, 4),
    return_on_capital_employed DECIMAL(10, 4),
    net_income_per_ebt DECIMAL(10, 4),
    ebt_per_ebit DECIMAL(10, 4),
    ebit_per_revenue DECIMAL(10, 4),
    debt_ratio DECIMAL(10, 4),
    debt_equity_ratio DECIMAL(10, 4),
    long_term_debt_to_capitalization DECIMAL(10, 4),
    total_debt_to_capitalization DECIMAL(10, 4),
    interest_coverage DECIMAL(10, 4),
    cash_flow_to_debt_ratio DECIMAL(10, 4),
    company_equity_multiplier DECIMAL(10, 4),
    receivables_turnover DECIMAL(10, 4),
    payables_turnover DECIMAL(10, 4),
    inventory_turnover DECIMAL(10, 4),
    fixed_asset_turnover DECIMAL(10, 4),
    asset_turnover DECIMAL(10, 4),
    operating_cash_flow_per_share DECIMAL(20, 4),
    free_cash_flow_per_share DECIMAL(20, 4),
    cash_per_share DECIMAL(20, 4),
    payout_ratio DECIMAL(10, 4),
    operating_cash_flow_sales_ratio DECIMAL(10, 4),
    free_cash_flow_operating_cash_flow_ratio DECIMAL(10, 4),
    cash_flow_coverage_ratios DECIMAL(10, 4),
    short_term_coverage_ratios DECIMAL(10, 4),
    capital_expenditure_coverage_ratio DECIMAL(10, 4),
    dividend_paid_and_capex_coverage_ratio DECIMAL(10, 4),
    dividend_payout_ratio DECIMAL(10, 4),
    price_book_value_ratio DECIMAL(10, 4),
    price_to_book_ratio DECIMAL(10, 4),
    price_to_sales_ratio DECIMAL(10, 4),
    price_earnings_ratio DECIMAL(10, 4),
    price_to_free_cash_flows_ratio DECIMAL(10, 4),
    price_to_operating_cash_flows_ratio DECIMAL(10, 4),
    price_cash_flow_ratio DECIMAL(10, 4),
    price_earnings_to_growth_ratio DECIMAL(10, 4),
    price_sales_ratio DECIMAL(10, 4),
    dividend_yield DECIMAL(10, 4),
    enterprise_value_multiple DECIMAL(10, 4),
    price_fair_value DECIMAL(10, 4),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date_period (symbol, date, period),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_calendar_year (calendar_year)
) ENGINE=InnoDB;

-- Key metrics
CREATE TABLE key_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    calendar_year INT,
    period VARCHAR(10),
    revenue_per_share DECIMAL(20, 4),
    net_income_per_share DECIMAL(20, 4),
    operating_cash_flow_per_share DECIMAL(20, 4),
    free_cash_flow_per_share DECIMAL(20, 4),
    cash_per_share DECIMAL(20, 4),
    book_value_per_share DECIMAL(20, 4),
    tangible_book_value_per_share DECIMAL(20, 4),
    shareholders_equity_per_share DECIMAL(20, 4),
    interest_debt_per_share DECIMAL(20, 4),
    market_cap BIGINT,
    enterprise_value BIGINT,
    pe_ratio DECIMAL(10, 4),
    price_to_sales_ratio DECIMAL(10, 4),
    pocf_ratio DECIMAL(10, 4),
    pfcf_ratio DECIMAL(10, 4),
    pb_ratio DECIMAL(10, 4),
    ptb_ratio DECIMAL(10, 4),
    ev_to_sales DECIMAL(10, 4),
    enterprise_value_over_ebitda DECIMAL(10, 4),
    ev_to_operating_cash_flow DECIMAL(10, 4),
    ev_to_free_cash_flow DECIMAL(10, 4),
    earnings_yield DECIMAL(10, 4),
    free_cash_flow_yield DECIMAL(10, 4),
    debt_to_equity DECIMAL(10, 4),
    debt_to_assets DECIMAL(10, 4),
    net_debt_to_ebitda DECIMAL(10, 4),
    current_ratio DECIMAL(10, 4),
    interest_coverage DECIMAL(10, 4),
    income_quality DECIMAL(10, 4),
    dividend_yield DECIMAL(10, 4),
    payout_ratio DECIMAL(10, 4),
    sales_general_and_administrative_to_revenue DECIMAL(10, 4),
    research_and_development_to_revenue DECIMAL(10, 4),
    intangibles_to_total_assets DECIMAL(10, 4),
    capex_to_operating_cash_flow DECIMAL(10, 4),
    capex_to_revenue DECIMAL(10, 4),
    capex_to_depreciation DECIMAL(10, 4),
    stock_based_compensation_to_revenue DECIMAL(10, 4),
    graham_number DECIMAL(20, 4),
    roic DECIMAL(10, 4),
    return_on_tangible_assets DECIMAL(10, 4),
    graham_net_net DECIMAL(20, 4),
    working_capital BIGINT,
    tangible_asset_value BIGINT,
    net_current_asset_value BIGINT,
    invested_capital BIGINT,
    average_receivables BIGINT,
    average_payables BIGINT,
    average_inventory BIGINT,
    days_sales_outstanding DECIMAL(10, 4),
    days_payables_outstanding DECIMAL(10, 4),
    days_of_inventory_on_hand DECIMAL(10, 4),
    receivables_turnover DECIMAL(10, 4),
    payables_turnover DECIMAL(10, 4),
    inventory_turnover DECIMAL(10, 4),
    roe DECIMAL(10, 4),
    capex_per_share DECIMAL(20, 4),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date_period (symbol, date, period),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_calendar_year (calendar_year)
) ENGINE=InnoDB;

-- Financial growth metrics
CREATE TABLE financial_growth (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    calendar_year INT,
    period VARCHAR(10),
    revenue_growth DECIMAL(10, 4),
    gross_profit_growth DECIMAL(10, 4),
    ebit_growth DECIMAL(10, 4),
    operating_income_growth DECIMAL(10, 4),
    net_income_growth DECIMAL(10, 4),
    eps_growth DECIMAL(10, 4),
    eps_diluted_growth DECIMAL(10, 4),
    weighted_average_shares_growth DECIMAL(10, 4),
    weighted_average_shares_diluted_growth DECIMAL(10, 4),
    dividends_per_share_growth DECIMAL(10, 4),
    operating_cash_flow_growth DECIMAL(10, 4),
    free_cash_flow_growth DECIMAL(10, 4),
    ten_y_revenue_growth_per_share DECIMAL(10, 4),
    five_y_revenue_growth_per_share DECIMAL(10, 4),
    three_y_revenue_growth_per_share DECIMAL(10, 4),
    ten_y_operating_cf_growth_per_share DECIMAL(10, 4),
    five_y_operating_cf_growth_per_share DECIMAL(10, 4),
    three_y_operating_cf_growth_per_share DECIMAL(10, 4),
    ten_y_net_income_growth_per_share DECIMAL(10, 4),
    five_y_net_income_growth_per_share DECIMAL(10, 4),
    three_y_net_income_growth_per_share DECIMAL(10, 4),
    ten_y_shareholders_equity_growth_per_share DECIMAL(10, 4),
    five_y_shareholders_equity_growth_per_share DECIMAL(10, 4),
    three_y_shareholders_equity_growth_per_share DECIMAL(10, 4),
    ten_y_dividend_per_share_growth_per_share DECIMAL(10, 4),
    five_y_dividend_per_share_growth_per_share DECIMAL(10, 4),
    three_y_dividend_per_share_growth_per_share DECIMAL(10, 4),
    receivables_growth DECIMAL(10, 4),
    inventory_growth DECIMAL(10, 4),
    asset_growth DECIMAL(10, 4),
    book_value_per_share_growth DECIMAL(10, 4),
    debt_growth DECIMAL(10, 4),
    rd_expense_growth DECIMAL(10, 4),
    sga_expenses_growth DECIMAL(10, 4),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date_period (symbol, date, period),
    INDEX idx_symbol (symbol),
    INDEX idx_date (date),
    INDEX idx_calendar_year (calendar_year)
) ENGINE=InnoDB;

-- ============================================================================
-- NEWS AND MARKET DATA
-- ============================================================================

-- Stock news articles
CREATE TABLE stock_news (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20),
    published_date DATETIME,
    title TEXT,
    image VARCHAR(500),
    site VARCHAR(255),
    text LONGTEXT,
    url VARCHAR(500) UNIQUE,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE SET NULL,
    INDEX idx_symbol (symbol),
    INDEX idx_published_date (published_date),
    INDEX idx_cached_at (cached_at)
) ENGINE=InnoDB;

-- Market movers (gainers, losers, most active)
CREATE TABLE market_movers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    category VARCHAR(20) NOT NULL, -- 'gainers', 'losers', 'actives'
    name VARCHAR(255),
    `change` DECIMAL(20, 4),
    price DECIMAL(20, 4),
    changes_percentage VARCHAR(20),
    date DATE NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_category_date (symbol, category, date),
    INDEX idx_category_date (category, date),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB;

-- Sector performance
CREATE TABLE sector_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sector VARCHAR(255) NOT NULL,
    changes_percentage VARCHAR(20),
    date DATE NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_sector_date (sector, date),
    INDEX idx_date (date),
    INDEX idx_sector (sector)
) ENGINE=InnoDB;

-- ============================================================================
-- CALENDAR EVENTS
-- ============================================================================

-- Earnings calendar
CREATE TABLE earnings_calendar (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    eps DECIMAL(20, 4),
    eps_estimated DECIMAL(20, 4),
    time VARCHAR(20), -- 'bmo', 'amc', 'tbd'
    revenue BIGINT,
    revenue_estimated BIGINT,
    fiscal_date_ending DATE,
    updated_from_date DATE,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_date (date),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB;

-- Dividend calendar
CREATE TABLE dividend_calendar (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    label VARCHAR(50),
    adj_dividend DECIMAL(20, 4),
    dividend DECIMAL(20, 4),
    record_date DATE,
    payment_date DATE,
    declaration_date DATE,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date (symbol, date),
    INDEX idx_date (date),
    INDEX idx_payment_date (payment_date),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB;

-- ============================================================================
-- METADATA AND CACHING
-- ============================================================================

-- Cache metadata - Track cache status and expiration
CREATE TABLE cache_metadata (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cache_key VARCHAR(500) NOT NULL UNIQUE,
    endpoint VARCHAR(255) NOT NULL,
    symbol VARCHAR(20),
    params JSON,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    hit_count INT DEFAULT 0,
    last_hit_at TIMESTAMP,
    INDEX idx_cache_key (cache_key),
    INDEX idx_symbol (symbol),
    INDEX idx_endpoint (endpoint),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB;

-- API request log (for monitoring and rate limiting)
CREATE TABLE api_request_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    symbol VARCHAR(20),
    params JSON,
    response_status INT,
    response_time_ms INT,
    from_cache BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_endpoint (endpoint),
    INDEX idx_symbol (symbol),
    INDEX idx_created_at (created_at),
    INDEX idx_from_cache (from_cache)
) ENGINE=InnoDB;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Latest company data view
CREATE VIEW v_latest_company_data AS
SELECT 
    c.symbol,
    c.name,
    c.exchange,
    cp.price,
    cp.mkt_cap,
    cp.sector,
    cp.industry,
    cp.description,
    cp.website,
    cp.cached_at as profile_cached_at
FROM companies c
LEFT JOIN company_profiles cp ON c.symbol = cp.symbol;

-- Latest financial metrics view
CREATE VIEW v_latest_financial_metrics AS
SELECT 
    km.symbol,
    km.date,
    km.period,
    km.pe_ratio,
    km.pb_ratio,
    km.dividend_yield,
    km.roe,
    fr.return_on_assets,
    fr.debt_to_equity,
    fr.current_ratio,
    fr.quick_ratio
FROM key_metrics km
LEFT JOIN financial_ratios fr ON km.symbol = fr.symbol AND km.date = fr.date
WHERE km.id IN (
    SELECT MAX(id) 
    FROM key_metrics 
    GROUP BY symbol
);

-- Recent earnings view
CREATE VIEW v_recent_earnings AS
SELECT 
    ec.symbol,
    ec.date,
    ec.eps,
    ec.eps_estimated,
    ec.revenue,
    ec.revenue_estimated,
    (ec.eps - ec.eps_estimated) as eps_surprise,
    (ec.revenue - ec.revenue_estimated) as revenue_surprise
FROM earnings_calendar ec
WHERE ec.date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
ORDER BY ec.date DESC;
