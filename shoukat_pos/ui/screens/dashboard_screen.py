"""Dashboard screen with auto-refreshing stat cards."""

from typing import Any, Optional
import customtkinter as ctk
from ui.theme import Colors, Fonts
from ui.components import StatCard


class DashboardScreen(ctk.CTkFrame):
    """Dashboard screen displaying key metrics and quick actions."""
    
    def __init__(self, parent: ctk.CTkFrame, *args: Any, **kwargs: Any) -> None:
        """Initialize the dashboard screen.
        
        Args:
            parent: Parent widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, fg_color=Colors.BACKGROUND, *args, **kwargs)
        
        self._build_dashboard()
    
    def _build_dashboard(self) -> None:
        """Build the dashboard layout."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=(Fonts.PRIMARY, Fonts.XL, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        title_label.pack(anchor="w", padx=24, pady=(24, 16))
        
        # Stats grid
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=24, pady=8)
        
        # Configure grid for 4 columns
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        # Today's Sales card
        sales_card = StatCard(
            stats_frame,
            title="Today's Sales",
            value="Rs. 0",
            change=None,
            icon="💰",
        )
        sales_card.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        
        # Total Orders card
        orders_card = StatCard(
            stats_frame,
            title="Total Orders",
            value="0",
            change=None,
            icon="🛍️",
        )
        orders_card.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        
        # Low Stock card
        stock_card = StatCard(
            stats_frame,
            title="Low Stock Items",
            value="0",
            change=None,
            icon="⚠️",
            color=Colors.WARNING,
        )
        stock_card.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        
        # Customers card
        customers_card = StatCard(
            stats_frame,
            title="Total Customers",
            value="0",
            change=None,
            icon="👥",
        )
        customers_card.grid(row=0, column=3, padx=8, pady=8, sticky="ew")
        
        # Quick actions section
        actions_title = ctk.CTkLabel(
            self,
            text="Quick Actions",
            font=(Fonts.PRIMARY, Fonts.LG, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        actions_title.pack(anchor="w", padx=24, pady=(24, 16))
        
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=24, pady=8)
        
        # New Sale button
        new_sale_btn = ctk.CTkButton(
            actions_frame,
            text="🛍️ New Sale",
            width=140,
            height=44,
            font=(Fonts.PRIMARY, Fonts.MD),
        )
        new_sale_btn.pack(side="left", padx=8)
        
        # Add Product button
        add_product_btn = ctk.CTkButton(
            actions_frame,
            text="👕 Add Product",
            width=140,
            height=44,
            fg_color=Colors.SECONDARY,
            hover_color=Colors.SECONDARY_LIGHT,
            font=(Fonts.PRIMARY, Fonts.MD),
        )
        add_product_btn.pack(side="left", padx=8)
        
        # Print Labels button
        print_labels_btn = ctk.CTkButton(
            actions_frame,
            text="🏷️ Print Labels",
            width=140,
            height=44,
            fg_color=Colors.ACCENT,
            hover_color=Colors.ACCENT_LIGHT,
            font=(Fonts.PRIMARY, Fonts.MD),
        )
        print_labels_btn.pack(side="left", padx=8)
