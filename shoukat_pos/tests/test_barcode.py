"""Tests for Barcode Generator and TSPL Builder.

This module contains comprehensive tests for:
- Code 128 barcode generation at 203 DPI
- TSPL command building for BlackCopper BC-LP-1300
- Garment sticker layout generation
- Barcode scannability validation
"""

import pytest
from utils.barcode_generator import (
    calculate_barcode_dimensions,
    encode_code128,
    generate_barcode_tspl,
    validate_barcode_scannability,
    VALID_POINT_SIZES,
    DPMM
)
from utils.tspl_builder import (
    TSPLBuilder,
    generate_garment_sticker
)


class TestBarcodeDimensions:
    """Test barcode dimension calculations."""
    
    def test_valid_point_size_24(self):
        """Test dimension calculation with standard 24pt size."""
        width, height, quiet_zone = calculate_barcode_dimensions(
            data_length=4,
            point_size=24
        )
        
        # 4 digits: 35 + (4 * 11) = 79 modules
        assert width == 79
        assert height >= 80  # Minimum height
        assert quiet_zone == 16
    
    def test_valid_point_size_12(self):
        """Test dimension calculation with small 12pt size."""
        width, height, quiet_zone = calculate_barcode_dimensions(
            data_length=8,
            point_size=12
        )
        
        # 8 chars: 35 + (8 * 11) = 123 modules
        assert width == 123
        assert height >= 80
    
    def test_invalid_point_size_raises(self):
        """Test that invalid point sizes raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            calculate_barcode_dimensions(data_length=4, point_size=15)
        
        assert "Invalid point size" in str(exc_info.value)
        assert "Valid sizes" in str(exc_info.value)
    
    def test_long_data(self):
        """Test dimension calculation for long barcode data."""
        width, height, quiet_zone = calculate_barcode_dimensions(
            data_length=20,
            point_size=24
        )
        
        # 20 chars: 35 + (20 * 11) = 255 modules
        assert width == 255


class TestCode128Encoding:
    """Test Code 128 encoding validation."""
    
    def test_valid_numeric_data(self):
        """Test encoding of numeric data."""
        result = encode_code128("0001")
        assert result == "0001"
    
    def test_valid_alphanumeric_data(self):
        """Test encoding of alphanumeric data."""
        result = encode_code128("SSG001-M-BLU")
        assert result == "SSG001-M-BLU"
    
    def test_empty_data_raises(self):
        """Test that empty data raises assertion."""
        with pytest.raises(AssertionError):
            encode_code128("")
    
    def test_too_long_data_raises(self):
        """Test that data > 80 chars raises error."""
        with pytest.raises(AssertionError):
            encode_code128("A" * 81)
    
    def test_non_printable_char_raises(self):
        """Test that non-printable characters raise error."""
        with pytest.raises(ValueError):
            encode_code128("test\x00data")


class TestBarcodeTSPLGeneration:
    """Test TSPL barcode command generation."""
    
    def test_basic_barcode_command(self):
        """Test basic barcode command generation."""
        cmd = generate_barcode_tspl("0001", 12, 32)
        
        assert 'BARCODE 12,32,"128",80,1,0,2,3,"0001"' == cmd
    
    def test_custom_height(self):
        """Test barcode with custom height."""
        cmd = generate_barcode_tspl("0001", 12, 32, height_dots=100)
        
        assert '80' not in cmd  # Default height replaced
        assert '100' in cmd
    
    def test_no_human_readable(self):
        """Test barcode without human-readable text."""
        cmd = generate_barcode_tspl("0001", 12, 32, human_readable=False)
        
        assert ',0,' in cmd  # HR flag should be 0
    
    def test_custom_bar_widths(self):
        """Test barcode with custom bar widths."""
        cmd = generate_barcode_tspl(
            "0001", 12, 32, narrow_bar=3, wide_bar=4
        )
        
        assert ',3,4,' in cmd
    
    def test_special_chars_in_data(self):
        """Test barcode with special characters."""
        cmd = generate_barcode_tspl('test"data', 12, 32)
        
        # Quotes should be escaped
        assert '\\"' in cmd
    
    def test_invalid_x_coordinate(self):
        """Test that negative X raises assertion."""
        with pytest.raises(AssertionError):
            generate_barcode_tspl("0001", -1, 32)
    
    def test_invalid_y_coordinate(self):
        """Test that negative Y raises assertion."""
        with pytest.raises(AssertionError):
            generate_barcode_tspl("0001", 12, -1)


class TestBarcodeScannability:
    """Test barcode scannability validation."""
    
    def test_valid_dimensions(self):
        """Test validation of valid barcode dimensions."""
        is_valid, error = validate_barcode_scannability(
            width_dots=100,
            height_dots=80
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_height_too_small(self):
        """Test validation fails when height is too small."""
        is_valid, error = validate_barcode_scannability(
            width_dots=100,
            height_dots=40  # Less than 10mm (80 dots)
        )
        
        assert is_valid is False
        assert "below minimum" in error
    
    def test_width_too_small(self):
        """Test validation fails when width is too small."""
        is_valid, error = validate_barcode_scannability(
            width_dots=30,  # Below absolute minimum
            height_dots=80
        )
        
        assert is_valid is False
        assert "below minimum" in error
    
    def test_bad_aspect_ratio(self):
        """Test validation warns about bad aspect ratio."""
        is_valid, error = validate_barcode_scannability(
            width_dots=200,
            height_dots=80  # Less than 50% of width
        )
        
        assert is_valid is False
        assert "aspect ratio" in error


class TestTSPLBuilder:
    """Test TSPL command builder."""
    
    def test_initialization(self):
        """Test builder initialization with defaults."""
        builder = TSPLBuilder(28, 19)
        
        # Should have header commands
        tspl = builder.build()
        assert 'SIZE 28 mm,19 mm' in tspl
        assert 'GAP 2 mm,0 mm' in tspl
        assert 'CODEPAGE UTF-8' in tspl
        assert 'DIRECTION 1' in tspl
        assert 'CLS' in tspl
    
    def test_custom_gap(self):
        """Test builder with custom gap."""
        builder = TSPLBuilder(28, 19, gap_mm=3)
        
        tspl = builder.build()
        assert 'GAP 3 mm,0 mm' in tspl
    
    def test_text_command(self):
        """Test adding text to label."""
        builder = TSPLBuilder(28, 19)
        builder.text(112, 16, "2", 0, 1, 1, "SHOUKAT SONS")
        
        tspl = builder.build()
        assert 'TEXT 112,16,"2",0,1,1,"SHOUKAT SONS"' in tspl
    
    def test_barcode_command(self):
        """Test adding barcode to label."""
        builder = TSPLBuilder(28, 19)
        builder.barcode(12, 32, "128", 80, 1, 0, 2, 3, "0001")
        
        tspl = builder.build()
        assert 'BARCODE 12,32,"128",80,1,0,2,3,"0001"' in tspl
    
    def test_method_chaining(self):
        """Test that all methods return self for chaining."""
        builder = TSPLBuilder(28, 19)
        result = (builder
            .text(112, 16, "2", 0, 1, 1, "Test")
            .barcode(12, 32, "128", 80, 1, 0, 2, 3, "0001")
            .print_label(1)
            .end())
        
        assert result is builder
    
    def test_complete_label(self):
        """Test complete label generation."""
        builder = TSPLBuilder(28, 19)
        tspl = (builder
            .text(112, 16, "2", 0, 1, 1, "SHOUKAT SONS")
            .barcode(12, 32, "128", 80, 1, 0, 2, 3, "0001")
            .print_label(1)
            .end()
            .build())
        
        # Verify structure
        lines = tspl.split('\n')
        assert lines[0] == 'SIZE 28 mm,19 mm'
        assert lines[-1] == 'END'
        assert 'PRINT 1' in tspl
    
    def test_reset(self):
        """Test builder reset functionality."""
        builder = TSPLBuilder(28, 19)
        builder.text(112, 16, "2", 0, 1, 1, "Test")
        
        builder.reset()
        tspl = builder.build()
        
        # Should only have header, no text
        assert 'TEXT' not in tspl
        assert 'SIZE 28 mm,19 mm' in tspl
    
    def test_invalid_font_rotation(self):
        """Test that invalid rotation raises assertion."""
        builder = TSPLBuilder(28, 19)
        
        with pytest.raises(AssertionError):
            builder.text(112, 16, "2", 45, 1, 1, "Test")


class TestGarmentStickerGeneration:
    """Test complete garment sticker generation."""
    
    def test_standard_sticker(self):
        """Test generation of standard garment sticker."""
        tspl = generate_garment_sticker(
            shop_name="SHOUKAT SONS",
            barcode_data="0001",
            serial="0001",
            size="L",
            price_cents=220000,
            secret_code="LLRR",
            product_name="Cotton Shirt"
        )
        
        # Verify all elements present
        assert 'SIZE 28 mm,19 mm' in tspl
        assert 'SHOUKAT SONS' in tspl
        assert 'BARCODE' in tspl
        assert '"0001"' in tspl
        assert 'SN: 0001' in tspl
        assert 'Sz:L' in tspl
        assert 'Rs.2200' in tspl
        assert 'LLRR' in tspl
        assert 'Cotton Shirt' in tspl
        assert 'PRINT 1' in tspl
        assert 'END' in tspl
    
    def test_price_formatting(self):
        """Test that price is correctly formatted in Rupees."""
        tspl = generate_garment_sticker(
            shop_name="TEST",
            barcode_data="001",
            serial="001",
            size="M",
            price_cents=180050,  # Rs. 1,800.50
            secret_code="TEST",
            product_name="Test"
        )
        
        # Should show rupees (cents // 100)
        assert 'Rs.1800' in tspl
    
    def test_truncated_strings(self):
        """Test that long strings are truncated."""
        tspl = generate_garment_sticker(
            shop_name="VERY LONG SHOP NAME THAT EXCEEDS LIMIT",
            barcode_data="001",
            serial="001",
            size="XL",
            price_cents=100000,
            secret_code="CODE",
            product_name="Very Long Product Name That Is Too Long"
        )
        
        # Shop name limited to 16 chars
        assert 'VERY LONG SHOP N' in tspl
        # Product name limited to 20 chars
        assert 'Very Long Product Na' in tspl
    
    def test_different_sizes(self):
        """Test stickers with different garment sizes."""
        for size in ['S', 'M', 'L', 'XL', 'XXL']:
            tspl = generate_garment_sticker(
                shop_name="SHOP",
                barcode_data="001",
                serial="001",
                size=size,
                price_cents=100000,
                secret_code="CODE",
                product_name="Shirt"
            )
            
            assert f'Sz:{size}' in tspl
    
    def test_custom_dimensions(self):
        """Test sticker with custom dimensions."""
        tspl = generate_garment_sticker(
            shop_name="SHOP",
            barcode_data="001",
            serial="001",
            size="M",
            price_cents=100000,
            secret_code="CODE",
            product_name="Product",
            width_mm=40,
            height_mm=30
        )
        
        assert 'SIZE 40 mm,30 mm' in tspl


class TestIntegration:
    """Integration tests combining barcode and TSPL."""
    
    def test_full_workflow(self):
        """Test complete workflow from data to TSPL."""
        # Generate barcode data
        barcode_data = encode_code128("SSG001")
        
        # Calculate dimensions
        width, height, quiet_zone = calculate_barcode_dimensions(
            data_length=len(barcode_data)
        )
        
        # Validate scannability
        is_valid, error = validate_barcode_scannability(width, height)
        assert is_valid is True
        
        # Generate complete sticker
        tspl = generate_garment_sticker(
            shop_name="SHOUKAT SONS",
            barcode_data=barcode_data,
            serial="001",
            size="L",
            price_cents=250000,
            secret_code="RKML",
            product_name="Premium Cotton"
        )
        
        # Verify output
        assert len(tspl) > 100  # Should be substantial
        assert tspl.endswith('\nEND')
    
    def test_batch_generation(self):
        """Test generating multiple stickers."""
        stickers = []
        for i in range(1, 6):
            tspl = generate_garment_sticker(
                shop_name="SHOUKAT SONS",
                barcode_data=f"{i:04d}",
                serial=f"{i:04d}",
                size="M",
                price_cents=200000,
                secret_code="CODE",
                product_name=f"Product {i}"
            )
            stickers.append(tspl)
        
        # All should be unique
        assert len(set(stickers)) == 5
        
        # All should be valid TSPL
        for tspl in stickers:
            assert 'SIZE 28 mm,19 mm' in tspl
            assert 'END' in tspl