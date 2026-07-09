"""Reusable UI components for Shoukat POS.

This module provides custom widgets: DataTable, StatCard, SearchBar, Toast, EmptyState.
"""

import customtkinter as ctk
from typing import Optional, List, Dict, Any, Callable, Tuple
from datetime import datetime
import tkinter as tk


class DataTable(ctk.CTkFrame):
    """A scrollable data table with sorting, pagination, and row actions.
    
    Attributes:
        columns: List of column definitions (name, width, sortable, formatter)
        data: List of row data dictionaries
        on_row_click: Callback when a row is clicked
        on_action: Callback for row action buttons
    """
    
    def __init__(
        self,
        master: Any,
        columns: List[Dict[str, Any]],
        data: Optional[List[Dict[str, Any]]] = None,
        on_row_click: Optional[Callable] = None,
        on_action: Optional[Callable] = None,
        page_size: int = 25,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.columns = columns
        self.data = data or []
        self.filtered_data = self.data.copy()
        self.on_row_click = on_row_click
        self.on_action = on_action
        self.page_size = page_size
        self.current_page = 0
        self.sort_column = None
        self.sort_reverse = False
        
        self._create_widgets()
        self._apply_pagination()
    
    def _create_widgets(self) -> None:
        """Create the table structure."""
        # Scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Header row
        self.header_frame = ctk.CTkFrame(self.scroll_frame)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        for col in self.columns:
            width = col.get("width", 100)
            name = col["name"]
            
            header_btn = ctk.CTkButton(
                self.header_frame,
                text=name,
                command=lambda c=name: self._sort_by(c),
                width=width,
                height=30,
                fg_color="transparent",
                hover_color=self._apply_alpha(self._get_color("PRIMARY"), 0.3),
                anchor="w"
            )
            header_btn.pack(side="left", padx=1)
            
            if col.get("sortable", True):
                sort_indicator = ctk.CTkLabel(
                    self.header_frame,
                    text="▲",
                    width=20,
                    font=ctk.CTkFont(size=10)
                )
                sort_indicator.pack(side="left")
        
        # Data rows container
        self.rows_frame = ctk.CTkFrame(self.scroll_frame)
        self.rows_frame.pack(fill="both", expand=True)
        
        # Pagination
        self.pagination_frame = ctk.CTkFrame(self)
        self.pagination_frame.pack(fill="x", pady=5)
        
        self.prev_btn = ctk.CTkButton(
            self.pagination_frame,
            text="Previous",
            command=self._prev_page,
            width=80
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Page 1 of 1"
        )
        self.page_label.pack(side="left", padx=10)
        
        self.next_btn = ctk.CTkButton(
            self.pagination_frame,
            text="Next",
            command=self._next_page,
            width=80
        )
        self.next_btn.pack(side="left", padx=5)
    
    def _apply_alpha(self, color: str, alpha: float) -> str:
        """Apply alpha to hex color (simplified)."""
        return color
    
    def _get_color(self, name: str) -> str:
        """Get color from theme."""
        colors = {
            "PRIMARY": "#1A237E",
            "SECONDARY": "#0D47A1",
            "ACCENT": "#00BCD4",
            "SUCCESS": "#2E7D32",
            "WARNING": "#F57C00",
            "DANGER": "#C62828",
            "BACKGROUND": "#F5F5F5",
            "CARD": "#FFFFFF",
            "TEXT_PRIMARY": "#263238"
        }
        return colors.get(name, "#000000")
    
    def _sort_by(self, column: str) -> None:
        """Sort data by column."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        col_def = next((c for c in self.columns if c["name"] == column), None)
        formatter = col_def.get("formatter") if col_def else None
        
        self.filtered_data.sort(
            key=lambda x: x.get(column, ""),
            reverse=self.sort_reverse
        )
        self._apply_pagination()
    
    def _apply_pagination(self) -> None:
        """Apply pagination and render rows."""
        # Clear existing rows
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
        
        total_pages = max(1, (len(self.filtered_data) + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, total_pages - 1)
        
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_data))
        page_data = self.filtered_data[start_idx:end_idx]
        
        # Render rows
        for row_data in page_data:
            self._render_row(row_data)
        
        # Update pagination controls
        self.page_label.configure(text=f"Page {self.current_page + 1} of {total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
    
    def _render_row(self, row_data: Dict[str, Any]) -> None:
        """Render a single row."""
        row_frame = ctk.CTkFrame(self.rows_frame)
        row_frame.pack(fill="x", padx=5, pady=1)
        
        for col in self.columns:
            name = col["name"]
            width = col.get("width", 100)
            formatter = col.get("formatter")
            
            value = row_data.get(name, "")
            if formatter:
                value = formatter(value)
            
            cell = ctk.CTkLabel(
                row_frame,
                text=str(value),
                width=width,
                anchor="w"
            )
            cell.pack(side="left", padx=1)
        
        # Row click binding
        if self.on_row_click:
            row_frame.bind("<Button-1>", lambda e, d=row_data: self.on_row_click(d))
            for child in row_frame.winfo_children():
                child.bind("<Button-1>", lambda e, d=row_data: self.on_row_click(d))
    
    def _prev_page(self) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._apply_pagination()
    
    def _next_page(self) -> None:
        """Go to next page."""
        self.current_page += 1
        self._apply_pagination()
    
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """Set new data and reset to first page."""
        self.data = data
        self.filtered_data = data.copy()
        self.current_page = 0
        self._apply_pagination()
    
    def filter(self, predicate: Callable[[Dict], bool]) -> None:
        """Filter data using predicate function."""
        self.filtered_data = [row for row in self.data if predicate(row)]
        self.current_page = 0
        self._apply_pagination()


class StatCard(ctk.CTkFrame):
    """A statistics card displaying a metric with trend indicator.
    
    Attributes:
        title: Card title
        value: Current value
        change: Change percentage (positive or negative)
        icon: Optional icon text
    """
    
    def __init__(
        self,
        master: Any,
        title: str,
        value: str,
        change: Optional[float] = None,
        icon: Optional[str] = None,
        command: Optional[Callable] = None,
        color: Optional[str] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.title = title
        self.value = value
        self.change = change
        self.icon = icon
        self.command = command
        self.color = color or "PRIMARY"
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create card widgets."""
        self.configure(corner_radius=10, fg_color=self._get_color("CARD"))
        
        # Content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(
            content,
            text=self.title,
            font=ctk.CTkFont(size=14, weight="normal"),
            text_color=self._get_color("TEXT_PRIMARY")
        )
        title_label.pack(anchor="w")
        
        # Value
        value_label = ctk.CTkLabel(
            content,
            text=self.value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self._get_color(self.color)
        )
        value_label.pack(anchor="w", pady=(5, 0))
        
        # Change indicator
        if self.change is not None:
            change_text = f"{self.change:+.1f}%"
            change_color = self._get_color("SUCCESS") if self.change >= 0 else self._get_color("DANGER")
            arrow = "↑" if self.change >= 0 else "↓"
            
            change_label = ctk.CTkLabel(
                content,
                text=f"{arrow} {change_text}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=change_color
            )
            change_label.pack(anchor="w", pady=(5, 0))
        
        # Click binding
        if self.command:
            self.bind("<Button-1>", lambda e: self.command())
            for child in content.winfo_children():
                child.bind("<Button-1>", lambda e: self.command())
    
    def _get_color(self, name: str) -> str:
        """Get color from theme."""
        colors = {
            "PRIMARY": "#1A237E",
            "SECONDARY": "#0D47A1",
            "ACCENT": "#00BCD4",
            "SUCCESS": "#2E7D32",
            "WARNING": "#F57C00",
            "DANGER": "#C62828",
            "CARD": "#FFFFFF",
            "TEXT_PRIMARY": "#263238"
        }
        return colors.get(name, "#000000")
    
    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self.value = value
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and child.cget("font")[1] == 28:
                        child.configure(text=value)
                        break


