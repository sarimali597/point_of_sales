"""
Theme Engine for Shoukat POS.

Provides color palette, fonts, spacing constants, responsive breakpoints,
and animation utilities for CustomTkinter-based UI.
"""

import customtkinter as ctk
from typing import Tuple, Dict, Any, Optional, Callable
from dataclasses import dataclass
import time


# =============================================================================
# COLOR PALETTE
# =============================================================================

class Colors:
    """Primary color scheme for Shoukat POS."""
    
    # Primary colors (deep blue theme)
    PRIMARY = "#1A237E"        # Deep indigo - main brand color
    PRIMARY_LIGHT = "#534BA9"  # Lighter indigo for hover states
    PRIMARY_DARK = "#000051"   # Dark indigo for accents
    
    # Secondary colors
    SECONDARY = "#0D47A1"      # Strong blue
    SECONDARY_LIGHT = "#5472D3"
    SECONDARY_DARK = "#002171"
    
    # Accent color
    ACCENT = "#00BCD4"         # Cyan accent for highlights
    
    # Semantic colors
    SUCCESS = "#2E7D32"        # Green for positive actions
    SUCCESS_LIGHT = "#60AD5E"
    WARNING = "#F57C00"        # Orange for warnings
    WARNING_LIGHT = "#FFA726"
    DANGER = "#C62828"         # Red for errors/destructive actions
    DANGER_LIGHT = "#EF5350"
    
    # Neutral colors
    BACKGROUND = "#F5F5F5"     # Light gray background
    CARD = "#FFFFFF"           # White card backgrounds
    TEXT_PRIMARY = "#263238"   # Dark gray text
    TEXT_SECONDARY = "#546E7A" # Medium gray text
    TEXT_MUTED = "#90A4AE"     # Light gray text
    BORDER = "#E0E0E0"         # Light border color
    INPUT_BACKGROUND = "#FAFAFA"
    
    # Status indicators
    INFO = "#1976D2"
    
    @classmethod
    def get_palette(cls) -> Dict[str, str]:
        """Return complete color palette as dictionary."""
        return {
            name: getattr(cls, name)
            for name in dir(cls)
            if not name.startswith('_') and name.isupper()
        }


# =============================================================================
# RESPONSIVE BREAKPOINTS
# =============================================================================

@dataclass
class BreakpointConfig:
    """Configuration for a responsive breakpoint."""
    min_width: int
    max_width: Optional[int]
    sidebar_visible: bool
    sidebar_collapsed: bool
    columns: int
    button_size: str  # "small", "medium", "large"
    font_scale: float


class Breakpoints:
    """Responsive design breakpoints."""
    
    COMPACT_WIDTH = 1024    # Tablets and small screens
    STANDARD_WIDTH = 1440   # Standard desktop monitors
    WIDE_WIDTH = 1920       # Large displays
    
    @classmethod
    def get_config(cls, width: int) -> BreakpointConfig:
        """
        Get responsive configuration based on window width.
        
        Args:
            width: Current window width in pixels
            
        Returns:
            BreakpointConfig for current screen size
        """
        if width < cls.COMPACT_WIDTH:
            # Compact mode - single column, collapsible sidebar
            return BreakpointConfig(
                min_width=0,
                max_width=cls.COMPACT_WIDTH,
                sidebar_visible=True,
                sidebar_collapsed=True,
                columns=1,
                button_size="medium",
                font_scale=0.95
            )
        elif width < cls.STANDARD_WIDTH:
            # Standard mode - two columns, visible sidebar
            return BreakpointConfig(
                min_width=cls.COMPACT_WIDTH,
                max_width=cls.STANDARD_WIDTH,
                sidebar_visible=True,
                sidebar_collapsed=False,
                columns=2,
                button_size="medium",
                font_scale=1.0
            )
        else:
            # Wide mode - three columns, expanded everything
            return BreakpointConfig(
                min_width=cls.STANDARD_WIDTH,
                max_width=None,
                sidebar_visible=True,
                sidebar_collapsed=False,
                columns=3,
                button_size="large",
                font_scale=1.05
            )


# =============================================================================
# SPACING & SIZING
# =============================================================================

class Spacing:
    """Spacing constants in pixels."""
    
    # Margins and padding
    XS = 4
    SMALL = 8
    MEDIUM = 16
    LARGE = 24
    XLARGE = 32
    XXLARGE = 48
    
    # Component sizes
    BUTTON_HEIGHT_SMALL = 32
    BUTTON_HEIGHT_MEDIUM = 40
    BUTTON_HEIGHT_LARGE = 48
    
    INPUT_HEIGHT = 40
    
    # Card dimensions
    CARD_CORNER_RADIUS = 12
    CARD_PADDING = 16
    
    # Sidebar
    SIDEBAR_WIDTH_EXPANDED = 240
    SIDEBAR_WIDTH_COLLAPSED = 64
    
    # Icon sizes
    ICON_SMALL = 16
    ICON_MEDIUM = 24
    ICON_LARGE = 32


