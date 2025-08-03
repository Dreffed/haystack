#!/usr/bin/env python3
"""
Test script to validate database pooling and logging improvements
"""

import os
import sys
import time
import tempfile
from datetime import datetime

# Add project paths
sys.path.insert(0, os.path.dirname(__file__))

def test_logging_system():
    """Test the logging configuration"""
    print("Testing logging system...")
    
    try:
        from utils.logging_config import setup_logging, get_logger, logging_context, set_correlation_id
        
        # Set up logging
        setup_logging(log_level="DEBUG", log_dir="./test_logs")
        
        # Get logger
        logger = get_logger('test.logging')
        
        # Test basic logging
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.debug("Test debug message")
        
        # Test correlation ID
        correlation_id = set_correlation_id()
        logger.info(f"Test with correlation ID: {correlation_id}")
        
        # Test logging context
        with logging_context(engine_name="test_engine", operation="test_operation", item_id=123):
            logger.info("Test message with context")
        
        print("PASSED: Logging system test")
        return True
        
    except Exception as e:
        print(f"FAILED: Logging system test - {e}")
        return False

def test_retry_utils():
    """Test retry and circuit breaker utilities"""
    print("Testing retry utilities...")
    
    try:
        from utils.retry_utils import smart_retry, robust_database_operation, RateLimiter
        
        # Test retry decorator
        @smart_retry(max_attempts=3, base_delay=0.1)
        def flaky_function(fail_count=2):
            if hasattr(flaky_function, '_call_count'):
                flaky_function._call_count += 1
            else:
                flaky_function._call_count = 1
            
            if flaky_function._call_count <= fail_count:
                raise ConnectionError(f"Simulated failure {flaky_function._call_count}")
            
            return "Success!"
        
        # Reset call count
        flaky_function._call_count = 0
        result = flaky_function(fail_count=2)
        assert result == "Success!", "Retry decorator should succeed after retries"
        
        # Test rate limiter
        limiter = RateLimiter(max_calls=3, time_window=1.0)
        
        # Should allow 3 calls
        for i in range(3):
            assert limiter.acquire(timeout=1.0), f"Rate limiter should allow call {i+1}"
        
        # 4th call should be blocked
        assert not limiter.acquire(timeout=0.1), "Rate limiter should block 4th call"
        
        print("PASSED: Retry utilities test")
        return True
        
    except Exception as e:
        print(f"FAILED: Retry utilities test - {e}")
        return False

def test_database_pool():
    """Test database connection pooling (without actual database)"""
    print("Testing database pool configuration...")
    
    try:
        from db.database_pool import DatabaseConfig, create_database_config
        
        # Test config creation from dict
        config_dict = {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db'
        }
        
        db_config = create_database_config(config_dict)
        assert db_config.host == 'localhost', "Config should parse host correctly"
        assert db_config.port == 3306, "Config should parse port correctly"
        assert db_config.pool_size == 10, "Config should have default pool size"
        
        # Test config creation from environment
        os.environ['DB_HOST'] = 'env_host'
        os.environ['DB_USER'] = 'env_user'
        os.environ['DB_PASSWORD'] = 'env_password'
        os.environ['DB_NAME'] = 'env_db'
        
        env_config = create_database_config(None)
        assert env_config.host == 'env_host', "Config should read from environment"
        assert env_config.user == 'env_user', "Config should read user from environment"
        
        print("PASSED: Database pool configuration test")
        return True
        
    except Exception as e:
        print(f"FAILED: Database pool test - {e}")
        return False

def test_enhanced_peregrin_db():
    """Test enhanced PeregrinDB interface (without actual database)"""
    print("Testing enhanced PeregrinDB interface...")
    
    try:
        from db.PeregrinDB_v2 import PeregrinDB, PeregrinDBError
        
        # Test initialization
        db = PeregrinDB()
        assert db.get_id() == -1, "Initial engine ID should be -1"
        
        info = db.info()
        assert info[0] == 'PeregrinDB', "Database title should be correct"
        assert info[1] == '2.0', "Database version should be 2.0"
        
        # Test pool status without connection
        status = db.get_pool_status()
        assert status['status'] == 'not_connected', "Pool should show not connected"
        
        print("PASSED: Enhanced PeregrinDB interface test")
        return True
        
    except Exception as e:
        print(f"FAILED: Enhanced PeregrinDB test - {e}")
        return False

def test_syntax_validation():
    """Test that all Python files have valid syntax"""
    print("Testing Python syntax validation...")
    
    import py_compile
    
    files_to_test = [
        'utils/logging_config.py',
        'utils/retry_utils.py',
        'db/database_pool.py',
        'db/PeregrinDB_v2.py',
        'engines/craigslist.py',
        'engines/peregrinbase.py'
    ]
    
    failed_files = []
    
    for file_path in files_to_test:
        try:
            if os.path.exists(file_path):
                py_compile.compile(file_path, doraise=True)
                print(f"  OK: {file_path}")
            else:
                print(f"  WARN: {file_path} - File not found")
        except py_compile.PyCompileError as e:
            print(f"  ERROR: {file_path} - Syntax error: {e}")
            failed_files.append(file_path)
    
    if failed_files:
        print(f"FAILED: Syntax validation failed for {len(failed_files)} files")
        return False
    else:
        print("PASSED: All Python files have valid syntax")
        return True

def main():
    """Run all tests"""
    print("Starting Haystack improvements validation tests...\n")
    
    tests = [
        ("Logging System", test_logging_system),
        ("Retry Utilities", test_retry_utils),
        ("Database Pool", test_database_pool),
        ("Enhanced PeregrinDB", test_enhanced_peregrin_db),
        ("Syntax Validation", test_syntax_validation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"CRASHED: {test_name} test - {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\nAll tests passed! The improvements are working correctly.")
        return 0
    else:
        print(f"\n{failed} test(s) failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())