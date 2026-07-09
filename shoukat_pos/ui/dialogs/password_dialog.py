"""Password dialog for sensitive operations."""

from typing import Any, Optional, Callable
import customtkinter as ctk
from ui.theme import Colors, Fonts


class PasswordDialog(ctk.CTkToplevel):
    """Modal dialog for password verification."""
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        title: str = "Password Required",
        message: str = "Please enter your password to continue:",
        on_verify: Optional[Callable[[str], bool]] = None,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Initialize the password dialog.
        
        Args:
            parent: Parent window.
            title: Dialog title.
            message: Instruction message.
            on_verify: Callback to verify password (returns True if valid).
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)
        
        self.on_verify = on_verify
        self.result: Optional[str] = None
        
        # Configure dialog
        self.title(title)
        self.geometry("400x220")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._build_dialog(message)
    
    def _build_dialog(self, message: str) -> None:
        """Build the dialog layout."""
        # Message
        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_PRIMARY,
        )
        msg_label.pack(pady=(24, 16))
        
        # Password entry
        self.password_entry = ctk.CTkEntry(
            self,
            placeholder_text="Enter password",
            show="•",
            width=320,
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER,
        )
        self.password_entry.pack(pady=(0, 16))
        self.password_entry.bind("<Return>", lambda e: self._verify())
        self.password_entry.focus()
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            height=36,
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY,
        )
        cancel_btn.pack(side="right", padx=(8, 0))
        
        # Verify button
        verify_btn = ctk.CTkButton(
            btn_frame,
            text="Verify",
            command=self._verify,
            width=100,
            height=36,
        )
        verify_btn.pack(side="right")
    
    def _verify(self) -> None:
        """Verify the entered password."""
        password = self.password_entry.get()
        
        if not password:
            return
        
        if self.on_verify:
            if self.on_verify(password):
                self.result = password
                self.destroy()
        else:
            # Default: accept any non-empty password
            self.result = password
            self.destroy()
