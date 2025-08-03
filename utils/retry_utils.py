#!/usr/bin/env python3
"""
Retry and Circuit Breaker Utilities for Haystack
Provides robust error handling for network operations and database connections
"""

import time
import random
from typing import Callable, Any, Optional, List, Type, Union
from functools import wraps
import threading
from datetime import datetime, timedelta

from tenacity import (
    retry, stop_after_attempt, wait_exponential, 
    retry_if_exception_type, before_sleep_log, after_log
)
from circuitbreaker import circuit

from utils.logging_config import get_logger, logging_context

logger = get_logger('retry_utils')

class RetryableError(Exception):
    """Base class for errors that should trigger retries"""
    pass

class NetworkError(RetryableError):
    """Network-related errors that should be retried"""
    pass

class DatabaseRetryableError(RetryableError):
    """Database errors that should be retried"""
    pass

class RateLimitError(RetryableError):
    """Rate limiting errors that should be retried"""
    pass

# Common exceptions that should trigger retries
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    NetworkError,
    DatabaseRetryableError,
    RateLimitError,
    # Database specific
    Exception,  # We'll be more specific in practice
)

# Exceptions that should NOT trigger retries
NON_RETRYABLE_EXCEPTIONS = (
    KeyboardInterrupt,
    SystemExit,
    ValueError,  # Usually programming errors
    TypeError,   # Usually programming errors
)

def is_retryable_exception(exception: Exception) -> bool:
    """Determine if an exception should trigger a retry"""
    if isinstance(exception, NON_RETRYABLE_EXCEPTIONS):
        return False
    
    # Check for specific database errors that are retryable
    if hasattr(exception, 'args') and exception.args:
        error_msg = str(exception).lower()
        retryable_patterns = [
            'connection', 'timeout', 'network', 'temporary',
            'lock wait timeout', 'deadlock', 'server has gone away',
            'too many connections', 'connection refused'
        ]
        if any(pattern in error_msg for pattern in retryable_patterns):
            return True
    
    return isinstance(exception, RETRYABLE_EXCEPTIONS)

def smart_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Smart retry decorator with exponential backoff and jitter
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retryable_exceptions: List of exception types that should trigger retries
    """
    if retryable_exceptions is None:
        retryable_exceptions = RETRYABLE_EXCEPTIONS
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    with logging_context(operation=f"{func.__name__}_attempt_{attempt + 1}"):
                        result = func(*args, **kwargs)
                        
                        if attempt > 0:
                            logger.info(f"Operation succeeded after {attempt + 1} attempts: {func.__name__}")
                        
                        return result
                        
                except Exception as e:
                    last_exception = e
                    
                    # Check if this exception should trigger a retry
                    if not is_retryable_exception(e):
                        logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                        raise
                    
                    if attempt < max_attempts - 1:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        
                        # Add jitter to prevent thundering herd
                        if jitter:
                            delay *= (0.5 + random.random() * 0.5)
                        
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # If we get here, all attempts failed
            raise last_exception
        
        return wrapper
    return decorator

def database_retry(max_attempts: int = 3, base_delay: float = 0.5):
    """Specialized retry decorator for database operations"""
    return smart_retry(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    )

def network_retry(max_attempts: int = 5, base_delay: float = 1.0):
    """Specialized retry decorator for network operations"""
    return smart_retry(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )

# Circuit breaker configurations
DATABASE_CIRCUIT = circuit(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=Exception
)

NETWORK_CIRCUIT = circuit(
    failure_threshold=10,
    recovery_timeout=60,
    expected_exception=Exception
)

def database_circuit_breaker(func: Callable) -> Callable:
    """Circuit breaker for database operations"""
    @DATABASE_CIRCUIT
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database circuit breaker triggered for {func.__name__}: {e}")
            raise DatabaseRetryableError(f"Database operation failed: {e}")
    
    return wrapper

def network_circuit_breaker(func: Callable) -> Callable:
    """Circuit breaker for network operations"""
    @NETWORK_CIRCUIT
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Network circuit breaker triggered for {func.__name__}: {e}")
            raise NetworkError(f"Network operation failed: {e}")
    
    return wrapper

class RateLimiter:
    """Thread-safe rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = threading.Lock()
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire rate limit permission
        
        Args:
            timeout: Maximum time to wait for permission
            
        Returns:
            True if permission granted, False if timeout exceeded
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                now = time.time()
                
                # Remove old calls outside the time window
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
                
                # Check if we can make a new call
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return True
            
            # Check timeout
            if timeout is not None and time.time() - start_time > timeout:
                return False
            
            # Wait a bit before trying again
            time.sleep(0.1)
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def rate_limited(max_calls: int, time_window: float):
    """
    Rate limiting decorator
    
    Args:
        max_calls: Maximum number of calls allowed
        time_window: Time window in seconds
    """
    limiter = RateLimiter(max_calls, time_window)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.acquire(timeout=30.0):  # 30 second timeout
                raise RateLimitError(f"Rate limit exceeded for {func.__name__}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

class BackoffStrategy:
    """Base class for backoff strategies"""
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for the given attempt number"""
        raise NotImplementedError

class ExponentialBackoff(BackoffStrategy):
    """Exponential backoff strategy"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, multiplier: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
    
    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.multiplier ** attempt)
        return min(delay, self.max_delay)

