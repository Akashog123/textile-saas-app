# backend/utils/__init__.py
"""
Utility modules for the SE-Textile-App backend.
"""

from .response_helpers import (
    success_response,
    error_response,
    paginated_response,
    created_response,
    not_found_response,
    forbidden_response,
    validation_error_response,
    handle_exceptions,
    get_pagination_params,
    paginate_query,
    serialize_pagination
)

from .auth_utils import (
    generate_jwt,
    decode_jwt,
    token_required,
    roles_required,
    check_shop_ownership,
    check_product_ownership,
    get_user_shops,
    resource_owner_required
)

__all__ = [
    # Response helpers
    'success_response',
    'error_response',
    'paginated_response',
    'created_response',
    'not_found_response',
    'forbidden_response',
    'validation_error_response',
    'handle_exceptions',
    'get_pagination_params',
    'paginate_query',
    'serialize_pagination',
    # Auth utilities
    'generate_jwt',
    'decode_jwt',
    'token_required',
    'roles_required',
    'check_shop_ownership',
    'check_product_ownership',
    'get_user_shops',
    'resource_owner_required'
]
