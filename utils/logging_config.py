#!/usr/bin/env python3
"""
Comprehensive Logging Configuration for Haystack
Provides structured logging with correlation IDs, context tracking, and multiple output formats
"""

import os
import sys
import logging
import logging.config
import uuid
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pathlib import Path
import json
from contextlib import contextmanager

# Thread-local storage for correlation IDs and context
_context = threading.local()

class ContextFilter(logging.Filter):
    """Logging filter that adds correlation ID and context to log records"""
    
    def filter(self, record):
        # Add correlation ID
        record.correlation_id = getattr(_context, 'correlation_id', 'no-correlation-id')
        
        # Add engine context
        record.engine_name = getattr(_context, 'engine_name', 'system')
        record.engine_id = getattr(_context, 'engine_id', 0)
        
        # Add operation context
        record.operation = getattr(_context, 'operation', 'unknown')
        record.item_id = getattr(_context, 'item_id', None)
        
        # Add user context (for API calls)
        record.user_id = getattr(_context, 'user_id', 'system')
        record.request_id = getattr(_context, 'request_id', None)
        
        return True

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', 'no-correlation-id'),
            'engine_name': getattr(record, 'engine_name', 'system'),
            'engine_id': getattr(record, 'engine_id', 0),
            'operation': getattr(record, 'operation', 'unknown'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process
        }
        
        # Add optional fields if present
        if hasattr(record, 'item_id') and record.item_id:
            log_entry['item_id'] = record.item_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'request_id') and record.request_id:
            log_entry['request_id'] = record.request_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith('_'):
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class HaystackFormatter(logging.Formatter):
    """Custom formatter for human-readable console output"""
    
    def format(self, record):
        # Color codes for different log levels
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m'  # Magenta
        }
        reset = '\033[0m'
        
        # Get correlation ID and engine context
        correlation_id = getattr(record, 'correlation_id', 'no-id')[:8]
        engine_name = getattr(record, 'engine_name', 'system')
        operation = getattr(record, 'operation', 'unknown')
        
        # Format the message
        color = colors.get(record.levelname, '')
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        formatted_message = (
            f"{color}[{timestamp}] {record.levelname:<8}{reset} "
            f"[{correlation_id}] [{engine_name}:{operation}] "
            f"{record.name}: {record.getMessage()}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"
        
        return formatted_message

def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Union[str, Path]] = None,
    enable_json_logging: bool = True,
    enable_console_logging: bool = True,
    enable_file_logging: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Set up comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to ./logs)
        enable_json_logging: Enable structured JSON logging to file
        enable_console_logging: Enable console logging
        enable_file_logging: Enable file logging
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup files to keep
    """
    
    # Create log directory
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console': {
                '()': HaystackFormatter,
            },
            'json': {
                '()': JSONFormatter,
            },
            'file': {
                'format': '[%(asctime)s] %(levelname)-8s [%(correlation_id)s] [%(engine_name)s:%(operation)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'filters': {
            'context': {
                '()': ContextFilter,
            }
        },
        'handlers': {},
        'loggers': {
            'haystack': {
                'level': log_level,
                'handlers': [],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',  # Reduce SQLAlchemy noise
                'handlers': [],
                'propagate': True
            },
            'sqlalchemy.pool': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': True
            }
        },
        'root': {
            'level': log_level,
            'handlers': []
        }
    }
    
    handlers = []
    
    # Console handler
    if enable_console_logging:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'console',
            'filters': ['context'],
            'stream': 'ext://sys.stdout'
        }
        handlers.append('console')
    
    # File handler for general logs
    if enable_file_logging:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'file',
            'filters': ['context'],
            'filename': str(log_dir / 'haystack.log'),
            'maxBytes': max_file_size,
            'backupCount': backup_count,
            'encoding': 'utf8'
        }
        handlers.append('file')
    
    # JSON handler for structured logging
    if enable_json_logging:
        config['handlers']['json'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json',
            'filters': ['context'],
            'filename': str(log_dir / 'haystack.json'),
            'maxBytes': max_file_size,
            'backupCount': backup_count,
            'encoding': 'utf8'
        }
        handlers.append('json')
        
        # Separate error log in JSON format
        config['handlers']['error_json'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filters': ['context'],
            'filename': str(log_dir / 'haystack_errors.json'),
            'maxBytes': max_file_size,
            'backupCount': backup_count,
            'encoding': 'utf8'
        }
        handlers.append('error_json')
    
    # Apply handlers to all loggers
    config['loggers']['haystack']['handlers'] = handlers
    config['root']['handlers'] = handlers
    
    # Apply the configuration
    logging.config.dictConfig(config)
    
    # Log the startup
    logger = logging.getLogger('haystack.logging')
    logger.info(f"Logging initialized - Level: {log_level}, Handlers: {', '.join(handlers)}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the haystack prefix"""
    if not name.startswith('haystack.'):
        name = f'haystack.{name}'
    return logging.getLogger(name)

