# backend/utils/database_health.py

"""
Database Health Monitoring and Connection Management
"""

import time
from contextlib import contextmanager
from flask import current_app
from models.model import db
from sqlalchemy import text
import threading

# Thread-local storage for connection tracking
_local = threading.local()

class DatabaseHealthMonitor:
    """Monitor database connection health and detect issues"""
    
    def __init__(self):
        self.connection_errors = 0
        self.last_error_time = None
        self.max_errors = 10
        self.error_reset_interval = 300  # 5 minutes
    
    def record_error(self):
        """Record a database connection error"""
        self.connection_errors += 1
        self.last_error_time = time.time()
        
        # Reset error count if enough time has passed
        if self.connection_errors > self.max_errors:
            current_time = time.time()
            if current_time - self.last_error_time > self.error_reset_interval:
                self.connection_errors = 0
    
    def is_healthy(self):
        """Check if database connection is healthy"""
        if self.connection_errors >= self.max_errors:
            current_time = time.time()
            if (self.last_error_time and 
                current_time - self.last_error_time < self.error_reset_interval):
                return False
        return True
    
    def get_status(self):
        """Get current database health status"""
        return {
            "healthy": self.is_healthy(),
            "error_count": self.connection_errors,
            "last_error": self.last_error_time
        }

# Global health monitor instance
health_monitor = DatabaseHealthMonitor()

@contextmanager
def database_session(timeout=30):
    """
    Context manager for database sessions with proper cleanup and error handling
    """
    session = None
    try:
        session = db.session
        session.begin()
        yield session
        session.commit()
    except Exception as e:
        if session:
            session.rollback()
        health_monitor.record_error()
        print(f"Database session error: {e}")
        raise
    finally:
        if session:
            session.close()

def check_database_connection():
    """Check if database connection is working"""
    try:
        with database_session():
            result = db.session.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        health_monitor.record_error()
        print(f"Database health check failed: {e}")
        return False

def get_database_pool_status():
    """Get current database pool status"""
    try:
        engine = db.engine
        pool = engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "health": health_monitor.get_status()
        }
    except Exception as e:
        print(f"Failed to get pool status: {e}")
        return {"error": str(e), "health": health_monitor.get_status()}

def reset_database_connections():
    """Attempt to reset database connections"""
    try:
        db.engine.dispose()
        health_monitor.connection_errors = 0
        return True
    except Exception as e:
        print(f"Failed to reset database connections: {e}")
        return False
