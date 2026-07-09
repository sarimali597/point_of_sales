"""Main application window and screen router for Shoukat POS.

This module provides the App class (main window), LoginApp class (authentication),
and ScreenRouter for managing screen navigation with frame caching.
"""

from typing import Dict, Type, Optional, Any
import customtkinter as ctk
from ui.theme import Theme, Colors, Fonts, Breakpoints
from ui.animations import Animation
from services.auth_service import AuthService
from database.connection import ConnectionManager


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
            Animation.fade_in(current_frame, duration_ms=150)
        
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


class LoginApp(ctk.CTk):
    """Login application window for Shoukat POS.
    
    This class provides the authentication screen before accessing the main POS.
    
    Attributes:
        auth_service: AuthService instance for authentication.
        connection_manager: Database connection manager.
    """
    
    def __init__(self, connection_manager: ConnectionManager) -> None:
        """Initialize the login application.
        
        Args:
            connection_manager: Database connection manager instance.
        """
        super().__init__()
        
        self.connection_manager = connection_manager
        self.auth_service = AuthService(connection_manager)
        
        # Apply theme
        self.theme = Theme()
        self.theme.apply()
        
        # Window configuration
        self.title("Shoukat POS - Login")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Center window
        self._center_window()
        
        # Build UI
        self._build_login_ui()
    
    def _center_window(self) -> None:
        """Center the window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _build_login_ui(self) -> None:
        """Build the login user interface."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Logo and title
        logo_label = ctk.CTkLabel(
            main_frame,
            text="🏪",
            font=(Fonts.PRIMARY, 48),
        )
        logo_label.pack(pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Shoukat Sons Garments",
            font=(Fonts.PRIMARY, 20, Fonts.BOLD),
            text_color=Colors.PRIMARY,
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Point of Sale System",
            font=(Fonts.PRIMARY, 14),
            text_color=Colors.TEXT_SECONDARY,
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Username field
        username_label = ctk.CTkLabel(
            main_frame,
            text="Username",
            font=(Fonts.PRIMARY, Fonts.MD),
            anchor="w",
        )
        username_label.pack(fill="x", pady=(0, 8))
        
        self.username_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter username",
            height=44,
            corner_radius=8,
            font=(Fonts.PRIMARY, Fonts.MD),
        )
        self.username_entry.pack(fill="x", pady=(0, 20))
        self.username_entry.bind("<Return>", lambda e: self._attempt_login())
        
        # Password field
        password_label = ctk.CTkLabel(
            main_frame,
            text="Password",
            font=(Fonts.PRIMARY, Fonts.MD),
            anchor="w",
        )
        password_label.pack(fill="x", pady=(0, 8))
        
        self.password_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter password",
            show="•",
            height=44,
            corner_radius=8,
            font=(Fonts.PRIMARY, Fonts.MD),
        )
        self.password_entry.pack(fill="x", pady=(0, 20))
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())
        
        # Error message label
        self.error_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=(Fonts.PRIMARY, Fonts.SM),
            text_color=Colors.DANGER,
            justify="center",
        )
        self.error_label.pack(pady=(0, 20))
        
        # Login button
        login_btn = ctk.CTkButton(
            main_frame,
            text="Login",
            command=self._attempt_login,
            height=44,
            corner_radius=8,
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
            fg_color=Colors.PRIMARY,
            hover_color=Colors.PRIMARY_DARK,
        )
        login_btn.pack(fill="x", pady=(0, 10))
        
        # Default credentials hint
        hint_label = ctk.CTkLabel(
            main_frame,
            text="Default: admin / admin123",
            font=(Fonts.PRIMARY, Fonts.XS),
            text_color=Colors.TEXT_SECONDARY,
            justify="center",
        )
        hint_label.pack()
    
    def _attempt_login(self) -> None:
        """Attempt to login with provided credentials."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.error_label.configure(text="Please enter both username and password")
            return
        
        try:
            # Attempt login
            user = self.auth_service.login(username, password)
            
            if user:
                # Login successful
                self.destroy()
                
                # Launch main application
                from ui.app import App
                app = App(user=user, connection_manager=self.connection_manager)
                app.run()
            else:
                # Login failed
                self.error_label.configure(text="Invalid username or password")
                self.password_entry.delete(0, 'end')
                
        except Exception as e:
            self.error_label.configure(text=f"Login error: {str(e)}")
    
    def run(self) -> None:
        """Start the login application main loop."""
        self.mainloop()


class App(ctk.CTk):
    """Main application window for Shoukat POS.
    
    This class sets up the main window, sidebar navigation,
    and screen routing infrastructure.
    
    Attributes:
        router: ScreenRouter instance for navigation.
        sidebar: Navigation sidebar frame.
        content_area: Main content area frame.
        current_user: Currently logged-in user.
        connection_manager: Database connection manager.
    """
    
    def __init__(
        self,
        user: Optional[Dict[str, Any]] = None,
        connection_manager: Optional[ConnectionManager] = None
    ) -> None:
        """Initialize the main application.
        
        Args:
            user: Logged-in user dictionary.
            connection_manager: Database connection manager instance.
        """
        super().__init__()
        
        self.current_user = user or {"username": "admin", "role": "admin"}
        self.connection_manager = connection_manager
        
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
        
        # Initialize router BEFORE registering screens
        self.router = ScreenRouter(self.content_area)
        self._register_screens()
        
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
            text=f"👤 {self.current_user.get('username', 'User')}",
            text_color=Colors.CARD,
            font=(Fonts.PRIMARY, Fonts.SM),
            anchor="w",
        )
        user_label.pack(fill="x")
        
        role_label = ctk.CTkLabel(
            bottom_frame,
            text=self.current_user.get('role', 'user').title(),
            text_color=Colors.CARD,
            font=(Fonts.PRIMARY, Fonts.XS),
            anchor="w",
        )
        role_label.pack(fill="x")
        
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
            command=self._logout,
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
    
    def _register_screens(self) -> None:
        """Register all application screens with the router."""
        try:
            from ui.screens.dashboard_screen import DashboardScreen
            self.router.register("dashboard", DashboardScreen)
        except Exception as e:
            print(f"Warning: Could not register dashboard: {e}")
        
        try:
            from ui.screens.sales.new_sale import NewSaleScreen
            self.router.register("new_sale", NewSaleScreen)
        except Exception as e:
            print(f"Warning: Could not register new_sale: {e}")
        
        try:
            from ui.screens.products.product_list import ProductListScreen
            self.router.register("products", ProductListScreen)
        except Exception as e:
            print(f"Warning: Could not register products: {e}")
        
        try:
            from ui.screens.customers.customer_manager import CustomerManagerScreen
            self.router.register("customers", CustomerManagerScreen)
        except Exception as e:
            print(f"Warning: Could not register customers: {e}")
        
        try:
            from ui.screens.reports.sales_report import SalesReportScreen
            self.router.register("reports", SalesReportScreen)
        except Exception as e:
            print(f"Warning: Could not register reports: {e}")
        
        try:
            from ui.screens.settings.general_settings import GeneralSettingsScreen
            self.router.register("settings", GeneralSettingsScreen)
        except Exception as e:
            print(f"Warning: Could not register settings: {e}")
        
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
    
    def _logout(self) -> None:
        """Logout and return to login screen."""
        self.destroy()
        
        # Re-launch login screen
        login_app = LoginApp(self.connection_manager)
        login_app.run()
    
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
