"""
SQL Query Constants

This module contains all SQL query strings used throughout the application.
Using constants ensures consistency and makes queries easier to maintain.
"""
from typing import Dict

# =============================================================================
# USER QUERIES
# =============================================================================

USER_GET_BY_USERNAME = """
    SELECT * FROM users WHERE username = ? AND is_active = 1
"""

USER_UPDATE_LOGIN = """
    UPDATE users 
    SET last_login_at = CURRENT_TIMESTAMP, 
        failed_login_attempts = 0,
        locked_until = NULL
    WHERE id = ?
"""

USER_INCREMENT_FAILED_LOGIN = """
    UPDATE users 
    SET failed_login_attempts = failed_login_attempts + 1
    WHERE id = ?
"""

USER_LOCK_ACCOUNT = """
    UPDATE users 
    SET locked_until = ?
    WHERE id = ?
"""


# =============================================================================
# CATEGORY QUERIES
# =============================================================================

CATEGORY_GET_ALL = """
    SELECT * FROM categories ORDER BY name
"""

CATEGORY_GET_BY_ID = """
    SELECT * FROM categories WHERE id = ?
"""

CATEGORY_INSERT = """
    INSERT INTO categories (name, code, description, tax_rate, parent_id)
    VALUES (?, ?, ?, ?, ?)
"""

CATEGORY_UPDATE = """
    UPDATE categories 
    SET name = ?, code = ?, description = ?, tax_rate = ?, parent_id = ?
    WHERE id = ?
"""

CATEGORY_DELETE = """
    DELETE FROM categories WHERE id = ?
"""


# =============================================================================
# STYLE QUERIES
# =============================================================================

STYLE_GET_ALL = """
    SELECT s.*, c.name as category_name
    FROM styles s
    JOIN categories c ON s.category_id = c.id
    WHERE s.is_active = 1
    ORDER BY s.name
"""

STYLE_GET_BY_ID = """
    SELECT s.*, c.name as category_name
    FROM styles s
    JOIN categories c ON s.category_id = c.id
    WHERE s.id = ?
"""

STYLE_GET_BY_CODE = """
    SELECT * FROM styles WHERE style_code = ?
"""

STYLE_SEARCH = """
    SELECT s.*, c.name as category_name
    FROM styles s
    JOIN categories c ON s.category_id = c.id
    WHERE s.name LIKE ? OR s.style_code LIKE ?
    ORDER BY s.name
"""

STYLE_INSERT = """
    INSERT INTO styles (style_code, name, category_id, description, base_sale_price, tax_rate, season)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

STYLE_UPDATE = """
    UPDATE styles 
    SET name = ?, category_id = ?, description = ?, base_sale_price = ?, 
        tax_rate = ?, season = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
"""

STYLE_DEACTIVATE = """
    UPDATE styles SET is_active = 0 WHERE id = ?
"""

STYLE_GET_VARIANTS = """
    SELECT v.*, s.name as style_name, c.name as category_name
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    JOIN categories c ON s.category_id = c.id
    WHERE v.style_id = ?
    ORDER BY v.size, v.color
"""


# =============================================================================
# VARIANT QUERIES
# =============================================================================

VARIANT_GET_ALL = """
    SELECT v.*, s.name as style_name, c.name as category_name
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    JOIN categories c ON s.category_id = c.id
    ORDER BY s.name, v.size, v.color
"""

VARIANT_GET_BY_ID = """
    SELECT v.*, s.name as style_name, c.name as category_name
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    JOIN categories c ON s.category_id = c.id
    WHERE v.id = ?
"""

VARIANT_GET_BY_BARCODE = """
    SELECT v.*, s.name as style_name, c.name as category_name, s.base_sale_price
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    JOIN categories c ON s.category_id = c.id
    WHERE v.barcode = ?
"""

VARIANT_SEARCH = """
    SELECT v.*, s.name as style_name, c.name as category_name
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    JOIN categories c ON s.category_id = c.id
    WHERE v.barcode LIKE ? OR s.name LIKE ? OR v.size LIKE ? OR v.color LIKE ?
    ORDER BY s.name, v.size, v.color
"""

VARIANT_GET_LOW_STOCK = """
    SELECT v.*, s.name as style_name
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    WHERE v.quantity <= v.reorder_point
    ORDER BY v.quantity ASC
"""

VARIANT_INSERT = """
    INSERT INTO variants (style_id, size, color, barcode, quantity, reorder_point)
    VALUES (?, ?, ?, ?, ?, ?)
"""

VARIANT_UPDATE = """
    UPDATE variants 
    SET size = ?, color = ?, quantity = ?, reorder_point = ?, 
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
"""

VARIANT_UPDATE_STOCK = """
    UPDATE variants 
    SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
"""

VARIANT_GET_MATRIX = """
    SELECT v.*, s.name as style_name, s.base_sale_price
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    WHERE v.style_id = ?
    ORDER BY v.size, v.color
