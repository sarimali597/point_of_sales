"""
Shoukat Sons Garments POS - Settings Data Models

This module defines the strongly-typed data structures for all application settings,
including printer configurations, shop details, tax rules, and feature flags.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from enum import Enum


class ReceiptWidth(Enum):
    """Receipt paper width options."""
    MM_58 = "58mm"
    MM_80 = "80mm"


class StickerSize(Enum):
    """Label sticker size options."""
    MM_28x19 = "28x19"
    MM_32x25 = "32x25"
    MM_32x19 = "32x19"
    MM_34x24 = "34x24"


@dataclass
class ShopDetails:
    """Shop branding and contact information."""
    name: str = "SHOUKAT SONS GARMENTS"
    address: str = ""
    phone: str = ""
    email: str = ""
    gstin: str = ""  # GST Identification Number
    footer_message: str = "Thank you for your business!"


@dataclass
class PrinterSettings:
    """Thermal printer configuration."""
    # Label printer (BlackCopper BC-LP-1300)
    label_printer_name: str = "BC-LP-1300"
    label_printer_enabled: bool = True
    sticker_size: str = "28x19"  # width x height in mm
    gap_mm: int = 2
    printer_dpi: int = 203
    copies_per_item: int = 1
    
    # Receipt printer (ESC/POS)
    receipt_printer_name: str = "ESC/POS Thermal"
    receipt_printer_enabled: bool = True
    receipt_width: str = "80mm"
    print_receipt_auto: bool = True
    copies_receipt: int = 1


@dataclass
class TaxSettings:
    """Tax configuration for Pakistan GST/VAT."""
    tax_enabled: bool = False
    tax_rate: float = 0.0  # e.g., 17.0 for 17%
    tax_label: str = "GST"
    inclusive_pricing: bool = False  # Whether prices include tax


@dataclass
class InventorySettings:
    """Inventory management configuration."""
    default_reorder_point: int = 5
    low_stock_threshold: int = 5
    medium_stock_threshold: int = 10
    track_batches: bool = True
    fifo_enabled: bool = True
    allow_negative_stock: bool = False
    quarantine_returns: bool = False  # Return to quarantine instead of immediate restock


@dataclass
class SalesSettings:
    """Sales transaction configuration."""
    currency_symbol: str = "Rs."
    decimal_places: int = 2
    allow_credit_sales: bool = True
    default_credit_limit: float = 10000.0
    allow_partial_payments: bool = True
    allow_discounts: bool = True
    max_discount_percent: float = 20.0
    invoice_prefix: str = "INV"
    invoice_date_format: str = "%Y%m%d"
    invoice_sequence_length: int = 4  # INV-20260709-0001


@dataclass
class LoyaltySettings:
    """Customer loyalty program configuration."""
    loyalty_enabled: bool = False
    points_per_currency: float = 0.01  # 1 point per Rs. 100
    points_label: str = "Points"
    redemption_rate: float = 1.0  # Rs. 1 per point
    min_points_redeem: int = 100
    points_expiry_days: int = 365


@dataclass
class SecuritySettings:
    """Security and access control configuration."""
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    require_password_for_void: bool = True
    require_password_for_refund: bool = True
    audit_logging_enabled: bool = True
    encrypt_backups: bool = True


@dataclass
class BackupSettings:
    """Backup configuration."""
    backup_enabled: bool = True
    backup_frequency: str = "daily"  # daily, weekly, monthly
    backup_time: str = "02:00"  # 2 AM
    backup_retention_days: int = 30
    backup_directory: str = ""  # Empty = default location
    encryption_enabled: bool = True


@dataclass
class BarcodeSettings:
    """Barcode generation configuration."""
    barcode_format: str = "code128"  # code128, ean13, upc
    include_price_in_barcode: bool = False
    barcode_font_size: int = 24  # Valid: 6, 12, 18, 24, 30, 36 at 203 DPI
    barcode_height_mm: int = 10
    quiet_zone_mm: int = 2


@dataclass
class SecretCodeSettings:
    """Secret code mapping for purchase price encoding."""
    enabled: bool = True
    code_map: Dict[str, str] = field(default_factory=lambda: {
        "0": "L",
        "1": "R",
        "2": "K",
        "3": "B",
        "4": "S",
        "5": "M",
        "6": "N",
        "7": "T",
        "8": "H",
        "9": "W",
    })


@dataclass
class DisplaySettings:
    """UI display configuration."""
    theme: str = "dark"  # dark, light, blue
    language: str = "en"
    date_format: str = "%d/%m/%Y"
    time_format: str = "%H:%M"
    show_images: bool = True
    compact_mode: bool = False
    sidebar_collapsed: bool = False


@dataclass
class SettingsData:
    """
    Master settings container combining all setting categories.
    
    This dataclass serves as the single source of truth for all application
    configuration. It is serialized to/from SQLite and validated before saving.
    """
    # Schema version for migration tracking
    schema_version: int = 3
    
    # Setting categories
    shop: ShopDetails = field(default_factory=ShopDetails)
    printer: PrinterSettings = field(default_factory=PrinterSettings)
    tax: TaxSettings = field(default_factory=TaxSettings)
    inventory: InventorySettings = field(default_factory=InventorySettings)
    sales: SalesSettings = field(default_factory=SalesSettings)
    loyalty: LoyaltySettings = field(default_factory=LoyaltySettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    backup: BackupSettings = field(default_factory=BackupSettings)
    barcode: BarcodeSettings = field(default_factory=BarcodeSettings)
    secret_code: SecretCodeSettings = field(default_factory=SecretCodeSettings)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert settings to nested dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SettingsData':
        """Create SettingsData from dictionary, handling missing keys gracefully."""
        if not data:
            return cls()
        
        # Handle nested dataclasses
        nested_classes = {
            'shop': ShopDetails,
            'printer': PrinterSettings,
            'tax': TaxSettings,
            'inventory': InventorySettings,
            'sales': SalesSettings,
            'loyalty': LoyaltySettings,
            'security': SecuritySettings,
            'backup': BackupSettings,
            'barcode': BarcodeSettings,
            'secret_code': SecretCodeSettings,
            'display': DisplaySettings,
        }
        
        clean_data = {}
        for key, value in data.items():
            if key in nested_classes and isinstance(value, dict):
                # Create nested dataclass from dict
                nested_cls = nested_classes[key]
                clean_data[key] = nested_cls(**{
                    k: v for k, v in value.items() 
                    if k in nested_cls.__dataclass_fields__
                })
            elif key in cls.__dataclass_fields__:
                clean_data[key] = value
        
        return cls(**clean_data)
