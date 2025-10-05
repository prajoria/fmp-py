#!/usr/bin/env python3
"""
Data Access Layer (DAL) for FMP cache database
Provides high-level functions for CRUD operations on all tables
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .connection import get_db
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class CompanyDAL:
    """Data access layer for company-related tables"""
    
    def __init__(self):
        self.db = get_db()
        self.cache_manager = get_cache_manager()
    
    def upsert_company(self, symbol: str, name: str, **kwargs) -> bool:
        """
        Insert or update company
        
        Args:
            symbol (str): Stock symbol
            name (str): Company name
            **kwargs: Additional company fields
            
        Returns:
            bool: Success status
        """
        query = """
        INSERT INTO companies 
        (symbol, name, exchange, exchange_short_name, type, currency, 
         country, is_etf, is_actively_trading)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        exchange = VALUES(exchange),
        exchange_short_name = VALUES(exchange_short_name),
        type = VALUES(type),
        currency = VALUES(currency),
        country = VALUES(country),
        is_etf = VALUES(is_etf),
        is_actively_trading = VALUES(is_actively_trading),
        updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            self.db.execute_update(query, (
                symbol.upper(),
                name,
                kwargs.get('exchange'),
                kwargs.get('exchangeShortName'),
                kwargs.get('type'),
                kwargs.get('currency'),
                kwargs.get('country'),
                kwargs.get('isEtf', False),
                kwargs.get('isActivelyTrading', True)
            ))
            return True
        except Exception as e:
            logger.error(f"Error upserting company {symbol}: {e}")
            return False
    
    def get_company(self, symbol: str) -> Optional[Dict]:
        """Get company by symbol"""
        query = "SELECT * FROM companies WHERE symbol = %s"
        return self.db.execute_query(query, (symbol.upper(),), fetch='one')
    
    def get_all_companies(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all companies"""
        query = "SELECT * FROM companies ORDER BY symbol"
        if limit:
            query += f" LIMIT {limit}"
        return self.db.execute_query(query)
    
    def upsert_company_profile(self, symbol: str, profile_data: Dict, 
                              ttl_seconds: int = 86400) -> bool:
        """
        Insert or update company profile
        
        Args:
            symbol (str): Stock symbol
            profile_data (dict): Profile data from FMP API
            ttl_seconds (int): Time to live in seconds
            
        Returns:
            bool: Success status
        """
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        query = """
        INSERT INTO company_profiles
        (symbol, company_name, price, beta, vol_avg, mkt_cap, last_div, `range`,
         changes, cik, isin, cusip, industry, sector, website, description, ceo,
         full_time_employees, address, city, state, zip, country, phone, image,
         ipo_date, default_image, is_adr, dcf, dcf_diff, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        company_name = VALUES(company_name),
        price = VALUES(price),
        beta = VALUES(beta),
        vol_avg = VALUES(vol_avg),
        mkt_cap = VALUES(mkt_cap),
        last_div = VALUES(last_div),
        `range` = VALUES(`range`),
        changes = VALUES(changes),
        cik = VALUES(cik),
        isin = VALUES(isin),
        cusip = VALUES(cusip),
        industry = VALUES(industry),
        sector = VALUES(sector),
        website = VALUES(website),
        description = VALUES(description),
        ceo = VALUES(ceo),
        full_time_employees = VALUES(full_time_employees),
        address = VALUES(address),
        city = VALUES(city),
        state = VALUES(state),
        zip = VALUES(zip),
        country = VALUES(country),
        phone = VALUES(phone),
        image = VALUES(image),
        ipo_date = VALUES(ipo_date),
        default_image = VALUES(default_image),
        is_adr = VALUES(is_adr),
        dcf = VALUES(dcf),
        dcf_diff = VALUES(dcf_diff),
        cached_at = CURRENT_TIMESTAMP,
        expires_at = VALUES(expires_at)
        """
        
        try:
            self.db.execute_update(query, (
                symbol.upper(),
                profile_data.get('companyName'),
                profile_data.get('price'),
                profile_data.get('beta'),
                profile_data.get('volAvg'),
                profile_data.get('mktCap'),
                profile_data.get('lastDiv'),
                profile_data.get('range'),
                profile_data.get('changes'),
                profile_data.get('cik'),
                profile_data.get('isin'),
                profile_data.get('cusip'),
                profile_data.get('industry'),
                profile_data.get('sector'),
                profile_data.get('website'),
                profile_data.get('description'),
                profile_data.get('ceo'),
                profile_data.get('fullTimeEmployees'),
                profile_data.get('address'),
                profile_data.get('city'),
                profile_data.get('state'),
                profile_data.get('zip'),
                profile_data.get('country'),
                profile_data.get('phone'),
                profile_data.get('image'),
                profile_data.get('ipoDate'),
                profile_data.get('defaultImage', False),
                profile_data.get('isAdr', False),
                profile_data.get('dcf'),
                profile_data.get('dcfDiff'),
                expires_at
            ))
            return True
        except Exception as e:
            logger.error(f"Error upserting company profile {symbol}: {e}")
            return False
    
    def get_company_profile(self, symbol: str, 
                           check_expiry: bool = True) -> Optional[Dict]:
        """
        Get company profile
        
        Args:
            symbol (str): Stock symbol
            check_expiry (bool): Check if cache is expired
            
        Returns:
            dict: Company profile or None
        """
        query = """
        SELECT * FROM company_profiles 
        WHERE symbol = %s
        """
        
        if check_expiry:
            query += " AND expires_at > NOW()"
        
        return self.db.execute_query(query, (symbol.upper(),), fetch='one')


class QuoteDAL:
    """Data access layer for quote data"""
    
    def __init__(self):
        self.db = get_db()
    
    def upsert_quote(self, symbol: str, quote_data: Dict, 
                    ttl_seconds: int = 300) -> bool:
        """
        Insert or update quote
        
        Args:
            symbol (str): Stock symbol
            quote_data (dict): Quote data from FMP API
            ttl_seconds (int): Time to live in seconds
            
        Returns:
            bool: Success status
        """
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        query = """
        INSERT INTO quotes
        (symbol, price, changes_percentage, `change`, day_low, day_high,
         year_high, year_low, market_cap, price_avg_50, price_avg_200,
         volume, avg_volume, `open`, previous_close, eps, pe,
         earnings_announcement, shares_outstanding, timestamp_unix, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s)
        """
        
        try:
            self.db.execute_update(query, (
                symbol.upper(),
                quote_data.get('price'),
                quote_data.get('changesPercentage'),
                quote_data.get('change'),
                quote_data.get('dayLow'),
                quote_data.get('dayHigh'),
                quote_data.get('yearHigh'),
                quote_data.get('yearLow'),
                quote_data.get('marketCap'),
                quote_data.get('priceAvg50'),
                quote_data.get('priceAvg200'),
                quote_data.get('volume'),
                quote_data.get('avgVolume'),
                quote_data.get('open'),
                quote_data.get('previousClose'),
                quote_data.get('eps'),
                quote_data.get('pe'),
                quote_data.get('earningsAnnouncement'),
                quote_data.get('sharesOutstanding'),
                quote_data.get('timestamp'),
                expires_at
            ))
            return True
        except Exception as e:
            logger.error(f"Error upserting quote {symbol}: {e}")
            return False
    
    def get_quote(self, symbol: str, check_expiry: bool = True) -> Optional[Dict]:
        """
        Get latest quote for symbol
        
        Args:
            symbol (str): Stock symbol
            check_expiry (bool): Check if cache is expired
            
        Returns:
            dict: Quote data or None
        """
        query = """
        SELECT * FROM quotes
        WHERE symbol = %s
        """
        
        if check_expiry:
            query += " AND expires_at > NOW()"
        
        query += " ORDER BY cached_at DESC LIMIT 1"
        
        return self.db.execute_query(query, (symbol.upper(),), fetch='one')
    
    def get_quotes(self, symbols: List[str], 
                  check_expiry: bool = True) -> List[Dict]:
        """Get quotes for multiple symbols"""
        if not symbols:
            return []
        
        placeholders = ','.join(['%s'] * len(symbols))
        query = f"""
        SELECT * FROM quotes
        WHERE symbol IN ({placeholders})
        """
        
        if check_expiry:
            query += " AND expires_at > NOW()"
        
        query += " ORDER BY symbol, cached_at DESC"
        
        symbols_upper = [s.upper() for s in symbols]
        return self.db.execute_query(query, tuple(symbols_upper))


class HistoricalPriceDAL:
    """Data access layer for historical price data"""
    
    def __init__(self):
        self.db = get_db()
    
    def upsert_daily_prices(self, symbol: str, 
                           prices_data: List[Dict]) -> int:
        """
        Insert or update daily historical prices
        
        Args:
            symbol (str): Stock symbol
            prices_data (list): List of price dictionaries
            
        Returns:
            int: Number of records inserted/updated
        """
        if not prices_data:
            return 0
        
        query = """
        INSERT INTO historical_prices_daily
        (symbol, date, `open`, high, low, `close`, adj_close, volume,
         unadjusted_volume, `change`, change_percent, vwap, label, change_over_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `open` = VALUES(`open`),
        high = VALUES(high),
        low = VALUES(low),
        `close` = VALUES(`close`),
        adj_close = VALUES(adj_close),
        volume = VALUES(volume),
        unadjusted_volume = VALUES(unadjusted_volume),
        `change` = VALUES(`change`),
        change_percent = VALUES(change_percent),
        vwap = VALUES(vwap),
        label = VALUES(label),
        change_over_time = VALUES(change_over_time),
        cached_at = CURRENT_TIMESTAMP
        """
        
        try:
            params_list = [
                (
                    symbol.upper(),
                    price.get('date'),
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('adjClose'),
                    price.get('volume'),
                    price.get('unadjustedVolume'),
                    price.get('change'),
                    price.get('changePercent'),
                    price.get('vwap'),
                    price.get('label'),
                    price.get('changeOverTime')
                )
                for price in prices_data
            ]
            
            return self.db.execute_many(query, params_list)
        except Exception as e:
            logger.error(f"Error upserting daily prices for {symbol}: {e}")
            return 0
    
    def get_daily_prices(self, symbol: str, from_date: Optional[str] = None,
                        to_date: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[Dict]:
        """
        Get daily historical prices
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            limit (int, optional): Maximum number of records
            
        Returns:
            list: Historical price data
        """
        query = """
        SELECT * FROM historical_prices_daily
        WHERE symbol = %s
        """
        params = [symbol.upper()]
        
        if from_date:
            query += " AND date >= %s"
            params.append(from_date)
        
        if to_date:
            query += " AND date <= %s"
            params.append(to_date)
        
        query += " ORDER BY date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.db.execute_query(query, tuple(params))
    
    def upsert_intraday_prices(self, symbol: str, period: str,
                              prices_data: List[Dict]) -> int:
        """
        Insert or update intraday historical prices
        
        Args:
            symbol (str): Stock symbol
            period (str): Time period (e.g., '5min', '1hour')
            prices_data (list): List of price dictionaries
            
        Returns:
            int: Number of records inserted/updated
        """
        if not prices_data:
            return 0
        
        query = """
        INSERT INTO historical_prices_intraday
        (symbol, datetime, period, `open`, high, low, `close`, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `open` = VALUES(`open`),
        high = VALUES(high),
        low = VALUES(low),
        `close` = VALUES(`close`),
        volume = VALUES(volume),
        cached_at = CURRENT_TIMESTAMP
        """
        
        try:
            params_list = [
                (
                    symbol.upper(),
                    price.get('date'),
                    period,
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('volume')
                )
                for price in prices_data
            ]
            
            return self.db.execute_many(query, params_list)
        except Exception as e:
            logger.error(f"Error upserting intraday prices for {symbol}: {e}")
            return 0
    
    def get_intraday_prices(self, symbol: str, period: str,
                           from_datetime: Optional[str] = None,
                           to_datetime: Optional[str] = None,
                           limit: Optional[int] = None) -> List[Dict]:
        """Get intraday historical prices"""
        query = """
        SELECT * FROM historical_prices_intraday
        WHERE symbol = %s AND period = %s
        """
        params = [symbol.upper(), period]
        
        if from_datetime:
            query += " AND datetime >= %s"
            params.append(from_datetime)
        
        if to_datetime:
            query += " AND datetime <= %s"
            params.append(to_datetime)
        
        query += " ORDER BY datetime DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.db.execute_query(query, tuple(params))


# Create global instances
company_dal = CompanyDAL()
quote_dal = QuoteDAL()
historical_price_dal = HistoricalPriceDAL()
