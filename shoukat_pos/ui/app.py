"""
Main Application Window for Shoukat POS.

Implements the main CTk window with screen router, frame caching,
sidebar navigation, and responsive layout management.
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Optional, Any, Type
import logging
from datetime import datetime

from ui.theme import Colors, Breakpoints, ThemeManager
from ui.screens.login_screen import LoginScreen
from ui.screens.dashboard_screen import DashboardScreen

logger = logging.getLogger(__name__)


class ScreenRouter:
    """
    Screen router with frame caching for instant navigation.
    
    Maintains a cache of instantiated screen frames and uses lift()
    to switch between them without destroying/recreating, preserving
    scroll position and state.
    """
    
    def __init__(self, parent: ctk.CTkFrame):
        """
        Initialize screen router.
        
        Args:
            parent: Parent container widget (usually main app frame)
        """
        self.parent = parent
        self.frames: Dict[str, ctk.CTkFrame] = {}
        self.current_screen: Optional[str] = None
        self.navigation_history: list = []
    
    def register_frame(self, name: str, frame: ctk.CTkFrame) -> None:
        """
        Register a screen frame in the cache.
        
        Args:
            name: Unique screen identifier
            frame: Frame instance to cache
        """
        assert name not in self.frames, f"Screen '{name}' already registered"
        frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        frame.lift()  # Bring to front initially
        self.frames[name] = frame
        logger.debug(f"Registered screen: {name}")
    
    def navigate_to(
        self, 
        name: str, 
        **kwargs: Any
    ) -> Optional[ctk.CTkFrame]:
        """
        Navigate to a screen by name.
        
        Args:
            name: Screen identifier to navigate to
            **kwargs: Data to pass to the screen (if it supports refresh)
            
        Returns:
            The navigated-to frame, or None if not found
        """
        if name not in self.frames:
            logger.error(f"Screen not found: {name}")
            return None
        
        # Track history for back navigation
        if self.current_screen and self.current_screen != name:
            self.navigation_history.append(self.current_screen)
            if len(self.navigation_history) > 10:
                self.navigation_history.pop(0)
        
        # Hide current screen
        if self.current_screen and self.current_screen in self.frames:
            self.frames[self.current_screen].lower()
        
        # Show target screen
        target_frame = self.frames[name]
        target_frame.lift()
        
        # Call refresh method if exists and kwargs provided
        if kwargs and hasattr(target_frame, 'refresh'):
            try:
                target_frame.refresh(**kwargs)
            except Exception as e:
                logger.error(f"Error refreshing screen {name}: {e}")
        
        self.current_screen = name
        logger.debug(f"Navigated to: {name}")
        return target_frame
    
    def go_back(self) -> Optional[str]:
        """
        Navigate to previous screen in history.
        
        Returns:
            Previous screen name, or None if no history
        """
        if not self.navigation_history:
            return None
        
        previous = self.navigation_history.pop()
        self.navigate_to(previous)
        return previous
    
    def clear_history(self) -> None:
        """Clear navigation history."""
        self.navigation_history.clear()


class App(ctk.CTk):
    """
    Main application window for Shoukat POS.
    
    Features:
    - Responsive layout with adaptive sidebar
    - Screen router with frame caching
    - Global session management
    - Graceful shutdown handling
    """
    
    def __init__(self):
        """Initialize main application window."""
        super().__init__()
        
        # Configure root window
        self.title("Shoukat POS - Garment Retail Management")
        self.geometry("1400x900")
        self.minsize(1024, 768)
        
        # Apply theme
        ThemeManager.apply_theme()
        
        # State
        self.current_user: Optional[Dict[str, Any]] = None
        self.sidebar_collapsed = False
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create components
        self._create_sidebar()
        self._create_main_area()
        self._create_router()
        
        # Bind events
        self.bind("<Configure>", self._on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Show login screen first
        self._show_login()
        
        logger.info("Application initialized")
    
    def _create_sidebar(self) -> None:
        """Create left sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0,
            fg_color=Colors.PRIMARY
        )
        self.sidebar.grid(row=0, column=0, sticky="ns", rowspan=1)
        self.sidebar.grid_propagate(False)
        
        # Logo area
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            height=100
        )
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        logo_frame.grid_propagate(False)
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="SHOUKAT SONS",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Colors.CARD
        )
        logo_label.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            logo_frame,
            text="Garments POS",
            font=ctk.CTkFont(size=11),
            text_color=Colors.TEXT_MUTED
        )
        subtitle.pack(anchor="w")
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", "dashboard"),
            ("New Sale", "pos"),
            ("Products", "products"),
            ("Customers", "customers"),
            ("Reports", "reports"),
            ("Settings", "settings"),
        ]
        
        for i, (text, screen_name) in enumerate(nav_buttons):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=lambda s=screen_name: self._navigate(s),
                fg_color="transparent",
                hover_color=Colors.PRIMARY_LIGHT,
                anchor="w",
                padx=20,
                height=45,
                font=ctk.CTkFont(size=14)
            )
            btn.grid(row=i+1, column=0, sticky="ew", padx=0, pady=2)
        
        # User info at bottom
        self.user_info_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        self.user_info_frame.grid(row=8, column=0, sticky="ew", padx=20, pady=20)
        
        self.user_label = ctk.CTkLabel(
            self.user_info_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=Colors.TEXT_MUTED
        )
        self.user_label.pack(anchor="w")
        
        self.logout_btn = ctk.CTkButton(
            self.user_info_frame,
            text="Logout",
            command=self._logout,
            fg_color=Colors.DANGER,
            hover_color=Colors.DANGER_LIGHT,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.logout_btn.pack(fill="x", pady=(5, 0))
    
    def _create_main_area(self) -> None:
        """Create main content area."""
        self.main_area = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=Colors.BACKGROUND
        )
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
    
    def _create_router(self) -> None:
        """Initialize screen router and register screens."""
        self.router = ScreenRouter(self.main_area)
        
        # Register initial screens (more will be added as we build them)
        # Dashboard will be created after login
        logger.debug("Screen router initialized")
    
    def _show_login(self) -> None:
        """Display login screen."""
        # Hide sidebar during login
        self.sidebar.grid_remove()
        
        # Create login screen
        self.login_screen = LoginScreen(self.main_area, on_login_success=self._on_login_success)
        self.router.register_frame("login", self.login_screen)
        self.router.navigate_to("login")
    
    def _on_login_success(self, user_data: Dict[str, Any]) -> None:
        """
        Handle successful login.
        
        Args:
            user_data: User information dictionary
        """
        self.current_user = user_data
        logger.info(f"User logged in: {user_data['username']}")
        
        # Show sidebar
        self.sidebar.grid()
        
        # Update user info
        self.user_label.configure(
            text=f"{user_data['full_name']}\n({user_data['role'].title()})"
        )
        
        # Create and show dashboard
        self.dashboard_screen = DashboardScreen(self.main_area, user_data=user_data)
        self.router.register_frame("dashboard", self.dashboard_screen)
        self.router.navigate_to("dashboard")
        
        # Register placeholder screens (to be implemented)
        self._register_placeholder_screens()
    
    def _register_placeholder_screens(self) -> None:
        """Register placeholder frames for unimplemented screens."""
        placeholders = ["pos", "products", "customers", "reports", "settings"]
        
        for screen_name in placeholders:
            placeholder = ctk.CTkFrame(self.main_area, fg_color=Colors.BACKGROUND)
            label = ctk.CTkLabel(
                placeholder,
                text=f"{screen_name.upper()} Screen\n(Coming Soon)",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=Colors.TEXT_SECONDARY
            )
            label.place(relx=0.5, rely=0.5, anchor="center")
            self.router.register_frame(screen_name, placeholder)
    
    def _navigate(self, screen_name: str) -> None:
        """
        Navigate to a screen.
        
        Args:
            screen_name: Target screen identifier
        """
        if not self.current_user:
            logger.warning("Navigation attempted without login")
            return
        
        self.router.navigate_to(screen_name)
    
    def _on_window_resize(self, event: Any) -> None:
        """Handle window resize for responsive layout."""
        if event.widget == self and event.width:
            config = Breakpoints.get_config(event.width)
            
            # Collapse sidebar in compact mode
            if config.sidebar_collapsed and not self.sidebar_collapsed:
                self.sidebar.grid_remove()
                self.sidebar_collapsed = True
            elif not config.sidebar_collapsed and self.sidebar_collapsed:
                self.sidebar.grid()
                self.sidebar_collapsed = False
    
    def _logout(self) -> None:
        """Handle logout action."""
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            logger.info("User logged out")
            self.current_user = None
            
            # Clear router and show login
            self.sidebar.grid_remove()
            self._show_login()
    
    def _on_close(self) -> None:
        """Handle application close event."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit Shoukat POS?"):
            logger.info("Application closing")
            self.destroy()


def run_app() -> None:
    """Start the application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run_app()