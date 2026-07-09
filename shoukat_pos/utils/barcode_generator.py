"""Barcode Generator for Code 128 at 203 DPI.

This module generates Code 128 barcodes optimized for thermal printers
operating at 203 DPI (BlackCopper BC-LP-1300).

Key Constraints:
- At 203 DPI, valid font sizes are multiples of 6pt: 6, 12, 18, 24, 30, 36
- Barcode bars must align with printer dot grid for reliable scanning
- Quiet zone of 2mm minimum required on each side
"""

from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# Valid point sizes for Code 128 at 203 DPI
VALID_POINT_SIZES = [6, 12, 18, 24, 30, 36]

# DPI constants
DPI = 203
DPMM = 8  # dots per mm at 203 DPI


def calculate_barcode_dimensions(
    data_length: int,
    point_size: int = 24,
    include_human_readable: bool = True
) -> Tuple[int, int, int]:
    """Calculate barcode dimensions in dots.
    
    Args:
        data_length: Number of characters in barcode data
        point_size: Font size in points (must be multiple of 6)
        include_human_readable: Whether to include human-readable text
        
    Returns:
        Tuple of (width_dots, height_dots, quiet_zone_dots)
        
    Raises:
        ValueError: If point_size is not a valid size
    """
    if point_size not in VALID_POINT_SIZES:
        raise ValueError(
            f"Invalid point size {point_size}. "
            f"Valid sizes at 203 DPI: {VALID_POINT_SIZES}"
        )
    
    # Code 128 encoding:
    # - Start code: 11 modules
    # - Each character: 11 modules
    # - Check digit: 11 modules
    # - Stop code: 13 modules
    # Total modules = 11 + (data_length * 11) + 11 + 13 = 35 + (data_length * 11)
    total_modules = 35 + (data_length * 11)
    
    # At 203 DPI, 1 module = 1 dot (narrow bar)
    # Wide bar = 2-3 dots depending on ratio
    width_dots = total_modules
    
    # Height depends on point size
    # Standard height is typically 10mm (80 dots) for small labels
    height_dots = int(point_size * DPMM / 72 * 10)  # Convert pt to dots
    if height_dots < 40:
        height_dots = 80  # Minimum 10mm for reliability
    
    # Quiet zone: 10x narrow bar width on each side
    quiet_zone_dots = 16  # 2mm on each side
    
    return width_dots, height_dots, quiet_zone_dots


def encode_code128(data: str) -> str:
    """Encode data as Code 128 barcode pattern.
    
    This function converts alphanumeric data into Code 128 symbol structure,
    including start code, data characters, check digit, and stop code.
    
    Args:
        data: Data string to encode (ASCII printable characters)
        
    Returns:
        Encoded pattern string for TSPL BARCODE command
        
    Note:
        For TSPL printers, we send the raw data and let the printer
        firmware handle the encoding. This function validates the data.
    """
    assert data, "Data cannot be empty"
    assert len(data) <= 80, "Code 128 max length is 80 characters"
    
    # Validate ASCII printable range
    for char in data:
        code = ord(char)
        if code < 32 or code > 126:
            raise ValueError(
                f"Character '{char}' (code {code}) not supported in Code 128"
            )
    
    # TSPL handles encoding internally, just return validated data
    return data


def generate_barcode_tspl(
    data: str,
    x_dots: int,
    y_dots: int,
    height_dots: int = 80,
    human_readable: bool = True,
    narrow_bar: int = 2,
    wide_bar: int = 3
) -> str:
    """Generate TSPL BARCODE command for Code 128.
    
    Args:
        data: Data to encode in barcode
        x_dots: X position in dots from left edge
        y_dots: Y position in dots from bottom edge
        height_dots: Barcode height in dots (default 80 = 10mm)
        human_readable: Show human-readable text below barcode
        narrow_bar: Narrow bar width in dots (default 2)
        wide_bar: Wide bar width in dots (default 3)
        
    Returns:
        TSPL BARCODE command string
        
    Example:
        >>> cmd = generate_barcode_tspl("0001", 12, 32)
        >>> print(cmd)
        BARCODE 12,32,"128",80,1,0,2,3,"0001"
    """
    assert data, "Data cannot be empty"
    assert x_dots >= 0, "X must be non-negative"
    assert y_dots >= 0, "Y must be non-negative"
    assert height_dots > 0, "Height must be positive"
    assert narrow_bar > 0, "Narrow bar must be positive"
    assert wide_bar >= narrow_bar, "Wide bar must be >= narrow bar"
    
    # Validate and encode data
    encoded_data = encode_code128(data)
    
    # Escape quotes in data
    escaped_data = encoded_data.replace('"', '\\"')
    
    # Build TSPL command
    # Format: BARCODE x,y,"type",height,human_read,rotation,narrow,wide,"data"
    hr_flag = 1 if human_readable else 0
    command = (
        f'BARCODE {x_dots},{y_dots},"128",{height_dots},{hr_flag},0,'
        f'{narrow_bar},{wide_bar},"{escaped_data}"'
    )
    
    logger.debug(f"Generated barcode command: {command}")
    return command


def validate_barcode_scannability(
    width_dots: int,
    height_dots: int,
    printer_dpi: int = 203
) -> Tuple[bool, str]:
    """Validate that barcode dimensions will produce scannable output.
    
    Args:
        width_dots: Barcode width in dots
        height_dots: Barcode height in dots
        printer_dpi: Printer resolution in DPI
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    assert width_dots > 0, "Width must be positive"
    assert height_dots > 0, "Height must be positive"
    
    # Minimum height for reliable scanning
    min_height_dots = int(10 * DPMM)  # 10mm
    if height_dots < min_height_dots:
        return False, (
            f"Barcode height {height_dots} dots ({height_dots/DPMM:.1f}mm) "
            f"is below minimum {min_height_dots} dots (10mm)"
        )
    
    # Minimum width for typical data lengths
    # Code 128 with 4 digits needs ~79 modules
    min_width_dots = 50  # Absolute minimum
    if width_dots < min_width_dots:
        return False, (
            f"Barcode width {width_dots} dots is below minimum {min_width_dots}"
        )
    
    # Aspect ratio check (height should be >= width for most scanners)
    if height_dots < width_dots * 0.5:
        return False, (
            "Barcode aspect ratio may cause scanning issues "
            "(height should be at least 50% of width)"
        )
    
    return True, ""