"""


# =============================================================================
# BATCH QUERIES
# =============================================================================

BATCH_GET_BY_VARIANT = """
    SELECT b.*, v.barcode
    FROM batches b
    JOIN variants v ON b.variant_id = v.id
    WHERE b.variant_id = ?
    ORDER BY b.date_received ASC
"""

BATCH_GET_FIFO = """
    SELECT * FROM batches
    WHERE variant_id = ? AND quantity_remaining > 0
    ORDER BY date_received ASC
"""

BATCH_INSERT = """
    INSERT INTO batches (variant_id, purchase_price, secret_code, quantity_received, 
                         quantity_remaining, vendor_id, bilty_no, bill_no, date_received)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

BATCH_UPDATE_REMAINING = """
    UPDATE batches 
    SET quantity_remaining = quantity_remaining - ?
    WHERE id = ?
"""


# =============================================================================
# CUSTOMER QUERIES
# =============================================================================

CUSTOMER_GET_ALL = """
    SELECT * FROM customers WHERE is_active = 1 ORDER BY name
"""

CUSTOMER_GET_BY_ID = """
    SELECT * FROM customers WHERE id = ?
"""

CUSTOMER_GET_BY_PHONE = """
    SELECT * FROM customers WHERE phone = ?
"""

CUSTOMER_SEARCH = """
    SELECT * FROM customers 
    WHERE name LIKE ? OR phone LIKE ?
    ORDER BY name
"""

CUSTOMER_INSERT = """
    INSERT INTO customers (name, phone, email, address, credit_limit)
    VALUES (?, ?, ?, ?, ?)
"""

CUSTOMER_UPDATE = """
    UPDATE customers 
    SET name = ?, phone = ?, email = ?, address = ?, credit_limit = ?, 
        notes = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
"""

CUSTOMER_ADD_DUE = """
    UPDATE customers 
    SET total_due = total_due + ?, 
        total_purchases = total_purchases + ?,
        last_purchase_date = CURRENT_DATE
    WHERE id = ?
"""

CUSTOMER_ADD_PAYMENT = """
    UPDATE customers 
    SET total_due = total_due - ?, 
        total_paid = total_paid + ?,
        last_purchase_date = CURRENT_DATE
    WHERE id = ?
"""

CUSTOMER_GET_PURCHASE_HISTORY = """
    SELECT s.*, u.full_name as cashier_name
    FROM sales s
    LEFT JOIN users u ON s.user_id = u.id
    WHERE s.customer_id = ?
    ORDER BY s.sale_date DESC
"""


# =============================================================================
# SALE QUERIES
# =============================================================================

SALE_GET_BY_ID = """
    SELECT s.*, c.name as customer_name, u.full_name as cashier_name
    FROM sales s
    LEFT JOIN customers c ON s.customer_id = c.id
    LEFT JOIN users u ON s.user_id = u.id
    WHERE s.id = ?
"""

SALE_GET_BY_INVOICE = """
    SELECT s.*, c.name as customer_name, u.full_name as cashier_name
    FROM sales s
    LEFT JOIN customers c ON s.customer_id = c.id
    LEFT JOIN users u ON s.user_id = u.id
    WHERE s.invoice_number = ?
"""

SALE_GET_ITEMS = """
    SELECT si.*, v.barcode, v.size, v.color, s.name as style_name
    FROM sale_items si
    JOIN variants v ON si.variant_id = v.id
    JOIN styles s ON v.style_id = s.id
    WHERE si.sale_id = ?
"""

SALE_INSERT = """
    INSERT INTO sales (invoice_number, customer_id, user_id, subtotal, tax_amount, 
                       discount_amount, grand_total, payment_type, paid_amount, 
                       due_amount, change_amount, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

SALE_ITEM_INSERT = """
    INSERT INTO sale_items (sale_id, variant_id, batch_id, quantity, unit_price, 
                            tax_amount, total_amount)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

SALE_GET_DAILY_TOTALS = """
    SELECT 
        COUNT(*) as total_sales,
        SUM(grand_total) as total_revenue,
        SUM(CASE WHEN payment_type = 'cash' THEN grand_total ELSE 0 END) as cash_sales,
        SUM(CASE WHEN payment_type = 'credit' THEN grand_total ELSE 0 END) as credit_sales
    FROM sales
    WHERE DATE(sale_date) = DATE(?)
"""

SALE_GET_DATE_RANGE = """
    SELECT s.*, c.name as customer_name
    FROM sales s
    LEFT JOIN customers c ON s.customer_id = c.id
    WHERE DATE(s.sale_date) BETWEEN DATE(?) AND DATE(?)
    ORDER BY s.sale_date DESC
"""

SALE_VOID = """
    UPDATE sales SET status = 'voided', updated_at = CURRENT_TIMESTAMP WHERE id = ?
"""


