"""
Dashboard Screen for Shoukat POS.

Displays real-time statistics and recent activity from the database.
"""
import customtkinter as ctk
from datetime import datetime, timedelta
from typing import Optional
from database.connection import ConnectionManager
# Fix: Import Colors and Fonts from ui.theme, not ui.components
from ui.theme import Colors, Fonts 
from ui.components import StatCard


class DashboardScreen(ctk.CTkFrame):
    """Real-time dashboard with actual data from database."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.connection_manager = ConnectionManager.get_instance()
        
        # Store references to cards for updates
        self.today_sales_card: Optional[StatCard] = None
        self.orders_card: Optional[StatCard] = None
        self.low_stock_card: Optional[StatCard] = None
        self.credit_due_card: Optional[StatCard] = None
        self.activity_label: Optional[ctk.CTkLabel] = None
        
        self._build_dashboard()
        
        # Refresh data after a short delay to allow UI to render
        self.after(100, self._refresh_data)
        
        # Auto-refresh every 30 seconds
        self.after(30000, self._refresh_data)
        
    def _build_dashboard(self):
        """Build the dashboard UI layout."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Apply theme colors
        bg_color = Colors.BACKGROUND
        card_bg = Colors.CARD
        
        # Header
        header = ctk.CTkFrame(self, height=80, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        header.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header, 
            text="Dashboard", 
            font=(Fonts.PRIMARY, 28, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w")
        
        date_str = datetime.now().strftime("%d %B %Y")
        subtitle = ctk.CTkLabel(
            header, 
            text=f"Last updated: {date_str}", 
            font=(Fonts.PRIMARY, 12),
            text_color=Colors.TEXT_SECONDARY
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(5,0))
        
        # Stats Grid
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1)
        stats_frame.grid_rowconfigure(0, weight=1)
        
        # Create 4 stat cards
        self.today_sales_card = StatCard(
            stats_frame, 
            "Today's Sales", 
            "Rs. 0", 
            "+0%", 
            Colors.SUCCESS
        )
        self.today_sales_card.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.orders_card = StatCard(
            stats_frame, 
            "Orders Today", 
            "0", 
            "+0", 
            Colors.PRIMARY
        )
        self.orders_card.grid(row=0, column=1, padx=10, sticky="ew")
        
        self.low_stock_card = StatCard(
            stats_frame, 
            "Low Stock Items", 
            "0", 
            "Action Needed", 
            Colors.WARNING
        )
        self.low_stock_card.grid(row=0, column=2, padx=10, sticky="ew")
        
        self.credit_due_card = StatCard(
            stats_frame, 
            "Credit Due", 
            "Rs. 0", 
            "Outstanding", 
            Colors.DANGER
        )
        self.credit_due_card.grid(row=0, column=3, padx=10, sticky="ew")
        
        # Recent Activity Section
        activity_frame = ctk.CTkFrame(self, fg_color=card_bg, corner_radius=10)
        activity_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        activity_frame.grid_columnconfigure(0, weight=1)
        
        act_title = ctk.CTkLabel(
            activity_frame, 
            text="Recent Sales", 
            font=(Fonts.PRIMARY, 18, Fonts.BOLD),
            text_color=Colors.TEXT_PRIMARY
        )
        act_title.pack(pady=15, padx=15, anchor="w")
        
        self.activity_label = ctk.CTkLabel(
            activity_frame, 
            text="Loading recent sales...", 
            text_color=Colors.TEXT_SECONDARY,
            font=(Fonts.PRIMARY, 14)
        )
        self.activity_label.pack(pady=20)
        
    def _refresh_data(self):
        """Fetch real data from database and update UI."""
        try:
            conn = self.connection_manager.get_read_connection()
            cursor = conn.cursor()
            
            # 1. Today's Sales Total
            today_start = datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
            cursor.execute(
                """SELECT COALESCE(SUM(grand_total), 0) 
                   FROM sales 
                   WHERE sale_date >= ? AND status != 'voided'""",
                (today_start,)
            )
            today_sales = cursor.fetchone()[0] or 0
            if self.today_sales_card:
                self.today_sales_card.update_value(f"Rs. {today_sales/100:,.0f}")
            
            # 2. Orders Count Today
            cursor.execute(
                """SELECT COUNT(*) 
                   FROM sales 
                   WHERE sale_date >= ? AND status != 'voided'""",
                (today_start,)
            )
            order_count = cursor.fetchone()[0] or 0
            if self.orders_card:
                self.orders_card.update_value(str(order_count))
            
            # 3. Low Stock Items (quantity <= reorder_point)
            cursor.execute(
                """SELECT COUNT(*) 
                   FROM variants 
                   WHERE quantity <= reorder_point"""
            )
            low_stock = cursor.fetchone()[0] or 0
            if self.low_stock_card:
                self.low_stock_card.update_value(str(low_stock))
                
                # Change indicator text based on severity
                if low_stock > 10:
                    if hasattr(self.low_stock_card, 'update_indicator'):
                        self.low_stock_card.update_indicator("Critical", Colors.DANGER)
                elif low_stock > 0:
                    if hasattr(self.low_stock_card, 'update_indicator'):
                        self.low_stock_card.update_indicator("Action Needed", Colors.WARNING)
                else:
                    if hasattr(self.low_stock_card, 'update_indicator'):
                        self.low_stock_card.update_indicator("All Good", Colors.SUCCESS)
            
            # 4. Total Credit Due
            cursor.execute(
                """SELECT COALESCE(SUM(total_due), 0) 
                   FROM customers 
                   WHERE total_due > 0"""
            )
            credit_due = cursor.fetchone()[0] or 0
            if self.credit_due_card:
                self.credit_due_card.update_value(f"Rs. {credit_due/100:,.0f}")
            
            # 5. Recent Sales (Last 5)
            cursor.execute(
                """SELECT invoice_number, grand_total, sale_date, customer_id
                   FROM sales 
                   WHERE status != 'voided'
                   ORDER BY sale_date DESC 
                   LIMIT 5"""
            )
            recent_sales = cursor.fetchall()
            
            if self.activity_label:
                if not recent_sales:
                    self.activity_label.configure(text="No recent sales found")
                else:
                    lines = []
                    for sale in recent_sales:
                        inv_num = sale[0]
                        amount = sale[1] / 100
                        date_str = sale[2][:16].replace("T", " ") if "T" in sale[2] else sale[2]
                        customer = "Walk-in" if not sale[3] else f"Customer #{sale[3]}"
                        lines.append(f"{inv_num} - {customer} - Rs. {amount:,.0f} ({date_str})")
                    
                    self.activity_label.configure(text="\n".join(lines))
            
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
            if self.activity_label:
                self.activity_label.configure(text="Error loading data")
        finally:
            # Schedule next refresh only if widget still exists
            try:
                self.after(30000, self._refresh_data)
            except Exception:
                pass
