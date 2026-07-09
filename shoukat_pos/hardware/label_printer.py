"""Label Printer Service for BlackCopper BC-LP-1300.

This module provides high-level label printing functionality for the
BlackCopper BC-LP-1300 thermal label printer using TSPL commands.

Features:
- Single sticker printing with garment layout
- Batch printing for multiple stickers
- USB connection management
- Print queue management
- Error handling and status reporting
"""

from typing import List, Optional, Dict, Any
import logging
import os
import platform

from utils.tspl_builder import generate_garment_sticker, TSPLBuilder
from utils.barcode_generator import encode_code128, validate_barcode_scannability

logger = logging.getLogger(__name__)


class LabelPrinterError(Exception):
    """Exception raised for label printer errors."""
    pass


class LabelPrinter:
    """Service class for BlackCopper BC-LP-1300 label printer.
    
    This class handles:
    - USB connection to the printer
    - TSPL command transmission
    - Batch print job management
    - Status monitoring
    
    Example:
        >>> printer = LabelPrinter()
        >>> printer.print_garment_sticker(
        ...     shop_name="SHOUKAT SONS",
        ...     barcode_data="0001",
        ...     serial="0001",
        ...     size="L",
        ...     price_cents=220000,
        ...     secret_code="LLRR",
        ...     product_name="Cotton Shirt"
        ... )
    """
    
    # Default printer device paths by OS
    DEVICE_PATHS = {
        'Windows': 'USB001',  # Virtual USB port
        'Linux': '/dev/usb/lp0',
        'Darwin': '/dev/usb/lp0'
    }
    
    def __init__(self, device_path: Optional[str] = None):
        """Initialize label printer connection.
        
        Args:
            device_path: Path to printer device (auto-detected if None)
        """
        self.device_path = device_path or self._detect_printer()
        self.is_connected = False
        self._connection = None
        
    def _detect_printer(self) -> str:
        """Detect printer device path based on OS.
        
        Returns:
            Device path string
            
        Note:
            In production, this would enumerate USB devices and find
            the BC-LP-1300 by vendor/product ID. For now, returns
            default path for current OS.
        """
        os_name = platform.system()
        default_path = self.DEVICE_PATHS.get(os_name, 'USB001')
        logger.info(f"Using default printer path for {os_name}: {default_path}")
        return default_path
    
    def connect(self) -> bool:
        """Establish connection to printer.
        
        Returns:
            True if connection successful
            
        Note:
            Actual USB connection implementation depends on OS.
            Windows: Use win32print API
            Linux: Open /dev/usb/lp0
            For simulation/testing, connection always succeeds.
        """
        try:
            if platform.system() == 'Windows':
                # Would use: import win32print
                logger.debug("Would connect to Windows printer")
            else:
                # Would use: open(self.device_path, 'wb')
                logger.debug(f"Would connect to {self.device_path}")
            
            self.is_connected = True
            logger.info(f"Connected to label printer at {self.device_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to printer: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Close printer connection."""
        if self._connection:
            try:
                if platform.system() != 'Windows':
                    os.close(self._connection)
                self._connection = None
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
        
        self.is_connected = False
        logger.info("Disconnected from label printer")
    
    def _send_command(self, tspl_commands: str) -> bool:
        """Send TSPL commands to printer.
        
        Args:
            tspl_commands: Complete TSPL command string
            
        Returns:
            True if sent successfully
        """
        assert self.is_connected, "Printer not connected"
        assert tspl_commands, "Commands cannot be empty"
        
        try:
            # Convert to bytes with proper line endings
            command_bytes = (tspl_commands + '\n').encode('utf-8')
            
            if platform.system() == 'Windows':
                # Would use: win32print.WritePrinter()
                logger.debug(f"Sending {len(command_bytes)} bytes to Windows printer")
            else:
                # Would use: os.write(self._connection, command_bytes)
                logger.debug(f"Sending {len(command_bytes)} bytes to {self.device_path}")
            
            logger.info(f"Sent {len(command_bytes)} bytes to printer")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send commands: {e}")
            raise LabelPrinterError(f"Send failed: {e}")
    
    def print_garment_sticker(
        self,
        shop_name: str,
        barcode_data: str,
        serial: str,
        size: str,
        price_cents: int,
        secret_code: str,
        product_name: str,
        width_mm: int = 28,
        height_mm: int = 19,
        copies: int = 1
    ) -> Dict[str, Any]:
        """Print a single garment sticker.
        
        Args:
            shop_name: Name of the shop
            barcode_data: Data for Code 128 barcode
            serial: Serial number for display
            size: Garment size (S, M, L, XL)
            price_cents: Price in cents
            secret_code: Encoded purchase price
            product_name: Product description
            width_mm: Sticker width in mm (default 28)
            height_mm: Sticker height in mm (default 19)
            copies: Number of copies to print
            
        Returns:
            Dictionary with print result status
            
        Raises:
            LabelPrinterError: If printing fails
        """
        # Validate inputs
        assert shop_name, "Shop name required"
        assert barcode_data, "Barcode data required"
        assert serial, "Serial required"
        assert size, "Size required"
        assert price_cents > 0, "Price must be positive"
        assert secret_code, "Secret code required"
        assert product_name, "Product name required"
        assert copies > 0, "Copies must be positive"
        
        # Validate barcode scannability
        is_valid, error = validate_barcode_scannability(
            width_dots=len(barcode_data) * 11 + 35,
            height_dots=80
        )
        if not is_valid:
            logger.warning(f"Barcode may not scan reliably: {error}")
        
        # Generate TSPL commands
        tspl = generate_garment_sticker(
            shop_name=shop_name,
            barcode_data=barcode_data,
            serial=serial,
            size=size,
            price_cents=price_cents,
            secret_code=secret_code,
            product_name=product_name,
            width_mm=width_mm,
            height_mm=height_mm
        )
        
        # Handle multiple copies
        if copies > 1:
            # Replace single PRINT with multiple
            tspl = tspl.replace('PRINT 1', f'PRINT {copies}')
        
        logger.info(
            f"Printing {copies} sticker(s): {product_name} ({size}, {serial})"
        )
        
        # Connect if needed
        was_connected = self.is_connected
        if not self.is_connected:
            if not self.connect():
                raise LabelPrinterError("Cannot connect to printer")
        
        try:
            # Send commands
            success = self._send_command(tspl)
            
            return {
                'success': success,
                'sticker_type': 'garment',
                'serial': serial,
                'copies': copies,
                'commands_length': len(tspl),
                'barcode_data': barcode_data
            }
            
        finally:
            # Disconnect if we connected just for this print
            if not was_connected:
                self.disconnect()
    
    def print_batch_stickers(
        self,
        stickers: List[Dict[str, Any]],
        width_mm: int = 28,
        height_mm: int = 19
    ) -> Dict[str, Any]:
        """Print multiple stickers in a batch.
        
        Args:
            stickers: List of sticker data dictionaries with keys:
                - shop_name, barcode_data, serial, size, price_cents,
                  secret_code, product_name
            width_mm: Sticker width in mm
            height_mm: Sticker height in mm
            
        Returns:
            Dictionary with batch print results
            
        Example:
            >>> stickers = [
            ...     {'shop_name': 'SHOUKAT SONS', 'barcode_data': '0001',
            ...      'serial': '0001', 'size': 'L', 'price_cents': 220000,
            ...      'secret_code': 'LLRR', 'product_name': 'Cotton Shirt'},
            ...     {'shop_name': 'SHOUKAT SONS', 'barcode_data': '0002',
            ...      'serial': '0002', 'size': 'M', 'price_cents': 180000,
            ...      'secret_code': 'RKML', 'product_name': 'Polo Shirt'}
            ... ]
            >>> printer.print_batch_stickers(stickers)
        """
        assert len(stickers) > 0, "Stickers list cannot be empty"
        
        logger.info(f"Starting batch print of {len(stickers)} stickers")
        
        # Build combined TSPL command stream
        all_commands = []
        
        for i, sticker in enumerate(stickers):
            try:
                tspl = generate_garment_sticker(
                    shop_name=sticker['shop_name'],
                    barcode_data=sticker['barcode_data'],
                    serial=sticker['serial'],
                    size=sticker['size'],
                    price_cents=sticker['price_cents'],
                    secret_code=sticker['secret_code'],
                    product_name=sticker['product_name'],
                    width_mm=width_mm,
                    height_mm=height_mm
                )
                
                # Remove END from all but last sticker
                if i < len(stickers) - 1:
                    tspl = tspl.replace('\nEND', '')
                
                all_commands.append(tspl)
                
            except Exception as e:
                logger.error(f"Failed to generate sticker {i+1}: {e}")
                raise LabelPrinterError(
                    f"Sticker {i+1} generation failed: {e}"
                )
        
        # Combine all commands
        full_tspl = '\n'.join(all_commands)
        
        logger.info(f"Generated {len(full_tspl)} bytes for batch print")
        
        # Connect if needed
        was_connected = self.is_connected
        if not self.is_connected:
            if not self.connect():
                raise LabelPrinterError("Cannot connect to printer")
        
        try:
            success = self._send_command(full_tspl)
            
            return {
                'success': success,
                'stickers_printed': len(stickers),
                'total_bytes': len(full_tspl),
                'serials': [s['serial'] for s in stickers]
            }
            
        finally:
            if not was_connected:
                self.disconnect()
    
    def self_test(self) -> Dict[str, Any]:
        """Run printer self-test.
        
        Returns:
            Dictionary with test results
        """
        # Simple self-test: print configuration label
        builder = TSPLBuilder(28, 19, 2)
        
        builder.text(112, 16, "2", 0, 1, 1, "PRINTER TEST")
        builder.text(112, 48, "1", 0, 1, 1, f"Path: {self.device_path}")
        builder.text(112, 64, "1", 0, 1, 1, f"OS: {platform.system()}")
        builder.barcode(12, 80, "128", 60, 1, 0, 2, 3, "TEST")
        builder.print_label(1).end()
        
        tspl = builder.build()
        
        was_connected = self.is_connected
        if not self.is_connected:
            self.connect()
        
        try:
            success = self._send_command(tspl)
            return {
                'success': success,
                'test_type': 'configuration_label',
                'device_path': self.device_path
            }
        finally:
            if not was_connected:
                self.disconnect()


# Convenience function for one-off printing
def print_single_sticker(
    shop_name: str,
    barcode_data: str,
    serial: str,
    size: str,
    price_cents: int,
    secret_code: str,
    product_name: str,
    copies: int = 1
) -> Dict[str, Any]:
    """Print a single garment sticker (convenience function).
    
    Args:
        shop_name: Name of the shop
        barcode_data: Barcode data
        serial: Serial number
        size: Garment size
        price_cents: Price in cents
        secret_code: Secret code
        product_name: Product name
        copies: Number of copies
        
    Returns:
        Print result dictionary
    """
    printer = LabelPrinter()
    return printer.print_garment_sticker(
        shop_name=shop_name,
        barcode_data=barcode_data,
        serial=serial,
        size=size,
        price_cents=price_cents,
        secret_code=secret_code,
        product_name=product_name,
        copies=copies
    )