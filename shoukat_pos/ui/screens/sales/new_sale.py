"""
New Sale Screen for Shoukat POS.

Handles barcode scanning, cart management, customer selection,
payment processing, and receipt printing.
"""
import customtkinter as ctk
from typing import Dict, List, Optional, Any
from datetime import datetime
from database.connection import ConnectionManager
from ui.theme import Colors, Fonts
import logging

logger = logging.getLogger(__name__)


class NewSaleScreen(ctk.CTkFrame):
    """Screen for processing new sales transactions."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.connection_manager = ConnectionManager.get_instance()
        self.cart: List[Dict[str, Any]] = []
        self.current_customer: Optional[Dict[str, Any]] = None
        
        # Build UI
        self._build_ui()
        self._bind_events()
        
    def _build_ui(self):
        """Build the complete sale screen UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=3)  # Product entry & cart
        self.grid_columnconfigure(1, weight=2)  # Customer & payment
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel (Product entry + Cart)
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # Product entry section
        self._build_product_entry(left_panel)
        
        # Cart table
        self._build_cart_table(left_panel)
        
        # Right panel (Customer + Payment + Actions)
        right_panel = ctk.CTkFrame(self, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_panel.grid_rowconfigure((0, 1, 2), weight=0)
        right_panel.grid_rowconfigure(3, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Customer section
        self._build_customer_section(right_panel)
        
        # Payment section
        self._build_payment_section(right_panel)
        
        # Totals section
        self._build_totals_section(right_panel)
        
        # Action buttons
        self._build_action_buttons(right_panel)
        
    def _build_product_entry(self, parent):
        """Build product entry area with barcode scanner."""
        entry_frame = ctk.CTkFrame(parent, height=100, fg_color=Colors.CARD)
        entry_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        entry_frame.grid_columnconfigure(1, weight=1)
        entry_frame.pack_propagate(False)
        
        # Title
        title = ctk.CTkLabel(
            entry_frame,
            text="🛍️ Add Products",
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")
        
        # Barcode input
        barcode_label = ctk.CTkLabel(
            entry_frame,
            text="Barcode:",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY
        )
        barcode_label.grid(row=1, column=0, padx=15, sticky="e")
        
        self.barcode_entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text="Scan or enter barcode",
            height=40,
            font=(Fonts.PRIMARY, Fonts.MD)
        )
        self.barcode_entry.grid(row=1, column=1, padx=15, pady=10, sticky="ew")
        self.barcode_entry.focus_set()
        
        # Manual search button
        search_btn = ctk.CTkButton(
            entry_frame,
            text="🔍 Search",
            command=self._open_product_search,
            height=36,
            width=100,
            font=(Fonts.PRIMARY, Fonts.SM)
        )
        search_btn.grid(row=1, column=2, padx=15, pady=10)
        
    def _build_cart_table(self, parent):
        """Build cart items table."""
        cart_frame = ctk.CTkFrame(parent, fg_color=Colors.CARD)
        cart_frame.grid(row=1, column=0, sticky="nsew")
        cart_frame.grid_columnconfigure(0, weight=1)
        cart_frame.grid_rowconfigure(1, weight=1)
        
        # Cart header
        header = ctk.CTkLabel(
            cart_frame,
            text="🛒 Shopping Cart",
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        header.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Cart scrollable frame
        self.cart_scroll = ctk.CTkScrollableFrame(cart_frame, fg_color="transparent")
        self.cart_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        
        # Cart headers
        headers = ["#", "Product", "Size", "Color", "Qty", "Price", "Total", "Action"]
        for col, header_text in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.cart_scroll,
                text=header_text,
                font=(Fonts.PRIMARY, Fonts.SM, Fonts.BOLD),
                text_color=Colors.TEXT_SECONDARY,
                width=80 if col > 0 else 40
            )
            lbl.grid(row=0, column=col, padx=5, pady=5, sticky="w")
        
        self.cart_items_frame = ctk.CTkFrame(self.cart_scroll, fg_color="transparent")
        self.cart_items_frame.grid(row=1, column=0, sticky="ew")
        
    def _build_customer_section(self, parent):
        """Build customer selection section."""
        cust_frame = ctk.CTkFrame(parent, height=140, fg_color=Colors.CARD)
        cust_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        cust_frame.grid_columnconfigure(0, weight=1)
        cust_frame.pack_propagate(False)
        
        # Title
        title = ctk.CTkLabel(
            cust_frame,
            text="👥 Customer",
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        # Customer dropdown
        self.customer_var = ctk.StringVar(value="Walk-in Customer")
        self.customer_combo = ctk.CTkComboBox(
            cust_frame,
            variable=self.customer_var,
            values=["Walk-in Customer"],
            command=self._on_customer_selected,
            height=36,
            font=(Fonts.PRIMARY, Fonts.MD)
        )
        self.customer_combo.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        # New customer button
        new_cust_btn = ctk.CTkButton(
            cust_frame,
            text="+ New Customer",
            command=self._add_new_customer,
            height=32,
            width=120,
            font=(Fonts.PRIMARY, Fonts.SM)
        )
        new_cust_btn.grid(row=2, column=0, padx=15, pady=5, sticky="w")
        
        # Credit info label
        self.credit_label = ctk.CTkLabel(
            cust_frame,
            text="",
            font=(Fonts.PRIMARY, Fonts.SM),
            text_color=Colors.TEXT_SECONDARY
        )
        self.credit_label.grid(row=3, column=0, padx=15, pady=5, sticky="w")
        
    def _build_payment_section(self, parent):
        """Build payment type selection."""
        pay_frame = ctk.CTkFrame(parent, height=140, fg_color=Colors.CARD)
        pay_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        pay_frame.grid_columnconfigure(0, weight=1)
        pay_frame.pack_propagate(False)
        
        # Title
        title = ctk.CTkLabel(
            pay_frame,
            text="💳 Payment",
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")
        
        # Payment type radio buttons
        self.payment_type = ctk.StringVar(value="cash")
        
        cash_radio = ctk.CTkRadioButton(
            pay_frame,
            text="Cash",
            variable=self.payment_type,
            value="cash",
            command=self._update_payment_fields
        )
        cash_radio.grid(row=1, column=0, padx=15, sticky="w")
        
        credit_radio = ctk.CTkRadioButton(
            pay_frame,
            text="Credit",
            variable=self.payment_type,
            value="credit",
            command=self._update_payment_fields
        )
        credit_radio.grid(row=2, column=0, padx=15, sticky="w")
        
        # Paid amount field
        paid_label = ctk.CTkLabel(
            pay_frame,
            text="Amount Paid:",
            font=(Fonts.PRIMARY, Fonts.SM),
            text_color=Colors.TEXT_SECONDARY
        )
        paid_label.grid(row=3, column=0, padx=15, sticky="w", pady=(10, 0))
        
        self.paid_entry = ctk.CTkEntry(
            pay_frame,
            placeholder_text="0",
            height=32,
            font=(Fonts.PRIMARY, Fonts.MD)
        )
        self.paid_entry.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        
    def _build_totals_section(self, parent):
        """Build totals display."""
        totals_frame = ctk.CTkFrame(parent, fg_color=Colors.CARD)
        totals_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        totals_frame.grid_columnconfigure(1, weight=1)
        
        # Subtotal
        ctk.CTkLabel(
            totals_frame,
            text="Subtotal:",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY
        ).grid(row=0, column=0, padx=15, pady=5, sticky="e")
        
        self.subtotal_label = ctk.CTkLabel(
            totals_frame,
            text="Rs. 0",
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        self.subtotal_label.grid(row=0, column=1, padx=15, pady=5, sticky="e")
        
        # Tax
        ctk.CTkLabel(
            totals_frame,
            text="Tax:",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY
        ).grid(row=1, column=0, padx=15, pady=5, sticky="e")
        
        self.tax_label = ctk.CTkLabel(
            totals_frame,
            text="Rs. 0",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_PRIMARY
        )
        self.tax_label.grid(row=1, column=1, padx=15, pady=5, sticky="e")
        
        # Discount
        ctk.CTkLabel(
            totals_frame,
            text="Discount:",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.TEXT_SECONDARY
        ).grid(row=2, column=0, padx=15, pady=5, sticky="e")
        
        self.discount_label = ctk.CTkLabel(
            totals_frame,
            text="Rs. 0",
            font=(Fonts.PRIMARY, Fonts.MD),
            text_color=Colors.DANGER
        )
        self.discount_label.grid(row=2, column=1, padx=15, pady=5, sticky="e")
        
        # Grand Total (large)
        ctk.CTkLabel(
            totals_frame,
            text="TOTAL:",
            font=(Fonts.PRIMARY, 16, Fonts.BOLD),
            text_color=Colors.PRIMARY
        ).grid(row=3, column=0, padx=15, pady=10, sticky="e")
        
        self.total_label = ctk.CTkLabel(
            totals_frame,
            text="Rs. 0",
            font=(Fonts.PRIMARY, 20, Fonts.BOLD),
            text_color=Colors.PRIMARY
        )
        self.total_label.grid(row=3, column=1, padx=15, pady=10, sticky="e")
        
        # Change display
        self.change_label = ctk.CTkLabel(
            totals_frame,
            text="Change: Rs. 0",
            font=(Fonts.PRIMARY, Fonts.SM),
            text_color=Colors.SUCCESS
        )
        self.change_label.grid(row=4, column=0, columnspan=2, padx=15, pady=5)
        
    def _build_action_buttons(self, parent):
        """Build action buttons (Hold, Cancel, Save & Print)."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="nsew")
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Hold button
        hold_btn = ctk.CTkButton(
            btn_frame,
            text="⏸ Hold",
            command=self._hold_sale,
            height=50,
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
            fg_color=Colors.WARNING,
            hover_color="#E65100"
        )
        hold_btn.grid(row=0, column=0, padx=5, pady=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="✕ Cancel",
            command=self._cancel_sale,
            height=50,
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
            fg_color=Colors.DANGER,
            hover_color="#B71C1C"
        )
        cancel_btn.grid(row=0, column=1, padx=5, pady=10)
        
        # Save & Print button (primary)
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Save & Print",
            command=self._complete_sale,
            height=50,
            font=(Fonts.PRIMARY, Fonts.MD, Fonts.BOLD),
            fg_color=Colors.SUCCESS,
            hover_color="#1B5E20"
        )
        save_btn.grid(row=0, column=2, padx=5, pady=10)
        
    def _bind_events(self):
        """Bind keyboard events."""
        self.barcode_entry.bind("<Return>", lambda e: self._process_barcode())
        self.paid_entry.bind("<Return>", lambda e: self._complete_sale())
        
    def _process_barcode(self):
        """Process scanned/entered barcode."""
        barcode = self.barcode_entry.get().strip()
        if not barcode:
            return
            
        try:
            conn = self.connection_manager.get_read_connection()
            cursor = conn.cursor()
            
            # Find variant by barcode
            cursor.execute(
                """SELECT v.id, v.barcode, v.size, v.color, v.quantity, 
                          s.name, s.base_sale_price, s.tax_rate
                   FROM variants v
                   JOIN styles s ON v.style_id = s.id
                   WHERE v.barcode = ?""",
                (barcode,)
            )
            row = cursor.fetchone()
            
            if row:
                variant_id, barcode, size, color, stock, name, price, tax_rate = row
                
                # Check stock
                existing_item = next((item for item in self.cart if item['variant_id'] == variant_id), None)
                current_qty = existing_item['qty'] if existing_item else 0
                
                if current_qty + 1 > stock:
                    logger.warning(f"Insufficient stock for {name}")
                    return
                
                # Add to cart
                if existing_item:
                    existing_item['qty'] += 1
                    existing_item['total'] = existing_item['qty'] * existing_item['price']
                else:
                    self.cart.append({
                        'variant_id': variant_id,
                        'barcode': barcode,
                        'name': name,
                        'size': size,
                        'color': color,
                        'price': price,
                        'tax_rate': tax_rate,
                        'qty': 1,
                        'tax': int(price * tax_rate / 100),
                        'total': price
                    })
                
                self._refresh_cart_display()
                self._calculate_totals()
                self.barcode_entry.delete(0, 'end')
                self.barcode_entry.focus_set()
            else:
                logger.warning(f"Barcode not found: {barcode}")
                
        except Exception as e:
            logger.error(f"Error processing barcode: {e}")
            
    def _refresh_cart_display(self):
        """Refresh cart items display."""
        # Clear existing items
        for widget in self.cart_items_frame.winfo_children():
            widget.destroy()
            
        # Display cart items
        for idx, item in enumerate(self.cart, 1):
            row_frame = ctk.CTkFrame(self.cart_items_frame, fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="ew", pady=2)
            
            ctk.CTkLabel(
                row_frame, text=str(idx), width=40,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=0, padx=5)
            
            ctk.CTkLabel(
                row_frame, text=item['name'][:15], width=80,
                font=(Fonts.PRIMARY, Fonts.SM), anchor="w"
            ).grid(row=0, column=1, padx=5)
            
            ctk.CTkLabel(
                row_frame, text=item['size'], width=50,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=2, padx=5)
            
            ctk.CTkLabel(
                row_frame, text=item['color'], width=50,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=3, padx=5)
            
            qty_spin = ctk.CTkSpinBox(
                row_frame, from_=1, to=99, width=50,
                font=(Fonts.PRIMARY, Fonts.SM),
                command=lambda v, i=item: self._update_item_qty(i, int(v))
            )
            qty_spin.set(item['qty'])
            qty_spin.grid(row=0, column=4, padx=5)
            
            ctk.CTkLabel(
                row_frame, text=f"Rs. {item['price']/100:,.0f}", width=80,
                font=(Fonts.PRIMARY, Fonts.SM)
            ).grid(row=0, column=5, padx=5)
            
            ctk.CTkLabel(
                row_frame, text=f"Rs. {item['total']/100:,.0f}", width=80,
                font=(Fonts.PRIMARY, Fonts.SM, Fonts.BOLD)
            ).grid(row=0, column=6, padx=5)
            
            remove_btn = ctk.CTkButton(
                row_frame, text="🗑", width=40, height=28,
                command=lambda i=item: self._remove_item(i),
                fg_color=Colors.DANGER,
                hover_color="#B71C1C"
            )
            remove_btn.grid(row=0, column=7, padx=5)
            
    def _update_item_qty(self, item: Dict, new_qty: int):
        """Update item quantity in cart."""
        if new_qty < 1:
            return
            
        conn = self.connection_manager.get_read_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM variants WHERE id = ?", (item['variant_id'],))
        row = cursor.fetchone()
        available_stock = row[0] if row else 0
        
        if new_qty > available_stock:
            return
            
        item['qty'] = new_qty
        item['total'] = new_qty * item['price']
        item['tax'] = int(new_qty * item['price'] * item['tax_rate'] / 100)
        
        self._refresh_cart_display()
        self._calculate_totals()
        
    def _remove_item(self, item: Dict):
        """Remove item from cart."""
        self.cart.remove(item)
        self._refresh_cart_display()
        self._calculate_totals()
        
    def _calculate_totals(self):
        """Calculate cart totals."""
        subtotal = sum(item['total'] for item in self.cart)
        total_tax = sum(item['tax'] for item in self.cart)
        discount = 0
        grand_total = subtotal + total_tax - discount
        
        self.subtotal_label.configure(text=f"Rs. {subtotal/100:,.0f}")
        self.tax_label.configure(text=f"Rs. {total_tax/100:,.0f}")
        self.discount_label.configure(text=f"- Rs. {discount/100:,.0f}")
        self.total_label.configure(text=f"Rs. {grand_total/100:,.0f}")
        
        try:
            paid = int(float(self.paid_entry.get() or 0) * 100)
            change = paid - grand_total
            self.change_label.configure(
                text=f"Change: Rs. {change/100:,.0f}",
                text_color=Colors.SUCCESS if change >= 0 else Colors.DANGER
            )
        except:
            pass
            
    def _on_customer_selected(self, selection):
        """Handle customer selection."""
        if selection == "Walk-in Customer":
            self.current_customer = None
            self.credit_label.configure(text="")
        else:
            conn = self.connection_manager.get_read_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, name, total_due, credit_limit 
                   FROM customers WHERE name = ?""",
                (selection,)
            )
            row = cursor.fetchone()
            if row:
                self.current_customer = {
                    'id': row[0],
                    'name': row[1],
                    'total_due': row[2],
                    'credit_limit': row[3]
                }
                due = row[2] / 100
                limit = row[3] / 100
                self.credit_label.configure(text=f"Due: Rs. {due:,.0f} | Limit: Rs. {limit:,.0f}")
                
    def _add_new_customer(self):
        """Open dialog to add new customer."""
        logger.info("Add new customer - TODO")
        
    def _open_product_search(self):
        """Open product search dialog."""
        logger.info("Product search - TODO")
        
    def _update_payment_fields(self):
        """Update payment fields based on payment type."""
        payment_type = self.payment_type.get()
        
        if payment_type == "credit":
            self.paid_entry.configure(state="disabled")
        else:
            self.paid_entry.configure(state="normal")
            
    def _hold_sale(self):
        """Hold current sale for later."""
        if not self.cart:
            return
        logger.info("Hold sale - TODO")
        
    def _cancel_sale(self):
        """Cancel current sale."""
        if not self.cart:
            return
            
        self.cart.clear()
        self.current_customer = None
        self.customer_var.set("Walk-in Customer")
        self.paid_entry.delete(0, 'end')
        self._refresh_cart_display()
        self._calculate_totals()
        self.credit_label.configure(text="")
        
    def _complete_sale(self):
        """Complete sale transaction."""
        if not self.cart:
            logger.warning("Cannot complete empty cart")
            return
            
        try:
            grand_total = sum(item['total'] + item['tax'] for item in self.cart)
            payment_type = self.payment_type.get()
            
            if payment_type == "cash":
                try:
                    paid = int(float(self.paid_entry.get() or 0) * 100)
                    if paid < grand_total:
                        logger.warning("Insufficient payment")
                        return
                except:
                    logger.warning("Invalid payment amount")
                    return
                    
            conn = None
            try:
                conn = self.connection_manager.execute_transaction().__enter__()
                
                cursor = conn.cursor()
                today = datetime.now().strftime("%Y%m%d")
                cursor.execute(
                    """SELECT invoice_number FROM sales 
                       WHERE invoice_number LIKE ? 
                       ORDER BY invoice_number DESC LIMIT 1""",
                    (f"INV-{today}-%",)
                )
                row = cursor.fetchone()
                if row:
                    last_num = int(row[0].split("-")[2])
                    inv_num = f"INV-{today}-{last_num + 1:04d}"
                else:
                    inv_num = f"INV-{today}-0001"
                
                cursor.execute(
                    """INSERT INTO sales 
                       (invoice_number, customer_id, subtotal, tax_amount, 
                        discount_amount, grand_total, payment_type, 
                        paid_amount, due_amount, status, user_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        inv_num,
                        self.current_customer['id'] if self.current_customer else None,
                        sum(item['total'] for item in self.cart),
                        sum(item['tax'] for item in self.cart),
                        0,
                        grand_total,
                        payment_type,
                        grand_total if payment_type == "cash" else 0,
                        0 if payment_type == "cash" else grand_total,
                        "completed",
                        1
                    )
                )
                sale_id = cursor.lastrowid
                
                for item in self.cart:
                    cursor.execute(
                        """INSERT INTO sale_items 
                           (sale_id, variant_id, quantity, unit_price, 
                            tax_amount, total_amount)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            sale_id,
                            item['variant_id'],
                            item['qty'],
                            item['price'],
                            item['tax'],
                            item['total']
                        )
                    )
                    
                    cursor.execute(
                        "UPDATE variants SET quantity = quantity - ? WHERE id = ?",
                        (item['qty'], item['variant_id'])
                    )
                
                if payment_type == "credit" and self.current_customer:
                    cursor.execute(
                        "UPDATE customers SET total_due = total_due + ? WHERE id = ?",
                        (grand_total, self.current_customer['id'])
                    )
                
                conn.commit()
                
                logger.info(f"Sale completed: {inv_num}")
                self._cancel_sale()
                
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Sale transaction failed: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error completing sale: {e}")
