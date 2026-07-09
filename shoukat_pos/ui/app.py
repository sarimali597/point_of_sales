"""Main application window and screen router for Shoukat POS.

This module provides the App class (main window) and ScreenRouter
for managing screen navigation with frame caching.
"""

from typing import Dict, Type, Optional, Any
import customtkinter as ctk
from ui.theme import Theme, Colors, Fonts, Breakpoints
from ui.animations import Animation


class ScreenRouter:
    """Screen router with frame caching for instant navigation.
    
    This router maintains instantiated screen frames in memory and uses
    lift() to bring active screens to the front, avoiding flicker and
    preserving scroll positions.
    
    Attributes:
        container: Parent widget that holds all screens.
        screens: Dictionary of screen name to frame instance.
        current_screen: Name of currently visible screen.
    """
    
    def __init__(self, container: ctk.CTkFrame) -> None:
        """Initialize the screen router.
        
        Args:
            container: Parent widget to hold all screen frames.
        """
        self.container = container
        self.screens: Dict[str, ctk.CTkFrame] = {}
        self.current_screen: Optional[str] = None
        self._history: list = []
    
    def register(
        self,
        name: str,
        screen_class: Type[ctk.CTkFrame],
        **kwargs: Any
    ) -> None:
        """Register a screen class for later navigation.
        
        Args:
            name: Unique screen identifier.
            screen_class: The screen class (not instance).
            **kwargs: Arguments to pass when instantiating the screen.
        """
        assert name not in self.screens, f"Screen '{name}' already registered"
        
        # Instantiate and store the screen
        screen = screen_class(self.container, **kwargs)
        self.screens[name] = screen
        
        # Position off-screen initially
        screen.place(x=0, y=0, relwidth=1, relheight=1)
        screen.lower()
    
    def navigate_to(
        self,
        name: str,
        push_history: bool = True,
        animate: bool = True
    ) -> None:
        """Navigate to a registered screen.
        
        Args:
            name: Screen identifier to navigate to.
            push_history: Whether to add current screen to history.
            animate: Whether to animate the transition.
        """
        assert name in self.screens, f"Screen '{name}' not registered"
        
        if self.current_screen == name:
            return  # Already on this screen
        
        # Push current screen to history
        if push_history and self.current_screen:
            self._history.append(self.current_screen)
        
        # Get target screen
        target_screen = self.screens[name]
        
        # Bring to front
        target_screen.lift()
        
        # Animate if requested
        if animate and self.current_screen:
            current_frame = self.screens[self.current_screen]
            Animation.fade_in(target_frame, duration_ms=150)
        
        self.current_screen = name
    
    def go_back(self) -> None:
        """Navigate back to previous screen."""
        if not self._history:
            return
        
        previous = self._history.pop()
        self.navigate_to(previous, push_history=False)
    
    def clear_history(self) -> None:
        """Clear navigation history."""
        self._history.clear()


