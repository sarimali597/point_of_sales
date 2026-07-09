"""
First-Run Wizard for Shoukat POS

This module handles the initial setup wizard that runs when no database exists.
It guides the administrator through:
1. Shop information configuration
2. Admin account creation
3. Printer setup (label & receipt)
4. Secret code mapping configuration
5. Tax rate setup
6. Initial category/product creation
"""

import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from pathlib import Path

from ui.theme import ThemeManager
from ui.components import Toast, ConfirmationDialog
from utils.validators import validate_phone, validate_text, validate_price
from services.auth_service import AuthService
from services.product_service import ProductService
from services.backup_service import BackupService


class FirstRunWizard(ctk.CTkToplevel):
    """Modal wizard for first-time application setup."""
    
    def __init__(self, parent: ctk.CTk, on_complete: Callable[[], None]):
        super().__init__(parent)
        
        self.title("Shoukat POS - First Time Setup")
        self.geometry("800x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()  # Modal behavior
        
        self.on_complete = on_complete
        self.current_step = 0
        self.setup_data: Dict[str, Any] = {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Content area expands
        
        # Create wizard components
        self._create_header()
        self._create_progress_bar()
        self._create_content_area()
        self._create_footer()
        
        # Show first step
        self._show_step(0)
    
    def _create_header(self):
        """Create wizard header with logo and title."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 20))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Welcome to Shoukat POS",
            font=ctk.CTkFont(size=28, weight="bold"),
            justify="center"
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Let's set up your store in a few simple steps",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack()
    
    def _create_progress_bar(self):
        """Create step progress indicator."""
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, sticky="ew", padx=40, pady=20)
        
        # Will be populated dynamically based on current step
        self._update_progress()
    
    def _update_progress(self):
        """Update progress bar visualization."""
        # Clear existing
        for widget in self.progress_frame.winfo_children():
            widget.destroy()
        
        steps = [
            "Shop Info",
            "Admin Account",
            "Label Printer",
            "Receipt Printer",
            "Secret Code",
            "Tax & Finish"
        ]
        
        total_steps = len(steps)
        
        # Create step indicators
        for i, step_name in enumerate(steps):
            frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
            frame.pack(side="left", expand=True, fill="x")
            
            # Circle indicator
            circle_color = ThemeManager.get_color("primary") if i <= self.current_step else "gray"
            circle = ctk.CTkLabel(
                frame,
                text=str(i + 1),
                width=32,
                height=32,
                corner_radius=16,
                fg_color=circle_color,
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            circle.pack(pady=(0, 5))
            
            # Step name
            name_label = ctk.CTkLabel(
                frame,
                text=step_name,
                font=ctk.CTkFont(size=11),
                text_color=circle_color if i <= self.current_step else "gray"
            )
            name_label.pack()
    
    def _create_content_area(self):
        """Create scrollable content area for wizard steps."""
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
    
    def _create_footer(self):
        """Create footer with navigation buttons."""
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=40, pady=(0, 30))
        
        # Back button
        self.back_btn = ctk.CTkButton(
            footer_frame,
            text="← Back",
            width=120,
            command=self._previous_step,
            state="disabled" if self.current_step == 0 else "normal"
        )
        self.back_btn.pack(side="left")
        
        # Next/Finish button
        self.next_btn = ctk.CTkButton(
            footer_frame,
            text="Next →",
            width=120,
            fg_color=ThemeManager.get_color("primary"),
            hover_color=ThemeManager.get_color("secondary"),
            command=self._next_step
        )
        self.next_btn.pack(side="right")
    
    def _show_step(self, step_index: int):
        """Display the content for a specific wizard step."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_step = step_index
        self._update_progress()
        
        # Update button states
        self.back_btn.configure(state="disabled" if step_index == 0 else "normal")
        is_last_step = step_index == 5
        self.next_btn.configure(text="Finish" if is_last_step else "Next →")
        
        # Render step content
        step_renderers = {
            0: self._render_shop_info_step,
            1: self._render_admin_account_step,
            2: self._render_label_printer_step,
            3: self._render_receipt_printer_step,
            4: self._render_secret_code_step,
            5: self._render_tax_finish_step,
        }
        
        renderer = step_renderers.get(step_index)
        if renderer:
            renderer()
    
    def _render_shop_info_step(self):
        """Step 1: Shop Information."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", pady=20)
        
        ctk.CTkLabel(
            container,
            text="Shop Information",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        # Shop Name
        ctk.CTkLabel(container, text="Shop Name *").pack(anchor="w")
        self.shop_name_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., Shoukat Sons Garments")
        self.shop_name_entry.pack(fill="x", pady=(5, 15))
        
        # Address
        ctk.CTkLabel(container, text="Address *").pack(anchor="w")
        self.address_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., Main Bazaar, Lahore")
        self.address_entry.pack(fill="x", pady=(5, 15))
        
        # Phone
        ctk.CTkLabel(container, text="Phone Number *").pack(anchor="w")
        self.phone_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., 03XX-XXXXXXX")
        self.phone_entry.pack(fill="x", pady=(5, 15))
        
        # GSTIN (optional)
        ctk.CTkLabel(container, text="GSTIN (Optional)").pack(anchor="w")
        self.gstin_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., 1234567890123")
        self.gstin_entry.pack(fill="x", pady=(5, 0))
    
    def _render_admin_account_step(self):
        """Step 2: Admin Account Creation."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", pady=20)
        
        ctk.CTkLabel(
            container,
            text="Create Admin Account",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        info_label = ctk.CTkLabel(
            container,
            text="This account will have full access to all features.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="left"
        )
        info_label.pack(anchor="w", pady=(0, 20))
        
        # Username
        ctk.CTkLabel(container, text="Username *").pack(anchor="w")
        self.admin_username_entry = ctk.CTkEntry(container, width=500, placeholder_text="Choose a username")
        self.admin_username_entry.pack(fill="x", pady=(5, 15))
        
        # Password
        ctk.CTkLabel(container, text="Password *").pack(anchor="w")
        self.admin_password_entry = ctk.CTkEntry(container, width=500, show="•", placeholder_text="Minimum 8 characters")
        self.admin_password_entry.pack(fill="x", pady=(5, 15))
        
        # Confirm Password
        ctk.CTkLabel(container, text="Confirm Password *").pack(anchor="w")
        self.admin_confirm_password_entry = ctk.CTkEntry(container, width=500, show="•", placeholder_text="Re-enter password")
        self.admin_confirm_password_entry.pack(fill="x", pady=(5, 0))
        
        # Password strength indicator
        self.password_strength_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        self.password_strength_label.pack(anchor="w", pady=(5, 0))
        
        # Bind password change to strength check
        self.admin_password_entry.configure(command=self._check_password_strength)
    
    def _check_password_strength(self, event=None):
        """Check and display password strength."""
        password = self.admin_password_entry.get()
        
        strength = 0
        if len(password) >= 8:
            strength += 1
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
            strength += 1
        
        strength_text = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong"]
        strength_colors = ["#C62828", "#F57C00", "#FBC02D", "#7CB342", "#2E7D32", "#1B5E20"]
        
        self.password_strength_label.configure(
            text=f"Password Strength: {strength_text[strength]}",
            text_color=strength_colors[strength]
        )
    
    def _render_label_printer_step(self):
        """Step 3: Label Printer Setup."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", pady=20)
        
        ctk.CTkLabel(
            container,
            text="Label Printer Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        info_label = ctk.CTkLabel(
            container,
            text="Configure your BlackCopper BC-LP-1300 thermal label printer.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="left"
        )
        info_label.pack(anchor="w", pady=(0, 20))
        
        # Sticker Size
        ctk.CTkLabel(container, text="Sticker Size *").pack(anchor="w")
        self.sticker_size_var = ctk.StringVar(value="28x19")
        sticker_size_dropdown = ctk.CTkOptionMenu(
            container,
            variable=self.sticker_size_var,
            values=["28x19", "32x25", "32x19", "34x24"],
            width=500
        )
        sticker_size_dropdown.pack(fill="x", pady=(5, 15))
        
        # Gap Size
        ctk.CTkLabel(container, text="Gap Between Stickers (mm)").pack(anchor="w")
        self.gap_size_entry = ctk.CTkEntry(container, width=500, placeholder_text="Default: 2")
        self.gap_size_entry.insert(0, "2")
        self.gap_size_entry.pack(fill="x", pady=(5, 15))
        
        # Test Print Button
        test_print_btn = ctk.CTkButton(
            container,
            text="🖨️ Print Test Label",
            width=200,
            command=self._test_label_print,
            fg_color=ThemeManager.get_color("accent")
        )
        test_print_btn.pack(pady=(10, 0))
    
    def _render_receipt_printer_step(self):
        """Step 4: Receipt Printer Setup."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", pady=20)
        
        ctk.CTkLabel(
            container,
            text="Receipt Printer Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        info_label = ctk.CTkLabel(
            container,
            text="Configure your 80mm thermal receipt printer.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="left"
        )
        info_label.pack(anchor="w", pady=(0, 20))
        
        # Receipt Width
        ctk.CTkLabel(container, text="Receipt Width *").pack(anchor="w")
        self.receipt_width_var = ctk.StringVar(value="80mm")
        receipt_width_dropdown = ctk.CTkOptionMenu(
            container,
            variable=self.receipt_width_var,
            values=["80mm", "58mm"],
            width=500
        )
        receipt_width_dropdown.pack(fill="x", pady=(5, 15))
        
        # Header Text
        ctk.CTkLabel(container, text="Receipt Header (Line 1)").pack(anchor="w")
        self.header_line1_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., SHOUKAT SONS GARMENTS")
        self.header_line1_entry.pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(container, text="Receipt Header (Line 2 - Address)").pack(anchor="w")
        self.header_line2_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., Main Bazaar, Lahore")
        self.header_line2_entry.pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(container, text="Receipt Header (Line 3 - Phone)").pack(anchor="w")
        self.header_line3_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., Phone: 03XX-XXXXXXX")
        self.header_line3_entry.pack(fill="x", pady=(5, 15))
        
        # Footer Text
        ctk.CTkLabel(container, text="Receipt Footer (Thank You Message)").pack(anchor="w")
        self.footer_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., Thank you for shopping!")
        self.footer_entry.pack(fill="x", pady=(5, 15))
        
        # Test Print Button
        test_print_btn = ctk.CTkButton(
            container,
            text="🖨️ Print Test Receipt",
            width=200,
            command=self._test_receipt_print,
            fg_color=ThemeManager.get_color("accent")
        )
        test_print_btn.pack(pady=(10, 0))
    
    def _render_secret_code_step(self):
        """Step 5: Secret Code Mapping."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", pady=20)
        
        ctk.CTkLabel(
            container,
            text="Secret Code Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        info_label = ctk.CTkLabel(
            container,
            text="Map digits (0-9) to secret code characters for purchase price encoding.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="left"
        )
        info_label.pack(anchor="w", pady=(0, 20))
        
        # Create grid for digit mappings
        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(fill="x", pady=(0, 20))
        
        self.secret_code_entries = {}
        
        default_mapping = {
            '0': 'L', '1': 'R', '2': 'K', '3': 'B', '4': 'S',
            '5': 'M', '6': 'N', '7': 'T', '8': 'H', '9': 'W'
        }
        
        for i, digit in enumerate(range(10)):
            row = i // 5
            col = (i % 5) * 2
            
            digit_label = ctk.CTkLabel(
                grid_frame,
                text=f"Digit {digit}:",
                width=80,
                anchor="e"
            )
            digit_label.grid(row=row, column=col, padx=(0, 10), pady=5, sticky="e")
            
            entry = ctk.CTkEntry(
                grid_frame,
                width=60,
                placeholder_text=default_mapping[str(digit)]
            )
            entry.insert(0, default_mapping[str(digit)])
            entry.grid(row=row, column=col+1, padx=(0, 20), pady=5)
            
            self.secret_code_entries[str(digit)] = entry
        
        # Preview section
        preview_frame = ctk.CTkFrame(container, fg_color=ThemeManager.get_color("background"))
        preview_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(
            preview_frame,
            text="Preview: Rs. 1,250 → ",
            font=ctk.CTkFont(size=13),
            justify="left"
        ).pack(side="left", padx=(10, 5), pady=10)
        
        self.code_preview_label = ctk.CTkLabel(
            preview_frame,
            text="RKMS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ThemeManager.get_color("primary"),
            justify="left"
        )
        self.code_preview_label.pack(side="left", padx=(5, 10), pady=10)
        
        # Restore Default Button
        restore_btn = ctk.CTkButton(
            container,
            text="Restore Default Mapping",
            width=200,
            command=self._restore_default_secret_code,
            fg_color="gray"
        )
        restore_btn.pack(pady=(10, 0))
    
    def _render_tax_finish_step(self):
        """Step 6: Tax Rate & Finish."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.grid(row=0, column=0, sticky="ew", pady=20)
        
        ctk.CTkLabel(
            container,
            text="Final Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        # Tax Rate
        ctk.CTkLabel(container, text="Default GST Tax Rate (%)").pack(anchor="w")
        self.tax_rate_entry = ctk.CTkEntry(container, width=500, placeholder_text="e.g., 17")
        self.tax_rate_entry.insert(0, "17")
        self.tax_rate_entry.pack(fill="x", pady=(5, 20))
        
        # Summary
        summary_frame = ctk.CTkFrame(container, fg_color=ThemeManager.get_color("background"))
        summary_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkLabel(
            summary_frame,
            text="Setup Summary",
            font=ctk.CTkFont(size=15, weight="bold"),
            justify="left"
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        summary_items = [
            "✓ Shop information configured",
            "✓ Admin account created",
            "✓ Label printer settings saved",
            "✓ Receipt printer settings saved",
            "✓ Secret code mapping defined",
            "✓ Tax rate configured"
        ]
        
        for item in summary_items:
            ctk.CTkLabel(
                summary_frame,
                text=item,
                font=ctk.CTkFont(size=13),
                justify="left",
                text_color=ThemeManager.get_color("success")
            ).pack(anchor="w", padx=15, pady=3)
        
        # Final info
        final_info = ctk.CTkLabel(
            container,
            text="After clicking Finish, you can add your first product and start selling!",
            font=ctk.CTkFont(size=13),
            text_color=ThemeManager.get_color("primary"),
            justify="center"
        )
        final_info.pack(pady=(20, 0))
    
    def _test_label_print(self):
        """Print a test label."""
        Toast.show(self, "Sending test label to printer...", type="info")
        # Implementation would call hardware.label_printer.test_print()
    
    def _test_receipt_print(self):
        """Print a test receipt."""
        Toast.show(self, "Sending test receipt to printer...", type="info")
        # Implementation would call hardware.receipt_printer.test_print()
    
    def _restore_default_secret_code(self):
        """Restore default secret code mapping."""
        default_mapping = {
            '0': 'L', '1': 'R', '2': 'K', '3': 'B', '4': 'S',
            '5': 'M', '6': 'N', '7': 'T', '8': 'H', '9': 'W'
        }
        
        for digit, char in default_mapping.items():
            entry = self.secret_code_entries[digit]
            entry.delete(0, 'end')
            entry.insert(0, char)
        
        Toast.show(self, "Default mapping restored", type="success")
    
    def _validate_current_step(self) -> bool:
        """Validate the current wizard step."""
        if self.current_step == 0:
            # Validate shop info
            shop_name = self.shop_name_entry.get().strip()
            address = self.address_entry.get().strip()
            phone = self.phone_entry.get().strip()
            
            if not shop_name or not address or not phone:
                Toast.show(self, "Please fill in all required fields", type="error")
                return False
            
            if not validate_phone(phone):
                Toast.show(self, "Invalid phone number format", type="error")
                return False
            
            self.setup_data['shop_info'] = {
                'name': shop_name,
                'address': address,
                'phone': phone,
                'gstin': self.gstin_entry.get().strip()
            }
            
        elif self.current_step == 1:
            # Validate admin account
            username = self.admin_username_entry.get().strip()
            password = self.admin_password_entry.get()
            confirm_password = self.admin_confirm_password_entry.get()
            
            if not username or not password:
                Toast.show(self, "Username and password are required", type="error")
                return False
            
            if len(password) < 8:
                Toast.show(self, "Password must be at least 8 characters", type="error")
                return False
            
            if password != confirm_password:
                Toast.show(self, "Passwords do not match", type="error")
                return False
            
            self.setup_data['admin'] = {
                'username': username,
                'password': password
            }
            
        elif self.current_step == 2:
            # Validate label printer
            sticker_size = self.sticker_size_var.get()
            gap_size = self.gap_size_entry.get()
            
            try:
                gap_value = int(gap_size)
                if gap_value < 0 or gap_value > 10:
                    raise ValueError()
            except ValueError:
                Toast.show(self, "Gap size must be between 0 and 10 mm", type="error")
                return False
            
            self.setup_data['label_printer'] = {
                'sticker_size': sticker_size,
                'gap_mm': gap_value
            }
            
        elif self.current_step == 3:
            # Validate receipt printer
            receipt_width = self.receipt_width_var.get()
            header1 = self.header_line1_entry.get().strip()
            
            if not header1:
                Toast.show(self, "Receipt header line 1 is required", type="error")
                return False
            
            self.setup_data['receipt_printer'] = {
                'width': receipt_width,
                'header_line1': header1,
                'header_line2': self.header_line2_entry.get().strip(),
                'header_line3': self.header_line3_entry.get().strip(),
                'footer': self.footer_entry.get().strip()
            }
            
        elif self.current_step == 4:
            # Validate secret code
            secret_map = {}
            used_chars = set()
            
            for digit, entry in self.secret_code_entries.items():
                char = entry.get().strip().upper()
                if not char:
                    Toast.show(self, f"Code character for digit {digit} is required", type="error")
                    return False
                if char in used_chars:
                    Toast.show(self, f"Duplicate code character '{char}' detected", type="error")
                    return False
                secret_map[digit] = char
                used_chars.add(char)
            
            self.setup_data['secret_code'] = secret_map
            
        elif self.current_step == 5:
            # Validate tax rate
            tax_rate_str = self.tax_rate_entry.get().strip()
            
            try:
                tax_rate = float(tax_rate_str)
                if tax_rate < 0 or tax_rate > 100:
                    raise ValueError()
            except ValueError:
                Toast.show(self, "Tax rate must be between 0 and 100", type="error")
                return False
            
            self.setup_data['tax_rate'] = tax_rate
        
        return True
    
    def _previous_step(self):
        """Navigate to previous step."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _next_step(self):
        """Navigate to next step or complete wizard."""
        if not self._validate_current_step():
            return
        
        if self.current_step < 5:
            self._show_step(self.current_step + 1)
        else:
            self._complete_wizard()
    
    def _complete_wizard(self):
        """Complete wizard and save all settings."""
        try:
            # Save shop info to config
            from config import ConfigManager
            ConfigManager.save_shop_info(self.setup_data['shop_info'])
            
            # Create admin user
            auth_service = AuthService()
            auth_service.create_user(
                username=self.setup_data['admin']['username'],
                password=self.setup_data['admin']['password'],
                role='admin',
                full_name='Administrator'
            )
            
            # Save printer settings
            ConfigManager.save_printer_settings('label', self.setup_data['label_printer'])
            ConfigManager.save_printer_settings('receipt', self.setup_data['receipt_printer'])
            
            # Save secret code mapping
            ConfigManager.save_secret_code_mapping(self.setup_data['secret_code'])
            
            # Save tax rate
            ConfigManager.save_tax_rate(self.setup_data['tax_rate'])
            
            # Mark setup as complete
            ConfigManager.mark_setup_complete()
            
            Toast.show(self, "Setup complete! Welcome to Shoukat POS", type="success")
            
            self.after(1000, lambda: [self.destroy(), self.on_complete()])
            
        except Exception as e:
            Toast.show(self, f"Setup failed: {str(e)}", type="error")
            import logging
            logging.exception("Wizard completion failed")


def run_first_run_wizard(parent: ctk.CTk, on_complete: Callable[[], None]):
    """Launch the first-run wizard."""
    wizard = FirstRunWizard(parent, on_complete)
    wizard.wait_window()