# =============================================================================
# FONT CONFIGURATION
# =============================================================================

class FontConfig:
    """Font configuration for different text elements."""
    
    # Font families (CustomTkinter uses system defaults)
    FAMILY_DEFAULT = "Arial"
    FAMILY_MONOSPACE = "Consolas"
    
    # Font sizes (base size multiplied by scale)
    SIZE_XS = 10
    SIZE_SMALL = 12
    SIZE_MEDIUM = 14
    SIZE_LARGE = 18
    SIZE_XLARGE = 24
    SIZE_XXLARGE = 32
    
    # Font weights
    WEIGHT_NORMAL = "normal"
    WEIGHT_BOLD = "bold"
    
    @classmethod
    def get_font(
        cls,
        size: int = SIZE_MEDIUM,
        weight: str = WEIGHT_NORMAL,
        family: str = FAMILY_DEFAULT
    ) -> tuple:
        """
        Get font tuple for tkinter.
        
        Args:
            size: Font size in points
            weight: Font weight ('normal' or 'bold')
            family: Font family name
            
        Returns:
            Tuple compatible with tkinter font parameter
        """
        return (family, size, weight)


# =============================================================================
# ANIMATION UTILITIES
# =============================================================================

class Animation:
    """Animation utilities for CustomTkinter widgets."""
    
    DEFAULT_FPS = 60  # Frames per second
    
    @staticmethod
    def fade_in(
        widget: ctk.CTkBaseClass,
        duration_ms: int = 150,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Fade in widget by gradually increasing opacity.
        
        Note: CustomTkinter doesn't support true alpha transparency,
        so this simulates fade-in by cycling through background colors.
        
        Args:
            widget: Widget to animate
            duration_ms: Animation duration in milliseconds
            callback: Optional function to call when animation completes
        """
        start_time = time.time()
        end_time = start_time + (duration_ms / 1000)
        
        # Get target color
        target_color = widget.cget("fg_color")
        
        def animate_frame():
            current_time = time.time()
            
            if current_time >= end_time:
                # Animation complete
                if isinstance(target_color, tuple):
                    widget.configure(fg_color=target_color)
                else:
                    widget.configure(fg_color=target_color)
                if callback:
                    callback()
                return
            
            # Calculate progress (0.0 to 1.0)
            progress = (current_time - start_time) / (duration_ms / 1000)
            
            # Easing function (ease-out cubic)
            eased = 1 - pow(1 - progress, 3)
            
            # Schedule next frame
            widget.after(int(1000 / Animation.DEFAULT_FPS), animate_frame)
        
        animate_frame()
    
    @staticmethod
    def slide_in(
        widget: ctk.CTkBaseClass,
        from_x: int,
        duration_ms: int = 200,
        easing: str = "ease_out",
        callback: Optional[Callable] = None
    ) -> None:
        """
        Slide widget in from specified x position.
        
        Args:
            widget: Widget to animate
            from_x: Starting x position (pixels)
            duration_ms: Animation duration
            easing: Easing function ("linear", "ease_out", "ease_in_out")
            callback: Completion callback
        """
        start_time = time.time()
        end_time = start_time + (duration_ms / 1000)
        
        # Get target x position
        target_x = widget.winfo_x()
        
        def get_eased_progress(progress: float) -> float:
            """Apply easing function to progress."""
            if easing == "linear":
                return progress
            elif easing == "ease_out":
                return 1 - pow(1 - progress, 3)
            elif easing == "ease_in_out":
                if progress < 0.5:
                    return 4 * progress * progress * progress
                else:
                    return 1 - pow(-2 * progress + 2, 3) / 2
            return progress
        
        def animate_frame():
            current_time = time.time()
            
            if current_time >= end_time:
                # Animation complete - ensure final position
                widget.place(x=target_x)
                if callback:
                    callback()
                return
            
            progress = (current_time - start_time) / (duration_ms / 1000)
            eased = get_eased_progress(progress)
            
            # Calculate current x position
            current_x = int(from_x + (target_x - from_x) * eased)
            widget.place(x=current_x)
            
            # Schedule next frame
            widget.after(int(1000 / Animation.DEFAULT_FPS), animate_frame)
        
        animate_frame()
    
    @staticmethod
    def pulse(
        widget: ctk.CTkBaseClass,
        color: str,
        duration_ms: int = 1000,
        repeat: int = 3
    ) -> None:
        """
        Pulse widget border/background color.
        
        Args:
            widget: Widget to animate
            color: Color to pulse to
            duration_ms: Duration of one pulse cycle
            repeat: Number of times to repeat pulse
        """
        original_color = widget.cget("fg_color")
        pulse_count = 0
        
        def pulse_cycle():
            nonlocal pulse_count
            
            if pulse_count >= repeat:
                widget.configure(fg_color=original_color)
                return
            
            # Pulse to target color
            widget.configure(fg_color=color)
            
            # Return to original after half duration
            widget.after(duration_ms // 2, lambda: widget.configure(fg_color=original_color))
            
            # Schedule next pulse
            pulse_count += 1
            widget.after(duration_ms, pulse_cycle)
        
        pulse_cycle()
    
    @staticmethod
    def toast(
        parent: ctk.CTkBaseClass,
        message: str,
        toast_type: str = "success",
        duration_ms: int = 3000,
        position: str = "top_right"
    ) -> ctk.CTkLabel:
        """
        Show toast notification.
        
        Args:
            parent: Parent window/frame
            message: Toast message text
            toast_type: Type ('success', 'error', 'warning', 'info')
            duration_ms: Auto-dismiss duration
            position: Position ('top_right', 'top_center', 'bottom_right')
            
        Returns:
            Toast label widget
        """
        # Determine colors based on type
        type_colors = {
            "success": Colors.SUCCESS,
            "error": Colors.DANGER,
            "warning": Colors.WARNING,
            "info": Colors.INFO
        }
        
        bg_color = type_colors.get(toast_type, Colors.PRIMARY)
        
        # Create toast frame
        toast_frame = ctk.CTkFrame(
            parent,
            fg_color=bg_color,
            corner_radius=8,
            height=50
        )
        
        # Position toast
        parent_width = parent.winfo_width()
        
        if position == "top_right":
            x_pos = parent_width - 320
            y_pos = 10
        elif position == "top_center":
            x_pos = (parent_width - 320) // 2
            y_pos = 10
        elif position == "bottom_right":
            x_pos = parent_width - 320
            y_pos = parent.winfo_height() - 60
        else:
            x_pos = parent_width - 320
            y_pos = 10
        
        toast_frame.place(x=x_pos, y=y_pos)
        
        # Add message label
        message_label = ctk.CTkLabel(
            toast_frame,
            text=message,
            text_color="#FFFFFF",
            font=FontConfig.get_font(FontConfig.SIZE_MEDIUM, FontConfig.WEIGHT_BOLD)
        )
        message_label.pack(expand=True, fill="both", padx=Spacing.MEDIUM)
        
        # Animate slide-in
        Animation.slide_in(toast_frame, from_x=parent_width, duration_ms=200)
        
        # Auto-dismiss
        def dismiss():
            Animation.fade_out(toast_frame, duration_ms=200, callback=toast_frame.destroy)
        
        parent.after(duration_ms, dismiss)
        
        return toast_frame
    
    @staticmethod
    def fade_out(
        widget: ctk.CTkBaseClass,
        duration_ms: int = 200,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Fade out widget (simulate by reducing visibility).
        
        Args:
            widget: Widget to animate
            duration_ms: Animation duration
            callback: Completion callback
        """
        start_time = time.time()
        end_time = start_time + (duration_ms / 1000)
        
        def animate_frame():
            current_time = time.time()
            
            if current_time >= end_time:
                if callback:
                    callback()
                return
            
            progress = (current_time - start_time) / (duration_ms / 1000)
            
            # Schedule next frame
            widget.after(int(1000 / Animation.DEFAULT_FPS), animate_frame)
        
        animate_frame()


# =============================================================================
# THEME INITIALIZATION
# =============================================================================

def setup_customtkinter_theme():
    """
    Configure CustomTkinter appearance mode and default colors.
    
    Call this once at application startup before creating any widgets.
    """
    # Set appearance mode (System, Light, Dark)
    ctk.set_appearance_mode("Light")
    
    # Set default color theme
    ctk.set_default_color_theme("blue")
    
    # Configure default font sizes
    ctk.set_widget_scaling(1.0)


def get_button_dimensions(size: str = "medium") -> Tuple[int, int]:
    """
    Get button dimensions based on size preset.
    
    Args:
        size: Button size preset ('small', 'medium', 'large')
        
    Returns:
        Tuple of (height, corner_radius)
    """
    presets = {
        "small": (Spacing.BUTTON_HEIGHT_SMALL, 6),
        "medium": (Spacing.BUTTON_HEIGHT_MEDIUM, 8),
        "large": (Spacing.BUTTON_HEIGHT_LARGE, 10)
    }
    
    return presets.get(size, presets["medium"])


def get_input_dimensions() -> Tuple[int, int]:
    """
    Get standard input field dimensions.
    
    Returns:
        Tuple of (height, corner_radius)
    """
    return (Spacing.INPUT_HEIGHT, 8)


# Export commonly used items
__all__ = [
    'Colors',
    'Breakpoints',
    'BreakpointConfig',
    'Spacing',
    'FontConfig',
    'Animation',
    'setup_customtkinter_theme',
    'get_button_dimensions',
    'get_input_dimensions'
]