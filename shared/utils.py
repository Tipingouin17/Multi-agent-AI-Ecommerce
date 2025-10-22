"""
Utility Functions for Multi-Agent E-commerce System

This module provides common utility functions used across all agents.
"""

import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
import structlog

logger = structlog.get_logger(__name__)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        Unique identifier string
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id


def generate_order_number() -> str:
    """
    Generate a unique order number.
    
    Returns:
        Order number in format ORD-YYYYMMDD-XXXXX
    """
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = str(uuid.uuid4())[:8].upper()
    return f"ORD-{date_part}-{random_part}"


def generate_tracking_number(carrier: str = "GENERIC") -> str:
    """
    Generate a tracking number.
    
    Args:
        carrier: Carrier code
        
    Returns:
        Tracking number
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:6].upper()
    return f"{carrier}-{timestamp}-{random_part}"


def calculate_hash(data: Union[str, Dict, List]) -> str:
    """
    Calculate SHA256 hash of data.
    
    Args:
        data: Data to hash (string, dict, or list)
        
    Returns:
        Hex digest of hash
    """
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True)
    
    return hashlib.sha256(data.encode()).hexdigest()


def format_currency(amount: Union[float, Decimal, int], currency: str = "EUR") -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code (EUR, USD, etc.)
        
    Returns:
        Formatted currency string
    """
    symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
        "JPY": "¥"
    }
    
    symbol = symbols.get(currency, currency)
    
    if currency == "JPY":
        # No decimal places for JPY
        return f"{symbol}{int(amount)}"
    else:
        return f"{symbol}{float(amount):.2f}"


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string to datetime object.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        datetime object or None if parsing fails
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning("Failed to parse date", date_str=date_str)
    return None


def format_date(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: datetime object
        format: Output format string
        
    Returns:
        Formatted date string
    """
    return dt.strftime(format)


def add_days(dt: datetime, days: int) -> datetime:
    """
    Add days to a datetime.
    
    Args:
        dt: Base datetime
        days: Number of days to add (can be negative)
        
    Returns:
        New datetime
    """
    return dt + timedelta(days=days)


def is_business_day(dt: datetime) -> bool:
    """
    Check if date is a business day (Monday-Friday).
    
    Args:
        dt: Date to check
        
    Returns:
        True if business day
    """
    return dt.weekday() < 5  # 0-4 = Monday-Friday


def calculate_delivery_date(
    order_date: datetime,
    processing_days: int = 1,
    shipping_days: int = 3,
    skip_weekends: bool = True
) -> datetime:
    """
    Calculate estimated delivery date.
    
    Args:
        order_date: Order placement date
        processing_days: Days for order processing
        shipping_days: Days for shipping
        skip_weekends: Whether to skip weekends
        
    Returns:
        Estimated delivery date
    """
    current_date = order_date
    total_days = processing_days + shipping_days
    days_added = 0
    
    while days_added < total_days:
        current_date = add_days(current_date, 1)
        
        if skip_weekends and not is_business_day(current_date):
            continue
        
        days_added += 1
    
    return current_date


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string for safe storage/display.
    
    Args:
        text: Input text
        max_length: Optional maximum length
        
    Returns:
        Sanitized string
    """
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email appears valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Basic phone number validation.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone appears valid
    """
    import re
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    # Check if it's 10-15 digits, optionally starting with +
    pattern = r'^\+?\d{10,15}$'
    return bool(re.match(pattern, cleaned))


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def safe_get(data: Dict, path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value using dot notation.
    
    Args:
        data: Dictionary to query
        path: Dot-separated path (e.g., "user.address.city")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def retry_on_exception(
    func,
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on exception.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Decorated function
    """
    import asyncio
    from functools import wraps
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        for attempt in range(max_attempts):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_attempts - 1:
                    raise
                logger.warning(
                    "Function failed, retrying",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    error=str(e)
                )
                await asyncio.sleep(delay)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        import time
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_attempts - 1:
                    raise
                logger.warning(
                    "Function failed, retrying",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    error=str(e)
                )
                time.sleep(delay)
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def get_env(key: str, default: Any = None, required: bool = False) -> Any:
    """
    Get environment variable with type conversion.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    
    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get boolean environment variable.
    
    Args:
        key: Environment variable name
        default: Default value
        
    Returns:
        Boolean value
    """
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int = 0) -> int:
    """
    Get integer environment variable.
    
    Args:
        key: Environment variable name
        default: Default value
        
    Returns:
        Integer value
    """
    try:
        return int(os.getenv(key, default))
    except (ValueError, TypeError):
        return default