# Context management functions
def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for current thread"""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    _context.correlation_id = correlation_id
    return correlation_id

def get_correlation_id() -> str:
    """Get correlation ID for current thread"""
    return getattr(_context, 'correlation_id', 'no-correlation-id')

def set_engine_context(engine_name: str, engine_id: int = 0):
    """Set engine context for current thread"""
    _context.engine_name = engine_name
    _context.engine_id = engine_id

def set_operation_context(operation: str, item_id: Optional[int] = None):
    """Set operation context for current thread"""
    _context.operation = operation
    if item_id is not None:
        _context.item_id = item_id

def set_user_context(user_id: str, request_id: Optional[str] = None):
    """Set user context for current thread"""
    _context.user_id = user_id
    if request_id is not None:
        _context.request_id = request_id

def clear_context():
    """Clear all context for current thread"""
    _context.__dict__.clear()

@contextmanager
def logging_context(
    correlation_id: Optional[str] = None,
    engine_name: Optional[str] = None,
    engine_id: Optional[int] = None,
    operation: Optional[str] = None,
    item_id: Optional[int] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
):
    """
    Context manager for setting logging context
    
    Usage:
        with logging_context(engine_name="craigslist", operation="scrape"):
            logger.info("Starting scraping operation")
    """
    # Store original context
    original_context = getattr(_context, '__dict__', {}).copy()
    
    try:
        # Set new context
        if correlation_id is not None:
            set_correlation_id(correlation_id)
        if engine_name is not None:
            _context.engine_name = engine_name
        if engine_id is not None:
            _context.engine_id = engine_id
        if operation is not None:
            _context.operation = operation
        if item_id is not None:
            _context.item_id = item_id
        if user_id is not None:
            _context.user_id = user_id
        if request_id is not None:
            _context.request_id = request_id
        
        yield
    finally:
        # Restore original context
        _context.__dict__.clear()
        _context.__dict__.update(original_context)

# Performance logging decorator
def log_performance(operation_name: str = None):
    """
    Decorator to log function execution time and performance metrics
    
    Usage:
        @log_performance("database_query")
        def my_function():
            pass
    """
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(f'performance.{func.__module__}.{func.__name__}')
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            start_memory = None
            
            try:
                import psutil
                process = psutil.Process()
                start_memory = process.memory_info().rss
            except ImportError:
                pass
            
            try:
                with logging_context(operation=operation):
                    result = func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                
                log_data = {
                    'operation': operation,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'status': 'success'
                }
                
                if start_memory:
                    try:
                        end_memory = process.memory_info().rss
                        log_data['memory_delta_mb'] = round((end_memory - start_memory) / 1024 / 1024, 2)
                    except:
                        pass
                
                logger.info(f"Performance: {operation}", extra=log_data)
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Performance: {operation} - FAILED",
                    extra={
                        'operation': operation,
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'status': 'error',
                        'error': str(e)
                    }
                )
                raise
        
        return wrapper
    return decorator

# Initialize default logging if not already done
if not logging.getLogger().handlers:
    setup_logging(
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        log_dir=os.getenv('LOG_DIR'),
        enable_json_logging=os.getenv('ENABLE_JSON_LOGGING', 'true').lower() == 'true',
        enable_console_logging=os.getenv('ENABLE_CONSOLE_LOGGING', 'true').lower() == 'true'
    )