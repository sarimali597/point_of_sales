"""Product list screen with variant grid view."""

from typing import Any
import customtkinter as ctk
from ui.theme import Colors, Fonts


class ProductListScreen(ctk.CTkFrame):
    """Product list screen with search, filters, and variant grid."""
    
    def __init__(self, parent: ctk.CTkFrame, *args: Any, **kwargs: Any) -> None:
        """Initialize the product list screen.
        
        Args:
            parent: Parent widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, fg_color=Colors.BACKGROUND, *args, **kwargs)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Products",
            font=(Fonts.PRIMARY, Fonts.XL, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        title_label.pack(anchor="w", padx=24, pady=(24, 16))
        
        # Placeholder message
        placeholder = ctk.CTkLabel(
            self,
            text="Product list functionality coming soon...",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        )
        placeholder.pack(pady=100)
