"""Tests for validator utilities.

Covers:
- Phone number validation (Pakistan format)
- Price validation (positive integers in cents)
- Email validation
- Serial number validation
- Text length validation

Note: All validators return Tuple[bool, Optional[str]] where:
- (True, None) means valid
- (False, "error message") means invalid
"""

import pytest
from utils.validators import (
    validate_phone,
    validate_price,
    validate_email,
    validate_serial,
    validate_text,
    validate_quantity,
)


class TestValidatePhone:
    """Test Pakistan phone number validation."""
    
    def test_valid_11_digit_mobile(self):
        """Test valid 11-digit mobile numbers."""
        is_valid, error = validate_phone("03001234567")
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_phone("03011234567")
        assert is_valid is True
        
        is_valid, error = validate_phone("03101234567")
        assert is_valid is True
    
    def test_valid_with_dashes(self):
        """Test valid numbers with dashes - digits are extracted."""
        is_valid, error = validate_phone("0300-1234567")
        assert is_valid is True
        assert error is None
    
    def test_invalid_empty_string(self):
        """Test that empty string is invalid."""
        is_valid, error = validate_phone("")
        assert is_valid is False
        assert error is not None
        assert "required" in error.lower()
    
    def test_invalid_too_short(self):
        """Test that too-short numbers are invalid."""
        is_valid, error = validate_phone("0300123456")  # 10 digits
        assert is_valid is False
        assert "11 digits" in error
    
    def test_invalid_too_long(self):
        """Test that too-long numbers are invalid."""
        is_valid, error = validate_phone("030012345678")  # 12 digits
        assert is_valid is False
        assert "11 digits" in error
    
    def test_invalid_non_numeric(self):
        """Test that non-numeric characters are removed, then validated."""
        # After removing non-digits, should be valid
        is_valid, error = validate_phone("0300-ABC-DEFG")
        # ABC and DEFG are removed, leaving 0300 which is too short
        assert is_valid is False
    
    def test_invalid_wrong_prefix(self):
        """Test that wrong prefix is invalid."""
        is_valid, error = validate_phone("04001234567")  # Should start with 03
        assert is_valid is False
        assert "start with 03" in error
    
    def test_returns_tuple_format(self):
        """Test that result is always a tuple."""
        result = validate_phone("03001234567")
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestValidatePrice:
    """Test price validation (cents as positive integers)."""
    
    def test_valid_positive_integer(self):
        """Test valid positive integer prices."""
        is_valid, error = validate_price(100)
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_price(220000)
        assert is_valid is True
        
        is_valid, error = validate_price(1000000)
        assert is_valid is True
    
    def test_zero_price(self):
        """Test that zero price is invalid."""
        is_valid, error = validate_price(0)
        assert is_valid is False
        assert error is not None
        assert "zero" in error.lower() or "greater" in error.lower()
    
    def test_negative_price(self):
        """Test that negative prices are invalid."""
        is_valid, error = validate_price(-100)
        assert is_valid is False
        assert "negative" in error.lower()
    
    def test_float_price(self):
        """Test that float prices are invalid."""
        is_valid, error = validate_price(100.50)
        assert is_valid is False
        assert "whole number" in error.lower()
    
    def test_non_numeric_price(self):
        """Test that non-numeric prices are invalid."""
        is_valid, error = validate_price("100")
        assert is_valid is False
        assert "whole number" in error.lower()
    
    def test_maximum_reasonable_price(self):
        """Test very large but valid price."""
        is_valid, error = validate_price(999999999)
        assert is_valid is True


class TestValidateEmail:
    """Test email validation."""
    
    def test_valid_emails(self):
        """Test valid email addresses."""
        is_valid, error = validate_email("test@example.com")
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_email("user.name@domain.co.uk")
        assert is_valid is True
    
    def test_invalid_empty_is_optional(self):
        """Test empty email is valid (optional field)."""
        is_valid, error = validate_email("")
        assert is_valid is True  # Empty is valid - email is optional
    
    def test_invalid_no_at(self):
        """Test email without @ is invalid."""
        is_valid, error = validate_email("userexample.com")
        assert is_valid is False
        assert "Invalid email" in error
    
    def test_invalid_no_domain(self):
        """Test email without domain is invalid."""
        is_valid, error = validate_email("user@")
        assert is_valid is False
    
    def test_invalid_no_tld(self):
        """Test email without TLD is invalid."""
        is_valid, error = validate_email("user@domain")
        assert is_valid is False
    
    def test_invalid_spaces(self):
        """Test email with spaces is invalid."""
        is_valid, error = validate_email("user @example.com")
        assert is_valid is False


