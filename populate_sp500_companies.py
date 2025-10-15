#!/usr/bin/env python3
"""
Quick script to populate companies table with S&P 500 constituents
"""

import mysql.connector
import requests
import pandas as pd
from io import StringIO

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='fmp_user',
        password='fmp_password',
        database='fmp_cache'
    )

def fetch_sp500_from_wikipedia():
    """Fetch S&P 500 list from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    try:
        # Read the first table from the Wikipedia page
        tables = pd.read_html(url)
        sp500_table = tables[0]
        
        # Get the symbols from the first column (usually 'Symbol' or 'Ticker symbol')
        symbols = sp500_table.iloc[:, 0].tolist()
        # Clean up symbols (remove any extra whitespace)
        symbols = [str(symbol).strip() for symbol in symbols if pd.notna(symbol)]
        
        print(f"Fetched {len(symbols)} S&P 500 symbols from Wikipedia")
        return symbols
    except Exception as e:
        print(f"Error fetching from Wikipedia: {e}")
        return []

def insert_companies(symbols):
    """Insert companies into the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Prepare the INSERT statement with ON DUPLICATE KEY UPDATE
        insert_query = """
        INSERT INTO companies (symbol, name, exchange, type, currency, country, is_actively_trading)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        name = COALESCE(VALUES(name), name),
        exchange = COALESCE(VALUES(exchange), exchange),
        updated_at = NOW()
        """
        
        # Insert each symbol
        for symbol in symbols:
            try:
                cursor.execute(insert_query, (
                    symbol,
                    f"{symbol} Inc.",  # Default company name
                    "NASDAQ",         # Default exchange
                    "stock",          # Type
                    "USD",            # Currency
                    "US",             # Country
                    True              # Is actively trading
                ))
            except Exception as e:
                print(f"Error inserting {symbol}: {e}")
                continue
        
        conn.commit()
        print(f"Successfully inserted/updated {len(symbols)} companies")
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Fetching S&P 500 companies...")
    symbols = fetch_sp500_from_wikipedia()
    
    if symbols:
        print("Inserting companies into database...")
        insert_companies(symbols)
        print("Done!")
    else:
        print("No symbols fetched, exiting.")