"""
Shoukat Sons Garments POS - Settings Tests

Comprehensive tests for settings data models, validation, persistence,
and schema migrations.
"""
import pytest
import sqlite3
import json
from pathlib import Path
from datetime import datetime

from models.settings import (
    SettingsData, ShopDetails, PrinterSettings, TaxSettings,
    InventorySettings, SalesSettings, LoyaltySettings, SecuritySettings,
    BackupSettings, BarcodeSettings, SecretCodeSettings, DisplaySettings
)
from models.settings_manager import (
    SettingsManager, SettingsValidationError, 
    get_settings, save_settings, update_setting,
    CURRENT_SCHEMA_VERSION
)


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_pos.db"
    # Initialize with empty database
    conn = sqlite3.connect(str(db_path))
    conn.close()
    return db_path


@pytest.fixture
def settings_manager(temp_db, monkeypatch):
    """Create a SettingsManager with temporary database."""
    # Clear singleton instance
    SettingsManager._instance = None
    SettingsManager._settings_cache = None
    
    # Monkeypatch the database path
    def mock_get_db_path(self):
        return temp_db
    
    monkeypatch.setattr(SettingsManager, '_get_db_path', mock_get_db_path)
    
    manager = SettingsManager()
    return manager


class TestSettingsData:
    """Tests for SettingsData dataclass."""
    
    def test_default_creation(self):
        """Test creating SettingsData with all defaults."""
        settings = SettingsData()
        
        assert settings.schema_version == 3
        assert settings.shop.name == "SHOUKAT SONS GARMENTS"
        assert settings.printer.printer_dpi == 203
        assert settings.tax.tax_rate == 0.0
        assert settings.inventory.default_reorder_point == 5
        assert settings.sales.currency_symbol == "Rs."
        assert settings.loyalty.loyalty_enabled is False
        assert settings.security.audit_logging_enabled is True
        assert settings.backup.encryption_enabled is True
        assert settings.barcode.barcode_font_size == 24
        assert len(settings.secret_code.code_map) == 10
        assert settings.display.theme == "dark"
    
    def test_to_dict(self):
        """Test converting SettingsData to dictionary."""
        settings = SettingsData()
        settings.shop.name = "Test Shop"
        settings.printer.printer_dpi = 300
        
        data = settings.to_dict()
        
        assert isinstance(data, dict)
        assert data['shop']['name'] == "Test Shop"
        assert data['printer']['printer_dpi'] == 300
        assert data['schema_version'] == 3
    
    def test_from_dict(self):
        """Test creating SettingsData from dictionary."""
        data = {
            'schema_version': 3,
            'shop': {'name': 'Custom Shop', 'phone': '03001234567'},
            'printer': {'printer_dpi': 300, 'gap_mm': 3},
            'tax': {'tax_enabled': True, 'tax_rate': 17.0},
        }
        
        settings = SettingsData.from_dict(data)
        
        assert settings.shop.name == "Custom Shop"
        assert settings.shop.phone == "03001234567"
        assert settings.printer.printer_dpi == 300
        assert settings.printer.gap_mm == 3
        assert settings.tax.tax_enabled is True
        assert settings.tax.tax_rate == 17.0
        # Unspecified fields should use defaults
        assert settings.inventory.default_reorder_point == 5
    
    def test_from_dict_empty(self):
        """Test creating SettingsData from empty dict."""
        settings = SettingsData.from_dict({})
        assert settings.shop.name == "SHOUKAT SONS GARMENTS"
    
    def test_from_dict_none(self):
        """Test creating SettingsData from None."""
        settings = SettingsData.from_dict(None)
        assert settings.shop.name == "SHOUKAT SONS GARMENTS"