class SearchBar(ctk.CTkFrame):
    """A search input field with clear button and debounced search.
    
    Attributes:
        placeholder: Placeholder text
        on_search: Callback when search query changes (debounced)
        debounce_ms: Debounce delay in milliseconds
    """
    
    def __init__(
        self,
        master: Any,
        placeholder: str = "Search...",
        on_search: Optional[Callable[[str], None]] = None,
        debounce_ms: int = 300,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.placeholder = placeholder
        self.on_search = on_search
        self.debounce_ms = debounce_ms
        self._debounce_job = None
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create search bar widgets."""
        self.configure(fg_color="transparent")
        
        # Entry frame
        entry_frame = ctk.CTkFrame(self)
        entry_frame.pack(fill="x")
        
        # Search icon
        search_icon = ctk.CTkLabel(
            entry_frame,
            text="🔍",
            font=ctk.CTkFont(size=16),
            width=30
        )
        search_icon.pack(side="left", padx=5)
        
        # Entry field
        self.entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text=self.placeholder,
            border_width=0,
            fg_color="transparent"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        
        # Clear button
        self.clear_btn = ctk.CTkButton(
            entry_frame,
            text="✕",
            width=24,
            height=24,
            command=self.clear,
            visible=False
        )
        self.clear_btn.pack(side="right", padx=5)
    
    def _on_key_release(self, event: tk.Event) -> None:
        """Handle key release with debouncing."""
        if self._debounce_job:
            self.after_cancel(self._debounce_job)
        
        query = self.entry.get()
        
        # Show/hide clear button
        if query:
            self.clear_btn.pack(side="right", padx=5)
        else:
            self.clear_btn.pack_forget()
        
        # Debounce search callback
        if self.on_search:
            self._debounce_job = self.after(
                self.debounce_ms,
                lambda: self.on_search(query)
            )
    
    def _on_focus_in(self, event: tk.Event) -> None:
        """Handle focus in."""
        pass
    
    def _on_focus_out(self, event: tk.Event) -> None:
        """Handle focus out."""
        pass
    
    def clear(self) -> None:
        """Clear the search field."""
        self.entry.delete(0, "end")
        self.clear_btn.pack_forget()
        if self.on_search:
            self.on_search("")
    
    def get_query(self) -> str:
        """Get current search query."""
        return self.entry.get()
    
    def set_query(self, query: str) -> None:
        """Set search query programmatically."""
        self.entry.delete(0, "end")
        self.entry.insert(0, query)
        if query:
            self.clear_btn.pack(side="right", padx=5)
        else:
            self.clear_btn.pack_forget()


class Toast(ctk.CTkToplevel):
    """A toast notification that slides in from the right.
    
    Attributes:
        message: Toast message
        toast_type: 'success', 'error', 'warning', or 'info'
        duration_ms: Auto-dismiss duration
    """
    
    def __init__(
        self,
        master: Any,
        message: str,
        toast_type: str = "success",
        duration_ms: int = 3000,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.message = message
        self.toast_type = toast_type
        self.duration_ms = duration_ms
        
        self._setup_window()
        self._create_widgets()
        self._animate_in()
        self._schedule_dismiss()
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=self._get_bg_color())
        
        # Position at top-right
        parent = self.master
        parent.update_idletasks()
        x = parent.winfo_rootx() + parent.winfo_width() - 320 - 20
        y = parent.winfo_rooty() + 20
        self.geometry(f"320x80+{x}+{y}")
    
    def _get_bg_color(self) -> str:
        """Get background color based on type."""
        colors = {
            "success": "#2E7D32",
            "error": "#C62828",
            "warning": "#F57C00",
            "info": "#0D47A1"
        }
        return colors.get(self.toast_type, "#263238")
    
    def _create_widgets(self) -> None:
        """Create toast content."""
        # Icon based on type
        icons = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ"
        }
        icon = icons.get(self.toast_type, "ℹ")
        
        # Icon label
        icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FFFFFF"
        )
        icon_label.place(relx=0.1, rely=0.5, anchor="center")
        
        # Message label
        msg_label = ctk.CTkLabel(
            self,
            text=self.message,
            font=ctk.CTkFont(size=14),
            text_color="#FFFFFF",
            wraplength=220,
            justify="left"
        )
        msg_label.place(relx=0.6, rely=0.5, anchor="center")
    
    def _animate_in(self) -> None:
        """Animate toast sliding in."""
        # Simple fade-in effect (simplified)
        pass
    
    def _schedule_dismiss(self) -> None:
        """Schedule auto-dismiss."""
        self.after(self.duration_ms, self._dismiss)
    
    def _dismiss(self) -> None:
        """Dismiss the toast."""
        self.destroy()


class EmptyState(ctk.CTkFrame):
    """An empty state component with illustration and CTA.
    
    Attributes:
        title: Empty state title
        subtitle: Description text
        cta_text: Call-to-action button text
        cta_command: Callback when CTA is clicked
    """
    
    def __init__(
        self,
        master: Any,
        title: str = "No Data",
        subtitle: str = "There's nothing here yet.",
        cta_text: Optional[str] = None,
        cta_command: Optional[Callable] = None,
        icon: str = "📭",
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.title = title
        self.subtitle = subtitle
        self.cta_text = cta_text
        self.cta_command = cta_command
        self.icon = icon
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """Create empty state widgets."""
        self.configure(fg_color="transparent")
        
        # Center frame
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        # Icon
        icon_label = ctk.CTkLabel(
            center,
            text=self.icon,
            font=ctk.CTkFont(size=64)
        )
        icon_label.pack(pady=(0, 20))
        
        # Title
        title_label = ctk.CTkLabel(
            center,
            text=self.title,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            center,
            text=self.subtitle,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 20))
        
        # CTA Button
        if self.cta_text and self.cta_command:
            cta_btn = ctk.CTkButton(
                center,
                text=self.cta_text,
                command=self.cta_command,
                width=150
            )
            cta_btn.pack()