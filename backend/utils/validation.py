# backend/utils/validation.py
"""
Input Validation and Sanitization Utilities
Provides validation helpers for IDs, emails, passwords, files, and query parameters
"""

import re
import os
from decimal import Decimal, InvalidOperation


# ID Validation
def validate_shop_id(shop_id):
    """
    Validate and convert shop ID to integer.
    
    Args:
        shop_id: Shop ID (string or int)
    
    Returns:
        int: Valid shop ID
    
    Raises:
        ValueError: If shop_id is invalid
    """
    try:
        shop_id = int(shop_id)
        if shop_id <= 0:
            raise ValueError("Shop ID must be positive")
        return shop_id
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid shop_id: {e}")


def validate_product_id(product_id):
    """
    Validate and convert product ID to integer.
    
    Args:
        product_id: Product ID (string or int)
    
    Returns:
        int: Valid product ID
    
    Raises:
        ValueError: If product_id is invalid
    """
    try:
        product_id = int(product_id)
        if product_id <= 0:
            raise ValueError("Product ID must be positive")
        return product_id
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid product_id: {e}")


def validate_user_id(user_id):
    """
    Validate and convert user ID to integer.
    
    Args:
        user_id: User ID (string or int)
    
    Returns:
        int: Valid user ID
    
    Raises:
        ValueError: If user_id is invalid
    """
    try:
        user_id = int(user_id)
        if user_id <= 0:
            raise ValueError("User ID must be positive")
        return user_id
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid user_id: {e}")


# Data Validation
def validate_email(email):
    """
    Validate email format using regex.
    
    Args:
        email: Email string
    
    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """
    Validate password strength.
    Requirements: min 8 chars, at least one letter and one number
    
    Args:
        password: Password string
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not password:
        return (False, "Password is required")
    
    min_length = int(os.getenv("PASSWORD_MIN_LENGTH", 8))
    
    if len(password) < min_length:
        return (False, f"Password must be at least {min_length} characters long")
    
    require_letter = os.getenv("PASSWORD_REQUIRE_LETTER", "True").lower() == "true"
    require_number = os.getenv("PASSWORD_REQUIRE_NUMBER", "True").lower() == "true"
    
    has_letter = bool(re.compile(r'[a-zA-Z]').search(password))
    has_number = bool(re.compile(r'\d').search(password))
    
    if require_letter and not has_letter:
        return (False, "Password must contain at least one letter")
    
    if require_number and not has_number:
        return (False, "Password must contain at least one number")
    
    return (True, "Password is valid")


def validate_price(price):
    """
    Validate price value (must be positive decimal).
    
    Args:
        price: Price value (string, float, or Decimal)
    
    Returns:
        Decimal: Valid price value
    
    Raises:
        ValueError: If price is invalid
    """
    try:
        price = Decimal(str(price))
        
        if price < 0:
            raise ValueError("Price must be non-negative")
        
        # Check max 2 decimal places
        if price.as_tuple().exponent < -2:
            raise ValueError("Price can have at most 2 decimal places")
        
        return price
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Invalid price: {e}")


def validate_quantity(quantity):
    """
    Validate quantity value (must be non-negative integer).
    
    Args:
        quantity: Quantity value (string or int)
    
    Returns:
        int: Valid quantity
    
    Raises:
        ValueError: If quantity is invalid
    """
    try:
        quantity = int(quantity)
        
        if quantity < 0:
            raise ValueError("Quantity must be non-negative")
        
        return quantity
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid quantity: {e}")


def validate_phone(phone):
    """
    Basic phone number validation.
    Allows digits, spaces, hyphens, parentheses, and + symbol.
    
    Args:
        phone: Phone number string
    
    Returns:
        bool: True if valid format, False otherwise
    """
    if not phone:
        return False
    
    # Basic pattern: allows international format
    pattern = r'^[\d\s\-\(\)\+]{8,20}$'
    return bool(re.match(pattern, phone))


# File Validation
def validate_file_upload(file, allowed_extensions, max_size_mb=16):
    """
    Validate uploaded file (extension and size).
    
    Args:
        file: FileStorage object from Flask request
        allowed_extensions: List of allowed file extensions (e.g., ['.csv', '.xlsx'])
        max_size_mb: Maximum file size in megabytes (default: 16)
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not file:
        return (False, "No file provided")
    
    if not file.filename:
        return (False, "Invalid filename")
    
    # Check file extension
    filename_lower = file.filename.lower()
    file_ext = None
    for ext in allowed_extensions:
        if filename_lower.endswith(ext.lower()):
            file_ext = ext
            break
    
    if not file_ext:
        return (False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
    
    # Check file size (seek to end to get size, then reset)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return (False, f"File too large. Maximum size: {max_size_mb}MB")
    
    if file_size == 0:
        return (False, "File is empty")
    
    return (True, "File is valid")


# Query Sanitization
def sanitize_string(value, max_length=255):
    """
    Sanitize string input by stripping dangerous characters and limiting length.
    
    Args:
        value: String value to sanitize
        max_length: Maximum allowed length (default: 255)
    
    Returns:
        str: Sanitized string
    """
    if not value:
        return ""
    
    # Convert to string
    value = str(value)
    
    # Strip leading/trailing whitespace
    value = value.strip()
    
    # Remove null bytes (can cause issues)
    value = value.replace('\x00', '')
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


def sanitize_int(value, min_val=None, max_val=None):
    """
    Safely convert value to integer with optional bounds checking.
    
    Args:
        value: Value to convert
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
    
    Returns:
        int: Sanitized integer value
    
    Raises:
        ValueError: If value cannot be converted or is out of bounds
    """
    try:
        value = int(value)
        
        if min_val is not None and value < min_val:
            raise ValueError(f"Value must be at least {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValueError(f"Value must be at most {max_val}")
        
        return value
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid integer value: {e}")

# Export all utilities
__all__ = [
    'validate_shop_id',
    'validate_product_id',
    'validate_user_id',
    'validate_email',
    'validate_password',
    'validate_price',
    'validate_quantity',
    'validate_phone',
    'validate_file_upload',
    'sanitize_string',
    'sanitize_int'
]
