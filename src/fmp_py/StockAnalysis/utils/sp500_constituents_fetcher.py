#!/usr/bin/env python3
"""
S&P 500 Constituents Fetcher
============================
Fetches the current list of S&P 500 constituent stocks from Wikipedia
and provides them for use in the historical chart fetcher.
"""

import os
import sys
import pandas as pd
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from io import StringIO

# Add database imports
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from StockAnalysis.database.connection import get_db
    from StockAnalysis.database.sp500_constituents_dal import SP500ConstituentsDal
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SP500ConstituentsFetcher:
    """
    Fetches S&P 500 constituent stocks from Wikipedia
    """
    
    def __init__(self, data_dir: Optional[str] = None, use_database: bool = True):
        """
        Initialize the fetcher
        
        Args:
            data_dir: Directory to store CSV files (default: data/ in project root)
            use_database: Whether to use database storage (default: True)
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to data directory in project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            self.data_dir = project_root / "data"
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        self.wikipedia_url = (
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies#S&P_500_component_stocks"
        )
        
        # Database setup
        self.use_database = use_database and DB_AVAILABLE
        self.db = None
        self.dal = None
        
        if self.use_database:
            try:
                self.db = get_db()
                self.dal = SP500ConstituentsDal(self.db)
                logger.info("Database connection established for S&P 500 data")
            except Exception as e:
                logger.warning(f"Database connection failed: {e}. Using CSV-only mode.")
                self.use_database = False
        
        logger.info(f"Initialized SP500ConstituentsFetcher with data directory: {self.data_dir}")
        logger.info(f"Database mode: {'enabled' if self.use_database else 'disabled'}")
    
    def fetch_constituents(self) -> pd.DataFrame:
        """
        Fetch S&P 500 constituents from Wikipedia
        
        Returns:
            DataFrame with S&P 500 constituent information
        """
        logger.info("Fetching S&P 500 constituents from Wikipedia...")
        
        try:
            # Set headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # First get the HTML content with proper headers
            response = requests.get(self.wikipedia_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML content with pandas
            tables = pd.read_html(StringIO(response.text), header=0)
            
            # Usually the first table is the constituents
            df = tables[0]
            
            logger.info(f"Successfully fetched {len(df)} S&P 500 constituents")
            
            # Clean up column names and data
            df = self._clean_dataframe(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching S&P 500 constituents: {e}")
            raise
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the DataFrame
        
        Args:
            df: Raw DataFrame from Wikipedia
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Cleaning S&P 500 constituents data...")
        
        # Standardize column names (Wikipedia table structure can vary)
        expected_columns = ['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry', 
                          'Headquarters Location', 'Date added', 'CIK', 'Founded']
        
        # Map actual columns to expected columns
        if len(df.columns) >= 4:
            # Most common column mapping
            column_mapping = {
                df.columns[0]: 'Symbol',
                df.columns[1]: 'Security', 
                df.columns[2]: 'GICS Sector',
                df.columns[3]: 'GICS Sub-Industry'
            }
            
            # Add other columns if they exist
            if len(df.columns) > 4:
                column_mapping[df.columns[4]] = 'Headquarters Location'
            if len(df.columns) > 5:
                column_mapping[df.columns[5]] = 'Date added'
            if len(df.columns) > 6:
                column_mapping[df.columns[6]] = 'CIK'
            if len(df.columns) > 7:
                column_mapping[df.columns[7]] = 'Founded'
            
            df = df.rename(columns=column_mapping)
        
        # Clean symbol column - remove any extra characters
        if 'Symbol' in df.columns:
            df['Symbol'] = df['Symbol'].astype(str).str.strip().str.upper()
            # Remove any symbols that are empty or invalid
            df = df[df['Symbol'].str.len() > 0]
            df = df[~df['Symbol'].str.contains('nan', case=False, na=False)]
        
        # Clean security (company name) column
        if 'Security' in df.columns:
            df['Security'] = df['Security'].astype(str).str.strip()
        
        # Clean sector information
        if 'GICS Sector' in df.columns:
            df['GICS Sector'] = df['GICS Sector'].astype(str).str.strip()
        
        # Add fetch timestamp
        df['Fetched_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Sort by symbol
        df = df.sort_values('Symbol').reset_index(drop=True)
        
        logger.info(f"Cleaned data: {len(df)} valid constituents")
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = "sp500_constituents.csv") -> str:
        """
        Save DataFrame to CSV file
        
        Args:
            df: DataFrame to save
            filename: CSV filename
            
        Returns:
            Path to saved file
        """
        csv_path = self.data_dir / filename
        
        try:
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved S&P 500 constituents to: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")
            raise
    
    def save_to_database(self, df: pd.DataFrame) -> int:
        """
        Save DataFrame to database
        
        Args:
            df: DataFrame to save
            
        Returns:
            Number of records successfully saved
        """
        if not self.use_database:
            logger.warning("Database not available for saving")
            return 0
        
        try:
            logger.info(f"Saving {len(df)} S&P 500 constituents to database...")
            count = self.dal.bulk_insert_from_dataframe(df)
            logger.info(f"Successfully saved {count} records to database")
            return count
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return 0
    
    def load_from_database(self) -> Optional[pd.DataFrame]:
        """
        Load S&P 500 constituents from database
        
        Returns:
            DataFrame with database data or None
        """
        if not self.use_database:
            logger.warning("Database not available for loading")
            return None
        
        try:
            constituents = self.dal.get_all_active_constituents()
            if constituents:
                df = pd.DataFrame(constituents)
                # Rename columns to match CSV format
                column_mapping = {
                    'symbol': 'Symbol',
                    'security': 'Security', 
                    'gics_sector': 'GICS Sector',
                    'gics_sub_industry': 'GICS Sub-Industry',
                    'headquarters_location': 'Headquarters Location',
                    'date_added': 'Date added',
                    'cik': 'CIK',
                    'founded': 'Founded'
                }
                df = df.rename(columns=column_mapping)
                logger.info(f"Loaded {len(df)} S&P 500 constituents from database")
                return df
            else:
                logger.info("No S&P 500 constituents found in database")
                return None
                
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            return None
    
    def get_symbols_list(self, df: Optional[pd.DataFrame] = None, from_database: bool = False) -> List[str]:
        """
        Get list of symbols from DataFrame or database
        
        Args:
            df: DataFrame (will fetch if not provided)
            from_database: Whether to fetch from database instead of DataFrame
            
        Returns:
            List of stock symbols
        """
        if from_database and self.use_database:
            try:
                symbols = self.dal.get_active_symbols()
                logger.info(f"Retrieved {len(symbols)} symbols from database")
                return symbols
            except Exception as e:
                logger.error(f"Error getting symbols from database: {e}")
                # Fall back to DataFrame approach
        
        if df is None:
            df = self.fetch_constituents()
        
        if 'Symbol' in df.columns:
            symbols = df['Symbol'].tolist()
            logger.info(f"Extracted {len(symbols)} symbols from S&P 500 data")
            return symbols
        else:
            logger.warning("No 'Symbol' column found in DataFrame")
            return []
    
    def get_symbols_by_sector(self, sector: str, df: Optional[pd.DataFrame] = None, from_database: bool = False) -> List[str]:
        """
        Get symbols filtered by GICS sector
        
        Args:
            sector: GICS sector name
            df: DataFrame (will fetch if not provided)
            from_database: Whether to fetch from database instead of DataFrame
            
        Returns:
            List of symbols in the specified sector
        """
        if from_database and self.use_database:
            try:
                symbols = self.dal.get_symbols_by_sector(sector)
                logger.info(f"Found {len(symbols)} symbols in sector '{sector}' from database")
                return symbols
            except Exception as e:
                logger.error(f"Error getting symbols by sector from database: {e}")
                # Fall back to DataFrame approach
        
        if df is None:
            df = self.fetch_constituents()
        
        if 'GICS Sector' in df.columns and 'Symbol' in df.columns:
            sector_df = df[df['GICS Sector'].str.contains(sector, case=False, na=False)]
            symbols = sector_df['Symbol'].tolist()
            logger.info(f"Found {len(symbols)} symbols in sector '{sector}'")
            return symbols
        else:
            logger.warning("Required columns not found for sector filtering")
            return []
    
    def print_sector_summary(self, df: Optional[pd.DataFrame] = None):
        """
        Print summary of constituents by sector
        
        Args:
            df: DataFrame (will fetch if not provided)
        """
        if df is None:
            df = self.fetch_constituents()
        
        if 'GICS Sector' in df.columns:
            sector_counts = df['GICS Sector'].value_counts()
            
            print(f"\n{'='*60}")
            print("S&P 500 CONSTITUENTS BY SECTOR")
            print(f"{'='*60}")
            print(f"{'Sector':<35} {'Count':<8} {'%':<6}")
            print("-" * 60)
            
            total = len(df)
            for sector, count in sector_counts.items():
                percentage = (count / total) * 100
                print(f"{sector:<35} {count:<8} {percentage:<6.1f}")
            
            print("-" * 60)
            print(f"{'TOTAL':<35} {total:<8} {'100.0':<6}")
            print(f"{'='*60}")
        else:
            logger.warning("No sector information available")
    
    def fetch_and_save(self, filename: str = "sp500_constituents.csv", save_to_db: bool = True) -> tuple[pd.DataFrame, str, int]:
        """
        Convenience method to fetch constituents and save to CSV and/or database
        
        Args:
            filename: CSV filename
            save_to_db: Whether to save to database
            
        Returns:
            Tuple of (DataFrame, csv_path, db_records_saved)
        """
        df = self.fetch_constituents()
        csv_path = self.save_to_csv(df, filename)
        
        db_records = 0
        if save_to_db and self.use_database:
            db_records = self.save_to_database(df)
        
        return df, csv_path, db_records
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for S&P 500 data
        
        Returns:
            Dictionary with database statistics
        """
        if not self.use_database:
            return {"database_available": False}
        
        try:
            stats = self.dal.get_table_stats()
            stats["database_available"] = True
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"database_available": False, "error": str(e)}