class TestSettingsValidation:
    """Tests for settings validation."""
    
    def test_valid_settings(self, settings_manager):
        """Test that valid settings pass validation."""
        settings = SettingsData()
        # Should not raise
        settings_manager.validate(settings)
    
    def test_invalid_phone(self, settings_manager):
        """Test phone number validation."""
        settings = SettingsData()
        settings.shop.phone = "invalid-phone"
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Invalid phone format" in str(exc_info.value)
    
    def test_valid_phone_formats(self, settings_manager):
        """Test various valid phone formats."""
        valid_phones = [
            "03001234567",
            "+923001234567",
            "3001234567",
        ]
        
        for phone in valid_phones:
            settings = SettingsData()
            settings.shop.phone = phone
            # Should not raise
            settings_manager.validate(settings)
    
    def test_invalid_email(self, settings_manager):
        """Test email validation."""
        settings = SettingsData()
        settings.shop.email = "not-an-email"
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Invalid email format" in str(exc_info.value)
    
    def test_invalid_tax_rate(self, settings_manager):
        """Test tax rate bounds."""
        settings = SettingsData()
        settings.tax.tax_rate = 150.0  # > 100
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Tax rate must be 0-100" in str(exc_info.value)
    
    def test_invalid_printer_dpi(self, settings_manager):
        """Test printer DPI validation."""
        settings = SettingsData()
        settings.printer.printer_dpi = -203
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Printer DPI must be positive" in str(exc_info.value)
    
    def test_invalid_barcode_font_size(self, settings_manager):
        """Test barcode font size validation."""
        settings = SettingsData()
        settings.barcode.barcode_font_size = 20  # Not in valid list
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Barcode font size must be one of" in str(exc_info.value)
    
    def test_valid_barcode_font_sizes(self, settings_manager):
        """Test valid barcode font sizes."""
        valid_sizes = [6, 12, 18, 24, 30, 36]
        
        for size in valid_sizes:
            settings = SettingsData()
            settings.barcode.barcode_font_size = size
            # Should not raise
            settings_manager.validate(settings)
    
    def test_invalid_theme(self, settings_manager):
        """Test theme validation."""
        settings = SettingsData()
        settings.display.theme = "purple"
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Invalid theme" in str(exc_info.value)
    
    def test_invalid_backup_frequency(self, settings_manager):
        """Test backup frequency validation."""
        settings = SettingsData()
        settings.backup.backup_frequency = "hourly"
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Invalid backup frequency" in str(exc_info.value)
    
    def test_invalid_secret_code_map(self, settings_manager):
        """Test secret code map validation."""
        settings = SettingsData()
        settings.secret_code.code_map = {"0": "A"}  # Only 1 entry
        
        with pytest.raises(SettingsValidationError) as exc_info:
            settings_manager.validate(settings)
        
        assert "Secret code map must have exactly 10 entries" in str(exc_info.value)


class TestSettingsPersistence:
    """Tests for settings save/load operations."""
    
    def test_save_and_load(self, settings_manager):
        """Test saving and loading settings."""
        settings = SettingsData()
        settings.shop.name = "Persistent Shop"
        settings.printer.printer_dpi = 300
        
        settings_manager.save(settings)
        
        # Clear cache
        settings_manager._settings_cache = None
        
        # Load and verify
        loaded = settings_manager.load()
        assert loaded.shop.name == "Persistent Shop"
        assert loaded.printer.printer_dpi == 300
    
    def test_load_creates_defaults(self, settings_manager):
        """Test that loading from empty DB creates defaults."""
        # Ensure DB is empty
        conn = sqlite3.connect(str(settings_manager.db_path))
        conn.execute("DELETE FROM settings")
        conn.commit()
        conn.close()
        
        settings_manager._settings_cache = None
        settings = settings_manager.load()
        
        assert settings.shop.name == "SHOUKAT SONS GARMENTS"
    
    def test_update_timestamp(self, settings_manager):
        """Test that save updates timestamp."""
        settings = SettingsData()
        original_time = settings.updated_at
        
        settings_manager.save(settings)
        
        loaded = settings_manager.load()
        assert loaded.updated_at >= original_time
    
    def test_singleton_pattern(self, settings_manager):
        """Test that SettingsManager is a singleton."""
        manager2 = SettingsManager()
        assert manager2 is settings_manager


