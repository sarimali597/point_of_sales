"""Theme engine with responsive breakpoints for Shoukat POS.

This module defines the color palette, typography, spacing, and responsive
breakpoints used throughout the application UI.
"""

from typing import Dict, Any, Tuple
import customtkinter as ctk


class Colors:
    """Color palette for Shoukat POS."""
    
    # Primary colors
    PRIMARY = "#1A237E"
    PRIMARY_LIGHT = "#5C4FB1"
    PRIMARY_DARK = "#000051"
    
    # Secondary colors
    SECONDARY = "#0D47A1"
    SECONDARY_LIGHT = "#5472D3"
    SECONDARY_DARK = "#002171"
    
    # Accent
    ACCENT = "#00BCD4"
    ACCENT_LIGHT = "#62EFFF"
    ACCENT_DARK = "#008BA3"
    
    # Semantic colors
    SUCCESS = "#2E7D32"
    SUCCESS_LIGHT = "#60AD5E"
    WARNING = "#F57C00"
    WARNING_LIGHT = "#FFA04B"
    DANGER = "#C62828"
    DANGER_LIGHT = "#FF5F52"
    INFO = "#1976D2"
    
    # Neutral colors
    BACKGROUND = "#F5F5F5"
    CARD = "#FFFFFF"
    TEXT_PRIMARY = "#263238"
    TEXT_SECONDARY = "#546E7A"
    TEXT_MUTED = "#90A4AE"
    BORDER = "#E0E0E0"
    DIVIDER = "#BDBDBD"
    
    # State colors
    HOVER = "rgba(26, 35, 126, 0.08)"
    SELECTED = "rgba(13, 71, 161, 0.12)"
    DISABLED = "#BDBDBD"


class Breakpoints:
    """Responsive breakpoints for different screen sizes."""
    
    COMPACT = 1024    # < 1024px: single column, collapsible sidebar
    STANDARD = 1440   # 1024-1440px: two columns, visible sidebar
    WIDE = 1920       # > 1440px: three columns, expanded tables
    
    @classmethod
    def get_breakpoint(cls, width: int) -> str:
        """Get breakpoint name based on width.
        
        Args:
            width: Window width in pixels.
            
        Returns:
            Breakpoint name: 'compact', 'standard', or 'wide'.
        """
        assert width >= 0, "Width must be non-negative"
        
        if width < cls.COMPACT:
            return "compact"
        elif width < cls.WIDE:
            return "standard"
        else:
            return "wide"


class Spacing:
    """Spacing constants for consistent layout."""
    
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48
    
    # Component-specific spacing
    BUTTON_PADDING_X = 16
    BUTTON_PADDING_Y = 10
    CARD_PADDING = 16
    TABLE_ROW_HEIGHT = 40
    INPUT_HEIGHT = 40


class Fonts:
    """Typography settings."""
    
    # Font families
    PRIMARY = "Helvetica Neue"
    MONOSPACE = "Courier New"
    
    # Font sizes
    XS = 10
    SM = 12
    MD = 14
    LG = 18
    XL = 24
    XXL = 32
    
    # Font weights
    LIGHT = "normal"
    REGULAR = "normal"
    BOLD = "bold"


