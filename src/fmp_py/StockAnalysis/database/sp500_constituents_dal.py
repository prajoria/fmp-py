#!/usr/bin/env python3
"""
S&P 500 Constituents Data Access Layer (DAL)
============================================
Database operations for S&P 500 constituent stocks data.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import pandas as pd

logger = logging.getLogger(__name__)


class SP500ConstituentsDal:
    """Data Access Layer for S&P 500 constituents database operations"""
    
    def __init__(self, db_connection):
        """
        Initialize the DAL with database connection
        
        Args:
            db_connection: Database connection object with execute_query method
        """
        self.db = db_connection
        
    def insert_or_update_constituent(
        self, 
        symbol: str,
        security: str,
        gics_sector: Optional[str] = None,
        gics_sub_industry: Optional[str] = None,
        headquarters_location: Optional[str] = None,
        date_added: Optional[date] = None,
        cik: Optional[str] = None,
        founded: Optional[str] = None,
        is_active: bool = True
    ) -> bool:
        """
        Insert or update a single S&P 500 constituent
        
        Args:
            symbol: Stock symbol
            security: Company name
            gics_sector: GICS sector classification
            gics_sub_industry: GICS sub-industry classification
            headquarters_location: Company headquarters location
            date_added: Date added to S&P 500
            cik: SEC CIK number
            founded: Year company was founded
            is_active: Whether the stock is currently active in S&P 500
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO sp500_constituents (
                    symbol, security, gics_sector, gics_sub_industry,
                    headquarters_location, date_added, cik, founded, is_active
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    security = VALUES(security),
                    gics_sector = VALUES(gics_sector),
                    gics_sub_industry = VALUES(gics_sub_industry),
                    headquarters_location = VALUES(headquarters_location),
                    date_added = VALUES(date_added),
                    cik = VALUES(cik),
                    founded = VALUES(founded),
                    is_active = VALUES(is_active),
                    updated_at = CURRENT_TIMESTAMP
            """
            
            params = (
                symbol, security, gics_sector, gics_sub_industry,
                headquarters_location, date_added, cik, founded, is_active
            )
            
            self.db.execute_query(query, params)
            logger.debug(f"Inserted/updated constituent: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting/updating constituent {symbol}: {e}")
            return False
    
    def bulk_insert_constituents(self, constituents_data: List[Dict[str, Any]]) -> int:
        """
        Bulk insert/update S&P 500 constituents
        
        Args:
            constituents_data: List of dictionaries with constituent data
            
        Returns:
            Number of successfully processed records
        """
        successful_count = 0
        
        try:
            # First, mark all existing records as inactive
            self.mark_all_inactive()
            
            # Then insert/update all new records
            for constituent in constituents_data:
                success = self.insert_or_update_constituent(
                    symbol=str(constituent.get('Symbol', '')).strip().upper(),
                    security=str(constituent.get('Security', '')).strip(),
                    gics_sector=str(constituent.get('GICS Sector', '')).strip() or None,
                    gics_sub_industry=str(constituent.get('GICS Sub-Industry', '')).strip() or None,
                    headquarters_location=str(constituent.get('Headquarters Location', '')).strip() or None,
                    date_added=self._parse_date(constituent.get('Date added')),
                    cik=str(constituent.get('CIK', '')).strip() or None,
                    founded=str(constituent.get('Founded', '')).strip() or None,
                    is_active=True
                )
                
                if success:
                    successful_count += 1
            
            logger.info(f"Successfully processed {successful_count}/{len(constituents_data)} constituents")
            return successful_count
            
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            return successful_count
    
    def bulk_insert_from_dataframe(self, df: pd.DataFrame) -> int:
        """
        Bulk insert from pandas DataFrame
        
        Args:
            df: DataFrame with S&P 500 constituent data
            
        Returns:
            Number of successfully processed records
        """
        try:
            # Convert DataFrame to list of dictionaries
            constituents_data = df.to_dict('records')
            return self.bulk_insert_constituents(constituents_data)
            
        except Exception as e:
            logger.error(f"Error converting DataFrame for bulk insert: {e}")
            return 0
    
    def get_all_active_constituents(self) -> List[Dict[str, Any]]:
        """
        Get all active S&P 500 constituents
        
        Returns:
            List of constituent records
        """
        try:
            query = """
                SELECT symbol, security, gics_sector, gics_sub_industry,
                       headquarters_location, date_added, cik, founded,
                       fetched_at, updated_at
                FROM sp500_constituents 
                WHERE is_active = TRUE
                ORDER BY symbol
            """
            
            result = self.db.execute_query(query)
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error fetching active constituents: {e}")
            return []
    
    def get_active_symbols(self) -> List[str]:
        """
        Get list of active S&P 500 symbols
        
        Returns:
            List of stock symbols
        """
        try:
            query = """
                SELECT symbol 
                FROM sp500_constituents 
                WHERE is_active = TRUE
                ORDER BY symbol
            """
            
            result = self.db.execute_query(query)
            return [row['symbol'] for row in result] if result else []
            
        except Exception as e:
            logger.error(f"Error fetching active symbols: {e}")
            return []
    
    def get_constituents_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        """
        Get constituents filtered by GICS sector
        
        Args:
            sector: GICS sector name
            
        Returns:
            List of constituent records in the sector
        """
        try:
            query = """
                SELECT symbol, security, gics_sector, gics_sub_industry,
                       headquarters_location, date_added, cik, founded
                FROM sp500_constituents 
                WHERE is_active = TRUE AND gics_sector LIKE %s
                ORDER BY symbol
            """
            
            result = self.db.execute_query(query, (f"%{sector}%",))
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error fetching constituents by sector {sector}: {e}")
            return []
    
    def get_symbols_by_sector(self, sector: str) -> List[str]:
        """
        Get symbols filtered by GICS sector
        
        Args:
            sector: GICS sector name
            
        Returns:
            List of symbols in the sector
        """
        constituents = self.get_constituents_by_sector(sector)
        return [c['symbol'] for c in constituents]
    
    def get_sector_statistics(self) -> List[Dict[str, Any]]:
        """
        Get statistics by sector
        
        Returns:
            List of sector statistics
        """
        try:
            query = """
                SELECT 
                    gics_sector,
                    COUNT(*) as count,
                    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sp500_constituents WHERE is_active = TRUE) as percentage
                FROM sp500_constituents 
                WHERE is_active = TRUE AND gics_sector IS NOT NULL
                GROUP BY gics_sector
                ORDER BY count DESC
            """
            
            result = self.db.execute_query(query)
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error fetching sector statistics: {e}")
            return []
    
    def mark_all_inactive(self) -> bool:
        """
        Mark all constituents as inactive (used before bulk refresh)
        
        Returns:
            True if successful
        """
        try:
            query = "UPDATE sp500_constituents SET is_active = FALSE"
            self.db.execute_query(query)
            logger.info("Marked all constituents as inactive")
            return True
            
        except Exception as e:
            logger.error(f"Error marking constituents inactive: {e}")
            return False
    
    def delete_constituent(self, symbol: str) -> bool:
        """
        Delete a constituent (hard delete)
        
        Args:
            symbol: Stock symbol to delete
            
        Returns:
            True if successful
        """
        try:
            query = "DELETE FROM sp500_constituents WHERE symbol = %s"
            self.db.execute_query(query, (symbol,))
            logger.info(f"Deleted constituent: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting constituent {symbol}: {e}")
            return False
    
    def get_constituent_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific constituent by symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Constituent record or None
        """
        try:
            query = """
                SELECT symbol, security, gics_sector, gics_sub_industry,
                       headquarters_location, date_added, cik, founded,
                       fetched_at, updated_at, is_active
                FROM sp500_constituents 
                WHERE symbol = %s
            """
            
            result = self.db.execute_query(query, (symbol.upper(),))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error fetching constituent {symbol}: {e}")
            return None
    
    def get_recently_added(self, days: int = 365) -> List[Dict[str, Any]]:
        """
        Get recently added constituents
        
        Args:
            days: Number of days back to look
            
        Returns:
            List of recently added constituents
        """
        try:
            query = """
                SELECT symbol, security, date_added, gics_sector
                FROM sp500_constituents 
                WHERE is_active = TRUE 
                  AND date_added >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY date_added DESC
            """
            
            result = self.db.execute_query(query, (days,))
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error fetching recently added constituents: {e}")
            return []
    
    def get_table_stats(self) -> Dict[str, Any]:
        """
        Get table statistics
        
        Returns:
            Dictionary with table statistics
        """
        try:
            stats = {}
            
            # Total count
            result = self.db.execute_query("SELECT COUNT(*) as total FROM sp500_constituents")
            stats['total_records'] = result[0]['total'] if result else 0
            
            # Active count
            result = self.db.execute_query("SELECT COUNT(*) as active FROM sp500_constituents WHERE is_active = TRUE")
            stats['active_records'] = result[0]['active'] if result else 0
            
            # Last updated
            result = self.db.execute_query("SELECT MAX(updated_at) as last_updated FROM sp500_constituents")
            stats['last_updated'] = result[0]['last_updated'] if result and result[0]['last_updated'] else None
            
            # Sector count
            result = self.db.execute_query("SELECT COUNT(DISTINCT gics_sector) as sectors FROM sp500_constituents WHERE is_active = TRUE")
            stats['unique_sectors'] = result[0]['sectors'] if result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching table statistics: {e}")
            return {}
    
    def _parse_date(self, date_str: Any) -> Optional[date]:
        """
        Parse date string to date object
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Date object or None
        """
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            if isinstance(date_str, date):
                return date_str
            elif isinstance(date_str, datetime):
                return date_str.date()
            elif isinstance(date_str, str):
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y']:
                    try:
                        return datetime.strptime(date_str.strip(), fmt).date()
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return None