class TestSettingsMigration:
    """Tests for schema migrations."""
    
    def test_migrate_v1_to_v2(self, settings_manager):
        """Test migration from v1 to v2 (adds loyalty settings)."""
        # Create v1 settings manually
        v1_data = {
            'schema_version': 1,
            'shop': {'name': 'Old Shop'},
            # No loyalty section
        }
        
        settings = SettingsData.from_dict(v1_data)
        settings.schema_version = 1
        
        # Migrate
        migrated = settings_manager._migrate_settings(settings)
        
        assert migrated.schema_version >= 2
        assert hasattr(migrated, 'loyalty')
        assert migrated.loyalty.points_per_currency == 0.01
    
    def test_migrate_v2_to_v3(self, settings_manager):
        """Test migration from v2 to v3 (adds barcode settings)."""
        v2_data = {
            'schema_version': 2,
            'shop': {'name': 'Shop'},
            'loyalty': {'loyalty_enabled': True},
            # No barcode section
        }
        
        settings = SettingsData.from_dict(v2_data)
        settings.schema_version = 2
        
        # Migrate
        migrated = settings_manager._migrate_settings(settings)
        
        assert migrated.schema_version >= 3
        assert hasattr(migrated, 'barcode')
        assert migrated.barcode.barcode_font_size == 24
    
    def test_auto_migration_on_load(self, settings_manager, temp_db):
        """Test that loading old settings triggers migration."""
        # Insert v1 settings directly
        v1_data = {
            'schema_version': 1,
            'shop': {'name': 'Migrated Shop'},
        }
        
        conn = sqlite3.connect(str(temp_db))
        conn.execute("""
            INSERT INTO settings (id, schema_version, settings_json, created_at, updated_at)
            VALUES (1, 1, ?, ?, ?)
        """, (json.dumps(v1_data), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        # Clear cache and reload
        SettingsManager._settings_cache = None
        manager = SettingsManager()
        
        settings = manager.load()
        assert settings.schema_version == CURRENT_SCHEMA_VERSION
        assert settings.shop.name == "Migrated Shop"


class TestSettingsUpdate:
    """Tests for field update operations."""
    
    def test_update_field(self, settings_manager):
        """Test updating a single field."""
        settings_manager.update_field('shop', 'name', 'Updated Shop')
        
        settings = settings_manager.load()
        assert settings.shop.name == "Updated Shop"
    
    def test_update_field_invalid_category(self, settings_manager):
        """Test updating with invalid category."""
        with pytest.raises(AttributeError) as exc_info:
            settings_manager.update_field('invalid', 'name', 'Value')
        
        assert "Unknown category" in str(exc_info.value)
    
    def test_update_field_invalid_field(self, settings_manager):
        """Test updating with invalid field."""
        with pytest.raises(AttributeError) as exc_info:
            settings_manager.update_field('shop', 'invalid_field', 'Value')
        
        assert "Unknown field" in str(exc_info.value)
    
    def test_get_category(self, settings_manager):
        """Test getting a category."""
        shop = settings_manager.get_category('shop')
        assert isinstance(shop, ShopDetails)
        assert shop.name == "SHOUKAT SONS GARMENTS"
    
    def test_reset_to_defaults(self, settings_manager):
        """Test resetting to defaults."""
        # Change a setting
        settings_manager.update_field('shop', 'name', 'Changed')
        
        # Reset
        defaults = settings_manager.reset_to_defaults()
        
        assert defaults.shop.name == "SHOUKAT SONS GARMENTS"
        
        # Verify persisted
        loaded = settings_manager.load()
        assert loaded.shop.name == "SHOUKAT SONS GARMENTS"


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_get_settings(self, settings_manager, temp_db, monkeypatch):
        """Test get_settings function."""
        # Setup
        SettingsManager._instance = None
        SettingsManager._settings_cache = None
        
        def mock_get_db_path(self):
            return temp_db
        
        monkeypatch.setattr(SettingsManager, '_get_db_path', mock_get_db_path)
        
        settings = get_settings()
        assert isinstance(settings, SettingsData)
    
    def test_update_setting(self, settings_manager, temp_db, monkeypatch):
        """Test update_setting function."""
        SettingsManager._instance = None
        
        def mock_get_db_path(self):
            return temp_db
        
        monkeypatch.setattr(SettingsManager, '_get_db_path', mock_get_db_path)
        
        update_setting('printer', 'printer_dpi', 300)
        
        settings = get_settings()
        assert settings.printer.printer_dpi == 300


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_multiple_saves(self, settings_manager):
        """Test multiple consecutive saves."""
        settings = SettingsData()
        
        for i in range(5):
            settings.shop.name = f"Shop {i}"
            settings_manager.save(settings)
        
        loaded = settings_manager.load()
        assert loaded.shop.name == "Shop 4"
    
    def test_concurrent_access(self, settings_manager):
        """Test concurrent read/write access."""
        import threading
        
        errors = []
        
        def writer():
            try:
                for i in range(10):
                    settings_manager.update_field('shop', 'name', f"Thread {i}")
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for i in range(10):
                    settings_manager.load()
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_large_settings_values(self, settings_manager):
        """Test with large text values."""
        settings = SettingsData()
        settings.shop.address = "A" * 10000  # 10KB address
        
        settings_manager.save(settings)
        loaded = settings_manager.load()
        
        assert len(loaded.shop.address) == 10000
    
    def test_special_characters(self, settings_manager):
        """Test special characters in settings."""
        settings = SettingsData()
        settings.shop.name = "Shop & Sons™ ©®"
        settings.shop.footer_message = "Thank you! 💰🛍️"
        
        settings_manager.save(settings)
        loaded = settings_manager.load()
        
        assert loaded.shop.name == "Shop & Sons™ ©®"
        assert "💰🛍️" in loaded.shop.footer_message