class Theme:
    """Theme configuration for CustomTkinter.
    
    This class configures the global appearance of the application,
    including colors, fonts, and component styling.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls) -> "Theme":
        """Singleton pattern to ensure single theme instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize theme (only once)."""
        if self._initialized:
            return
        self._initialized = True
        
    def apply(self) -> None:
        """Apply theme settings to CustomTkinter.
        
        Configures appearance mode, default colors, and font settings.
        Should be called before creating any widgets.
        """
        # Set appearance mode (Light/Dark/System)
        ctk.set_appearance_mode("Light")
        
        # Set default color theme
        ctk.set_default_color_theme("blue")
        
        # Configure default font
        ctk.set_widget_scaling(1.0)
        
    def get_colors(self) -> Dict[str, str]:
        """Get all color values as dictionary.
        
        Returns:
            Dictionary mapping color names to hex values.
        """
        return {
            "primary": Colors.PRIMARY,
            "primary_light": Colors.PRIMARY_LIGHT,
            "primary_dark": Colors.PRIMARY_DARK,
            "secondary": Colors.SECONDARY,
            "secondary_light": Colors.SECONDARY_LIGHT,
            "secondary_dark": Colors.SECONDARY_DARK,
            "accent": Colors.ACCENT,
            "accent_light": Colors.ACCENT_LIGHT,
            "accent_dark": Colors.ACCENT_DARK,
            "success": Colors.SUCCESS,
            "success_light": Colors.SUCCESS_LIGHT,
            "warning": Colors.WARNING,
            "warning_light": Colors.WARNING_LIGHT,
            "danger": Colors.DANGER,
            "danger_light": Colors.DANGER_LIGHT,
            "info": Colors.INFO,
            "background": Colors.BACKGROUND,
            "card": Colors.CARD,
            "text_primary": Colors.TEXT_PRIMARY,
            "text_secondary": Colors.TEXT_SECONDARY,
            "text_muted": Colors.TEXT_MUTED,
            "border": Colors.BORDER,
            "divider": Colors.DIVIDER,
            "disabled": Colors.DISABLED,
        }
    
    def get_spacing(self) -> Dict[str, int]:
        """Get all spacing values as dictionary.
        
        Returns:
            Dictionary mapping spacing names to pixel values.
        """
        return {
            "xs": Spacing.XS,
            "sm": Spacing.SM,
            "md": Spacing.MD,
            "lg": Spacing.LG,
            "xl": Spacing.XL,
            "xxl": Spacing.XXL,
            "button_padding_x": Spacing.BUTTON_PADDING_X,
            "button_padding_y": Spacing.BUTTON_PADDING_Y,
            "card_padding": Spacing.CARD_PADDING,
            "table_row_height": Spacing.TABLE_ROW_HEIGHT,
            "input_height": Spacing.INPUT_HEIGHT,
        }
    
    def get_responsive_config(self, width: int) -> Dict[str, Any]:
        """Get responsive configuration based on window width.
        
        Args:
            width: Current window width in pixels.
            
        Returns:
            Configuration dictionary with layout settings.
        """
        breakpoint = Breakpoints.get_breakpoint(width)
        
        configs = {
            "compact": {
                "sidebar_width": 60,
                "sidebar_collapsed": True,
                "columns": 1,
                "button_full_width": True,
                "table_pagination": 25,
                "card_padding": Spacing.SM,
            },
            "standard": {
                "sidebar_width": 220,
                "sidebar_collapsed": False,
                "columns": 2,
                "button_full_width": False,
                "table_pagination": 50,
                "card_padding": Spacing.MD,
            },
            "wide": {
                "sidebar_width": 260,
                "sidebar_collapsed": False,
                "columns": 3,
                "button_full_width": False,
                "table_pagination": 100,
                "card_padding": Spacing.LG,
            },
        }
        
        config = configs[breakpoint].copy()
        config["breakpoint"] = breakpoint
        return config
    
    @staticmethod
    def configure_card(
        parent: ctk.CTkFrame,
        corner_radius: int = 12,
        fg_color: str = Colors.CARD,
        border_color: str = Colors.BORDER,
        border_width: int = 1,
    ) -> ctk.CTkFrame:
        """Create a pre-styled card frame.
        
        Args:
            parent: Parent widget.
            corner_radius: Corner radius in pixels.
            fg_color: Foreground color.
            border_color: Border color.
            border_width: Border width in pixels.
            
        Returns:
            Configured CTkFrame instance.
        """
        card = ctk.CTkFrame(
            parent,
            corner_radius=corner_radius,
            fg_color=fg_color,
            border_color=border_color,
            border_width=border_width,
        )
        return card
    
    @staticmethod
    def configure_button(
        parent: ctk.CTkFrame,
        text: str,
        command: callable = None,
        variant: str = "primary",
        size: str = "md",
        width: int = 120,
        height: int = 40,
    ) -> ctk.CTkButton:
        """Create a pre-styled button.
        
        Args:
            parent: Parent widget.
            text: Button text.
            command: Callback function on click.
            variant: Button variant ('primary', 'secondary', 'success', 
                    'warning', 'danger', 'outline').
            size: Button size ('sm', 'md', 'lg').
            width: Button width in pixels.
            height: Button height in pixels.
            
        Returns:
            Configured CTkButton instance.
        """
        # Size mappings
        sizes = {
            "sm": {"height": 32, "font_size": Fonts.SM},
            "md": {"height": 40, "font_size": Fonts.MD},
            "lg": {"height": 48, "font_size": Fonts.LG},
        }
        size_config = sizes.get(size, sizes["md"])
        
        # Color mappings
        color_map = {
            "primary": {"fg": Colors.PRIMARY, "hover": Colors.PRIMARY_LIGHT},
            "secondary": {"fg": Colors.SECONDARY, "hover": Colors.SECONDARY_LIGHT},
            "success": {"fg": Colors.SUCCESS, "hover": Colors.SUCCESS_LIGHT},
            "warning": {"fg": Colors.WARNING, "hover": Colors.WARNING_LIGHT},
            "danger": {"fg": Colors.DANGER, "hover": Colors.DANGER_LIGHT},
            "outline": {"fg": "transparent", "hover": Colors.HOVER},
        }
        colors = color_map.get(variant, color_map["primary"])
        
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height if height else size_config["height"],
            fg_color=colors["fg"],
            hover_color=colors["hover"],
            text_color=Colors.CARD if variant != "outline" else Colors.TEXT_PRIMARY,
            corner_radius=8,
            font=(Fonts.PRIMARY, size_config["font_size"]),
        )
        return button
    
    @staticmethod
    def configure_entry(
        parent: ctk.CTkFrame,
        placeholder: str = "",
        width: int = 200,
        height: int = 40,
    ) -> ctk.CTkEntry:
        """Create a pre-styled text entry field.
        
        Args:
            parent: Parent widget.
            placeholder: Placeholder text.
            width: Entry width in pixels.
            height: Entry height in pixels.
            
        Returns:
            Configured CTkEntry instance.
        """
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=width,
            height=height,
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER,
            fg_color=Colors.CARD,
            text_color=Colors.TEXT_PRIMARY,
        )
        return entry
