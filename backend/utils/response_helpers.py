# backend/utils/response_helpers.py
"""
Standardized API Response Helpers
Reduces redundancy across routes by providing consistent response formatting.
"""

from flask import jsonify
from functools import wraps
import traceback


# ============================================================================
# STANDARD RESPONSE BUILDERS
# ============================================================================

def success_response(data=None, message=None, status_code=200, **extra):
    """
    Build a standardized success response.
    
    Args:
        data: Response data (dict, list, or None)
        message: Optional success message
        status_code: HTTP status code (default 200)
        **extra: Additional fields to include in response
    
    Returns:
        tuple: (response, status_code)
    """
    response = {"status": "success"}
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    # Add any extra fields
    response.update(extra)
    
    return jsonify(response), status_code


def error_response(message, status_code=400, error_code=None, details=None):
    """
    Build a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code (default 400)
        error_code: Optional error code for client handling
        details: Optional additional error details
    
    Returns:
        tuple: (response, status_code)
    """
    response = {
        "status": "error",
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return jsonify(response), status_code


def paginated_response(items, pagination, message=None, **extra):
    """
    Build a standardized paginated response.
    
    Args:
        items: List of items for current page
        pagination: Pagination object or dict with page info
        message: Optional message
        **extra: Additional fields
    
    Returns:
        tuple: (response, 200)
    """
    # Handle SQLAlchemy pagination object
    if hasattr(pagination, 'page'):
        pagination_info = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    else:
        pagination_info = pagination
    
    response = {
        "status": "success",
        "data": items,
        "pagination": pagination_info,
        "count": len(items)
    }
    
    if message:
        response["message"] = message
    
    response.update(extra)
    
    return jsonify(response), 200


def created_response(data=None, message="Created successfully", **extra):
    """Shorthand for 201 created response."""
    return success_response(data, message, 201, **extra)


def not_found_response(resource="Resource", message=None):
    """Shorthand for 404 not found response."""
    msg = message or f"{resource} not found"
    return error_response(msg, 404, error_code="NOT_FOUND")


def forbidden_response(message="You don't have permission to perform this action"):
    """Shorthand for 403 forbidden response."""
    return error_response(message, 403, error_code="FORBIDDEN")


def validation_error_response(message, field=None):
    """Shorthand for validation error response."""
    details = {"field": field} if field else None
    return error_response(message, 400, error_code="VALIDATION_ERROR", details=details)


# ============================================================================
# ROUTE DECORATORS
# ============================================================================

def handle_exceptions(log_prefix="API"):
    """
    Decorator to standardize exception handling across routes.
    
    Args:
        log_prefix: Prefix for log messages
    
    Usage:
        @handle_exceptions("Product Route")
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValueError as e:
                print(f"[{log_prefix} - Validation Error] {e}")
                return validation_error_response(str(e))
            except Exception as e:
                print(f"[{log_prefix} - Error] {e}")
                traceback.print_exc()
                return error_response(
                    "An unexpected error occurred",
                    500,
                    error_code="INTERNAL_ERROR"
                )
        return decorated
    return decorator


def validate_required_params(*required_params, source='json'):
    """
    Decorator to validate required parameters.
    
    Args:
        *required_params: Parameter names that are required
        source: Where to look for params ('json', 'args', 'form')
    
    Usage:
        @validate_required_params('shop_id', 'product_id', source='json')
        def my_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request
            
            if source == 'json':
                data = request.get_json(silent=True) or {}
            elif source == 'args':
                data = request.args.to_dict()
            elif source == 'form':
                data = request.form.to_dict()
            else:
                data = {}
            
            missing = [p for p in required_params if not data.get(p)]
            
            if missing:
                return validation_error_response(
                    f"Missing required parameters: {', '.join(missing)}"
                )
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============================================================================
# PAGINATION HELPERS
# ============================================================================

def get_pagination_params(default_page=1, default_per_page=20, max_per_page=100):
    """
    Extract pagination parameters from request args.
    
    Returns:
        tuple: (page, per_page)
    """
    from flask import request
    
    try:
        page = max(1, int(request.args.get('page', default_page)))
    except (ValueError, TypeError):
        page = default_page
    
    try:
        per_page = int(request.args.get('per_page', default_per_page))
        per_page = max(1, min(per_page, max_per_page))
    except (ValueError, TypeError):
        per_page = default_per_page
    
    return page, per_page


def paginate_query(query, page=1, per_page=20):
    """
    Apply pagination to SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Pagination object
    """
    return query.paginate(page=page, per_page=per_page, error_out=False)


def serialize_pagination(pagination, serializer=None):
    """
    Serialize paginated items.
    
    Args:
        pagination: SQLAlchemy pagination object
        serializer: Optional function to serialize each item
    
    Returns:
        tuple: (items_list, pagination_info)
    """
    if serializer:
        items = [serializer(item) for item in pagination.items]
    elif hasattr(pagination.items[0] if pagination.items else None, 'to_dict'):
        items = [item.to_dict() for item in pagination.items]
    else:
        items = pagination.items
    
    return items, {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'success_response',
    'error_response',
    'paginated_response',
    'created_response',
    'not_found_response',
    'forbidden_response',
    'validation_error_response',
    'handle_exceptions',
    'validate_required_params',
    'get_pagination_params',
    'paginate_query',
    'serialize_pagination'
]
