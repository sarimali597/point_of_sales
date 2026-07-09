"""
Product List Screen for Shoukat POS.

Displays all products in a searchable, filterable grid with variant management.
"""
import customtkinter as ctk
from typing import Dict, List, Optional
from database.connection import ConnectionManager
from ui.theme import Colors, Fonts
import logging

logger = logging.getLogger(__name__)


class ProductListScreen(ctk.CTkFrame):
    """Product list with search, filters, and variant management."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.connection_manager = ConnectionManager.get_instance()
        self.current_category = "All"
        self.search_query = ""
        
        self._build_ui()
        self._load_products()
        
    def _build_ui(self):
        """Build product list UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with search and filters
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="👕 Products",
            font=(Fonts.PRIMARY, 24, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Search bar
        self.search_entry = ctk.CTkEntry(
            header_frame,
            placeholder_text="Search by name or barcode...",
            height=36,
            width=300,
            font=(Fonts.PRIMARY, Fonts.MD)
        )
        self.search_entry.grid(row=0, column=1, padx=20, sticky="e")
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())
        
        # Category filter
        self.category_var = ctk.StringVar(value="All")
        self.category_combo = ctk.CTkComboBox(
            header_frame,
            variable=self.category_var,
            values=["All"],
            command=self._on_category_change,
            width=150,
            height=36,
            font=(Fonts.PRIMARY, Fonts.MD)
        )
        self.category_combo.grid(row=0, column=2, padx=10, sticky="e")
        
        # Add product button
        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add Product",
            command=self._add_product,
            height=36,
            width=120,
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
            fg_color=Colors.SUCCESS,
            hover_color="#1B5E20"
        )
        add_btn.grid(row=0, column=3, padx=10, sticky="e")
        
        # Product table
        table_frame = ctk.CTkFrame(self, fg_color=Colors.CARD)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)
        
        # Table header
        header = ctk.CTkLabel(
            table_frame,
            text="Product Inventory",
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        header.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Scrollable product list
        self.products_scroll = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        self.products_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        
        # Column headers
        headers = ["#", "Style Code", "Name", "Category", "Variants", "Stock", "Price", "Actions"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(
                self.products_scroll,
                text=text,
                font=(Fonts.PRIMARY, Fonts.SM, Fonts.BOLD),
                text_color=Colors.TEXT_SECONDARY,
                width=[40, 100, 150, 100, 80, 80, 100, 120][col]
            ).grid(row=0, column=col, padx=5, pady=5, sticky="w")
            
        self.products_list_frame = ctk.CTkFrame(self.products_scroll, fg_color="transparent")
        self.products_list_frame.grid(row=1, column=0, sticky="ew")
        
    def _load_products(self):
        """Load products from database."""
        try:
            conn = self.connection_manager.get_read_connection()
            cursor = conn.cursor()
            
            # Build query with filters
            query = """
                SELECT s.id, s.style_code, s.name, c.name as category,
                       COUNT(DISTINCT v.id) as variant_count,
                       COALESCE(SUM(v.quantity), 0) as total_stock,
                       s.base_sale_price
                FROM styles s
                JOIN categories c ON s.category_id = c.id
                LEFT JOIN variants v ON s.id = v.style_id
                WHERE s.is_active = 1
            """
            params = []
            
            if self.current_category != "All":
                query += " AND c.name = ?"
                params.append(self.current_category)
                
            if self.search_query:
                query += " AND (s.name LIKE ? OR s.style_code LIKE ?)"
                search_pattern = f"%{self.search_query}%"
                params.extend([search_pattern, search_pattern])
                
            query += " GROUP BY s.id ORDER BY s.name"
            
            cursor.execute(query, params)
            products = cursor.fetchall()
            
            # Display products
            self._display_products(products)
            
            # Load categories for filter
            self._load_categories()
            
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            
    def _load_categories(self):
        """Load categories for filter dropdown."""
        try:
            conn = self.connection_manager.get_read_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories ORDER BY name")
            categories = ["All"] + [row[0] for row in cursor.fetchall()]
            self.category_combo.configure(values=categories)
        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            
    def _display_products(self, products):
        """Display products in the list."""
        # Clear existing
        for widget in self.products_list_frame.winfo_children():
            widget.destroy()
            
        if not products:
            ctk.CTkLabel(
                self.products_list_frame,
                text="No products found",
                font=(Fonts.PRIMARY, Fonts.MD),
                text_color=Colors.TEXT_SECONDARY
            ).grid(row=0, column=0, pady=20)
            return
            
        # Display each product
        for idx, product in enumerate(products, 1):
            prod_id, style_code, name, category, variants, stock, price = product
            
            row_frame = ctk.CTkFrame(self.products_list_frame, fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="ew", pady=3)
            
            # ID
            ctk.CTkLabel(
                row_frame, text=str(idx), width=40,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=0, padx=5)
            
            # Style code
            ctk.CTkLabel(
                row_frame, text=style_code, width=100,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=1, padx=5)
            
            # Name
            ctk.CTkLabel(
                row_frame, text=name[:20], width=150,
                font=(Fonts.PRIMARY, Fonts.SM), anchor="w"
            ).grid(row=0, column=2, padx=5)
            
            # Category
            ctk.CTkLabel(
                row_frame, text=category, width=100,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=3, padx=5)
            
            # Variants count
            ctk.CTkLabel(
                row_frame, text=str(variants), width=80,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=4, padx=5)
            
            # Stock with color coding
            stock_color = Colors.SUCCESS if stock > 10 else (Colors.WARNING if stock > 0 else Colors.DANGER)
            ctk.CTkLabel(
                row_frame, text=str(stock), width=80,
                font=(Fonts.PRIMARY, Fonts.SM),
                text_color=stock_color
            ).grid(row=0, column=5, padx=5)
            
            # Price
            ctk.CTkLabel(
                row_frame, text=f"Rs. {price/100:,.0f}", width=100,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=6, padx=5)
            
            # Actions
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=7, padx=5)
            
            ctk.CTkButton(
                actions_frame, text="✏️", width=35, height=28,
                command=lambda p=prod_id: self._edit_product(p),
                font=(Fonts.PRIMARY, Fonts.SM)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                actions_frame, text="🗑", width=35, height=28,
                command=lambda p=prod_id: self._delete_product(p),
                fg_color=Colors.DANGER,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).pack(side="left", padx=2)
            
    def _on_search(self):
        """Handle search input."""
        self.search_query = self.search_entry.get().strip()
        self._load_products()
        
    def _on_category_change(self, selection):
        """Handle category filter change."""
        self.current_category = selection
        self._load_products()
        
    def _add_product(self):
        """Open add product dialog."""
        logger.info("Add product - TODO")
        
    def _edit_product(self, product_id: int):
        """Open edit product dialog."""
        logger.info(f"Edit product {product_id} - TODO")
        
    def _delete_product(self, product_id: int):
        """Delete product after confirmation."""
        logger.info(f"Delete product {product_id} - TODO")
