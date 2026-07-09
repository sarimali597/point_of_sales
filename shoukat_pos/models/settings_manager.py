"""
Shoukat Sons Garments POS - Settings Manager

This module provides a singleton manager for loading, validating, saving, and
migrating application settings stored in SQLite. It ensures type safety and
data integrity across application restarts.
"""
import sqlite3
import json
import re
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

from models.settings import (
    SettingsData, ShopDetails, PrinterSettings, TaxSettings,
    InventorySettings, SalesSettings, LoyaltySettings, SecuritySettings,
    BackupSettings, BarcodeSettings, SecretCodeSettings, DisplaySettings
)


# Current schema version - increment when adding new fields
CURRENT_SCHEMA_VERSION = 3


class SettingsValidationError(ValueError):
    """Raised when settings validation fails."""
    pass


class SettingsManager:
    """
    Singleton manager for application settings.
    
    Handles loading, validation, saving, and migration of settings stored
    in SQLite. Uses lazy loading to cache settings in memory after first load.
    """
    
    _instance: Optional['SettingsManager'] = None
    _settings_cache: Optional[SettingsData] = None
    
    def __new__(cls) -> 'SettingsManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.db_path = self._get_db_path()
        self._ensure_settings_table()
        self._initialized = True
    
    def _get_db_path(self) -> Path:
        """Get database path from config or default location."""
        try:
            from config import DATABASE_PATH
            return Path(DATABASE_PATH)
        except ImportError:
            return Path(__file__).parent.parent / "data" / "shoukat_pos.db"
    
    def _ensure_settings_table(self) -> None:
        """Create settings table if it doesn't exist, or migrate old schema."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Check if old key-value schema exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='settings'
            """)
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check column structure
                cursor.execute("PRAGMA table_info(settings)")
                columns = {row[1] for row in cursor.fetchall()}
                
                if 'key' in columns and 'value' in columns:
                    # Old key-value schema exists - migrate it
                    self._migrate_from_key_value(conn)
                    return
            
            # Create new JSON-based schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    schema_version INTEGER DEFAULT 1,
                    settings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    def _migrate_from_key_value(self, conn: sqlite3.Connection) -> None:
        """Migrate from old key-value settings to new JSON schema."""
        cursor = conn.cursor()
        
        # Read all key-value settings
        cursor.execute("SELECT key, value FROM settings")
        kv_settings = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Build new SettingsData from old values
        shop_name = kv_settings.get('shop_name', 'SHOUKAT SONS GARMENTS')
        shop_address = kv_settings.get('shop_address', '')
        shop_phone = kv_settings.get('shop_phone', '')
        gstin = kv_settings.get('gstin', '')
        tax_rate = float(kv_settings.get('tax_rate', '0.0'))
        
        settings = SettingsData(
            shop=ShopDetails(
                name=shop_name,
                address=shop_address,
                phone=shop_phone,
                gstin=gstin,
            ),
            tax=TaxSettings(
                tax_enabled=tax_rate > 0,
                tax_rate=tax_rate,
            ),
        )
        
        # Drop old table and create new one
        cursor.execute("DROP TABLE settings")
        cursor.execute("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                schema_version INTEGER DEFAULT 1,
                settings_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Insert migrated settings
        settings_json = json.dumps(settings.to_dict())
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO settings (id, schema_version, settings_json, created_at, updated_at)
            VALUES (1, 1, ?, ?, ?)
        """, (settings_json, now, now))
        
        conn.commit()
    
    def load(self) -> SettingsData:
        """
        Load settings from database with lazy caching.
        
        Returns:
            SettingsData: Current application settings
            
        Raises:
            FileNotFoundError: If database doesn't exist
        """
        if self._settings_cache is not None:
            return self._settings_cache
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT settings_json FROM settings WHERE id = 1")
            row = cursor.fetchone()
            
            if row is None:
                # No settings exist, create defaults
                settings = SettingsData()
                self.save(settings)
                return settings
            
            settings_dict = json.loads(row[0])
            settings = SettingsData.from_dict(settings_dict)
            
            # Apply migrations if needed
            if settings.schema_version < CURRENT_SCHEMA_VERSION:
                settings = self._migrate_settings(settings)
            
            self._settings_cache = settings
            return settings
            
        finally:
            conn.close()
    
    def save(self, settings: SettingsData, validate: bool = True) -> None:
        """
        Save settings to database with validation.
        
        Args:
            settings: SettingsData to save
            validate: Whether to validate before saving (default True)
            
        Raises:
            SettingsValidationError: If validation fails
        """
        if validate:
            self.validate(settings)
        
        # Update timestamp
        settings.updated_at = datetime.now().isoformat()
        
        # Ensure schema version is current
        settings.schema_version = CURRENT_SCHEMA_VERSION
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Check if settings exist
            cursor.execute("SELECT id FROM settings WHERE id = 1")
            exists = cursor.fetchone() is not None
            
            settings_json = json.dumps(settings.to_dict())
            now = datetime.now().isoformat()
            
            if exists:
                cursor.execute("""
                    UPDATE settings 
                    SET settings_json = ?, updated_at = ?, schema_version = ?
                    WHERE id = 1
                """, (settings_json, now, CURRENT_SCHEMA_VERSION))
            else:
                cursor.execute("""
                    INSERT INTO settings (id, settings_json, created_at, updated_at, schema_version)
                    VALUES (1, ?, ?, ?, ?)
                """, (settings_json, now, now, CURRENT_SCHEMA_VERSION))
            
            conn.commit()
            
            # Update cache
            self._settings_cache = settings
            
        finally:
            conn.close()
    
    def validate(self, settings: SettingsData) -> None:
        """
        Validate settings data for correctness.
        
        Args:
            settings: SettingsData to validate
            
        Raises:
            SettingsValidationError: If any setting is invalid
        """
        errors = []
        
        # Validate shop details
        if settings.shop.phone and not self._validate_phone(settings.shop.phone):
            errors.append(f"Invalid phone format: {settings.shop.phone}")
        
        if settings.shop.email and not self._validate_email(settings.shop.email):
            errors.append(f"Invalid email format: {settings.shop.email}")
        
        # Validate printer settings
        if settings.printer.printer_dpi <= 0:
            errors.append(f"Printer DPI must be positive: {settings.printer.printer_dpi}")
        
        if settings.printer.gap_mm < 0:
            errors.append(f"Gap must be non-negative: {settings.printer.gap_mm}")
        
        if settings.printer.copies_per_item < 1:
            errors.append(f"Copies per item must be >= 1: {settings.printer.copies_per_item}")
        
        if settings.printer.copies_receipt < 1:
            errors.append(f"Copies receipt must be >= 1: {settings.printer.copies_receipt}")
        
        # Validate tax settings
        if not 0 <= settings.tax.tax_rate <= 100:
            errors.append(f"Tax rate must be 0-100: {settings.tax.tax_rate}")
        
        # Validate inventory settings
        if settings.inventory.default_reorder_point < 0:
            errors.append(f"Reorder point must be non-negative")
        
        if settings.inventory.low_stock_threshold < 0:
            errors.append(f"Low stock threshold must be non-negative")
        
        if settings.inventory.medium_stock_threshold < settings.inventory.low_stock_threshold:
            errors.append("Medium threshold must be >= low threshold")
        
        # Validate sales settings
        if settings.sales.decimal_places < 0 or settings.sales.decimal_places > 4:
            errors.append(f"Decimal places must be 0-4: {settings.sales.decimal_places}")
        
        if settings.sales.default_credit_limit < 0:
            errors.append(f"Credit limit must be non-negative")
        
        if not 0 <= settings.sales.max_discount_percent <= 100:
            errors.append(f"Max discount must be 0-100: {settings.sales.max_discount_percent}")
        
        if settings.sales.invoice_sequence_length < 1:
            errors.append(f"Invoice sequence length must be >= 1")
        
        # Validate loyalty settings
        if settings.loyalty.points_per_currency < 0:
            errors.append(f"Points per currency must be non-negative")
        
        if settings.loyalty.redemption_rate < 0:
            errors.append(f"Redemption rate must be non-negative")
        
        if settings.loyalty.min_points_redeem < 0:
            errors.append(f"Min points redeem must be non-negative")
        
        # Validate security settings
        if settings.security.session_timeout_minutes < 1:
            errors.append(f"Session timeout must be >= 1 minute")
        
        if settings.security.max_login_attempts < 1:
            errors.append(f"Max login attempts must be >= 1")
        
        # Validate backup settings
        if settings.backup.backup_retention_days < 1:
            errors.append(f"Backup retention must be >= 1 day")
        
        if settings.backup.backup_frequency not in ["daily", "weekly", "monthly"]:
            errors.append(f"Invalid backup frequency: {settings.backup.backup_frequency}")
        
        # Validate barcode settings
        valid_font_sizes = [6, 12, 18, 24, 30, 36]
        if settings.barcode.barcode_font_size not in valid_font_sizes:
            errors.append(f"Barcode font size must be one of {valid_font_sizes}: {settings.barcode.barcode_font_size}")
        
        if settings.barcode.barcode_height_mm <= 0:
            errors.append(f"Barcode height must be positive")
        
        if settings.barcode.quiet_zone_mm < 0:
            errors.append(f"Quiet zone must be non-negative")
        
        # Validate secret code settings
        if len(settings.secret_code.code_map) != 10:
            errors.append(f"Secret code map must have exactly 10 entries")
        
        # Validate display settings
        if settings.display.theme not in ["dark", "light", "blue"]:
            errors.append(f"Invalid theme: {settings.display.theme}")
        
        if settings.display.language not in ["en", "ur", "pk"]:
            errors.append(f"Unsupported language: {settings.display.language}")
        
        if errors:
            raise SettingsValidationError("; ".join(errors))
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format (Pakistan format)."""
        # Accept formats: +92XXXXXXXXXX, 03XXXXXXXXX, XXXXXXXXX, or placeholder with X
        if not phone or phone == "03XX-XXXXXXX":
            return True  # Allow empty or placeholder
        
        # Remove common separators
        cleaned = phone.replace("-", "").replace(" ", "")
        
        # Check if it's all X's (placeholder)
        if cleaned.replace("X", "").replace("+", "").replace("0", "") == "":
            return True
        
        # Validate actual phone pattern
        pattern = r'^(\+92|0)?3\d{9}$'
        return bool(re.match(pattern, cleaned))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _migrate_settings(self, settings: SettingsData) -> SettingsData:
        """
        Migrate settings from older schema versions to current.
        
        Args:
            settings: SettingsData with old schema version
            
        Returns:
            SettingsData: Migrated settings with current schema version
        """
        current_version = settings.schema_version
        
        # Migration v1 -> v2: Add loyalty settings
        if current_version == 1:
            # Loyalty settings didn't exist, use defaults
            settings.loyalty = LoyaltySettings()
            current_version = 2
        
        # Migration v2 -> v3: Add barcode settings
        if current_version == 2:
            # Barcode settings didn't exist, use defaults
            settings.barcode = BarcodeSettings()
            current_version = 3
        
        # Future migrations would go here
        # if current_version == 3:
        #     ...
        #     current_version = 4
        
        settings.schema_version = current_version
        return settings
    
    def reset_to_defaults(self) -> SettingsData:
        """
        Reset all settings to factory defaults.
        
        Returns:
            SettingsData: Default settings
        """
        self._settings_cache = None
        defaults = SettingsData()
        self.save(defaults)
        return defaults
    
    def update_field(self, category: str, field: str, value: Any) -> None:
        """
        Update a single settings field.
        
        Args:
            category: Settings category (e.g., 'shop', 'printer')
            field: Field name within category
            value: New value
            
        Raises:
            AttributeError: If category or field doesn't exist
        """
        settings = self.load()
        
        if not hasattr(settings, category):
            raise AttributeError(f"Unknown category: {category}")
        
        category_obj = getattr(settings, category)
        if not hasattr(category_obj, field):
            raise AttributeError(f"Unknown field: {field} in {category}")
        
        setattr(category_obj, field, value)
        self.save(settings)
    
    def clear_cache(self) -> None:
        """Clear the settings cache to force reload from database."""
        self._settings_cache = None
    
    def get_category(self, category: str) -> Any:
        """
        Get a specific settings category.
        
        Args:
            category: Category name (e.g., 'shop', 'printer')
            
        Returns:
            The settings category object
        """
        settings = self.load()
        if not hasattr(settings, category):
            raise AttributeError(f"Unknown category: {category}")
        return getattr(settings, category)


# Convenience functions
def get_settings() -> SettingsData:
    """Get current application settings."""
    manager = SettingsManager()
    return manager.load()


def save_settings(settings: SettingsData) -> None:
    """Save application settings."""
    manager = SettingsManager()
    manager.save(settings)


def update_setting(category: str, field: str, value: Any) -> None:
    """Update a single setting field."""
    manager = SettingsManager()
    manager.update_field(category, field, value)
