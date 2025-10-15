#!/usr/bin/env python3
"""
Database connection module for FMP cache
Manages MySQL database connections and provides connection pooling
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling, Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration from environment variables"""
    
    def __init__(self):
        self.host = os.getenv('FMP_DB_HOST', 'localhost')
        self.port = int(os.getenv('FMP_DB_PORT', '3306'))
        self.database = os.getenv('FMP_DB_NAME', 'fmp_cache')
        self.user = os.getenv('FMP_DB_USER', 'fmp_user')
        self.password = os.getenv('FMP_DB_PASSWORD', 'fmp_password')
        self.pool_name = os.getenv('FMP_DB_POOL_NAME', 'fmp_pool')
        self.pool_size = int(os.getenv('FMP_DB_POOL_SIZE', '32'))  # MySQL connector max is 32
        self.pool_reset_session = True
        self.autocommit = False
        self.charset = 'utf8mb4'
        self.collation = 'utf8mb4_unicode_ci'
        self.use_unicode = True
        # Additional connection pool settings
        self.connect_timeout = int(os.getenv('FMP_DB_CONNECT_TIMEOUT', '60'))
        self.read_timeout = int(os.getenv('FMP_DB_READ_TIMEOUT', '60'))
        self.write_timeout = int(os.getenv('FMP_DB_WRITE_TIMEOUT', '60'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for mysql.connector"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'charset': self.charset,
            'collation': self.collation,
            'use_unicode': self.use_unicode,
            'autocommit': self.autocommit,
            'connect_timeout': self.connect_timeout,
            'read_timeout': self.read_timeout,
            'write_timeout': self.write_timeout
        }


class DatabaseConnection:
    """
    Database connection manager with connection pooling
    
    Usage:
        db = DatabaseConnection()
        
        # Using context manager
        with db.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM companies LIMIT 10")
                results = cursor.fetchall()
        
        # Direct usage
        conn = db.connection_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
    """
    
    _instance = None
    _connection_pool = None
    
    def __new__(cls):
        """Singleton pattern to ensure single connection pool"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database connection pool"""
        if self._connection_pool is None:
            self.config = DatabaseConfig()
            self._create_connection_pool()
    
    def _create_connection_pool(self):
        """Create MySQL connection pool"""
        try:
            pool_config = self.config.to_dict()
            pool_config['pool_name'] = self.config.pool_name
            pool_config['pool_size'] = self.config.pool_size
            pool_config['pool_reset_session'] = self.config.pool_reset_session
            
            self._connection_pool = pooling.MySQLConnectionPool(**pool_config)
            
            logger.info(
                f"Database connection pool created: "
                f"{self.config.user}@{self.config.host}:{self.config.port}/{self.config.database} "
                f"(pool_size={self.config.pool_size})"
            )
            
            # Test connection
            self.test_connection()
            
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    
    @property
    def connection_pool(self) -> pooling.MySQLConnectionPool:
        """Get the connection pool"""
        if self._connection_pool is None:
            self._create_connection_pool()
        return self._connection_pool
    
    @contextmanager
    def get_connection(self, max_retries=3, retry_delay=1):
        """
        Context manager for database connections with retry logic
        
        Args:
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
            
        Yields:
            mysql.connector.connection.MySQLConnection: Database connection
        """
        import time
        
        connection = None
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                connection = self.connection_pool.get_connection()
                yield connection
                connection.commit()
                return
            except Error as e:
                last_error = e
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass
                
                # If it's a pool exhaustion error and we have retries left, wait and retry
                if "pool exhausted" in str(e).lower() and attempt < max_retries:
                    logger.warning(f"Connection pool exhausted, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"Database error: {e}")
                    raise
            finally:
                if connection and connection.is_connected():
                    connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=True, buffered=False):
        """
        Context manager for database cursor
        
        Args:
            dictionary (bool): Return rows as dictionaries
            buffered (bool): Use buffered cursor
            
        Yields:
            mysql.connector.cursor: Database cursor
        """
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary, buffered=buffered)
            try:
                yield cursor
                connection.commit()
            except Error as e:
                connection.rollback()
                logger.error(f"Cursor error: {e}")
                raise
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result:
                        logger.info("Database connection test successful")
                        return True
            return False
        except Error as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                     fetch: str = 'all') -> Optional[Any]:
        """
        Execute a SELECT query
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            fetch (str): Fetch method - 'all', 'one', or 'many'
            
        Returns:
            Query results
        """
        try:
            with self.get_cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                
                if fetch == 'all':
                    return cursor.fetchall()
                elif fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'many':
                    return cursor.fetchmany()
                else:
                    return cursor.fetchall()
                    
        except Error as e:
            logger.error(f"Query execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            
        Returns:
            int: Number of affected rows
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.rowcount
                
        except Error as e:
            logger.error(f"Update execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_many(self, query: str, params_list: list) -> int:
        """
        Execute multiple queries with different parameters
        
        Args:
            query (str): SQL query
            params_list (list): List of parameter tuples
            
        Returns:
            int: Number of affected rows
        """
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(query, params_list)
                return cursor.rowcount
                
        except Error as e:
            logger.error(f"Batch execution error: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def get_last_insert_id(self) -> Optional[int]:
        """
        Get the last inserted ID
        
        Returns:
            int: Last insert ID
        """
        try:
            result = self.execute_query("SELECT LAST_INSERT_ID() as id", fetch='one')
            return result['id'] if result else None
        except Error as e:
            logger.error(f"Error getting last insert ID: {e}")
            return None
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        # Connection pool doesn't have a direct close method
        # Connections are closed when they're returned to the pool
        logger.info("All connections will be closed when returned to pool")


# Global database instance
_db_instance = None


def get_db() -> DatabaseConnection:
    """
    Get global database instance
    
    Returns:
        DatabaseConnection: Database connection instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


# Convenience functions
def execute_query(query: str, params: Optional[tuple] = None, 
                 fetch: str = 'all') -> Optional[Any]:
    """Execute a SELECT query using global database instance"""
    return get_db().execute_query(query, params, fetch)


def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """Execute an UPDATE/INSERT/DELETE query using global database instance"""
    return get_db().execute_update(query, params)


def execute_many(query: str, params_list: list) -> int:
    """Execute multiple queries using global database instance"""
    return get_db().execute_many(query, params_list)


@contextmanager
def get_connection():
    """Get database connection using global instance"""
    with get_db().get_connection() as conn:
        yield conn


@contextmanager
def get_cursor(dictionary=True, buffered=False):
    """Get database cursor using global instance"""
    with get_db().get_cursor(dictionary=dictionary, buffered=buffered) as cursor:
        yield cursor