class LinearBackoff(BackoffStrategy):
    """Linear backoff strategy"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        delay = self.base_delay * (attempt + 1)
        return min(delay, self.max_delay)

def robust_operation(
    operation_name: str,
    max_attempts: int = 3,
    backoff_strategy: Optional[BackoffStrategy] = None,
    circuit_breaker: bool = True,
    rate_limit: Optional[tuple] = None
):
    """
    Comprehensive decorator combining retry, circuit breaker, and rate limiting
    
    Args:
        operation_name: Name of the operation for logging
        max_attempts: Maximum retry attempts
        backoff_strategy: Backoff strategy to use
        circuit_breaker: Whether to use circuit breaker
        rate_limit: Tuple of (max_calls, time_window) for rate limiting
    """
    if backoff_strategy is None:
        backoff_strategy = ExponentialBackoff()
    
    def decorator(func: Callable) -> Callable:
        # Apply rate limiting if specified
        if rate_limit:
            func = rate_limited(rate_limit[0], rate_limit[1])(func)
        
        # Apply circuit breaker if enabled
        if circuit_breaker:
            if 'database' in operation_name.lower():
                func = database_circuit_breaker(func)
            elif 'network' in operation_name.lower():
                func = network_circuit_breaker(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    with logging_context(
                        operation=f"{operation_name}_attempt_{attempt + 1}",
                        attempt=attempt + 1,
                        max_attempts=max_attempts
                    ):
                        result = func(*args, **kwargs)
                        
                        if attempt > 0:
                            logger.info(
                                f"Operation '{operation_name}' succeeded after {attempt + 1} attempts"
                            )
                        
                        return result
                        
                except Exception as e:
                    last_exception = e
                    
                    if not is_retryable_exception(e):
                        logger.error(f"Non-retryable exception in '{operation_name}': {e}")
                        raise
                    
                    if attempt < max_attempts - 1:
                        delay = backoff_strategy.get_delay(attempt)
                        
                        logger.warning(
                            f"Attempt {attempt + 1} failed for '{operation_name}': {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for '{operation_name}': {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator

# Convenience decorators for common patterns
def robust_database_operation(func: Callable) -> Callable:
    """Robust decorator for database operations"""
    return robust_operation(
        operation_name=f"database_{func.__name__}",
        max_attempts=3,
        backoff_strategy=ExponentialBackoff(base_delay=0.5, max_delay=10.0),
        circuit_breaker=True
    )(func)

def robust_network_operation(func: Callable) -> Callable:
    """Robust decorator for network operations"""
    return robust_operation(
        operation_name=f"network_{func.__name__}",
        max_attempts=5,
        backoff_strategy=ExponentialBackoff(base_delay=1.0, max_delay=30.0),
        circuit_breaker=True,
        rate_limit=(10, 60)  # 10 calls per minute
    )(func)

def robust_scraping_operation(func: Callable) -> Callable:
    """Robust decorator for web scraping operations"""
    return robust_operation(
        operation_name=f"scraping_{func.__name__}",
        max_attempts=3,
        backoff_strategy=ExponentialBackoff(base_delay=2.0, max_delay=60.0),
        circuit_breaker=True,
        rate_limit=(30, 60)  # 30 calls per minute to be respectful
    )(func)