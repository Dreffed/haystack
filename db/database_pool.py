#!/usr/bin/env python3
"""
Database Connection Pool Manager for Haystack
Using SQLAlchemy with connection pooling and proper error handling
"""

import os
import logging
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import configparser

from sqlalchemy import create_engine, text, exc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import pymysql

# Set up logger
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration container"""
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = 'utf8mb4'
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

class DatabaseError(Exception):
    """Base database exception"""
    pass

class ConnectionError(DatabaseError):
    """Database connection specific error"""
    pass

class QueryError(DatabaseError):
    """Database query specific error"""
    pass

class DatabasePool:
    """
    Thread-safe database connection pool manager
    Provides connection pooling, automatic retries, and proper error handling
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine = None
        self._session_factory = None
        self._lock = threading.Lock()
        self._is_initialized = False
        
        # Initialize the connection pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the SQLAlchemy engine with connection pooling"""
        try:
            # Build connection string
            connection_string = (
                f"mysql+pymysql://{self.config.user}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
                f"?charset={self.config.charset}"
            )
            
            # Create engine with connection pooling
            self._engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=False,  # Set to True for SQL query logging
                pool_reset_on_return='commit'
            )
            
            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)
            
            # Test connection
            self._test_connection()
            
            self._is_initialized = True
            logger.info(f"Database pool initialized successfully - {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise ConnectionError(f"Database pool initialization failed: {e}")
    
    def _test_connection(self):
        """Test database connectivity"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.debug("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise ConnectionError(f"Database connection test failed: {e}")
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions with automatic cleanup
        Usage: 
            with db_pool.get_session() as session:
                result = session.execute(text("SELECT * FROM table"))
        """
        if not self._is_initialized:
            raise ConnectionError("Database pool not initialized")
        
        session = None
        try:
            session = self._session_factory()
            yield session
            session.commit()
        except exc.SQLAlchemyError as e:
            if session:
                session.rollback()
            logger.error(f"Database session error: {e}")
            raise QueryError(f"Database operation failed: {e}")
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Unexpected database error: {e}")
            raise DatabaseError(f"Unexpected database error: {e}")
        finally:
            if session:
                session.close()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for raw database connections
        Usage:
            with db_pool.get_connection() as conn:
                result = conn.execute(text("SELECT * FROM table"))
        """
        if not self._is_initialized:
            raise ConnectionError("Database pool not initialized")
        
        conn = None
        try:
            conn = self._engine.connect()
            yield conn
            conn.commit()
        except exc.SQLAlchemyError as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise QueryError(f"Database operation failed: {e}")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Unexpected database error: {e}")
            raise DatabaseError(f"Unexpected database error: {e}")
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(text(query), params or {})
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed - Query: {query[:100]}..., Error: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute an UPDATE/INSERT/DELETE query and return affected rows
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(text(query), params or {})
                return result.rowcount
        except Exception as e:
            logger.error(f"Update execution failed - Query: {query[:100]}..., Error: {e}")
            raise
    
    def execute_insert(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute an INSERT query and return the last inserted ID
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute(text(query), params or {})
                return result.lastrowid
        except Exception as e:
            logger.error(f"Insert execution failed - Query: {query[:100]}..., Error: {e}")
            raise
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status for monitoring"""
        if not self._engine:
            return {"status": "not_initialized"}
        
        pool = self._engine.pool
        return {
            "status": "active",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
    
    def health_check(self) -> bool:
        """Perform health check on database connection"""
        try:
            self._test_connection()
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False
    
    def close(self):
        """Close all connections and dispose of the engine"""
        try:
            if self._engine:
                self._engine.dispose()
                logger.info("Database pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")
        finally:
            self._is_initialized = False

class DatabasePoolManager:
    """
    Singleton manager for database pool instances
    Ensures single pool instance per configuration
    """
    
    _instances: Dict[str, DatabasePool] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_pool(cls, config: DatabaseConfig, pool_name: str = "default") -> DatabasePool:
        """Get or create a database pool instance"""
        if pool_name not in cls._instances:
            with cls._lock:
                if pool_name not in cls._instances:
                    cls._instances[pool_name] = DatabasePool(config)
        
        return cls._instances[pool_name]
    
    @classmethod
    def close_all_pools(cls):
        """Close all database pools"""
        with cls._lock:
            for pool_name, pool in cls._instances.items():
                try:
                    pool.close()
                    logger.info(f"Closed database pool: {pool_name}")
                except Exception as e:
                    logger.error(f"Error closing pool {pool_name}: {e}")
            cls._instances.clear()

def create_database_config(config_source) -> DatabaseConfig:
    """
    Create DatabaseConfig from various sources
    Supports: dict, configparser.ConfigParser, environment variables
    """
    if isinstance(config_source, dict):
        return DatabaseConfig(
            host=config_source.get('host', 'localhost'),
            port=int(config_source.get('port', 3306)),
            user=config_source['user'],
            password=config_source['password'],
            database=config_source['database'],
            charset=config_source.get('charset', 'utf8mb4'),
            pool_size=int(config_source.get('pool_size', 10)),
            max_overflow=int(config_source.get('max_overflow', 20)),
            pool_timeout=int(config_source.get('pool_timeout', 30)),
            pool_recycle=int(config_source.get('pool_recycle', 3600))
        )
    
    elif isinstance(config_source, configparser.ConfigParser):
        db_section = config_source['Database']
        return DatabaseConfig(
            host=db_section.get('Server', 'localhost'),
            port=int(db_section.get('Port', 3306)),
            user=db_section.get('User'),
            password=db_section.get('Password'),
            database=db_section.get('Schema'),
            charset=db_section.get('Charset', 'utf8mb4'),
            pool_size=int(db_section.get('PoolSize', 10)),
            max_overflow=int(db_section.get('MaxOverflow', 20)),
            pool_timeout=int(db_section.get('PoolTimeout', 30)),
            pool_recycle=int(db_section.get('PoolRecycle', 3600))
        )
    
    else:
        # Environment variables
        return DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'test'),
            charset=os.getenv('DB_CHARSET', 'utf8mb4'),
            pool_size=int(os.getenv('DB_POOL_SIZE', 10)),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 20)),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30)),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', 3600))
        )

# Global database pool instance
_default_pool: Optional[DatabasePool] = None

def initialize_default_pool(config_source) -> DatabasePool:
    """Initialize the default database pool"""
    global _default_pool
    if _default_pool is None:
        config = create_database_config(config_source)
        _default_pool = DatabasePoolManager.get_pool(config, "default")
    return _default_pool

def get_default_pool() -> Optional[DatabasePool]:
    """Get the default database pool if initialized"""
    return _default_pool