class App(ctk.CTk):
    """Main application window for Shoukat POS.
    
    This class sets up the main window, sidebar navigation,
    and screen routing infrastructure.
    
    Attributes:
        router: ScreenRouter instance for navigation.
        sidebar: Navigation sidebar frame.
        content_area: Main content area frame.
    """
    
    def __init__(self) -> None:
        """Initialize the main application."""
        super().__init__()
        
        # Apply theme
        self.theme = Theme()
        self.theme.apply()
        
        # Window configuration
        self.title("Shoukat Sons Garments - POS")
        self.geometry("1440x900")
        self.minsize(1024, 768)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Current breakpoint
        self.current_breakpoint = "standard"
        
        # Build UI
        self._build_sidebar()
        self._build_content_area()
        
        # Initialize router
        self.router = ScreenRouter(self.content_area)
        
        # Bind resize event for responsive layout
        self.bind("<Configure>", self._on_resize)
    
    def _build_sidebar(self) -> None:
        """Build the navigation sidebar."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            fg_color=Colors.PRIMARY,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns", rowspan=1)
        self.sidebar.grid_propagate(False)
        
        # Logo area
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            height=80,
        )
        logo_frame.pack(fill="x", padx=16, pady=(16, 8))
        logo_frame.pack_propagate(False)
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="🏪\nShoukat Sons",
            text_color=Colors.CARD,
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            justify="left",
        )
        logo_label.place(rely=0.5, anchor="center")
        
        # Navigation buttons
        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("🛍️", "New Sale", "new_sale"),
            ("👕", "Products", "products"),
            ("👥", "Customers", "customers"),
            ("📈", "Reports", "reports"),
            ("⚙️", "Settings", "settings"),
        ]
        
        for icon, text, screen_name in nav_items:
            btn = self._create_nav_button(icon, text, screen_name)
            btn.pack(fill="x", padx=8, pady=2)
        
        # Bottom section (user info)
        bottom_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
        )
        bottom_frame.pack(side="bottom", fill="x", padx=16, pady=16)
        
        user_label = ctk.CTkLabel(
            bottom_frame,
            text="👤 Admin",
            text_color=Colors.CARD,
            font=(Fonts.PRIMARY, Fonts.SM),
            anchor="w",
        )
        user_label.pack(fill="x")
        
        logout_btn = ctk.CTkButton(
            bottom_frame,
            text="Logout",
            width=160,
            height=32,
            fg_color="transparent",
            border_width=1,
            border_color=Colors.CARD,
            text_color=Colors.CARD,
            hover_color=Colors.PRIMARY_LIGHT,
            font=(Fonts.PRIMARY, Fonts.SM),
        )
        logout_btn.pack(fill="x", pady=(8, 0))
    
    def _create_nav_button(
        self,
        icon: str,
        text: str,
        screen_name: str
    ) -> ctk.CTkButton:
        """Create a navigation button.
        
        Args:
            icon: Icon emoji.
            text: Button text.
            screen_name: Target screen name.
            
        Returns:
            Created button instance.
        """
        def on_click() -> None:
            # Update button states
            for child in self.sidebar.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(fg_color="transparent")
            
            # Navigate
            self.router.navigate_to(screen_name)
        
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"{icon}  {text}",
            command=on_click,
            anchor="w",
            height=44,
            corner_radius=8,
            fg_color="transparent",
            hover_color=Colors.PRIMARY_LIGHT,
            font=(Fonts.PRIMARY, Fonts.MD),
        )
        
        # Set active state for first button (Dashboard)
        if screen_name == "dashboard":
            btn.configure(fg_color=Colors.PRIMARY_LIGHT)
        
        return btn
    
    def _build_content_area(self) -> None:
        """Build the main content area."""
        self.content_area = ctk.CTkFrame(
            self,
            fg_color=Colors.BACKGROUND,
        )
        self.content_area.grid(row=0, column=1, sticky="nsew")
        
        # Register all screens
        self._register_screens()
    
    def _register_screens(self) -> None:
        """Register all application screens with the router."""
        from ui.screens.dashboard_screen import DashboardScreen
        from ui.screens.sales.new_sale import NewSaleScreen
        from ui.screens.products.product_list import ProductListScreen
        from ui.screens.customers.customer_manager import CustomerManagerScreen
        from ui.screens.reports.sales_report import SalesReportScreen
        from ui.screens.settings.general_settings import GeneralSettingsScreen
        
        # Register screens
        self.router.register("dashboard", DashboardScreen)
        self.router.register("new_sale", NewSaleScreen)
        self.router.register("products", ProductListScreen)
        self.router.register("customers", CustomerManagerScreen)
        self.router.register("reports", SalesReportScreen)
        self.router.register("settings", GeneralSettingsScreen)
        
        # Navigate to dashboard by default
        self.router.navigate_to("dashboard", push_history=False, animate=False)
    
    def _on_resize(self, event: Any) -> None:
        """Handle window resize for responsive layout.
        
        Args:
            event: Configure event.
        """
        if event.widget != self:
            return
        
        width = self.winfo_width()
        new_breakpoint = Breakpoints.get_breakpoint(width)
        
        if new_breakpoint != self.current_breakpoint:
            self.current_breakpoint = new_breakpoint
            config = self.theme.get_responsive_config(width)
            
            # Adjust sidebar width
            new_width = config["sidebar_width"]
            self.sidebar.configure(width=new_width)
            
            # TODO: Adjust other layout elements based on breakpoint
    
    def register_screen(
        self,
        name: str,
        screen_class: Type[ctk.CTkFrame],
        **kwargs: Any
    ) -> None:
        """Register a screen for navigation.
        
        Args:
            name: Unique screen identifier.
            screen_class: The screen class to instantiate.
            **kwargs: Arguments to pass to screen constructor.
        """
        self.router.register(name, screen_class, **kwargs)
    
    def navigate_to(self, screen_name: str) -> None:
        """Navigate to a screen.
        
        Args:
            screen_name: Screen identifier.
        """
        self.router.navigate_to(screen_name)
    
    def run(self) -> None:
        """Start the application main loop."""
        self.mainloop()
