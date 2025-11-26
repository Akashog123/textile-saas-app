# backend/utils/connection_recovery.py

"""
Database Connection Recovery Utilities
"""

import os
import time
from models.model import db
from utils.database_health import reset_database_connections, health_monitor
from flask import current_app
from sqlalchemy import text

def attempt_database_recovery():
    """
    Attempt to recover from database connection issues
    """
    try:
        print("Attempting database connection recovery...")
        
        # Step 1: Reset the database engine
        if reset_database_connections():
            print("Database connections reset successfully")
        
        # Step 2: Test the connection
        from utils.database_health import check_database_connection
        if check_database_connection():
            print("Database connection test passed")
            return True
        else:
            print("Database connection test failed after reset")
            return False
            
    except Exception as e:
        print(f"Database recovery failed: {e}")
        return False

def handle_connection_timeout():
    """
    Handle database connection timeout errors
    """
    print("Database connection timeout detected")
    
    # Try recovery
    if attempt_database_recovery():
        print("Database recovery successful")
        return True
    else:
        print("Database recovery failed - manual intervention may be required")
        return False

def optimize_database_settings():
    """
    Apply database optimization settings
    """
    try:
        engine = db.engine
        
        # For SQLite, optimize settings
        if "sqlite" in str(engine.url):
            # Enable WAL mode for better concurrent access
            with engine.connect() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.execute(text("PRAGMA synchronous=NORMAL"))
                conn.execute(text("PRAGMA cache_size=10000"))
                conn.execute(text("PRAGMA temp_store=MEMORY"))
                conn.commit()
            
            print("SQLite optimization settings applied")
            return True
            
    except Exception as e:
        print(f"Failed to optimize database settings: {e}")
        return False

def get_connection_recommendations():
    """
    Get recommendations for database connection issues
    """
    status = health_monitor.get_status()
    
    recommendations = []
    
    if not status["healthy"]:
        recommendations.append("Database connection unhealthy - consider restarting the application")
        recommendations.append("Check if database file is accessible and not locked")
        
    if status["error_count"] > 5:
        recommendations.append("High error count detected - monitor for patterns")
        recommendations.append("Consider increasing connection pool size")
        
    return {
        "status": status,
        "recommendations": recommendations,
        "last_check": time.time()
    }
