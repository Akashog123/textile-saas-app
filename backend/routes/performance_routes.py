"""
Performance monitoring and health check endpoints
"""

from flask import Blueprint, jsonify, request
from utils.performance_utils import get_cache_stats, clear_cache
from models.model import db
import psutil
import time
from datetime import datetime

performance_bp = Blueprint("performance", __name__)

@performance_bp.route("/health", methods=["GET"])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Database health
        try:
            db.session.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Cache stats
        cache_stats = get_cache_stats()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "memory": memory_usage,
            "cpu_percent": cpu_percent,
            "cache": cache_stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@performance_bp.route("/metrics", methods=["GET"])
def performance_metrics():
    """Detailed performance metrics"""
    try:
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "cpu_percent": psutil.cpu_percent(interval=1),
                "disk_total": disk.total,
                "disk_free": disk.free,
                "disk_percent": (disk.used / disk.total) * 100
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": process.create_time()
            },
            "cache": get_cache_stats()
        }
        
        return jsonify({
            "status": "success",
            "metrics": metrics
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get metrics: {str(e)}"
        }), 500

@performance_bp.route("/cache/clear", methods=["POST"])
def clear_cache_endpoint():
    """Clear performance cache"""
    try:
        old_stats = get_cache_stats()
        clear_cache()
        new_stats = get_cache_stats()
        
        return jsonify({
            "status": "success",
            "message": "Cache cleared successfully",
            "old_stats": old_stats,
            "new_stats": new_stats
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to clear cache: {str(e)}"
        }), 500

@performance_bp.route("/cache/stats", methods=["GET"])
def cache_performance():
    """Get cache performance statistics"""
    try:
        from utils.performance_utils import get_cache_stats
        
        cache_stats = get_cache_stats()
        
        return jsonify({
            "status": "success",
            "cache_performance": cache_stats,
            "cache_hit_ratio": "N/A (requires implementation)",
            "recommendations": [
                "Consider Redis for production-scale caching",
                "Monitor cache hit ratios",
                "Set appropriate TTL values"
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get cache stats: {str(e)}"
        }), 500

@performance_bp.route("/slow-queries", methods=["GET"])
def slow_queries():
    """Identify potentially slow database operations"""
    try:
        # This would need to be implemented based on your database
        # For SQLite, we can use EXPLAIN QUERY PLAN
        slow_operations = []
        
        # Example: Check product queries
        from models.model import Product, Shop, SalesData
        
        start_time = time.time()
        products = Product.query.limit(10).all()
        query_time = time.time() - start_time
        
        if query_time > 0.1:  # If query takes more than 100ms
            slow_operations.append({
                "query": "Product listing",
                "time": query_time,
                "recommendation": "Consider adding indexes or optimizing query"
            })
        
        return jsonify({
            "status": "success",
            "slow_operations": slow_operations,
            "total_checked": 1
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to analyze slow queries: {str(e)}"
        }), 500