# =============================================================================
# RETURN QUERIES
# =============================================================================

RETURN_INSERT = """
    INSERT INTO returns (return_number, sale_id, user_id, reason, refund_amount, 
                         refund_type, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

RETURN_ITEM_INSERT = """
    INSERT INTO return_items (return_id, sale_item_id, variant_id, quantity, 
                              unit_price, total_amount)
    VALUES (?, ?, ?, ?, ?, ?)
"""

SALE_ITEM_MARK_RETURNED = """
    UPDATE sale_items SET is_returned = 1 WHERE id = ?
"""


# =============================================================================
# HELD SALE QUERIES
# =============================================================================

HELD_SALE_INSERT = """
    INSERT INTO held_sales (hold_number, sale_data, customer_id, user_id)
    VALUES (?, ?, ?, ?)
"""

HELD_SALE_GET_ALL = """
    SELECT h.*, u.full_name as cashier_name, c.name as customer_name
    FROM held_sales h
    LEFT JOIN users u ON h.user_id = u.id
    LEFT JOIN customers c ON h.customer_id = c.id
    WHERE h.status = 'held'
    ORDER BY h.held_at DESC
"""

HELD_SALE_RESUME = """
    UPDATE held_sales 
    SET status = 'resumed', resumed_at = CURRENT_TIMESTAMP 
    WHERE hold_number = ?
"""

HELD_SALE_DELETE = """
    DELETE FROM held_sales WHERE hold_number = ?
"""


# =============================================================================
# CREDIT PAYMENT QUERIES
# =============================================================================

CREDIT_PAYMENT_INSERT = """
    INSERT INTO credit_payments (customer_id, sale_id, amount, payment_method, 
                                  reference_no, notes, user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

CREDIT_PAYMENT_GET_BY_CUSTOMER = """
    SELECT cp.*, u.full_name as cashier_name
    FROM credit_payments cp
    LEFT JOIN users u ON cp.user_id = u.id
    WHERE cp.customer_id = ?
    ORDER BY cp.payment_date DESC
"""


# =============================================================================
# AUDIT LOG QUERIES
# =============================================================================

AUDIT_LOG_INSERT = """
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, 
                           user_id, hmac_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

AUDIT_LOG_GET_BY_RECORD = """
    SELECT * FROM audit_log 
    WHERE table_name = ? AND record_id = ?
    ORDER BY timestamp DESC
"""

AUDIT_LOG_GET_TAMPER_CHECK = """
    SELECT id, table_name, record_id, action, timestamp, hmac_hash
    FROM audit_log
    ORDER BY id
"""


# =============================================================================
# SETTINGS QUERIES
# =============================================================================

SETTING_GET_ALL = """
    SELECT * FROM settings ORDER BY key
"""

SETTING_GET_BY_KEY = """
    SELECT * FROM settings WHERE key = ?
"""

SETTING_UPSERT = """
    INSERT INTO settings (key, value, type, description, updated_by)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET 
        value = excluded.value,
        updated_at = CURRENT_TIMESTAMP,
        updated_by = excluded.updated_by
"""


# =============================================================================
# REPORT QUERIES
# =============================================================================

REPORT_PRODUCT_SALES = """
    SELECT 
        s.name as style_name,
        v.size,
        v.color,
        SUM(si.quantity) as qty_sold,
        SUM(si.total_amount) as revenue
    FROM sale_items si
    JOIN variants v ON si.variant_id = v.id
    JOIN styles s ON v.style_id = s.id
    JOIN sales sa ON si.sale_id = sa.id
    WHERE DATE(sa.sale_date) BETWEEN DATE(?) AND DATE(?)
    GROUP BY v.style_id, v.size, v.color
    ORDER BY revenue DESC
"""

REPORT_CATEGORY_SALES = """
    SELECT 
        c.name as category_name,
        SUM(si.quantity) as qty_sold,
        SUM(si.total_amount) as revenue
    FROM sale_items si
    JOIN variants v ON si.variant_id = v.id
    JOIN styles s ON v.style_id = s.id
    JOIN categories c ON s.category_id = c.id
    JOIN sales sa ON si.sale_id = sa.id
    WHERE DATE(sa.sale_date) BETWEEN DATE(?) AND DATE(?)
    GROUP BY c.id
    ORDER BY revenue DESC
"""

REPORT_STOCK_VALUATION = """
    SELECT 
        s.name as style_name,
        v.size,
        v.color,
        v.quantity,
        SUM(b.purchase_price * b.quantity_remaining) as cost_value,
        SUM(s.base_sale_price * v.quantity) as sale_value
    FROM variants v
    JOIN styles s ON v.style_id = s.id
    LEFT JOIN batches b ON v.id = b.variant_id AND b.quantity_remaining > 0
    GROUP BY v.id
    ORDER BY s.name, v.size, v.color
"""
