"""TSPL Command Builder for BlackCopper BC-LP-1300 Thermal Label Printer.

This module provides a fluent interface for building TSPL (TSC Printer Language)
commands for thermal label printers operating at 203 DPI.

Attributes:
    DPI: Printer resolution in dots per inch (203 for BC-LP-1300)
    DPMM: Dots per millimeter at 203 DPI (approximately 8)
"""

from typing import Optional, List


class TSPLBuilder:
    """Fluent builder for TSPL thermal printer commands.
    
    All coordinates are specified in dots (1mm = 8 dots at 203 DPI).
    The builder pattern allows chaining multiple method calls.
    
    Example:
        >>> builder = TSPLBuilder(28, 19, 2)
        >>> tspl = (builder
        ...     .text(112, 16, "2", 0, 1, 1, "SHOUKAT SONS")
        ...     .barcode(12, 32, "128", 80, 1, 0, 2, 2, "0001")
        ...     .print_label(1)
        ...     .end()
        ...     .build())
    """
    
    DPI: int = 203
    DPMM: int = 8  # dots per mm at 203 DPI
    
    def __init__(self, width_mm: int, height_mm: int, gap_mm: int = 2):
        """Initialize TSPL builder with label dimensions.
        
        Args:
            width_mm: Label width in millimeters
            height_mm: Label height in millimeters
            gap_mm: Gap between labels in millimeters (default 2)
        """
        assert width_mm > 0, "Width must be positive"
        assert height_mm > 0, "Height must be positive"
        assert gap_mm >= 0, "Gap must be non-negative"
        
        self._commands: List[str] = []
        self._width_mm = width_mm
        self._height_mm = height_mm
        
        # Initialize with standard header commands
        self.size(width_mm, height_mm)
        self.gap(gap_mm, 0)
        self.codepage("UTF-8")
        self.direction(1)
        self.cls()
    
    def size(self, width_mm: int, height_mm: int) -> 'TSPLBuilder':
        """Set label size.
        
        Args:
            width_mm: Label width in millimeters
            height_mm: Label height in millimeters
            
        Returns:
            Self for method chaining
        """
        assert width_mm > 0, "Width must be positive"
        assert height_mm > 0, "Height must be positive"
        self._commands.append(f'SIZE {width_mm} mm,{height_mm} mm')
        return self
    
    def gap(self, gap_mm: int, offset_mm: int) -> 'TSPLBuilder':
        """Set gap between labels.
        
        Args:
            gap_mm: Gap distance in millimeters
            offset_mm: Offset distance in millimeters
            
        Returns:
            Self for method chaining
        """
        assert gap_mm >= 0, "Gap must be non-negative"
        assert offset_mm >= 0, "Offset must be non-negative"
        self._commands.append(f'GAP {gap_mm} mm,{offset_mm} mm')
        return self
    
    def codepage(self, name: str) -> 'TSPLBuilder':
        """Set character code page.
        
        Args:
            name: Code page name (e.g., "UTF-8", "PC437", "PC850")
            
        Returns:
            Self for method chaining
        """
        assert name, "Code page name cannot be empty"
        self._commands.append(f'CODEPAGE {name}')
        return self
    
    def direction(self, direction: int) -> 'TSPLBuilder':
        """Set print direction.
        
        Args:
            direction: 0 for normal, 1 for reverse (bottom to top)
            
        Returns:
            Self for method chaining
        """
        assert direction in (0, 1), "Direction must be 0 or 1"
        self._commands.append(f'DIRECTION {direction}')
        return self
    
    def cls(self) -> 'TSPLBuilder':
        """Clear image buffer.
        
        Returns:
            Self for method chaining
        """
        self._commands.append('CLS')
        return self
    
    def text(self, x: int, y: int, font: str, rotation: int,
             x_multiplication: int, y_multiplication: int,
             content: str) -> 'TSPLBuilder':
        """Add text to label.
        
        Args:
            x: X coordinate in dots from left edge
            y: Y coordinate in dots from bottom edge
            font: Font type ("0"-"9", "A"-"Z", "1"-"8" for Chinese)
            rotation: Rotation angle (0, 90, 180, 270)
            x_multiplication: Horizontal magnification (1-10)
            y_multiplication: Vertical magnification (1-10)
            content: Text content to print
            
        Returns:
            Self for method chaining
        """
        assert x >= 0, "X coordinate must be non-negative"
        assert y >= 0, "Y coordinate must be non-negative"
        assert rotation in (0, 90, 180, 270), "Rotation must be 0, 90, 180, or 270"
        assert 1 <= x_multiplication <= 10, "X multiplication must be 1-10"
        assert 1 <= y_multiplication <= 10, "Y multiplication must be 1-10"
        
        # Escape quotes in content
        escaped_content = content.replace('"', '\\"')
        self._commands.append(
            f'TEXT {x},{y},"{font}",{rotation},{x_multiplication},{y_multiplication},"{escaped_content}"'
        )
        return self
    
    def barcode(self, x: int, y: int, code_type: str, height: int,
                human_readable: int, rotation: int,
                narrow_bar: int, wide_bar: int,
                content: str) -> 'TSPLBuilder':
        """Add barcode to label.
        
        Args:
            x: X coordinate in dots from left edge
            y: Y coordinate in dots from bottom edge
            code_type: Barcode type ("128" for Code 128, "39" for Code 39, etc.)
            height: Barcode height in dots
            human_readable: 1 to show human-readable text below barcode, 0 otherwise
            rotation: Rotation angle (0, 90, 180, 270)
            narrow_bar: Narrow bar width in dots (typically 2 for 203 DPI)
            wide_bar: Wide bar width in dots (typically 3-4 for 203 DPI)
            content: Barcode data
            
        Returns:
            Self for method chaining
        """
        assert x >= 0, "X coordinate must be non-negative"
        assert y >= 0, "Y coordinate must be non-negative"
        assert height > 0, "Barcode height must be positive"
        assert human_readable in (0, 1), "Human readable must be 0 or 1"
        assert rotation in (0, 90, 180, 270), "Rotation must be 0, 90, 180, or 270"
        assert narrow_bar > 0, "Narrow bar must be positive"
        assert wide_bar >= narrow_bar, "Wide bar must be >= narrow bar"
        assert content, "Barcode content cannot be empty"
        
        # Escape quotes in content
        escaped_content = content.replace('"', '\\"')
        self._commands.append(
            f'BARCODE {x},{y},"{code_type}",{height},{human_readable},'
            f'{rotation},{narrow_bar},{wide_bar},"{escaped_content}"'
        )
        return self
    
    def line(self, x_start: int, y_start: int, x_end: int, y_end: int,
             thickness: int) -> 'TSPLBuilder':
        """Draw a line.
        
        Args:
            x_start: Starting X coordinate in dots
            y_start: Starting Y coordinate in dots
            x_end: Ending X coordinate in dots
            y_end: Ending Y coordinate in dots
            thickness: Line thickness in dots
            
        Returns:
            Self for method chaining
        """
        assert thickness > 0, "Thickness must be positive"
        self._commands.append(
            f'LINE {x_start},{y_start},{x_end},{y_end},{thickness}'
        )
        return self
    
    def box(self, x_start: int, y_start: int, x_end: int, y_end: int,
            thickness: int) -> 'TSPLBuilder':
        """Draw a rectangular box.
        
        Args:
            x_start: Top-left X coordinate in dots
            y_start: Top-left Y coordinate in dots
            x_end: Bottom-right X coordinate in dots
            y_end: Bottom-right Y coordinate in dots
            thickness: Border thickness in dots
            
        Returns:
            Self for method chaining
        """
        assert thickness > 0, "Thickness must be positive"
        self._commands.append(
            f'BOX {x_start},{y_start},{x_end},{y_end},{thickness}'
        )
        return self
    
    def image(self, x: int, y: int, mode: str, width: int, height: int,
              image_data: bytes) -> 'TSPLBuilder':
        """Add bitmap image to label.
        
        Args:
            x: X coordinate in dots from left edge
            y: Y coordinate in dots from bottom edge
            mode: Image mode ("B" for black/white, "GRB" for grayscale)
            width: Image width in dots
            height: Image height in dots
            image_data: Raw bitmap data (already converted to TSPL format)
            
        Returns:
            Self for method chaining
        """
        assert x >= 0, "X coordinate must be non-negative"
        assert y >= 0, "Y coordinate must be non-negative"
        assert width > 0, "Width must be positive"
        assert height > 0, "Height must be positive"
        assert mode in ("B", "GRB"), "Mode must be B or GRB"
        assert len(image_data) == (width * height + 7) // 8, \
            "Image data size mismatch"
        
        # Convert image data to hex string for TSPL
        hex_data = image_data.hex().upper()
        self._commands.append(
            f'PUTIMAGE {x},{y},{mode},{width},{height},{hex_data}'
        )
        return self
    
    def print_label(self, copies: int = 1, copy_offset: int = 0) -> 'TSPLBuilder':
        """Add print command.
        
        Args:
            copies: Number of copies to print (default 1)
            copy_offset: Offset between copies in dots (default 0)
            
        Returns:
            Self for method chaining
        """
        assert copies > 0, "Copies must be positive"
        assert copy_offset >= 0, "Copy offset must be non-negative"
        
        if copy_offset > 0:
            self._commands.append(f'PRINT {copies},{copy_offset}')
        else:
            self._commands.append(f'PRINT {copies}')
        return self
    
    def end(self) -> 'TSPLBuilder':
        """Add END command to finalize label definition.
        
        Returns:
            Self for method chaining
        """
        self._commands.append('END')
        return self
    
    def build(self) -> str:
        """Build final TSPL command string.
        
        Returns:
            Complete TSPL command string ready to send to printer
        """
        return '\n'.join(self._commands)
    
    def reset(self) -> 'TSPLBuilder':
        """Reset builder to initial state with header commands.
        
        Returns:
            Self for method chaining
        """
        self._commands.clear()
        self.size(self._width_mm, self._height_mm)
        self.gap(2, 0)
        self.codepage("UTF-8")
        self.direction(1)
        self.cls()
        return self


