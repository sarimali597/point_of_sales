"""Customer Manager screen for managing customers and credit."""

from typing import Any
import customtkinter as ctk
from ui.theme import Colors, Fonts


class CustomerManagerScreen(ctk.CTkFrame):
    """Customer Manager screen for customer management."""
    
    def __init__(self, parent: ctk.CTkFrame, *args: Any, **kwargs: Any) -> None:
        """Initialize the customer manager screen.
        
        Args:
            parent: Parent widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, fg_color=Colors.BACKGROUND, *args, **kwargs)
        
        # Title
        title = ctk.CTkLabel(
            self,
            text="Customers",
            font=(Fonts.PRIMARY, Fonts.XL, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=24, pady=24)
        
        # Placeholder message
        placeholder = ctk.CTkLabel(
            self,
            text="👥 Customers Screen\n\nThis screen will include:\n" +
                 "• Customer list with search\n" +
                 "• Customer details\n" +
                 "• Purchase history\n" +
                 "• Credit payment recording\n" +
                 "• Add/Edit/Delete actions",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        )
        placeholder.pack(expand=True)
