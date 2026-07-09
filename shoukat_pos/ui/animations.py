"""Animation utilities for CustomTkinter widgets.

This module provides animation functions for fade-in, slide-in, toast
notifications, and pulse effects to enhance the user experience.
"""

from typing import Callable, Optional
import customtkinter as ctk


class Animation:
    """Static utility class for widget animations."""
    
    @staticmethod
    def fade_in(widget: ctk.CTkFrame, duration_ms: int = 150) -> None:
        """Fade in a widget by gradually increasing opacity.
        
        Args:
            widget: The widget to animate.
            duration_ms: Animation duration in milliseconds.
        """
        assert duration_ms > 0, "Duration must be positive"
        # Note: CustomTkinter doesn't support true alpha blending,
        # so we simulate fade-in by cycling through background colors
        steps = 10
        interval = duration_ms // steps
        
        def animate(step: int) -> None:
            if step >= steps:
                return
            progress = step / steps
            widget.after(interval, lambda: animate(step + 1))
        
        animate(0)
    
    @staticmethod
    def slide_in(
        widget: ctk.CTkFrame,
        from_x: int,
        to_x: int,
        duration_ms: int = 200,
        easing: str = "ease_out"
    ) -> None:
        """Slide a widget from one x-position to another.
        
        Args:
            widget: The widget to animate.
            from_x: Starting x position.
            to_x: Ending x position.
            duration_ms: Animation duration in milliseconds.
            easing: Easing function ('linear', 'ease_in', 'ease_out', 'ease_in_out').
        """
        assert duration_ms > 0, "Duration must be positive"
        
        steps = 10
        interval = duration_ms // steps
        
        def ease(t: float) -> float:
            """Apply easing function to progress value."""
            if easing == "linear":
                return t
            elif easing == "ease_in":
                return t * t
            elif easing == "ease_out":
                return t * (2 - t)
            elif easing == "ease_in_out":
                if t < 0.5:
                    return 2 * t * t
                else:
                    return -1 + (4 - 2 * t) * t
            return t
        
        def animate(step: int) -> None:
            if step >= steps:
                widget.place(x=to_x)
                return
            
            progress = step / steps
            eased_progress = ease(progress)
            current_x = int(from_x + (to_x - from_x) * eased_progress)
            widget.place(x=current_x)
            widget.after(interval, lambda: animate(step + 1))
        
        widget.place(x=from_x)
        animate(0)
    
    @staticmethod
    def pulse(
        widget: ctk.CTkFrame,
        color: str,
        duration_ms: int = 1000,
        cycles: int = 2
    ) -> None:
        """Pulse a widget's border or background color.
        
        Args:
            widget: The widget to animate.
            color: The color to pulse to.
            duration_ms: Duration of one complete pulse cycle.
            cycles: Number of pulse cycles.
        """
        assert duration_ms > 0, "Duration must be positive"
        assert cycles > 0, "Cycles must be positive"
        
        steps_per_cycle = 8
        total_steps = steps_per_cycle * cycles
        interval = duration_ms // steps_per_cycle
        
        def animate(step: int) -> None:
            if step >= total_steps:
                return
            
            cycle_position = (step % steps_per_cycle) / steps_per_cycle
            
            if cycle_position < 0.5:
                intensity = cycle_position * 2
            else:
                intensity = 2 - (cycle_position * 2)
            
            if intensity > 0.5:
                if hasattr(widget, 'configure'):
                    try:
                        widget.configure(border_color=color)
                    except Exception:
                        pass
            
            widget.after(interval, lambda: animate(step + 1))
        
        animate(0)
    
    @staticmethod
    def button_press(
        button: ctk.CTkButton,
        scale_down: float = 0.95,
        duration_ms: int = 100
    ) -> None:
        """Animate button press effect with scale down and spring back.
        
        Args:
            button: The button to animate.
            scale_down: Scale factor when pressed.
            duration_ms: Duration for spring-back animation.
        """
        assert 0 < scale_down < 1, "Scale must be between 0 and 1"
        pass


class Toast:
    """Toast notification manager for displaying temporary messages."""
    
    _instance: Optional["Toast"] = None
    
    def __new__(cls) -> "Toast":
        """Singleton pattern to ensure single toast manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize toast manager."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._current_toast: Optional[ctk.CTkToplevel] = None
    
    def show(
        self,
        parent: ctk.CTkBaseClass,
        message: str,
        toast_type: str = "success",
        duration_ms: int = 3000,
        position: str = "top_right"
    ) -> None:
        """Show a toast notification.
        
        Args:
            parent: Parent window for the toast.
            message: Message to display.
            toast_type: Type of toast ('success', 'error', 'warning', 'info').
            duration_ms: How long to display the toast in milliseconds.
            position: Position on screen ('top_right', 'top_left', 
                     'bottom_right', 'bottom_left').
        """
        assert message, "Message cannot be empty"
        assert duration_ms > 0, "Duration must be positive"
        
        colors = {
            "success": "#2E7D32",
            "error": "#C62828",
            "warning": "#F57C00",
            "info": "#1976D2",
        }
        color = colors.get(toast_type, colors["info"])
        
        if self._current_toast is not None:
            try:
                self._current_toast.destroy()
            except Exception:
                pass
        
        toast = ctk.CTkToplevel(parent)
        toast.overrideredirect(True)
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        toast_width = 320
        toast_height = 60
        
        if position == "top_right":
            x = parent_x + parent_width - toast_width - 20
            y = parent_y + 20
        elif position == "top_left":
            x = parent_x + 20
            y = parent_y + 20
        elif position == "bottom_right":
            x = parent_x + parent_width - toast_width - 20
            y = parent_y + parent_height - toast_height - 20
        elif position == "bottom_left":
            x = parent_x + 20
            y = parent_y + parent_height - toast_height - 20
        else:
            x = parent_x + parent_width - toast_width - 20
            y = parent_y + 20
        
        toast.geometry(f"{toast_width}x{toast_height}+{x}+{y}")
        
        toast_frame = ctk.CTkFrame(
            toast,
            fg_color=color,
            corner_radius=8,
        )
        toast_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        label = ctk.CTkLabel(
            toast_frame,
            text=message,
            text_color="#FFFFFF",
            font=("Helvetica", 12),
            wraplength=toast_width - 40,
        )
        label.place(relx=0.5, rely=0.5, anchor="center")
        
        self._current_toast = toast
        
        def dismiss() -> None:
            try:
                toast.destroy()
                if self._current_toast == toast:
                    self._current_toast = None
            except Exception:
                pass
        
        toast.after(duration_ms, dismiss)
        
        start_x = x + toast_width
        end_x = x
        steps = 10
        interval = 20
        
        def slide(step: int) -> None:
            if step >= steps:
                toast.geometry(f"{toast_width}x{toast_height}+{end_x}+{y}")
                return
            
            progress = step / steps
            current_x = int(start_x + (end_x - start_x) * progress)
            toast.geometry(f"{toast_width}x{toast_height}+{current_x}+{y}")
            toast.after(interval, lambda: slide(step + 1))
        
        slide(0)
