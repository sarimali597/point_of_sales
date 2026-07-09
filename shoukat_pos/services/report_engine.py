"""
Reports & Analytics Engine for Shoukat Sons Garments POS.

Provides garment-specific analytics including:
- Size-Color Matrix Heatmaps
- Sales Trends (Daily/Weekly/Monthly/Seasonal)
- Inventory Valuation (Cost vs Retail, FIFO)
- Product Performance (Sell-through rates)
- Customer Analytics (Credit exposure, Loyalty)
- Employee Performance (Commission basis)
- Tax Compliance (GST/VAT reports)

All monetary values returned as floats (Rupees) for UI display,
but calculations use integer cents internally where possible.
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple, Union, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import csv
import io

from database.connection import ConnectionManager, get_connection_manager


@dataclass
class MatrixCell:
    """Represents a single cell in the Size-Color matrix."""
    style_id: int
    style_name: str
    color: str
    size: str
    stock_qty: int
    sales_qty: int
    revenue: float  # In Rupees
    is_low_stock: bool
    is_dead_stock: bool


@dataclass
class TrendPoint:
    """A single data point in a time-series trend."""
    period: str  # e.g., "2026-01-15" or "2026-W03" or "2026-01"
    sales_count: int
    gross_revenue: float
    net_revenue: float
    returns_count: int
    return_amount: float
    profit: float  # Estimated based on FIFO cost


@dataclass
class InventoryItem:
    """Single item for inventory valuation report."""
    product_id: int
    product_name: str
    variant_info: str  # "Size: L, Color: Blue"
    category: str
    collection: str
    quantity: int
    cost_price: float
    retail_price: float
    total_cost_value: float
    total_retail_value: float
    potential_profit: float
    days_in_stock: int
    status: Literal['active', 'low_stock', 'dead_stock', 'overstock']


@dataclass
class EmployeePerformance:
    """Performance metrics for a cashier/salesperson."""
    user_id: int
    username: str
    total_sales: int
    total_revenue: float
    avg_transaction_value: float
    returns_handled: int
    commission_earned: float


class ReportEngine:
    """
    Central engine for generating all POS reports.
    
    Uses optimized SQL queries with GROUP BY and CASE statements
    to aggregate data efficiently without loading entire tables.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self._conn_manager: Optional[ConnectionManager] = None
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get a read-only connection for reporting queries."""
        # Use global config DB path if none specified
        actual_db_path = self.db_path or get_connection_manager().db_path
        
        if self._conn_manager is None:
            # Create a dedicated manager for this path
            from database.connection import ConnectionManager as CM
            self._conn_manager = CM()
            self._conn_manager.db_path = actual_db_path
        
        return self._conn_manager.get_read_connection()
    
    # =========================================================================
    # 1. SIZE-COLOR MATRIX HEATMAP
    # =========================================================================
    
    def get_size_color_matrix(
        self, 
        style_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a Size-Color matrix heatmap for garment variants.
        
        Args:
            style_id: Filter by specific style (None for all)
            start_date: ISO date string to filter sales
            end_date: ISO date string to filter sales
            
        Returns:
            Dictionary with 'headers' (sizes), 'rows' (colors), 
            'data' (nested dict of cells), and 'summary' stats.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Build dynamic query based on filters
        style_filter = "AND p.style_id = ?" if style_id else ""
        style_params = [style_id] if style_id else []
        
        # Get current stock levels per variant
        stock_query = f"""
            SELECT 
                p.style_id,
                p.name as style_name,
                v.color,
                v.size,
                COALESCE(SUM(b.quantity), 0) as stock_qty,
                p.category,
                p.collection
            FROM products p
            JOIN variants v ON p.id = v.product_id
            LEFT JOIN batches b ON v.id = b.variant_id
            WHERE 1=1 {style_filter}
            GROUP BY p.id, v.id
            ORDER BY p.style_id, v.color, v.size
        """
        
        cursor.execute(stock_query, style_params)
        stock_rows = cursor.fetchall()
        
        # Get sales data for the period
        date_filter = ""
        date_params = []
        if start_date:
            date_filter += " AND s.sale_date >= ?"
            date_params.append(start_date)
        if end_date:
            date_filter += " AND s.sale_date <= ?"
            date_params.append(end_date)
            
        sales_query = f"""
            SELECT 
                p.style_id,
                v.color,
                v.size,
                COUNT(si.id) as sales_qty,
                SUM(si.total_price) as revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN variants v ON si.variant_id = v.id
            JOIN products p ON v.product_id = p.id
            WHERE s.status = 'completed' {date_filter}
            GROUP BY p.style_id, v.color, v.size
        """
        
        cursor.execute(sales_query, date_params)
        sales_rows = cursor.fetchall()
        conn.close()
        
        # Organize data into matrix structure
        # Structure: {style_id: {color: {size: MatrixCell}}}
        matrix_data = defaultdict(lambda: defaultdict(dict))
        all_sizes = set()
        all_colors = set()
        
        # Initialize with stock data
        for row in stock_rows:
            style_id, style_name, color, size, stock, category, collection = row
            all_sizes.add(size)
            all_colors.add(color)
            
            matrix_data[style_id][color][size] = MatrixCell(
                style_id=style_id,
                style_name=style_name,
                color=color,
                size=size,
                stock_qty=stock,
                sales_qty=0,
                revenue=0.0,
                is_low_stock=stock < 5,
                is_dead_stock=False
            )
        
        # Overlay sales data
        for row in sales_rows:
            style_id, color, size, sales_qty, revenue = row
            revenue_val = (revenue or 0) / 100.0  # Convert cents to Rupees
            
            if color in matrix_data[style_id] and size in matrix_data[style_id][color]:
                cell = matrix_data[style_id][color][size]
                cell.sales_qty += sales_qty
                cell.revenue += revenue_val
                
                # Mark dead stock if no sales in 90 days (simplified logic)
                if start_date and cell.stock_qty > 0 and sales_qty == 0:
                    # Check if stock is old (would need batch created_at in real impl)
                    cell.is_dead_stock = True
        
        # Format output
        sorted_sizes = sorted(list(all_sizes), key=lambda x: (len(x), x))  # S, M, L, XL
        sorted_colors = sorted(list(all_colors))
        
        rows = []
        for style_id, colors in matrix_data.items():
            style_name = next(iter(colors.values())).get(sorted_sizes[0], None)
            if not style_name:
                continue
            style_name = style_name.style_name
            
            for color in sorted_colors:
                if color not in colors:
                    continue
                    
                row_data = {
                    'style_id': style_id,
                    'style_name': style_name,
                    'color': color,
                    'cells': {}
                }
                
                for size in sorted_sizes:
                    cell = colors[color].get(size)
                    if cell:
                        row_data['cells'][size] = {
                            'stock': cell.stock_qty,
                            'sales': cell.sales_qty,
                            'revenue': round(cell.revenue, 2),
                            'is_low_stock': cell.is_low_stock,
                            'is_dead_stock': cell.is_dead_stock
                        }
                    else:
                        row_data['cells'][size] = None  # No such variant
                
                rows.append(row_data)
        
        return {
            'headers': sorted_sizes,
            'rows': rows,
            'summary': {
                'total_styles': len(matrix_data),
                'total_variants': sum(
                    len(size_dict) 
                    for color_dict in matrix_data.values() 
                    for size_dict in color_dict.values()
                ),
                'total_stock': sum(
                    cell.stock_qty 
                    for color_dict in matrix_data.values() 
                    for size_dict in color_dict.values()
                    for cell in size_dict.values() if isinstance(cell, MatrixCell)
                ),
                'total_sales': sum(
                    cell.sales_qty 
                    for color_dict in matrix_data.values() 
                    for size_dict in color_dict.values()
                    for cell in size_dict.values() if isinstance(cell, MatrixCell)
                )
            }
        }
    
    # =========================================================================
    # 2. SALES TRENDS & TIME-SERIES ANALYSIS
    # =========================================================================
    
    def get_sales_trends(
        self,
        group_by: Literal['day', 'week', 'month', 'year'] = 'day',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[TrendPoint]:
        """
        Generate time-series sales trends.
        
        Args:
            group_by: Time granularity for grouping
            start_date: Start of range (ISO format)
            end_date: End of range (ISO format)
            
        Returns:
            List of TrendPoint objects ordered chronologically
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # SQLite date formatting based on grouping
        if group_by == 'day':
            date_fmt = "%Y-%m-%d"
        elif group_by == 'week':
            date_fmt = "%Y-W%W"  # Year-WeekNumber
        elif group_by == 'month':
            date_fmt = "%Y-%m"
        else:
            date_fmt = "%Y"
        
        date_filter = ""
        params = []
        if start_date:
            date_filter += " AND sale_date >= ?"
            params.append(start_date)
        if end_date:
            date_filter += " AND sale_date <= ?"
            params.append(end_date)
        
        # Main sales aggregation
        query = f"""
            SELECT 
                strftime('{date_fmt}', sale_date) as period,
                COUNT(*) as sales_count,
                SUM(grand_total) as gross_revenue,
                SUM(COALESCE(discount_amount, 0)) as discount_total,
                SUM(COALESCE(tax_amount, 0)) as tax_total
            FROM sales
            WHERE status = 'completed' {date_filter}
            GROUP BY period
            ORDER BY period ASC
        """
        
        cursor.execute(query, params)
        sales_data = {row[0]: row for row in cursor.fetchall()}
        
        # Returns aggregation
        returns_query = f"""
            SELECT 
                strftime('{date_fmt}', r.return_date) as period,
                COUNT(*) as returns_count,
                SUM(r.refund_amount) as return_amount
            FROM returns r
            JOIN sales s ON r.sale_id = s.id
            WHERE s.status = 'completed' {date_filter}
            GROUP BY period
        """
        
        cursor.execute(returns_query, params)
        returns_data = {row[0]: row for row in cursor.fetchall()}
        
        # Calculate profit (simplified: assume 40% average margin if exact FIFO not tracked here)
        # In production, this would join with batch costs
        trends = []
        all_periods = sorted(set(list(sales_data.keys()) + list(returns_data.keys())))
        
        for period in all_periods:
            s_row = sales_data.get(period, (period, 0, 0, 0, 0))
            r_row = returns_data.get(period, (period, 0, 0))
            
            gross = (s_row[2] or 0) / 100.0
            net = gross - ((s_row[3] or 0) / 100.0)
            ret_amt = (r_row[2] or 0) / 100.0
            
            # Estimate profit: (Net Sales - Returns) * 0.40 margin
            estimated_profit = (net - ret_amt) * 0.40
            
            trends.append(TrendPoint(
                period=period,
                sales_count=s_row[1] or 0,
                gross_revenue=round(gross, 2),
                net_revenue=round(net, 2),
                returns_count=r_row[1] or 0,
                return_amount=round(ret_amt, 2),
                profit=round(estimated_profit, 2)
            ))
        
        conn.close()
        return trends
    
    # =========================================================================
    # 3. INVENTORY VALUATION & AGED STOCK
    # =========================================================================
    
    def get_inventory_valuation(
        self,
        include_zero_stock: bool = False
    ) -> List[InventoryItem]:
        """
        Generate detailed inventory valuation report.
        
        Calculates:
        - Total value at Cost Price
        - Total value at Retail Price
        - Potential Profit
        - Days in Stock (based on first batch creation)
        - Status (Active, Low, Dead, Overstock)
        
        Args:
            include_zero_stock: Include items with 0 quantity
            
        Returns:
            List of InventoryItem objects
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            SELECT 
                p.id as product_id,
                p.name as product_name,
                v.size,
                v.color,
                p.category,
                p.collection,
                SUM(b.quantity) as total_qty,
                AVG(b.cost_price) as avg_cost,
                v.retail_price,
                MIN(b.created_at) as first_batch_date
            FROM products p
            JOIN variants v ON p.id = v.product_id
            LEFT JOIN batches b ON v.id = b.variant_id
            GROUP BY p.id, v.id
            HAVING total_qty > 0 OR ?
            ORDER BY p.collection, p.category, p.name, v.color, v.size
        """
        
        cursor.execute(query, (include_zero_stock,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            pid, pname, size, color, cat, coll, qty, cost, retail, first_date = row
            
            if qty == 0 and not include_zero_stock:
                continue
                
            cost_val = (cost or 0) / 100.0
            retail_val = (retail or 0) / 100.0
            
            total_cost = qty * cost_val
            total_retail = qty * retail_val
            potential_profit = total_retail - total_cost
            
            # Calculate days in stock
            days_in_stock = 0
            if first_date:
                try:
                    start = datetime.strptime(first_date, '%Y-%m-%d %H:%M:%S')
                    delta = datetime.now() - start
                    days_in_stock = delta.days
                except ValueError:
                    days_in_stock = 0
            
            # Determine status
            if days_in_stock > 90 and qty > 0:
                status = 'dead_stock'
            elif qty < 5 and qty > 0:
                status = 'low_stock'
            elif qty > 50:  # Arbitrary threshold
                status = 'overstock'
            else:
                status = 'active'
            
            variant_info = f"Size: {size}, Color: {color}"
            
            results.append(InventoryItem(
                product_id=pid,
                product_name=pname,
                variant_info=variant_info,
                category=cat or 'Uncategorized',
                collection=coll or 'General',
                quantity=qty,
                cost_price=round(cost_val, 2),
                retail_price=round(retail_val, 2),
                total_cost_value=round(total_cost, 2),
                total_retail_value=round(total_retail, 2),
                potential_profit=round(potential_profit, 2),
                days_in_stock=days_in_stock,
                status=status
            ))
        
        return results
    
    # =========================================================================
    # 4. PRODUCT PERFORMANCE & SELL-THROUGH
    # =========================================================================
    
    def get_product_performance(
        self,
        limit: int = 20,
        sort_by: Literal['sales', 'revenue', 'profit', 'sell_through'] = 'revenue'
    ) -> List[Dict[str, Any]]:
        """
        Analyze product performance to identify top sellers and losers.
        
        Args:
            limit: Number of top/bottom items to return
            sort_by: Metric to sort by
            
        Returns:
            List of dicts with product stats and sell-through rate
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Calculate sell-through: Sales / (Sales + Current Stock)
        query = """
            SELECT 
                p.id,
                p.name,
                p.category,
                COALESCE(SUM(si.quantity), 0) as total_sold,
                COALESCE(SUM(si.total_price), 0) as total_revenue,
                COALESCE((
                    SELECT SUM(b.quantity) 
                    FROM variants v2 
                    JOIN batches b ON v2.id = b.variant_id 
                    WHERE v2.product_id = p.id
                ), 0) as current_stock,
                COUNT(DISTINCT v.id) as variant_count
            FROM products p
            LEFT JOIN variants v ON p.id = v.product_id
            LEFT JOIN sale_items si ON v.id = si.variant_id
            LEFT JOIN sales s ON si.sale_id = s.id AND s.status = 'completed'
            GROUP BY p.id
            ORDER BY 
                CASE WHEN ? = 'sales' THEN total_sold END DESC,
                CASE WHEN ? = 'revenue' THEN total_revenue END DESC,
                CASE WHEN ? = 'profit' THEN (total_revenue * 0.4) END DESC,
                CASE WHEN ? = 'sell_through' THEN 
                    CAST(total_sold AS FLOAT) / (total_sold + current_stock + 0.001)
                END DESC
            LIMIT ?
        """
        
        cursor.execute(query, (sort_by, sort_by, sort_by, sort_by, limit))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            pid, name, cat, sold, revenue, stock, variants = row
            
            revenue_val = (revenue or 0) / 100.0
            total_available = sold + (stock or 0)
            sell_through = (sold / total_available * 100) if total_available > 0 else 0
            
            results.append({
                'product_id': pid,
                'name': name,
                'category': cat or 'Uncategorized',
                'units_sold': sold,
                'current_stock': stock or 0,
                'revenue': round(revenue_val, 2),
                'estimated_profit': round(revenue_val * 0.4, 2),
                'sell_through_rate': round(sell_through, 1),
                'variant_count': variants,
                'performance_tier': 'star' if sell_through > 70 else ('slow' if sell_through < 20 else 'average')
            })
        
        return results
    
    # =========================================================================
    # 5. CUSTOMER ANALYTICS
    # =========================================================================
    
    def get_customer_analytics(
        self,
        top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Analyze customer behavior, spending, and credit risk.
        
        Args:
            top_n: Number of top customers to return
            
        Returns:
            List of customer profiles with spending and credit stats
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.id,
                c.name,
                c.phone,
                COUNT(s.id) as total_visits,
                SUM(s.grand_total) as total_spent,
                MAX(s.sale_date) as last_visit,
                c.credit_limit,
                c.total_due,
                c.loyalty_points
            FROM customers c
            LEFT JOIN sales s ON c.id = s.customer_id AND s.status = 'completed'
            GROUP BY c.id
            HAVING total_spent > 0 OR c.total_due > 0
            ORDER BY total_spent DESC
            LIMIT ?
        """
        
        cursor.execute(query, (top_n,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            cid, name, phone, visits, spent, last_visit, limit, due, points = row
            
            spent_val = (spent or 0) / 100.0
            limit_val = (limit or 0) / 100.0
            due_val = (due or 0) / 100.0
            
            # Calculate risk level
            if limit_val > 0:
                utilization = (due_val / limit_val) * 100
                if utilization > 90:
                    risk = 'critical'
                elif utilization > 70:
                    risk = 'high'
                elif utilization > 40:
                    risk = 'medium'
                else:
                    risk = 'low'
            else:
                risk = 'none' if due_val == 0 else 'cash_only'
            
            results.append({
                'customer_id': cid,
                'name': name or 'Walk-in Customer',
                'phone': phone,
                'total_visits': visits or 0,
                'total_spent': round(spent_val, 2),
                'last_visit': last_visit,
                'credit_limit': round(limit_val, 2),
                'current_due': round(due_val, 2),
                'credit_utilization': round(utilization if limit_val > 0 else 0, 1),
                'risk_level': risk,
                'loyalty_points': points or 0
            })
        
        return results
    
    # =========================================================================
    # 6. EMPLOYEE PERFORMANCE
    # =========================================================================
    
    def get_employee_performance(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[EmployeePerformance]:
        """
        Track cashier/salesperson performance for commissions.
        
        Args:
            start_date: Filter period start
            end_date: Filter period end
            
        Returns:
            List of EmployeePerformance objects
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        date_filter = ""
        params = []
        if start_date:
            date_filter += " AND s.sale_date >= ?"
            params.append(start_date)
        if end_date:
            date_filter += " AND s.sale_date <= ?"
            params.append(end_date)
        
        query = f"""
            SELECT 
                u.id,
                u.username,
                COUNT(s.id) as total_sales,
                SUM(s.grand_total) as total_revenue,
                SUM(CASE WHEN s.payment_type = 'credit' THEN 1 ELSE 0 END) as credit_sales,
                COALESCE((
                    SELECT COUNT(*) FROM returns r
                    JOIN sales s2 ON r.sale_id = s2.id
                    WHERE s2.cashier_id = u.id {date_filter}
                ), 0) as returns_handled
            FROM users u
            LEFT JOIN sales s ON u.id = s.cashier_id AND s.status = 'completed' {date_filter}
            GROUP BY u.id
            HAVING total_sales > 0
            ORDER BY total_revenue DESC
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            uid, uname, count, revenue, credit_count, returns = row
            
            rev_val = (revenue or 0) / 100.0
            avg_trans = (rev_val / count) if count > 0 else 0
            
            # Assume 2% commission for demo
            commission = rev_val * 0.02
            
            results.append(EmployeePerformance(
                user_id=uid,
                username=uname,
                total_sales=count or 0,
                total_revenue=round(rev_val, 2),
                avg_transaction_value=round(avg_trans, 2),
                returns_handled=returns or 0,
                commission_earned=round(commission, 2)
            ))
        
        return results
    
    # =========================================================================
    # 7. TAX & COMPLIANCE REPORTS
    # =========================================================================
    
    def get_tax_report(
        self,
        start_date: str,
        end_date: str,
        tax_rate: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate GST/VAT compliance report.
        
        Args:
            start_date: Period start (ISO)
            end_date: Period end (ISO)
            tax_rate: Default tax rate if not stored per item
            
        Returns:
            Summary of taxable sales, tax collected, and net sales
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                COUNT(*) as transaction_count,
                SUM(subtotal) as total_taxable,
                SUM(COALESCE(tax_amount, 0)) as tax_collected,
                SUM(grand_total) as gross_receipts,
                SUM(COALESCE(discount_amount, 0)) as total_discounts
            FROM sales
            WHERE status = 'completed'
              AND sale_date >= ?
              AND sale_date <= ?
        """
        
        cursor.execute(query, (start_date, end_date))
        row = cursor.fetchone()
        conn.close()
        
        if not row or row[0] == 0:
            return {
                'period': f"{start_date} to {end_date}",
                'transaction_count': 0,
                'total_taxable': 0.0,
                'tax_collected': 0.0,
                'gross_receipts': 0.0,
                'net_sales': 0.0,
                'effective_tax_rate': 0.0
            }
        
        count, taxable, tax, gross, discounts = row
        
        taxable_val = (taxable or 0) / 100.0
        tax_val = (tax or 0) / 100.0
        gross_val = (gross or 0) / 100.0
        disc_val = (discounts or 0) / 100.0
        
        net_sales = gross_val - tax_val
        eff_rate = (tax_val / taxable_val * 100) if taxable_val > 0 else 0
        
        return {
            'period': f"{start_date} to {end_date}",
            'transaction_count': count,
            'total_taxable': round(taxable_val, 2),
            'tax_collected': round(tax_val, 2),
            'gross_receipts': round(gross_val, 2),
            'total_discounts': round(disc_val, 2),
            'net_sales': round(net_sales, 2),
            'effective_tax_rate': round(eff_rate, 2)
        }
    
    # =========================================================================
    # 8. EXPORT FUNCTIONS
    # =========================================================================
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Export report data to CSV file.
        
        Args:
            data: List of dictionaries with report data
            filename: Output filename (without extension)
            
        Returns:
            Full path to generated CSV file
        """
        import os
        from config import BACKUP_DIR
        
        if not data:
            raise ValueError("Cannot export empty dataset")
        
        filepath = os.path.join(BACKUP_DIR, f"{filename}.csv")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return filepath
    
    def export_matrix_to_excel_format(self, matrix_data: Dict[str, Any]) -> str:
        """
        Export Size-Color matrix to a tab-separated format suitable for Excel.
        
        Args:
            matrix_data: Output from get_size_color_matrix()
            
        Returns:
            Full path to generated TSV file
        """
        import os
        from config import BACKUP_DIR
        
        filepath = os.path.join(BACKUP_DIR, "size_color_matrix.tsv")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Header row
            headers = ['Style', 'Color'] + matrix_data['headers']
            f.write('\t'.join(headers) + '\n')
            
            # Data rows
            for row in matrix_data['rows']:
                row_values = [row['style_name'], row['color']]
                for size in matrix_data['headers']:
                    cell = row['cells'].get(size)
                    if cell:
                        row_values.append(f"{cell['stock']} sold:{cell['sales']}")
                    else:
                        row_values.append('-')
                f.write('\t'.join(row_values) + '\n')
        
        return filepath
