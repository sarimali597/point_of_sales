"""
Database Schema Definition and Migration System

This module defines all database tables for the Shoukat POS system using a
three-level style-variant-batch architecture optimized for garment retail.
"""
import sqlite3
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# TABLE CREATION STATEMENTS
# =============================================================================

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'cashier',
    phone TEXT,
    is_active INTEGER DEFAULT 1,
    last_login_at TEXT,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    tax_rate REAL DEFAULT 0.0,
    parent_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_STYLES_TABLE = """
CREATE TABLE IF NOT EXISTS styles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    style_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    description TEXT,
    base_sale_price INTEGER NOT NULL,
    tax_rate REAL DEFAULT 0.0,
    season TEXT,
    image_path TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_VARIANTS_TABLE = """
CREATE TABLE IF NOT EXISTS variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    style_id INTEGER NOT NULL REFERENCES styles(id) ON DELETE CASCADE,
    size TEXT NOT NULL,
    color TEXT NOT NULL,
    barcode TEXT NOT NULL UNIQUE,
    quantity INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 5,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(style_id, size, color)
);
"""

CREATE_BATCHES_TABLE = """
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id INTEGER NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    purchase_price INTEGER NOT NULL,
    secret_code TEXT NOT NULL,
    quantity_received INTEGER NOT NULL,
    quantity_remaining INTEGER NOT NULL,
    vendor_id INTEGER REFERENCES vendors(id),
    bilty_no TEXT,
    bill_no TEXT,
    date_received TEXT DEFAULT CURRENT_DATE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_VENDORS_TABLE = """
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    gstin TEXT,
    balance_due INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CUSTOMERS_TABLE = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    email TEXT,
    address TEXT,
    total_purchases INTEGER DEFAULT 0,
    total_paid INTEGER DEFAULT 0,
    total_due INTEGER DEFAULT 0,
    credit_limit INTEGER DEFAULT 0,
    loyalty_points INTEGER DEFAULT 0,
    last_purchase_date TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SALES_TABLE = """
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT NOT NULL UNIQUE,
    sale_date TEXT DEFAULT CURRENT_TIMESTAMP,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id),
    subtotal INTEGER NOT NULL,
    tax_amount INTEGER DEFAULT 0,
    discount_amount INTEGER DEFAULT 0,
    grand_total INTEGER NOT NULL,
    payment_type TEXT NOT NULL,
    paid_amount INTEGER NOT NULL,
    due_amount INTEGER DEFAULT 0,
    change_amount INTEGER DEFAULT 0,
    status TEXT DEFAULT 'completed',
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SALE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    variant_id INTEGER NOT NULL REFERENCES variants(id),
    batch_id INTEGER REFERENCES batches(id),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    tax_amount INTEGER DEFAULT 0,
    total_amount INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_RETURNS_TABLE = """
CREATE TABLE IF NOT EXISTS returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_number TEXT NOT NULL UNIQUE,
    sale_id INTEGER NOT NULL REFERENCES sales(id),
    return_date TEXT DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    reason TEXT NOT NULL,
    refund_amount INTEGER NOT NULL,
    refund_type TEXT DEFAULT 'cash',
    status TEXT DEFAULT 'completed',
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_RETURN_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS return_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL REFERENCES returns(id) ON DELETE CASCADE,
    sale_item_id INTEGER NOT NULL REFERENCES sale_items(id),
    variant_id INTEGER NOT NULL REFERENCES variants(id),
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    total_amount INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_EXCHANGES_TABLE = """
CREATE TABLE IF NOT EXISTS exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange_number TEXT NOT NULL UNIQUE,
    original_sale_id INTEGER NOT NULL REFERENCES sales(id),
    new_sale_id INTEGER REFERENCES sales(id),
    exchange_date TEXT DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    reason TEXT NOT NULL,
    price_difference INTEGER DEFAULT 0,
    payment_status TEXT DEFAULT 'settled',
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_HELD_SALES_TABLE = """
CREATE TABLE IF NOT EXISTS held_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hold_number TEXT NOT NULL UNIQUE,
    sale_data TEXT NOT NULL,
    customer_id INTEGER,
    user_id INTEGER REFERENCES users(id),
    held_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resumed_at TEXT,
    status TEXT DEFAULT 'held'
);
"""

CREATE_CREDIT_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS credit_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    sale_id INTEGER REFERENCES sales(id),
    payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
    amount INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    reference_no TEXT,
    notes TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_values TEXT,
    new_values TEXT,
    user_id INTEGER REFERENCES users(id),
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    hmac_hash TEXT NOT NULL
);
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    type TEXT DEFAULT 'text',
    description TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id)
);
"""

CREATE_GIFT_CARDS_TABLE = """
CREATE TABLE IF NOT EXISTS gift_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_number TEXT NOT NULL UNIQUE,
    pin_hash TEXT NOT NULL,
    balance INTEGER NOT NULL,
    initial_amount INTEGER NOT NULL,
    issued_date TEXT DEFAULT CURRENT_TIMESTAMP,
    expiry_date TEXT,
    customer_id INTEGER REFERENCES customers(id),
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_LOYALTY_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS loyalty_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    sale_id INTEGER REFERENCES sales(id),
    transaction_type TEXT NOT NULL,
    points INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


# =============================================================================
# INDEX CREATION STATEMENTS
# =============================================================================

CREATE_INDEXES = """
-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_variants_barcode ON variants(barcode);
CREATE INDEX IF NOT EXISTS idx_variants_style_id ON variants(style_id);
CREATE INDEX IF NOT EXISTS idx_variants_stock ON variants(quantity);
CREATE INDEX IF NOT EXISTS idx_batches_variant_id ON batches(variant_id);
CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_number);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_variant ON sale_items(variant_id);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
"""


# =============================================================================
# TRIGGER CREATION STATEMENTS
# =============================================================================

CREATE_UPDATED_AT_TRIGGERS = """
-- Auto-update updated_at timestamp on UPDATE
CREATE TRIGGER IF NOT EXISTS update_users_timestamp
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_categories_timestamp
AFTER UPDATE ON categories
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_styles_timestamp
AFTER UPDATE ON styles
BEGIN
    UPDATE styles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_variants_timestamp
AFTER UPDATE ON variants
BEGIN
    UPDATE variants SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_customers_timestamp
AFTER UPDATE ON customers
BEGIN
    UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_sales_timestamp
AFTER UPDATE ON sales
BEGIN
    UPDATE sales SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


# =============================================================================
# SEED DATA
# =============================================================================

DEFAULT_ADMIN_USER = {
    "username": "admin",
    # Password: admin123 (will be hashed with bcrypt in application)
    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7cVNxmPdNu",
    "full_name": "Administrator",
    "role": "admin",
}

DEFAULT_CATEGORIES = [
    ("Shirts", "SHT", "Men's shirts including formal and casual"),
    ("Pants", "PNT", "Men's pants and trousers"),
    ("T-Shirts", "TSH", "Casual t-shirts"),
    ("Jeans", "JNS", "Denim jeans"),
    ("Kurta", "KRT", "Traditional kurta"),
    ("Waistcoat", "WSC", "Formal waistcoats"),
    ("Blazer", "BLZ", "Formal blazers"),
    ("Ties", "TIE", "Neckties and bow ties"),
    ("Accessories", "ACC", "Belts, cufflinks, and other accessories"),
]

DEFAULT_SETTINGS = [
    ("shop_name", "SHOUKAT SONS GARMENTS", "text", "Shop/business name"),
    ("shop_address", "Main Bazaar, Lahore", "text", "Shop address"),
    ("shop_phone", "03XX-XXXXXXX", "text", "Shop phone number"),
    ("gstin", "", "text", "GST Identification Number"),
    ("tax_rate", "0.0", "real", "Default tax rate percentage"),
    ("currency", "Rs.", "text", "Currency symbol"),
    ("sticker_size", "28x19", "text", "Default sticker size in mm"),
    ("gap_mm", "2", "integer", "Gap between stickers in mm"),
    ("receipt_width", "80mm", "text", "Receipt printer width"),
    ("secret_code_map", '{"0":"L","1":"R","2":"K","3":"B","4":"S","5":"M","6":"N","7":"T","8":"H","9":"W"}', "json", "Secret code digit mapping"),
    ("backup_enabled", "true", "boolean", "Enable automatic backups"),
    ("backup_frequency", "daily", "text", "Backup frequency"),
    ("backup_time", "02:00", "text", "Backup time (24-hour format)"),
    ("backup_retention", "30", "integer", "Number of backups to retain"),
]


def create_all_tables(conn: sqlite3.Connection) -> None:
    """
    Create all database tables if they don't exist.
    
    Args:
        conn: SQLite connection object
    """
    logger.info("Creating database tables...")
    
    tables = [
        CREATE_USERS_TABLE,
        CREATE_CATEGORIES_TABLE,
        CREATE_STYLES_TABLE,
        CREATE_VARIANTS_TABLE,
        CREATE_BATCHES_TABLE,
        CREATE_VENDORS_TABLE,
        CREATE_CUSTOMERS_TABLE,
        CREATE_SALES_TABLE,
        CREATE_SALE_ITEMS_TABLE,
        CREATE_RETURNS_TABLE,
        CREATE_RETURN_ITEMS_TABLE,
        CREATE_EXCHANGES_TABLE,
        CREATE_HELD_SALES_TABLE,
        CREATE_CREDIT_PAYMENTS_TABLE,
        CREATE_AUDIT_LOG_TABLE,
        CREATE_SETTINGS_TABLE,
        CREATE_GIFT_CARDS_TABLE,
        CREATE_LOYALTY_TRANSACTIONS_TABLE,
    ]
    
    for table_sql in tables:
        conn.execute(table_sql)
    
    # Create indexes
    conn.executescript(CREATE_INDEXES)
    
    # Create triggers
    conn.executescript(CREATE_UPDATED_AT_TRIGGERS)
    
    logger.info(f"Created {len(tables)} tables, indexes, and triggers")


def seed_default_data(conn: sqlite3.Connection) -> None:
    """
    Insert default data if tables are empty.
    
    Args:
        conn: SQLite connection object
    """
    logger.info("Seeding default data...")
    
    # Check if admin user exists
    result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if result[0] == 0:
        conn.execute(
            """INSERT INTO users (username, password_hash, full_name, role)
               VALUES (?, ?, ?, ?)""",
            (
                DEFAULT_ADMIN_USER["username"],
                DEFAULT_ADMIN_USER["password_hash"],
                DEFAULT_ADMIN_USER["full_name"],
                DEFAULT_ADMIN_USER["role"],
            ),
        )
        logger.info("Created default admin user")
    
    # Check if categories exist
    result = conn.execute("SELECT COUNT(*) FROM categories").fetchone()
    if result[0] == 0:
        for name, code, description in DEFAULT_CATEGORIES:
            conn.execute(
                """INSERT INTO categories (name, code, description)
                   VALUES (?, ?, ?)""",
                (name, code, description),
            )
        logger.info(f"Created {len(DEFAULT_CATEGORIES)} default categories")
    
    # Check if settings exist
    result = conn.execute("SELECT COUNT(*) FROM settings").fetchone()
    if result[0] == 0:
        for key, value, type_, description in DEFAULT_SETTINGS:
            conn.execute(
                """INSERT INTO settings (key, value, type, description)
                   VALUES (?, ?, ?, ?)""",
                (key, value, type_, description),
            )
        logger.info(f"Created {len(DEFAULT_SETTINGS)} default settings")
    
    conn.commit()
    logger.info("Default data seeding complete")


def get_next_invoice_number(conn: sqlite3.Connection) -> str:
    """
    Generate the next invoice number in format INV-YYYYMMDD-NNNN.
    
    Args:
        conn: SQLite connection object
        
    Returns:
        Next invoice number string
    """
    from datetime import datetime
    
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"INV-{today}-"
    
    result = conn.execute(
        """SELECT invoice_number FROM sales 
           WHERE invoice_number LIKE ? 
           ORDER BY invoice_number DESC LIMIT 1""",
        (prefix + "%",),
    ).fetchone()
    
    if result:
        last_num = int(result[0].split("-")[2])
        next_num = last_num + 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:04d}"


def get_next_serial_number(conn: sqlite3.Connection, prefix: str = "SN") -> str:
    """
    Generate the next serial number for barcodes.
    
    Args:
        conn: SQLite connection object
        prefix: Serial number prefix (default "SN")
        
    Returns:
        Next serial number string
    """
    result = conn.execute(
        """SELECT MAX(CAST(SUBSTR(barcode, LENGTH(?) + 1) AS INTEGER)) 
           FROM variants WHERE barcode LIKE ? || '%'""",
        (prefix, prefix),
    ).fetchone()
    
    last_num = result[0] if result[0] else 0
    next_num = last_num + 1
    
    return f"{prefix}{next_num:04d}"
