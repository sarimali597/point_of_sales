"""Login screen for Shoukat POS."""

from typing import Any, Optional
import customtkinter as ctk
from ui.theme import Colors, Fonts


class LoginScreen(ctk.CTkFrame):
    """Login screen with username and password fields."""
    
    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_login: Optional[callable] = None,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Initialize the login screen.
        
        Args:
            parent: Parent widget.
            on_login: Callback function when login is successful.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, fg_color=Colors.BACKGROUND, *args, **kwargs)
        
        self.on_login = on_login
        
        self._build_login_screen()
    
    def _build_login_screen(self) -> None:
        """Build the login screen layout."""
        # Center frame
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Title card
        title_card = ctk.CTkFrame(
            center_frame,
            fg_color=Colors.CARD,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
        )
        title_card.pack(pady=(0, 24))
        
        # App icon
        icon_label = ctk.CTkLabel(
            title_card,
            text="🏪",
            font=(Fonts.PRIMARY, 64),
        )
        icon_label.pack(pady=(32, 16))
        
        # App name
        app_name = ctk.CTkLabel(
            title_card,
            text="Shoukat Sons Garments",
            font=(Fonts.PRIMARY, Fonts.XL, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        app_name.pack(pady=(0, 8))
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            title_card,
            text="Point of Sale System",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        )
        subtitle.pack(pady=(0, 32))
        
        # Login form card
        form_card = ctk.CTkFrame(
            center_frame,
            fg_color=Colors.CARD,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER,
        )
        form_card.pack()
        
        # Username field
        username_label = ctk.CTkLabel(
            form_card,
            text="Username",
            font=(Fonts.PRIMARY, Fonts.SM),
            text_color=Colors.TEXT_SECONDARY,
        )
        username_label.grid(row=0, column=0, padx=24, pady=(24, 8), sticky="w")
        
        self.username_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="Enter username",
            width=280,
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.BACKGROUND,
        )
        self.username_entry.grid(row=1, column=0, padx=24, pady=(0, 16))
        
        # Password field
        password_label = ctk.CTkLabel(
            form_card,
            text="Password",
            font=(Fonts.PRIMARY, Fonts.SM),
            text_color=Colors.TEXT_SECONDARY,
        )
        password_label.grid(row=2, column=0, padx=24, pady=(8, 8), sticky="w")
        
        self.password_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="Enter password",
            show="•",
            width=280,
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.BACKGROUND,
        )
        self.password_entry.grid(row=3, column=0, padx=24, pady=(0, 24))
        
        # Bind Enter key to login
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())
        
        # Login button
        login_btn = ctk.CTkButton(
            form_card,
            text="Login",
            command=self._attempt_login,
            width=280,
            height=44,
            corner_radius=8,
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
        )
        login_btn.grid(row=4, column=0, padx=24, pady=(0, 24))
        
        # Error message label (hidden by default)
        self.error_label = ctk.CTkLabel(
            form_card,
            text="",
            font=(Fonts.PRIMARY, Fonts.SM),
            text_color=Colors.DANGER,
        )
        self.error_label.grid(row=5, column=0, padx=24, pady=(0, 16))
    
    def _attempt_login(self) -> None:
        """Attempt to login with entered credentials."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        # Clear previous error
        self.error_label.configure(text="")
        
        # Validate input
        if not username or not password:
            self.error_label.configure(text="Please enter both username and password")
            return
        
        # Call login callback if provided
        if self.on_login:
            self.on_login(username, password)
        else:
            # Default behavior - just clear fields
            self.username_entry.delete(0, "end")
            self.password_entry.delete(0, "end")
            self.error_label.configure(text="Login functionality not implemented yet")
    
    def focus_username(self) -> None:
        """Focus the username entry field."""
        self.username_entry.focus()
