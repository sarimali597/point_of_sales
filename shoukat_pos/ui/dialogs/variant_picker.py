"""Variant picker dialog for size-color selection."""

from typing import Any, Optional, Callable, Dict, List
import customtkinter as ctk
from ui.theme import Colors, Fonts


class VariantPicker(ctk.CTkToplevel):
    """Modal dialog for selecting product variants (size-color combinations)."""
    
    SIZES = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]
    COLORS = [
        ("Black", "#000000"),
        ("White", "#FFFFFF"),
        ("Blue", "#1976D2"),
        ("Red", "#C62828"),
        ("Green", "#2E7D32"),
        ("Navy", "#0D47A1"),
        ("Grey", "#757575"),
        ("Brown", "#5D4037"),
    ]
    
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        title: str = "Select Variant",
        available_variants: Optional[List[Dict[str, Any]]] = None,
        on_select: Optional[Callable[[Dict[str, Any]], None]] = None,
        *args: Any,
        **kwargs: Any
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        
        self.available_variants = available_variants or []
        self.on_select = on_select
        self.selected_variant: Optional[Dict[str, Any]] = None
        
        self.title(title)
        self.geometry("600x500")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self._build_dialog()
    
    def _build_dialog(self) -> None:
        title_label = ctk.CTkLabel(
            self,
            text="Select Size and Color",
            font=(Fonts.PRIMARY, Fonts.LG, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY,
        )
        title_label.pack(pady=(16, 8))
        
        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.pack(fill="x", padx=24, pady=(8, 16))
        
        ctk.CTkLabel(
            size_frame,
            text="Size:",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 8))
        
        self.size_var = ctk.StringVar(value="")
        size_btn_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        size_btn_frame.pack(fill="x")
        
        for size in self.SIZES:
            ctk.CTkRadioButton(
                size_btn_frame, text=size, variable=self.size_var,
                value=size, command=self._update_selection, width=60,
            ).pack(side="left", padx=4)
        
        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.pack(fill="x", padx=24, pady=(8, 16))
        
        ctk.CTkLabel(
            color_frame, text="Color:",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 8))
        
        self.color_var = ctk.StringVar(value="")
        color_btn_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        color_btn_frame.pack(fill="x")
        
        for color_name, _ in self.COLORS:
            ctk.CTkRadioButton(
                color_btn_frame, text=color_name, variable=self.color_var,
                value=color_name, command=self._update_selection, width=80,
            ).pack(side="left", padx=4)
        
        self.info_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        self.info_frame.pack(fill="x", padx=24, pady=16)
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="Please select both size and color",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY,
        )
        self.info_label.pack(pady=16)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 16))
        
        ctk.CTkButton(
            btn_frame, text="Cancel", command=self.destroy,
            width=100, height=36, fg_color="transparent",
            border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY,
        ).pack(side="right", padx=(8, 0))
        
        self.select_btn = ctk.CTkButton(
            btn_frame, text="Select", command=self._on_select_click,
            width=100, height=36, state="disabled",
        )
        self.select_btn.pack(side="right")
    
    def _update_selection(self) -> None:
        size = self.size_var.get()
        color = self.color_var.get()
        
        if size and color:
            variant = None
            for v in self.available_variants:
                if v.get("size") == size and v.get("color") == color:
                    variant = v
                    break
            
            if variant:
                qty = variant.get("quantity", 0)
                status = "In Stock" if qty > 0 else "Out of Stock"
                self.info_label.configure(
                    text=f"{size} / {color}\nStock: {qty} ({status})",
                    text_color=Colors.TEXT_PRIMARY,
                )
                self.selected_variant = variant
                self.select_btn.configure(state="normal" if qty > 0 else "disabled")
            else:
                self.info_label.configure(
                    text=f"{size} / {color}\nVariant not found",
                    text_color=Colors.DANGER,
                )
                self.selected_variant = None
                self.select_btn.configure(state="disabled")
        else:
            self.info_label.configure(
                text="Please select both size and color",
                text_color=Colors.TEXT_SECONDARY,
            )
            self.selected_variant = None
            self.select_btn.configure(state="disabled")
    
    def _on_select_click(self) -> None:
        if self.selected_variant and self.on_select:
            self.on_select(self.selected_variant)
        self.destroy()
