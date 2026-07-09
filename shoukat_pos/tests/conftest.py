"""
Pytest configuration and fixtures for Shoukat POS tests.

This module provides shared fixtures for all tests, including:
- Fresh in-memory database for each test
- Sample data generators
- Test utilities
- File-based database for integration tests
"""

import pytest
import sqlite3
import sys
from pathlib import Path
from typing import Generator, Dict, Any
from datetime import datetime
import bcrypt

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DATABASE_PRAGMAS
from database.schema import create_all_tables, seed_default_data
from database.connection import ConnectionManager


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


@pytest.fixture(scope='session')
def test_db_path(tmp_path_factory) -> str:
    """Create a temporary database file for integration tests."""
    temp_dir = tmp_path_factory.mktemp("data")
    db_path = temp_dir / "test_pos.db"
    yield str(db_path)
    # Cleanup after all tests
    if db_path.exists():
        db_path.unlink()
    wal_file = Path(str(db_path) + "-wal")
    shm_file = Path(str(db_path) + "-shm")
    if wal_file.exists():
        wal_file.unlink()
    if shm_file.exists():
        shm_file.unlink()


@pytest.fixture
def connection_manager(test_db_path: str) -> Generator[ConnectionManager, None, None]:
    """Create a ConnectionManager instance with a temporary database.
    
    This fixture is for integration tests that need to test the
    ConnectionManager itself or require file-based database features.
    """
    # Remove existing test db if present
    for ext in ['', '-wal', '-shm']:
        p = Path(test_db_path + ext)
        if p.exists():
            p.unlink()
    
    manager = ConnectionManager(test_db_path)
    manager.initialize_database()
    
    yield manager
    
    # Cleanup
    manager.close_all()
    for ext in ['', '-wal', '-shm']:
        p = Path(test_db_path + ext)
        if p.exists():
            p.unlink()


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
def sample_credit_customer(db_connection: sqlite3.Connection) -> dict:
    """Create a sample customer with existing credit balance."""
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO customers (name, phone, email, credit_limit, total_due)
           VALUES (?, ?, ?, ?, ?)""",
        ("Fatima Khan", "03017654321", "fatima@example.com", 10000000, 3500000)
    )
    db_connection.commit()
    
    return {
        "id": cursor.lastrowid,
        "name": "Fatima Khan",
        "phone": "03017654321",
        "email": "fatima@example.com",
        "credit_limit": 10000000,  # Rs. 100,000
        "total_due": 3500000,  # Already owes Rs. 35,000
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


@pytest.fixture
def sample_admin_user(db_connection: sqlite3.Connection) -> Dict[str, Any]:
    """Create a sample admin user for testing.
    
    Returns user data dict with plaintext password for test assertions.
    The user is inserted into the database with hashed password.
    """
    password = 'TestAdmin123!'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    user_data = {
        'username': 'admin_test',
        'password_hash': password_hash,
        'role': 'admin',
        'full_name': 'Test Administrator',
        'created_at': datetime.now().isoformat(),
        'plaintext_password': password,
    }
    
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO users (username, password_hash, role, full_name, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_data['username'], user_data['password_hash'], user_data['role'],
         user_data['full_name'], user_data['created_at'])
    )
    db_connection.commit()
    
    user_data['id'] = cursor.lastrowid
    return user_data


@pytest.fixture
def sample_cashier_user(db_connection: sqlite3.Connection) -> Dict[str, Any]:
    """Create a sample cashier user for testing."""
    password = 'Cashier123!'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    user_data = {
        'username': 'cashier_test',
        'password_hash': password_hash,
        'role': 'cashier',
        'full_name': 'Test Cashier',
        'created_at': datetime.now().isoformat(),
        'plaintext_password': password,
    }
    
    cursor = db_connection.cursor()
    cursor.execute(
        """INSERT INTO users (username, password_hash, role, full_name, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_data['username'], user_data['password_hash'], user_data['role'],
         user_data['full_name'], user_data['created_at'])
    )
    db_connection.commit()
    
    user_data['id'] = cursor.lastrowid
    return user_data


@pytest.fixture
def sample_variants(db_connection: sqlite3.Connection, sample_style: dict) -> list:
    """Create sample variants for a style (size-color matrix)."""
    variants_data = []
    
    test_variants = [
        ('S', 'Blue', 'SSG-SH-001-S-BLU', 15),
        ('M', 'Blue', 'SSG-SH-001-M-BLU', 20),
        ('L', 'Blue', 'SSG-SH-001-L-BLU', 25),
        ('XL', 'Blue', 'SSG-SH-001-XL-BLU', 10),
        ('M', 'Black', 'SSG-SH-001-M-BLK', 18),
        ('L', 'Black', 'SSG-SH-001-L-BLK', 22),
    ]
    
    cursor = db_connection.cursor()
    for size, color, barcode, qty in test_variants:
        cursor.execute(
            """INSERT INTO variants (style_id, size, color, barcode, quantity, reorder_point)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_style["id"], size, color, barcode, qty, 5)
        )
        
        variant = {
            "id": cursor.lastrowid,
            "style_id": sample_style["id"],
            "size": size,
            "color": color,
            "barcode": barcode,
            "quantity": qty,
            "reorder_point": 5,
        }
        variants_data.append(variant)
    
    db_connection.commit()
    return variants_data


@pytest.fixture
def mock_current_time(monkeypatch) -> Generator:
    """Mock datetime.now() for deterministic testing.
    
    Usage:
        def test_something(mock_current_time):
            mock_current_time.return_value = datetime(2026, 1, 1, 12, 0, 0)
            # Code using datetime.now() will return mocked time
    """
    fixed_time = datetime(2026, 1, 15, 10, 30, 0)
    
    class MockDateTime:
        @classmethod
        def now(cls):
            return fixed_time
        
        @classmethod
        def today(cls):
            return fixed_time.date()
    
    monkeypatch.setattr('datetime.datetime', MockDateTime)
    yield lambda: fixed_time


@pytest.fixture
def auth_headers(sample_admin_user: Dict) -> Dict[str, str]:
    """Create authorization headers for API-like testing."""
    # For future REST API extension
    return {
        'X-Username': sample_admin_user['username'],
        'X-Role': sample_admin_user['role'],
    }
