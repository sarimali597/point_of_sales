"""Confirmation dialog for destructive actions."""

from typing import Any, Optional, Callable
import customtkinter as ctk
from ui.theme import Colors, Fonts


class ConfirmationDialog(ctk.CTkToplevel):
    """Modal dialog for confirming destructive actions."""
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        title: str = "Confirm Action",
        message: str = "Are you sure you want to proceed?",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        danger: bool = False,
        on_confirm: Optional[Callable[[], None]] = None,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Initialize the confirmation dialog.
        
        Args:
            parent: Parent window.
            title: Dialog title.
            message: Confirmation message.
            confirm_text: Text for confirm button.
            cancel_text: Text for cancel button.
            danger: Whether this is a dangerous action (red button).
            on_confirm: Callback when confirmed.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)
        
        self.on_confirm = on_confirm
        self.confirmed = False
        
        # Configure dialog
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._build_dialog(message, confirm_text, cancel_text, danger)
    
    def _build_dialog(
        self,
        message: str,
        confirm_text: str,
        cancel_text: str,
        danger: bool
    ) -> None:
        """Build the dialog layout."""
        # Message
        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_PRIMARY,
            wraplength=350,
        )
        msg_label.pack(pady=(24, 24))
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            command=self.destroy,
            width=100,
            height=36,
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY,
        )
        cancel_btn.pack(side="right", padx=(8, 0))
        
        # Confirm button
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            command=self._on_confirm_click,
            width=100,
            height=36,
            fg_color=Colors.DANGER if danger else Colors.PRIMARY,
            hover_color=Colors.DANGER_LIGHT if danger else Colors.PRIMARY_LIGHT,
        )
        confirm_btn.pack(side="right")
    
    def _on_confirm_click(self) -> None:
        """Handle confirm button click."""
        self.confirmed = True
        
        if self.on_confirm:
            self.on_confirm()
        
        self.destroy()