def main():
    """Command line interface for S&P 500 constituents fetcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch S&P 500 constituents from Wikipedia")
    parser.add_argument('--output', '-o', type=str, default="sp500_constituents.csv",
                       help='Output CSV filename (default: sp500_constituents.csv)')
    parser.add_argument('--data-dir', type=str, help='Data directory path')
    parser.add_argument('--no-database', action='store_true', help='Disable database storage')
    parser.add_argument('--database-only', action='store_true', help='Use database data only (no web fetch)')
    parser.add_argument('--symbols-only', action='store_true', 
                       help='Print symbols list only (no CSV)')
    parser.add_argument('--sector-summary', action='store_true',
                       help='Show sector summary')
    parser.add_argument('--sector', type=str, help='Filter by specific sector')
    parser.add_argument('--database-stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    try:
        # Initialize fetcher
        fetcher = SP500ConstituentsFetcher(
            data_dir=args.data_dir, 
            use_database=not args.no_database
        )
        
        # Handle database stats
        if args.database_stats:
            stats = fetcher.get_database_stats()
            print(f"\n{'='*60}")
            print("S&P 500 DATABASE STATISTICS")
            print(f"{'='*60}")
            
            if stats.get('database_available'):
                print(f"Total Records: {stats.get('total_records', 'N/A')}")
                print(f"Active Records: {stats.get('active_records', 'N/A')}")
                print(f"Unique Sectors: {stats.get('unique_sectors', 'N/A')}")
                print(f"Last Updated: {stats.get('last_updated', 'N/A')}")
            else:
                print("Database not available")
                if 'error' in stats:
                    print(f"Error: {stats['error']}")
            
            print(f"{'='*60}")
            return 0
        
        # Determine data source
        if args.database_only:
            df = fetcher.load_from_database()
            if df is None:
                print("❌ No data found in database")
                return 1
        else:
            # Fetch from web
            df = fetcher.fetch_constituents()
        
        # Handle different output options
        if args.symbols_only:
            symbols = fetcher.get_symbols_list(df, from_database=args.database_only)
            print(f"S&P 500 Symbols ({len(symbols)}):")
            for symbol in symbols:
                print(symbol)
        
        elif args.sector:
            symbols = fetcher.get_symbols_by_sector(args.sector, df, from_database=args.database_only)
            print(f"S&P 500 Symbols in '{args.sector}' sector ({len(symbols)}):")
            for symbol in symbols:
                print(symbol)
        
        elif args.sector_summary:
            fetcher.print_sector_summary(df)
        
        else:
            # Default: save to CSV and optionally database
            if args.database_only:
                print(f"✅ Loaded {len(df)} S&P 500 constituents from database")
                # Save to CSV
                csv_path = fetcher.save_to_csv(df, args.output)
                print(f"📄 Saved to CSV: {csv_path}")
            else:
                # Fetch and save
                df, csv_path, db_records = fetcher.fetch_and_save(
                    args.output, 
                    save_to_db=not args.no_database
                )
                
                print(f"✅ Successfully fetched {len(df)} S&P 500 constituents")
                print(f"📄 Saved to CSV: {csv_path}")
                
                if not args.no_database and db_records > 0:
                    print(f"💾 Saved {db_records} records to database")
                elif not args.no_database:
                    print("⚠️  Database save failed or unavailable")
            
            symbols = fetcher.get_symbols_list(df)
            print(f"📊 {len(symbols)} symbols available")
            
            # Show sector summary
            fetcher.print_sector_summary(df)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())