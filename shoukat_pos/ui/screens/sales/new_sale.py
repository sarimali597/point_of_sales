"""New Sale screen for processing sales transactions."""

from typing import Any
import customtkinter as ctk
from ui.theme import Colors, Fonts


class NewSaleScreen(ctk.CTkFrame):
    """New Sale screen for processing sales."""
    
    def __init__(self, parent: ctk.CTkFrame, *args: Any, **kwargs: Any) -> None:
        """Initialize the new sale screen.
        
        Args:
            parent: Parent widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, fg_color=Colors.BACKGROUND, *args, **kwargs)
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="New Sale",
            font=(Fonts.PRIMARY, Fonts.XL, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=24, pady=24)
        
        # Placeholder message
        placeholder = ctk.CTkLabel(
            self,
            text="🛍️ New Sale Screen\n\nThis screen will include:\n" +
                 "• Barcode scanner input\n" +
                 "• Product search\n" +
                 "• Shopping cart\n" +
                 "• Payment processing\n" +
                 "• Receipt printing",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        )
        placeholder.pack(expand=True)
