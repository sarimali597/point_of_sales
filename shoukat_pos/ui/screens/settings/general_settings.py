"""General Settings screen for shop configuration."""

from typing import Any
import customtkinter as ctk
from ui.theme import Colors, Fonts


class GeneralSettingsScreen(ctk.CTkFrame):
    """General Settings screen for shop configuration."""
    
    def __init__(self, parent: ctk.CTkFrame, *args: Any, **kwargs: Any) -> None:
        """Initialize the general settings screen.
        
        Args:
            parent: Parent widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, fg_color=Colors.BACKGROUND, *args, **kwargs)
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="Settings",
            font=(Fonts.PRIMARY, Fonts.XL, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=24, pady=24)
        
        # Placeholder message
        placeholder = ctk.CTkLabel(
            self,
            text="⚙️ Settings Screen\n\nThis screen will include:\n" +
                 "• Shop information (name, address, phone)\n" +
                 "• Tax rate configuration\n" +
                 "• User management\n" +
                 "• Printer settings\n" +
                 "• Secret code mapping\n" +
                 "• Backup & restore",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        )
        placeholder.pack(expand=True)
