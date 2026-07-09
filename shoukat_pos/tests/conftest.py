"""
Pytest configuration and fixtures for Shoukat POS tests.

This module provides shared fixtures for all tests, including:
- Fresh in-memory database for each test
- Sample data generators
- Test utilities
"""

import pytest
import sqlite3
import sys
from pathlib import Path
from typing import Generator

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DATABASE_PRAGMAS
from database.schema import create_all_tables, seed_default_data


@pytest.fixture
def db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Create a fresh in-memory database for each test.
    
    This fixture:
    - Creates an in-memory SQLite database
    - Applies all production pragmas
    - Creates all tables
    - Seeds default data
    - Yields the connection for testing
    - Closes connection after test completes
    
    Yields:
        sqlite3.Connection configured identically to production
    """
    # Create in-memory database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # Apply all production pragmas
    for pragma_name, pragma_value in DATABASE_PRAGMAS.items():
        conn.execute(f"PRAGMA {pragma_name} = {repr(pragma_value)}")
    
    # Create schema
    create_all_tables(conn)
    
    # Seed default data
    seed_default_data(conn)
    
    yield conn
    
    # Cleanup
    conn.close()


@pytest.fixture
def sample_category(db_connection: sqlite3.Connection) -> dict:
    """Create a sample category for testing."""
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO categories (name, code, description, tax_rate)
           VALUES (?, ?, ?, ?)""",
        ("Test Shirts", "TST", "Test category for shirts", 0.0)
    )
    db_connection.commit()
    
    return {
        "id": cursor.lastrowid,
        "name": "Test Shirts",
        "code": "TST",
        "description": "Test category for shirts",
        "tax_rate": 0.0,
    }


@pytest.fixture
def sample_style(db_connection: sqlite3.Connection, sample_category: dict) -> dict:
    """Create a sample style for testing."""
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO styles (style_code, name, category_id, base_sale_price, tax_rate, season)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("TST-SH-001", "Test Cotton Shirt", sample_category["id"], 220000, 0.0, "Summer")
    )
    db_connection.commit()
    
    return {
        "id": cursor.lastrowid,
        "style_code": "TST-SH-001",
        "name": "Test Cotton Shirt",
        "category_id": sample_category["id"],
        "base_sale_price": 220000,  # Rs. 2,200 in cents
        "tax_rate": 0.0,
        "season": "Summer",
    }


@pytest.fixture
def sample_variant(db_connection: sqlite3.Connection, sample_style: dict) -> dict:
    """Create a sample variant for testing."""
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO variants (style_id, size, color, barcode, quantity, reorder_point)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (sample_style["id"], "M", "Blue", "TST001-M-BLU", 10, 5)
    )
    db_connection.commit()
    
    return {
        "id": cursor.lastrowid,
        "style_id": sample_style["id"],
        "size": "M",
        "color": "Blue",
        "barcode": "TST001-M-BLU",
        "quantity": 10,
        "reorder_point": 5,
    }


@pytest.fixture
def sample_batch(db_connection: sqlite3.Connection, sample_variant: dict) -> dict:
    """Create a sample batch for testing."""
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO batches (variant_id, purchase_price, secret_code, 
                                quantity_received, quantity_remaining, date_received)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (sample_variant["id"], 100000, "KML", 10, 10, "2026-01-01")
    )
    db_connection.commit()
    
    return {
        "id": cursor.lastrowid,
        "variant_id": sample_variant["id"],
        "purchase_price": 100000,  # Rs. 1,000 in cents
        "secret_code": "KML",
        "quantity_received": 10,
        "quantity_remaining": 10,
        "date_received": "2026-01-01",
    }


@pytest.fixture
def sample_customer(db_connection: sqlite3.Connection) -> dict:
    """Create a sample customer for testing."""
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO customers (name, phone, email, credit_limit, total_due)
           VALUES (?, ?, ?, ?, ?)""",
        ("Test Customer", "0300-1234567", "test@example.com", 1000000, 0)
    )
    db_connection.commit()
    
    return {
        "id": cursor.lastrowid,
        "name": "Test Customer",
        "phone": "0300-1234567",
        "email": "test@example.com",
        "credit_limit": 1000000,  # Rs. 10,000
        "total_due": 0,
    }


@pytest.fixture
def sample_user(db_connection: sqlite3.Connection) -> dict:
    """Create a sample cashier user for testing."""
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO users (username, password_hash, full_name, role)
           VALUES (?, ?, ?, ?)""",
        ("cashier1", "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7cVNxmPdNu", 
         "Test Cashier", "cashier")
    )
    db_connection.commit()
    
    return {
        "id": cursor.lastrowid,
        "username": "cashier1",
        "full_name": "Test Cashier",
        "role": "cashier",
    }