def generate_garment_sticker(
    shop_name: str,
    barcode_data: str,
    serial: str,
    size: str,
    price_cents: int,
    secret_code: str,
    product_name: str,
    width_mm: int = 28,
    height_mm: int = 19
) -> str:
    """Generate TSPL commands for a garment sticker label.
    
    This function creates a standardized sticker layout suitable for
    garment retail, with shop name, barcode, serial number, size,
    price, secret code, and product name.
    
    Args:
        shop_name: Name of the shop (max 16 characters recommended)
        barcode_data: Data to encode in Code 128 barcode
        serial: Serial number for display
        size: Garment size (S, M, L, XL, etc.)
        price_cents: Price in cents (e.g., 220050 for Rs. 2,200.50)
        secret_code: Encoded purchase price using secret mapping
        product_name: Product description (max 20 characters recommended)
        width_mm: Sticker width in millimeters (default 28)
        height_mm: Sticker height in millimeters (default 19)
        
    Returns:
        Complete TSPL command string for printing
        
    Example:
        >>> tspl = generate_garment_sticker(
        ...     shop_name="SHOUKAT SONS",
        ...     barcode_data="SSG001-M-BLU",
        ...     serial="0001",
        ...     size="M",
        ...     price_cents=220000,
        ...     secret_code="RKML",
        ...     product_name="Cotton Shirt"
        ... )
    """
    assert shop_name, "Shop name cannot be empty"
    assert barcode_data, "Barcode data cannot be empty"
    assert serial, "Serial cannot be empty"
    assert size, "Size cannot be empty"
    assert price_cents > 0, "Price must be positive"
    assert secret_code, "Secret code cannot be empty"
    assert product_name, "Product name cannot be empty"
    
    dpmm = TSPLBuilder.DPMM
    
    builder = TSPLBuilder(width_mm, height_mm, gap_mm=2)
    
    # Shop name (centered at top, small font)
    # Position: x=14mm (112 dots), y=2mm (16 dots)
    builder.text(
        x=14 * dpmm,
        y=2 * dpmm,
        font="2",
        rotation=0,
        x_multiplication=1,
        y_multiplication=1,
        content=shop_name[:16]
    )
    
    # Barcode (Code 128, centered, 10mm height)
    # Position: x=1.5mm (12 dots), y=4mm (32 dots)
    builder.barcode(
        x=1 * dpmm,
        y=4 * dpmm,
        code_type="128",
        height=10 * dpmm,
        human_readable=1,
        rotation=0,
        narrow_bar=2,
        wide_bar=3,
        content=barcode_data
    )
    
    # Serial number (below barcode, centered)
    # Position: x=14mm (112 dots), y=12.5mm (100 dots)
    builder.text(
        x=14 * dpmm,
        y=12.5 * dpmm,
        font="3",
        rotation=0,
        x_multiplication=1,
        y_multiplication=1,
        content=f"SN: {serial}"
    )
    
    # Size (left side)
    # Position: x=2mm (16 dots), y=16mm (128 dots)
    builder.text(
        x=2 * dpmm,
        y=16 * dpmm,
        font="2",
        rotation=0,
        x_multiplication=1,
        y_multiplication=1,
        content=f"Sz:{size}"
    )
    
    # Price (center)
    # Position: x=14mm (112 dots), y=16mm (128 dots)
    price_rupees = price_cents // 100
    builder.text(
        x=14 * dpmm,
        y=16 * dpmm,
        font="2",
        rotation=0,
        x_multiplication=1,
        y_multiplication=1,
        content=f"Rs.{price_rupees}"
    )
    
    # Secret code (right side)
    # Position: x=26mm (208 dots), y=16mm (128 dots)
    builder.text(
        x=26 * dpmm,
        y=16 * dpmm,
        font="2",
        rotation=0,
        x_multiplication=1,
        y_multiplication=1,
        content=secret_code
    )
    
    # Product name (bottom, centered, tiny font)
    # Position: x=14mm (112 dots), y=18mm (144 dots)
    builder.text(
        x=14 * dpmm,
        y=18 * dpmm,
        font="1",
        rotation=0,
        x_multiplication=1,
        y_multiplication=1,
        content=product_name[:20]
    )
    
    builder.print_label(1).end()
    return builder.build()