class TestValidateSerial:
    """Test serial number validation."""
    
    def test_valid_numeric_serial(self):
        """Test valid numeric serials (4-8 digits)."""
        is_valid, error = validate_serial("0001")
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_serial("0042")
        assert is_valid is True
        
        is_valid, error = validate_serial("12345678")
        assert is_valid is True
    
    def test_invalid_empty(self):
        """Test empty serial is invalid."""
        is_valid, error = validate_serial("")
        assert is_valid is False
        assert error is not None
    
    def test_invalid_too_long(self):
        """Test serials over 8 characters are invalid."""
        is_valid, error = validate_serial("1" * 9)
        assert is_valid is False
        assert "4-8" in error
    
    def test_invalid_special_chars(self):
        """Test serials with special chars are invalid."""
        is_valid, error = validate_serial("SER@AL#123")
        assert is_valid is False
        assert "digits" in error.lower()
    
    def test_invalid_letters(self):
        """Test serials with letters are invalid."""
        is_valid, error = validate_serial("ABC123")
        assert is_valid is False
        assert "digits" in error.lower()


class TestValidateText:
    """Test text length validation."""
    
    def test_valid_within_range(self):
        """Test text within valid length range."""
        is_valid, error = validate_text("Hello", "name", min_length=1, max_length=10)
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_text("A" * 100, "description", min_length=1, max_length=100)
        assert is_valid is True
    
    def test_too_short(self):
        """Test text below minimum length is invalid."""
        is_valid, error = validate_text("Hi", "name", min_length=5, max_length=10)
        assert is_valid is False
        assert "at least" in error.lower()
    
    def test_too_long(self):
        """Test text above maximum length is invalid."""
        is_valid, error = validate_text("A" * 51, "name", min_length=1, max_length=50)
        assert is_valid is False
        assert "exceed" in error.lower()
    
    def test_empty_not_allowed(self):
        """Test empty string when allow_empty=False is invalid."""
        is_valid, error = validate_text("", "name", allow_empty=False)
        assert is_valid is False
        assert "required" in error.lower()
    
    def test_empty_allowed(self):
        """Test empty string when allow_empty=True is valid."""
        is_valid, error = validate_text("", "notes", allow_empty=True)
        assert is_valid is True
        assert error is None
    
    def test_strips_whitespace_for_empty_check(self):
        """Test that whitespace-only string is treated as empty."""
        is_valid, error = validate_text("   ", "name", allow_empty=False)
        assert is_valid is False
        assert "required" in error.lower()
    
    def test_default_range(self):
        """Test default min/max length values."""
        # Default: min_length=1, max_length=255, allow_empty=False
        is_valid, error = validate_text("Short", "name")
        assert is_valid is True
        
        is_valid, error = validate_text("A" * 255, "description")
        assert is_valid is True
        
        is_valid, error = validate_text("A" * 256, "description")
        assert is_valid is False


class TestValidateQuantity:
    """Test quantity validation."""
    
    def test_valid_positive_integer(self):
        """Test valid positive quantities."""
        is_valid, error = validate_quantity(1)
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_quantity(100)
        assert is_valid is True
    
    def test_zero_not_allowed_by_default(self):
        """Test zero is invalid by default."""
        is_valid, error = validate_quantity(0)
        assert is_valid is False
        assert "greater" in error.lower()
    
    def test_zero_allowed_when_specified(self):
        """Test zero is valid when allow_zero=True."""
        is_valid, error = validate_quantity(0, allow_zero=True)
        assert is_valid is True
        assert error is None
    
    def test_negative_invalid(self):
        """Test negative quantities are invalid."""
        is_valid, error = validate_quantity(-5)
        assert is_valid is False
        assert "negative" in error.lower()
    
    def test_float_invalid(self):
        """Test float quantities are invalid."""
        is_valid, error = validate_quantity(5.5)
        assert is_valid is False
        assert "whole number" in error.lower()