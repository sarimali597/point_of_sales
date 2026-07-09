"""Currency, date, and quantity formatting utilities for POS display.

This module provides consistent formatting functions for displaying
monetary values, dates, and quantities throughout the POS system.

All formatting follows Pakistani retail conventions:
- Currency: Rs. 1,250 or Rs. 1,250.50
- Date: DD/MM/YYYY or DD/MM/YYYY HH:MM
- Quantity: Integer with thousand separators for large values
"""

from datetime import datetime
from typing import Optional, Union


def format_currency(cents: int, show_zeros: bool = True) -> str:
    """Format integer cents as Pakistani Rupees with comma separators.
    
    Args:
        cents: Amount in cents (e.g., 125050 for Rs. 1,250.50)
        show_zeros: If False, omit .00 for whole rupee amounts
        
    Returns:
        Formatted currency string (e.g., "Rs. 1,250.50" or "Rs. 1,250")
        
    Example:
        >>> format_currency(125050)
        'Rs. 1,250.50'
        >>> format_currency(125000, show_zeros=False)
        'Rs. 1,250'
        >>> format_currency(0)
        'Rs. 0.00'
    """
    assert isinstance(cents, int), "Cents must be an integer"
    assert cents >= 0, "Cents cannot be negative"
    
    rupees = cents // 100
    paise = cents % 100
    
    # Format rupees with comma separators (Pakistani/Indian numbering)
    # Groups: 3 digits, then 2 digits (e.g., 1,25,000)
    rupees_str = f"{rupees:,}"
    
    if paise > 0 or show_zeros:
        return f"Rs. {rupees_str}.{paise:02d}"
    else:
        return f"Rs. {rupees_str}"


def parse_currency(text: str) -> int:
    """Parse currency text back to integer cents.
    
    Args:
        text: Currency string (e.g., "Rs. 1,250.50" or "1250.50")
        
    Returns:
        Amount in cents
        
    Raises:
        ValueError: If text cannot be parsed as currency
        
    Example:
        >>> parse_currency("Rs. 1,250.50")
        125050
        >>> parse_currency("1250")
        125000
    """
    assert isinstance(text, str), "Text must be a string"
    
    # Remove currency symbol and whitespace
    cleaned = text.replace("Rs.", "").replace("Rs", "").strip()
    cleaned = cleaned.replace(",", "")  # Remove thousand separators
    
    try:
        value = float(cleaned)
        return int(round(value * 100))
    except ValueError:
        raise ValueError(f"Cannot parse '{text}' as currency")


def format_date(date_obj: Optional[datetime], format_str: str = "%d/%m/%Y") -> str:
    """Format datetime object as string.
    
    Args:
        date_obj: Datetime object to format (None returns empty string)
        format_str: strftime format string (default: "%d/%m/%Y")
        
    Returns:
        Formatted date string or empty string if None
        
    Example:
        >>> from datetime import datetime
        >>> format_date(datetime(2026, 7, 8))
        '08/07/2026'
        >>> format_date(datetime(2026, 7, 8, 14, 30), "%d/%m/%Y %H:%M")
        '08/07/2026 14:30'
    """
    if date_obj is None:
        return ""
    
    assert isinstance(date_obj, datetime), "Must be datetime object"
    
    return date_obj.strftime(format_str)


def format_datetime_full(dt: Optional[datetime]) -> str:
    """Format datetime with full date and time.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        Formatted string like "08/07/2026 14:32"
    """
    return format_date(dt, "%d/%m/%Y %H:%M")


def format_datetime_iso(dt: Optional[datetime]) -> str:
    """Format datetime as ISO 8601 string.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        ISO 8601 formatted string like "2026-07-08T14:32:00"
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def parse_date(text: str, format_str: str = "%d/%m/%Y") -> Optional[datetime]:
    """Parse date string to datetime object.
    
    Args:
        text: Date string to parse
        format_str: strptime format string (default: "%d/%m/%Y")
        
    Returns:
        Datetime object or None if parsing fails
    """
    assert isinstance(text, str), "Text must be a string"
    
    if not text.strip():
        return None
    
    try:
        return datetime.strptime(text.strip(), format_str)
    except ValueError:
        return None


def format_quantity(qty: int, show_thousands: bool = True) -> str:
    """Format quantity with optional thousand separators.
    
    Args:
        qty: Quantity value
        show_thousands: If True, add comma separators for values >= 1000
        
    Returns:
        Formatted quantity string
        
    Example:
        >>> format_quantity(1250)
        '1,250'
        >>> format_quantity(50, show_thousands=False)
        '50'
    """
    assert isinstance(qty, int), "Quantity must be an integer"
    assert qty >= 0, "Quantity cannot be negative"
    
    if show_thousands and qty >= 1000:
        return f"{qty:,}"
    else:
        return str(qty)


def format_size(size: str) -> str:
    """Normalize and format garment size.
    
    Args:
        size: Size string (may be lowercase or abbreviated)
        
    Returns:
        Standardized uppercase size string
        
    Example:
        >>> format_size("m")
        'M'
        >>> format_size("XL")
        'XL'
    """
    assert isinstance(size, str), "Size must be a string"
    assert size, "Size cannot be empty"
    
    # Common size mappings
    size_mappings = {
        'XS': 'XS', 'X-SMALL': 'XS', 'EXTRA SMALL': 'XS',
        'S': 'S', 'SMALL': 'S',
        'M': 'M', 'MEDIUM': 'M',
        'L': 'L', 'LARGE': 'L',
        'XL': 'XL', 'X-LARGE': 'XL', 'EXTRA LARGE': 'XL',
        'XXL': 'XXL', 'XL-LARGE': 'XXL', 'DOUBLE XL': 'XXL',
        'XXXL': 'XXXL', 'TRIPLE XL': 'XXXL',
    }
    
    normalized = size.strip().upper()
    return size_mappings.get(normalized, normalized)


def format_phone(phone: str) -> str:
    """Format phone number with standard Pakistani format.
    
    Args:
        phone: Raw phone number (e.g., "03001234567" or "+923001234567")
        
    Returns:
        Formatted phone number (e.g., "0300-1234567")
        
    Example:
        >>> format_phone("03001234567")
        '0300-1234567'
        >>> format_phone("+923001234567")
        '0300-1234567'
    """
    assert isinstance(phone, str), "Phone must be a string"
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Handle Pakistan country code
    if digits.startswith('92') and len(digits) == 13:
        digits = '0' + digits[2:]
    
    # Format as XXXX-XXXXXXX for 11-digit numbers
    if len(digits) == 11 and digits.startswith('03'):
        return f"{digits[:4]}-{digits[4:]}"
    
    # Return as-is if format doesn't match
    return digits


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append when truncating (default "...")
        
    Returns:
        Truncated text if longer than max_length, otherwise original text
        
    Example:
        >>> truncate_text("Premium Cotton Shirt", 15)
        'Premium Cot...'
        >>> truncate_text("Short", 10)
        'Short'
    """
    assert isinstance(text, str), "Text must be a string"
    assert isinstance(max_length, int), "Max length must be integer"
    assert max_length > 0, "Max length must be positive"
    assert isinstance(suffix, str), "Suffix must be string"
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix