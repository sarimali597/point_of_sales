"""
Dashboard Screen for Shoukat POS.

Main command center showing sales statistics, quick actions, and recent activity.
Provides real-time overview of store performance.
"""
import customtkinter as ctk
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ui.theme import Colors, Breakpoints, Animation
from ui.components import StatCard

logger = logging.getLogger(__name__)


class DashboardScreen(ctk.CTkFrame):
    """
    Dashboard screen with key metrics and quick actions.
    
    Features:
    - Dynamic greeting based on time of day
    - Auto-refreshing stat cards (sales, orders, low stock, credit)
    - Quick action buttons for common tasks
    - Recent transactions table
    - Responsive grid layout
    """
    
    def __init__(
        self, 
        parent: ctk.CTkFrame,
        user_data: Dict[str, Any],
        **kwargs: Any
    ):
        """
        Initialize dashboard screen.
        
        Args:
            parent: Parent container widget
            user_data: Current user information dictionary
            **kwargs: Additional keyword arguments passed to CTkFrame
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.user_data = user_data
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Content area expands
        
        # Create UI components
        self._create_header()
        self._create_stats_grid()
        self._create_quick_actions()
        self._create_recent_activity()
        
        # Apply fade-in animation
        Animation.fade_in(self, duration_ms=200)
        
        logger.debug("Dashboard screen initialized")
    
    def _create_header(self) -> None:
        """Create header with greeting and date."""
        header_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=80
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        header_frame.grid_propagate(False)
        
        # Greeting
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning"
        elif hour < 17:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        
        greeting_label = ctk.CTkLabel(
            header_frame,
            text=f"{greeting}, {self.user_data['full_name']}!",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        greeting_label.pack(anchor="w")
        
        # Date
        date_str = datetime.now().strftime("%A, %d %B %Y")
        date_label = ctk.CTkLabel(
            header_frame,
            text=date_str,
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w"
        )
        date_label.pack(anchor="w", pady=(5, 0))
    
    def _create_stats_grid(self) -> None:
        """Create grid of statistic cards."""
        stats_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        stats_container.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        
        # Configure 4-column grid
        for i in range(4):
            stats_container.grid_columnconfigure(i, weight=1)
        
        # Stat card data
        stats_data = [
            {
                "title": "Today's Sales",
                "value": "Rs. 0",
                "trend": "+0%",
                "trend_positive": True,
                "color": Colors.PRIMARY
            },
            {
                "title": "Orders Today",
                "value": "0",
                "trend": "0 orders",
                "trend_positive": True,
                "color": Colors.SUCCESS
            },
            {
                "title": "Low Stock Items",
                "value": "0",
                "trend": "Need attention",
                "trend_positive": False,
                "color": Colors.WARNING
            },
            {
                "title": "Pending Credit",
                "value": "Rs. 0",
                "trend": "Outstanding",
                "trend_positive": False,
                "color": Colors.DANGER
            }
        ]
        
        # Create stat cards
        self.stat_cards = []
        for i, data in enumerate(stats_data):
            col = i % 4
            row = i // 4
            
            card = StatCard(
                stats_container,
                title=data["title"],
                value=data["value"],
                trend=data["trend"],
                trend_positive=data["trend_positive"],
                color=data["color"],
                command=lambda d=data: self._on_stat_click(d)
            )
            card.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
            self.stat_cards.append(card)
    
    def _create_quick_actions(self) -> None:
        """Create quick action buttons grid."""
        actions_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        actions_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=10)
        actions_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            actions_frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        # Actions grid container
        actions_grid = ctk.CTkFrame(
            actions_frame,
            fg_color="transparent"
        )
        actions_grid.grid(row=1, column=0, sticky="ew")
        
        # Configure 5-column grid
        for i in range(5):
            actions_grid.grid_columnconfigure(i, weight=1)
        
        # Action buttons data
        actions = [
            ("🛒 New Sale", "pos", Colors.PRIMARY),
            ("➕ Add Product", "products", Colors.SUCCESS),
            ("👤 Customers", "customers", Colors.INFO),
            ("📊 Reports", "reports", Colors.WARNING),
            ("⚙️ Settings", "settings", Colors.TEXT_SECONDARY)
        ]
        
        self.action_buttons = []
        for i, (text, screen, color) in enumerate(actions):
            btn = ctk.CTkButton(
                actions_grid,
                text=text,
                command=lambda s=screen: self._navigate_to(s),
                height=60,
                font=ctk.CTkFont(size=13),
                fg_color=color,
                hover_color=self._lighten_color(color)
            )
            btn.grid(row=0, column=i, sticky="ew", padx=5)
            self.action_buttons.append(btn)
    
    def _create_recent_activity(self) -> None:
        """Create recent transactions section."""
        recent_frame = ctk.CTkFrame(
            self,
            fg_color=Colors.CARD,
            corner_radius=10
        )
        recent_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(10, 20))
        
        # Header
        header = ctk.CTkFrame(
            recent_frame,
            fg_color="transparent"
        )
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        title_label = ctk.CTkLabel(
            header,
            text="Recent Transactions",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        title_label.pack(side="left")
        
        view_all_btn = ctk.CTkButton(
            header,
            text="View All",
            width=80,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=Colors.BORDER,
            text_color=Colors.PRIMARY,
            command=lambda: self._navigate_to("reports")
        )
        view_all_btn.pack(side="right")
        
        # Empty state (no transactions yet)
        empty_label = ctk.CTkLabel(
            recent_frame,
            text="No transactions today\nSales will appear here",
            font=ctk.CTkFont(size=13),
            text_color=Colors.TEXT_MUTED,
            justify="center"
        )
        empty_label.pack(pady=40)
    
    def _on_stat_click(self, data: Dict[str, Any]) -> None:
        """
        Handle stat card click.
        
        Args:
            data: Stat card data dictionary
        """
        title = data.get("title", "")
        if "Sales" in title or "Orders" in title:
            self._navigate_to("reports")
        elif "Stock" in title:
            self._navigate_to("products")
        elif "Credit" in title:
            self._navigate_to("customers")
    
    def _navigate_to(self, screen_name: str) -> None:
        """
        Navigate to another screen.
        
        Args:
            screen_name: Target screen identifier
        """
        # Get parent app reference and navigate
        app = self.winfo_toplevel()
        if hasattr(app, '_navigate'):
            app._navigate(screen_name)
    
    def _lighten_color(self, color: str) -> str:
        """
        Lighten a hex color slightly for hover state.
        
        Args:
            color: Hex color string (#RRGGBB)
            
        Returns:
            Lightened hex color
        """
        # Simple lightening by increasing RGB values
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            factor = 1.1
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return color
    
    def refresh(self, **kwargs: Any) -> None:
        """
        Refresh dashboard data.
        
        Args:
            **kwargs: Optional data to update
        """
        # In production, this would fetch fresh data from services
        # For now, just log the refresh
        logger.debug("Dashboard refreshed")