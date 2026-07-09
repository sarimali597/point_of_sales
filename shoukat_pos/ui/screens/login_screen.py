"""
Login Screen for Shoukat POS.

Provides user authentication interface with username/password fields,
validation, and integration with AuthService.
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Dict, Any, Optional
import logging

from ui.theme import Colors, Animation
from services.auth_service import AuthService, AuthenticationError, AccountLockedError
from database.connection import ConnectionManager

logger = logging.getLogger(__name__)


class LoginScreen(ctk.CTkFrame):
    """
    Login screen with username and password authentication.
    
    Features:
    - Centered card layout
    - Password visibility toggle
    - Input validation
    - Loading state during authentication
    - Error handling with toast notifications
    """
    
    def __init__(
        self, 
        parent: ctk.CTkFrame,
        on_login_success: Callable[[Dict[str, Any]], None],
        **kwargs: Any
    ):
        """
        Initialize login screen.
        
        Args:
            parent: Parent container widget
            on_login_success: Callback function called with user data on successful login
            **kwargs: Additional keyword arguments passed to CTkFrame
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.on_login_success = on_login_success
        
        # Get database connection from parent app
        self.connection_manager = ConnectionManager.get_instance()
        self.auth_service: Optional[AuthService] = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create UI components
        self._create_login_card()
        self._bind_events()
        
        # Apply fade-in animation
        Animation.fade_in(self, duration_ms=200)
        
        logger.debug("Login screen initialized")
    
    def _create_login_card(self) -> None:
        """Create centered login card with form fields."""
        # Main card container
        self.card = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=Colors.CARD,
            width=400,
            height=450
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.grid_propagate(False)
        
        # Logo/Title area
        title_frame = ctk.CTkFrame(
            self.card,
            fg_color="transparent",
            height=100
        )
        title_frame.grid(row=0, column=0, padx=40, pady=(30, 20), sticky="ew")
        title_frame.grid_propagate(False)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="SHOUKAT SONS",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=Colors.PRIMARY
        )
        title_label.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Garments POS - Login",
            font=ctk.CTkFont(size=13),
            text_color=Colors.TEXT_SECONDARY
        )
        subtitle.pack(anchor="w")
        
        # Form container
        form_frame = ctk.CTkFrame(
            self.card,
            fg_color="transparent"
        )
        form_frame.grid(row=1, column=0, padx=40, pady=20, sticky="ew")
        
        # Username field
        self.username_label = ctk.CTkLabel(
            form_frame,
            text="Username",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        self.username_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter your username",
            height=45,
            font=ctk.CTkFont(size=14),
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.INPUT_BACKGROUND
        )
        self.username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Password field
        self.password_label = ctk.CTkLabel(
            form_frame,
            text="Password",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        self.password_label.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        
        # Password entry with toggle
        password_frame = ctk.CTkFrame(
            form_frame,
            fg_color="transparent"
        )
        password_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        password_frame.grid_columnconfigure(0, weight=1)
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Enter your password",
            show="•",
            height=45,
            font=ctk.CTkFont(size=14),
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.INPUT_BACKGROUND
        )
        self.password_entry.grid(row=0, column=0, sticky="ew")
        
        self.password_toggle_btn = ctk.CTkButton(
            password_frame,
            text="👁️",
            width=45,
            height=45,
            command=self._toggle_password_visibility,
            fg_color=Colors.BORDER,
            hover_color=Colors.TEXT_MUTED,
            font=ctk.CTkFont(size=16)
        )
        self.password_toggle_btn.grid(row=0, column=1, padx=(5, 0))
        self._password_visible = False
        
        # Login button
        self.login_btn = ctk.CTkButton(
            form_frame,
            text="Login",
            command=self._attempt_login,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_LIGHT
        )
        self.login_btn.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        
        # Footer text
        footer_label = ctk.CTkLabel(
            self.card,
            text="Default: admin / admin123",
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_MUTED
        )
        footer_label.grid(row=2, column=0, pady=(0, 20))
    
    def _bind_events(self) -> None:
        """Bind keyboard events for better UX."""
        # Enter key to submit
        self.bind("<Return>", lambda e: self._attempt_login())
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())
        
        # Auto-focus username field
        self.after(100, lambda: self.username_entry.focus())
    
    def _toggle_password_visibility(self) -> None:
        """Toggle password field visibility."""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_entry.configure(show="")
            self.password_toggle_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="•")
            self.password_toggle_btn.configure(text="👁️")
    
    def _set_loading_state(self, loading: bool) -> None:
        """
        Enable/disable loading state.
        
        Args:
            loading: True to show loading state, False otherwise
        """
        if loading:
            self.login_btn.configure(
                text="Authenticating...",
                state="disabled",
                fg_color=Colors.TEXT_MUTED
            )
            self.username_entry.configure(state="disabled")
            self.password_entry.configure(state="disabled")
            self.password_toggle_btn.configure(state="disabled")
        else:
            self.login_btn.configure(
                text="Login",
                state="normal",
                fg_color=Colors.PRIMARY
            )
            self.username_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
            self.password_toggle_btn.configure(state="normal")
    
    def _attempt_login(self) -> None:
        """Validate credentials and attempt login."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Validate inputs
        if not username:
            self._show_error("Please enter your username")
            return
        
        if not password:
            self._show_error("Please enter your password")
            return
        
        # Set loading state
        self._set_loading_state(True)
        
        try:
            # Initialize auth service
            self.auth_service = AuthService(self.connection_manager)
            
            # Attempt login
            session = self.auth_service.login(username, password)
            
            # Prepare user data for callback
            user_data = {
                'id': session.user_id,
                'username': session.username,
                'full_name': session.full_name,
                'role': session.role,
                'session_token': session.token,
                'expires_at': session.expires_at.isoformat()
            }
            
            logger.info(f"Login successful for user: {username}")
            
            # Call success callback
            self.after(200, lambda: self.on_login_success(user_data))
            
        except AccountLockedError as e:
            self._set_loading_state(False)
            self._show_error(str(e))
            
        except AuthenticationError as e:
            self._set_loading_state(False)
            self._show_error(str(e))
            
        except Exception as e:
            self._set_loading_state(False)
            logger.exception(f"Unexpected login error: {e}")
            self._show_error("An unexpected error occurred. Please try again.")
    
    def _show_error(self, message: str) -> None:
        """
        Display error message to user.
        
        Args:
            message: Error message to display
        """
        # Highlight password field
        self.password_entry.configure(border_color=Colors.DANGER)
        self.username_entry.configure(border_color=Colors.DANGER)
        
        # Show message box
        self.after(100, lambda: messagebox.showerror("Login Failed", message))
        
        # Reset border colors after delay
        self.after(2000, lambda: self._reset_field_colors())
    
    def _reset_field_colors(self) -> None:
        """Reset input field border colors to default."""
        if hasattr(self, 'username_entry') and hasattr(self, 'password_entry'):
            self.username_entry.configure(border_color=Colors.BORDER)
            self.password_entry.configure(border_color=Colors.BORDER)
    
    def refresh(self) -> None:
        """Refresh screen (called when navigating back to login)."""
        # Clear fields
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self._reset_field_colors()
        self._set_loading_state(False)
        self.after(100, lambda: self.username_entry.focus())