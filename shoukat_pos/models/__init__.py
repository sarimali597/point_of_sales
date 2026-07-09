"""
Shoukat Sons Garments POS - Data Models

This package contains all data models and settings management classes.
"""
from models.settings import (
    SettingsData,
    ShopDetails,
    PrinterSettings,
    TaxSettings,
    InventorySettings,
    SalesSettings,
    LoyaltySettings,
    SecuritySettings,
    BackupSettings,
    BarcodeSettings,
    SecretCodeSettings,
    DisplaySettings,
    ReceiptWidth,
    StickerSize,
)
from models.settings_manager import (
    SettingsManager,
    SettingsValidationError,
    get_settings,
    save_settings,
    update_setting,
    CURRENT_SCHEMA_VERSION,
)

__all__ = [
    # Data models
    "SettingsData",
    "ShopDetails",
    "PrinterSettings",
    "TaxSettings",
    "InventorySettings",
    "SalesSettings",
    "LoyaltySettings",
    "SecuritySettings",
    "BackupSettings",
    "BarcodeSettings",
    "SecretCodeSettings",
    "DisplaySettings",
    "ReceiptWidth",
    "StickerSize",
    # Manager
    "SettingsManager",
    "SettingsValidationError",
    "get_settings",
    "save_settings",
    "update_setting",
    "CURRENT_SCHEMA_VERSION",
]
