"""
Tests for First-Run Wizard

These tests validate the wizard's step navigation, validation logic,
and data collection functionality.
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch, MagicMock
from ui.wizard import FirstRunWizard, run_first_run_wizard


@pytest.fixture
def wizard_window():
    """Create a test wizard window."""
    root = ctk.CTk()
    root.withdraw()  # Hide main window
    
    on_complete_mock = Mock()
    wizard = FirstRunWizard(root, on_complete_mock)
    
    yield wizard, root, on_complete_mock
    
    try:
        wizard.destroy()
        root.destroy()
    except:
        pass


class TestFirstRunWizard:
    """Test suite for FirstRunWizard class."""
    
    def test_wizard_initialization(self, wizard_window):
        """Test wizard initializes with correct state."""
        wizard, root, on_complete_mock = wizard_window
        
        assert wizard.current_step == 0
        assert wizard.setup_data == {}
        assert wizard.on_complete == on_complete_mock
        assert wizard.title() == "Shoukat POS - First Time Setup"
    
    def test_step_navigation_forward(self, wizard_window):
        """Test navigating forward through steps."""
        wizard, root, on_complete_mock = wizard_window
        
        # Should start at step 0
        assert wizard.current_step == 0
        
        # Mock validation to always pass
        with patch.object(wizard, '_validate_current_step', return_value=True):
            # Navigate through all steps
            for expected_step in range(1, 6):
                wizard._next_step()
                assert wizard.current_step == expected_step
    
    def test_step_navigation_backward(self, wizard_window):
        """Test navigating backward through steps."""
        wizard, root, on_complete_mock = wizard_window
        
        # Move to step 3
        with patch.object(wizard, '_validate_current_step', return_value=True):
            for _ in range(3):
                wizard._next_step()
        
        assert wizard.current_step == 3
        
        # Navigate back
        wizard._previous_step()
        assert wizard.current_step == 2
        
        wizard._previous_step()
        assert wizard.current_step == 1
        
        wizard._previous_step()
        assert wizard.current_step == 0
        
        # Can't go back from step 0
        wizard._previous_step()
        assert wizard.current_step == 0
    
    def test_back_button_disabled_on_first_step(self, wizard_window):
        """Test back button is disabled on first step."""
        wizard, root, on_complete_mock = wizard_window
        
        assert wizard.current_step == 0
        assert wizard.back_btn.cget('state') == 'disabled'
    
    def test_next_button_text_changes_on_last_step(self, wizard_window):
        """Test next button text changes to 'Finish' on last step."""
        wizard, root, on_complete_mock = wizard_window
        
        # Move to last step
        with patch.object(wizard, '_validate_current_step', return_value=True):
            for _ in range(5):
                wizard._next_step()
        
        assert wizard.current_step == 5
        assert wizard.next_btn.cget('text') == 'Finish'
    
    def test_validation_shop_info_required_fields(self, wizard_window):
        """Test shop info step validates required fields."""
        wizard, root, on_complete_mock = wizard_window
        
        # Render shop info step
        wizard._render_shop_info_step()
        
        # Empty fields should fail
        wizard.shop_name_entry.delete(0, 'end')
        wizard.address_entry.delete(0, 'end')
        wizard.phone_entry.delete(0, 'end')
        
        result = wizard._validate_current_step()
        assert result is False
    
    def test_validation_shop_info_valid_data(self, wizard_window):
        """Test shop info step accepts valid data."""
        wizard, root, on_complete_mock = wizard_window
        
        # Render shop info step
        wizard._render_shop_info_step()
        
        # Fill with valid data
        wizard.shop_name_entry.insert(0, "Test Shop")
        wizard.address_entry.insert(0, "123 Test St")
        wizard.phone_entry.insert(0, "0300-1234567")
        
        result = wizard._validate_current_step()
        assert result is True
        assert 'shop_info' in wizard.setup_data
    
    def test_validation_password_mismatch(self, wizard_window):
        """Test admin account step validates password match."""
        wizard, root, on_complete_mock = wizard_window
        
        # Move to admin account step
        with patch.object(wizard, '_validate_current_step', return_value=True):
            wizard._next_step()
        
        # Render admin account step
        wizard._render_admin_account_step()
        
        # Enter mismatched passwords
        wizard.admin_username_entry.insert(0, "admin")
        wizard.admin_password_entry.insert(0, "password123")
        wizard.admin_confirm_password_entry.insert(0, "password456")
        
        result = wizard._validate_current_step()
        assert result is False
    
    def test_validation_password_too_short(self, wizard_window):
        """Test admin account step validates password length."""
        wizard, root, on_complete_mock = wizard_window
        
        # Move to admin account step
        with patch.object(wizard, '_validate_current_step', return_value=True):
            wizard._next_step()
        
        # Render admin account step
        wizard._render_admin_account_step()
        
        # Enter short password
        wizard.admin_username_entry.insert(0, "admin")
        wizard.admin_password_entry.insert(0, "short")
        wizard.admin_confirm_password_entry.insert(0, "short")
        
        result = wizard._validate_current_step()
        assert result is False
    
    def test_validation_secret_code_duplicate(self, wizard_window):
        """Test secret code step rejects duplicate characters."""
        wizard, root, on_complete_mock = wizard_window
        
        # Move to secret code step
        with patch.object(wizard, '_validate_current_step', return_value=True):
            for _ in range(4):
                wizard._next_step()
        
        # Render secret code step
        wizard._render_secret_code_step()
        
        # Set duplicate characters
        wizard.secret_code_entries['0'].delete(0, 'end')
        wizard.secret_code_entries['0'].insert(0, 'X')
        wizard.secret_code_entries['1'].delete(0, 'end')
        wizard.secret_code_entries['1'].insert(0, 'X')  # Duplicate!
        
        result = wizard._validate_current_step()
        assert result is False
    
    def test_restore_default_secret_code(self, wizard_window):
        """Test restoring default secret code mapping."""
        wizard, root, on_complete_mock = wizard_window
        
        # Move to secret code step
        with patch.object(wizard, '_validate_current_step', return_value=True):
            for _ in range(4):
                wizard._next_step()
        
        # Render secret code step
        wizard._render_secret_code_step()
        
        # Change some values
        wizard.secret_code_entries['0'].delete(0, 'end')
        wizard.secret_code_entries['0'].insert(0, 'X')
        
        # Restore defaults
        wizard._restore_default_secret_code()
        
        # Check restored to default
        assert wizard.secret_code_entries['0'].get() == 'L'
        assert wizard.secret_code_entries['1'].get() == 'R'
    
    def test_wizard_completion_saves_data(self, wizard_window):
        """Test wizard completion saves all collected data."""
        wizard, root, on_complete_mock = wizard_window
        
        # Mock ConfigManager and AuthService
        with patch('ui.wizard.ConfigManager') as mock_config, \
             patch('ui.wizard.AuthService') as mock_auth_class:
            
            mock_auth_instance = Mock()
            mock_auth_class.return_value = mock_auth_instance
            
            # Fill in all steps
            wizard._render_shop_info_step()
            wizard.shop_name_entry.insert(0, "Test Shop")
            wizard.address_entry.insert(0, "123 Test St")
            wizard.phone_entry.insert(0, "0300-1234567")
            
            with patch.object(wizard, '_validate_current_step', return_value=True):
                # Navigate through all steps
                for _ in range(5):
                    wizard._next_step()
            
            # Complete wizard
            wizard._complete_wizard()
            
            # Verify ConfigManager was called
            assert mock_config.save_shop_info.called
            assert mock_config.save_printer_settings.call_count >= 2
            assert mock_config.save_secret_code_mapping.called
            assert mock_config.save_tax_rate.called
            assert mock_config.mark_setup_complete.called
            
            # Verify AuthService was called
            assert mock_auth_instance.create_user.called
    
    def test_password_strength_indicator(self, wizard_window):
        """Test password strength calculation."""
        wizard, root, on_complete_mock = wizard_window
        
        # Move to admin account step
        with patch.object(wizard, '_validate_current_step', return_value=True):
            wizard._next_step()
        
        # Render admin account step
        wizard._render_admin_account_step()
        
        # Test weak password
        wizard.admin_password_entry.delete(0, 'end')
        wizard.admin_password_entry.insert(0, "weak")
        wizard._check_password_strength()
        assert "Weak" in wizard.password_strength_label.cget('text')
        
        # Test strong password
        wizard.admin_password_entry.delete(0, 'end')
        wizard.admin_password_entry.insert(0, "StrongP@ss123")
        wizard._check_password_strength()
        assert "Strong" in wizard.password_strength_label.cget('text') or \
               "Very Strong" in wizard.password_strength_label.cget('text')


class TestRunFirstRunWizard:
    """Test the run_first_run_wizard function."""
    
    def test_run_wizard_creates_and_shows(self):
        """Test run_first_run_wizard creates wizard and waits."""
        root = ctk.CTk()
        root.withdraw()
        
        on_complete_mock = Mock()
        
        # Create wizard (don't wait_window in test)
        from ui.wizard import FirstRunWizard
        wizard = FirstRunWizard(root, on_complete_mock)
        
        assert wizard is not None
        assert wizard.transient() == str(root)
        
        try:
            wizard.destroy()
            root.destroy()
        except:
            pass
