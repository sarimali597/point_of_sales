"""
Customer Manager Screen for Shoukat POS.

Displays customer list with search, credit management, and purchase history.
"""
import customtkinter as ctk
from typing import Dict, List, Optional
from database.connection import ConnectionManager
from ui.theme import Colors, Fonts
import logging

logger = logging.getLogger(__name__)


class CustomerManagerScreen(ctk.CTkFrame):
    """Customer management with search and credit tracking."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.connection_manager = ConnectionManager.get_instance()
        self.search_query = ""
        
        self._build_ui()
        self._load_customers()
        
    def _build_ui(self):
        """Build customer manager UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="👥 Customers",
            font=(Fonts.PRIMARY, 24, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Search bar
        self.search_entry = ctk.CTkEntry(
            header_frame,
            placeholder_text="Search by name or phone...",
            height=36,
            width=300,
            font=(Fonts.PRIMARY, Fonts.MD)
        )
        self.search_entry.grid(row=0, column=1, padx=20, sticky="e")
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())
        
        # Add customer button
        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add Customer",
            command=self._add_customer,
            height=36,
            width=130,
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
            fg_color=Colors.SUCCESS,
            hover_color="#1B5E20"
        )
        add_btn.grid(row=0, column=2, padx=10, sticky="e")
        
        # Customer table
        table_frame = ctk.CTkFrame(self, fg_color=Colors.CARD)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(1, weight=1)
        
        # Table header
        header = ctk.CTkLabel(
            table_frame,
            text="Customer Directory",
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        header.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Scrollable customer list
        self.customers_scroll = ctk.CTkScrollableFrame(table_frame, fg_color="transparent")
        self.customers_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        
        # Column headers
        headers = ["#", "Name", "Phone", "Total Purchases", "Paid", "Due", "Credit Limit", "Actions"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(
                self.customers_scroll,
                text=text,
                font=(Fonts.PRIMARY, Fonts.SM, Fonts.BOLD),
                text_color=Colors.TEXT_SECONDARY,
                width=[40, 150, 120, 100, 100, 100, 100, 140][col]
            ).grid(row=0, column=col, padx=5, pady=5, sticky="w")
            
        self.customers_list_frame = ctk.CTkFrame(self.customers_scroll, fg_color="transparent")
        self.customers_list_frame.grid(row=1, column=0, sticky="ew")
        
    def _load_customers(self):
        """Load customers from database."""
        try:
            conn = self.connection_manager.get_read_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, name, phone, total_purchases, total_paid, 
                       total_due, credit_limit, is_active
                FROM customers
                WHERE is_active = 1
            """
            params = []
            
            if self.search_query:
                query += " AND (name LIKE ? OR phone LIKE ?)"
                search_pattern = f"%{self.search_query}%"
                params.extend([search_pattern, search_pattern])
                
            query += " ORDER BY name"
            
            cursor.execute(query, params)
            customers = cursor.fetchall()
            
            self._display_customers(customers)
            
        except Exception as e:
            logger.error(f"Error loading customers: {e}")
            
    def _display_customers(self, customers):
        """Display customers in the list."""
        # Clear existing
        for widget in self.customers_list_frame.winfo_children():
            widget.destroy()
            
        if not customers:
            ctk.CTkLabel(
                self.customers_list_frame,
                text="No customers found",
                font=(Fonts.PRIMARY, Fonts.MD),
                text_color=Colors.TEXT_SECONDARY
            ).grid(row=0, column=0, pady=20)
            return
            
        # Display each customer
        for idx, cust in enumerate(customers, 1):
            cust_id, name, phone, purchases, paid, due, limit, is_active = cust
            
            row_frame = ctk.CTkFrame(self.customers_list_frame, fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="ew", pady=3)
            
            # ID
            ctk.CTkLabel(
                row_frame, text=str(idx), width=40,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=0, padx=5)
            
            # Name
            ctk.CTkLabel(
                row_frame, text=name[:18], width=150,
                font=(Fonts.PRIMARY, Fonts.SM), anchor="w"
            ).grid(row=0, column=1, padx=5)
            
            # Phone
            ctk.CTkLabel(
                row_frame, text=phone, width=120,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=2, padx=5)
            
            # Total purchases
            ctk.CTkLabel(
                row_frame, text=f"Rs. {purchases/100:,.0f}", width=100,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=3, padx=5)
            
            # Paid
            ctk.CTkLabel(
                row_frame, text=f"Rs. {paid/100:,.0f}", width=100,
                font=(Fonts.PRIMARY, Fonts.SM),
                text_color=Colors.SUCCESS
            ).grid(row=0, column=4, padx=5)
            
            # Due with color coding
            due_color = Colors.DANGER if due > 0 else Colors.SUCCESS
            ctk.CTkLabel(
                row_frame, text=f"Rs. {due/100:,.0f}", width=100,
                font=(Fonts.PRIMARY, Fonts.SM, Fonts.BOLD),
                text_color=due_color
            ).grid(row=0, column=5, padx=5)
            
            # Credit limit
            ctk.CTkLabel(
                row_frame, text=f"Rs. {limit/100:,.0f}", width=100,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=6, padx=5)
            
            # Actions
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=7, padx=5)
            
            ctk.CTkButton(
                actions_frame, text="✏️", width=35, height=28,
                command=lambda c=cust_id: self._edit_customer(c),
                font=(Fonts.PRIMARY, Fonts.SM)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                actions_frame, text="💰", width=35, height=28,
                command=lambda c=cust_id: self._record_payment(c),
                fg_color=Colors.SUCCESS,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                actions_frame, text="🗑", width=35, height=28,
                command=lambda c=cust_id: self._delete_customer(c),
                fg_color=Colors.DANGER,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).pack(side="left", padx=2)
            
    def _on_search(self):
        """Handle search input."""
        self.search_query = self.search_entry.get().strip()
        self._load_customers()
        
    def _add_customer(self):
        """Open add customer dialog."""
        logger.info("Add customer - TODO")
        
    def _edit_customer(self, customer_id: int):
        """Open edit customer dialog."""
        logger.info(f"Edit customer {customer_id} - TODO")
        
    def _record_payment(self, customer_id: int):
        """Open payment recording dialog."""
        logger.info(f"Record payment for customer {customer_id} - TODO")
        
    def _delete_customer(self, customer_id: int):
        """Delete customer after confirmation."""
        logger.info(f"Delete customer {customer_id} - TODO")
