"""Input validation utilities for POS data entry.

This module provides validation functions for common POS input types
including phone numbers, prices, emails, barcodes, and serial numbers.

All validators return a tuple of (is_valid: bool, error_message: str or None)
to enable user-friendly error messages in the UI.
"""

import re
from typing import Tuple, Optional


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate Pakistani mobile phone number.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, "error message") if invalid
        
    Example:
        >>> validate_phone("03001234567")
        (True, None)
        >>> validate_phone("123")
        (False, "Phone number must be 11 digits")
    """
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required"
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Handle Pakistan country code (+92)
    if digits.startswith('92'):
        digits = digits[2:]
    
    # Pakistani mobile numbers: 03XX-XXXXXXX (11 digits starting with 03)
    if len(digits) != 11:
        return False, "Phone number must be 11 digits"
    
    if not digits.startswith('03'):
        return False, "Phone number must start with 03"
    
    return True, None


def validate_price(price_cents: int) -> Tuple[bool, Optional[str]]:
    """Validate price value.
    
    Args:
        price_cents: Price in cents to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(price_cents, int):
        return False, "Price must be a whole number"
    
    if price_cents < 0:
        return False, "Price cannot be negative"
    
    if price_cents == 0:
        return False, "Price must be greater than zero"
    
    # Maximum price check (Rs. 10,00,000 = 10 million rupees)
    if price_cents > 10000000000:  # 10 crore rupees in cents
        return False, "Price exceeds maximum allowed value"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return True, None  # Email is optional
    
    email = email.strip()
    if not email:
        return True, None  # Empty email is valid (optional field)
    
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    if len(email) > 254:
        return False, "Email address too long"
    
    return True, None


def validate_barcode(barcode: str, barcode_type: str = "CODE128") -> Tuple[bool, Optional[str]]:
    """Validate barcode format.
    
    Args:
        barcode: Barcode data to validate
        barcode_type: Type of barcode ("CODE128", "CODE39", "EAN13")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not barcode or not isinstance(barcode, str):
        return False, "Barcode is required"
    
    barcode = barcode.strip()
    
    if not barcode:
        return False, "Barcode cannot be empty"
    
    if barcode_type == "CODE128":
        # Code 128 supports full ASCII, but we typically use alphanumeric
        if len(barcode) < 1 or len(barcode) > 80:
            return False, "Code 128 barcode must be 1-80 characters"
        return True, None
    
    elif barcode_type == "CODE39":
        # Code 39 supports uppercase letters, digits, and some symbols
        pattern = r'^[A-Z0-9 \-\.\$\+\/\%]+$'
        if not re.match(pattern, barcode.upper()):
            return False, "Code 39 barcode contains invalid characters"
        if len(barcode) < 1 or len(barcode) > 43:
            return False, "Code 39 barcode must be 1-43 characters"
        return True, None
    
    elif barcode_type == "EAN13":
        # EAN-13 must be exactly 13 digits
        if not barcode.isdigit():
            return False, "EAN-13 barcode must contain only digits"
        if len(barcode) != 13:
            return False, "EAN-13 barcode must be exactly 13 digits"
        
        # Validate EAN-13 checksum
        if not _validate_ean13_checksum(barcode):
            return False, "Invalid EAN-13 checksum"
        return True, None
    
    else:
        return False, f"Unknown barcode type: {barcode_type}"


def _validate_ean13_checksum(barcode: str) -> bool:
    """Validate EAN-13 checksum digit.
    
    Args:
        barcode: 13-digit EAN barcode
        
    Returns:
        True if checksum is valid
    """
    digits = [int(d) for d in barcode]
    
    # Sum odd-positioned digits (1st, 3rd, 5th, ...)
    odd_sum = sum(digits[i] for i in range(0, 12, 2))
    
    # Sum even-positioned digits (2nd, 4th, 6th, ...)
    even_sum = sum(digits[i] for i in range(1, 12, 2))
    
    # Calculate checksum
    total = odd_sum + (even_sum * 3)
    checksum = (10 - (total % 10)) % 10
    
    return checksum == digits[12]


def validate_serial(serial: str) -> Tuple[bool, Optional[str]]:
    """Validate product serial number.
    
    Serial numbers are typically 4-8 digit numeric codes.
    
    Args:
        serial: Serial number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not serial or not isinstance(serial, str):
        return False, "Serial number is required"
    
    serial = serial.strip()
    
    if not serial:
        return False, "Serial number cannot be empty"
    
    if not serial.isdigit():
        return False, "Serial number must contain only digits"
    
    if len(serial) < 4 or len(serial) > 8:
        return False, "Serial number must be 4-8 digits"
    
    return True, None


def validate_quantity(qty: int, allow_zero: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate quantity value.
    
    Args:
        qty: Quantity to validate
        allow_zero: If True, zero is considered valid
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(qty, int):
        return False, "Quantity must be a whole number"
    
    if qty < 0:
        return False, "Quantity cannot be negative"
    
    if not allow_zero and qty == 0:
        return False, "Quantity must be greater than zero"
    
    # Maximum quantity check (1 million)
    if qty > 1000000:
        return False, "Quantity exceeds maximum allowed value"
    
    return True, None


def validate_percentage(value: float, allow_zero: bool = True, 
                        max_value: float = 100.0) -> Tuple[bool, Optional[str]]:
    """Validate percentage value.
    
    Args:
        value: Percentage value to validate
        allow_zero: If True, zero is considered valid
        max_value: Maximum allowed percentage (default 100.0)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, (int, float)):
        return False, "Percentage must be a number"
    
    if value < 0:
        return False, "Percentage cannot be negative"
    
    if not allow_zero and value == 0:
        return False, "Percentage must be greater than zero"
    
    if value > max_value:
        return False, f"Percentage cannot exceed {max_value}%"
    
    return True, None


def validate_text(text: str, field_name: str, 
                  min_length: int = 1, 
                  max_length: int = 255,
                  allow_empty: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate text field.
    
    Args:
        text: Text to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        allow_empty: If True, empty string is valid
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(text, str):
        return False, f"{field_name} must be text"
    
    if not allow_empty and not text.strip():
        return False, f"{field_name} is required"
    
    if text and len(text) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    
    if text and len(text) > max_length:
        return False, f"{field_name} cannot exceed {max_length} characters"
    
    return True, None


def validate_secret_code(code: str, mapping_length: int = 10) -> Tuple[bool, Optional[str]]:
    """Validate secret code format.
    
    Secret codes encode purchase prices using a digit-to-character mapping.
    
    Args:
        code: Secret code to validate
        mapping_length: Expected number of unique characters in mapping (default 10)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not code or not isinstance(code, str):
        return False, "Secret code is required"
    
    code = code.strip().upper()
    
    if not code:
        return False, "Secret code cannot be empty"
    
    # Secret codes should only contain uppercase letters
    if not code.isalpha():
        return False, "Secret code must contain only letters"
    
    if not code.isupper():
        return False, "Secret code must be uppercase"
    
    # Reasonable length check (typically 3-6 characters for prices)
    if len(code) < 2 or len(code) > 10:
        return False, "Secret code must be 2-10 characters"
    
    return True, None