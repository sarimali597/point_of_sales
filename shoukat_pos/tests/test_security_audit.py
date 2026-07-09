"""
Test Suite for Security & Audit Features

This module tests the security and audit functionality including:
- Password hashing with bcrypt
- Account lockout after failed attempts
- Session management and timeout
- Audit log triggers for automatic logging
- Audit log integrity verification with HMAC
- Tamper detection
"""

import pytest
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Optional

from database.connection import ConnectionManager
from database.schema import create_all_tables, CREATE_AUDIT_TRIGGERS
from services.auth_service import AuthService, AuthenticationError, AccountLockedError
from utils.audit_logger import AuditLogger


class TestPasswordHashing:
    """Test bcrypt password hashing functionality."""
    
    def test_password_hash_is_not_plaintext(self):
        """Verify passwords are hashed, not stored in plaintext."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        password = "testpassword123"
        hashed = auth._hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$12$")  # bcrypt format with 12 rounds
        assert len(hashed) == 60  # Standard bcrypt hash length
    
    def test_same_password_different_hashes(self):
        """Verify bcrypt produces different hashes for same password (salt)."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        password = "samepassword"
        hash1 = auth._hash_password(password)
        hash2 = auth._hash_password(password)
        
        assert hash1 != hash2  # Different salts
        assert auth._verify_password(password, hash1)
        assert auth._verify_password(password, hash2)
    
    def test_password_verification_correct(self):
        """Test that correct passwords verify successfully."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        password = "correctpassword"
        hashed = auth._hash_password(password)
        
        assert auth._verify_password(password, hashed) is True
    
    def test_password_verification_incorrect(self):
        """Test that incorrect passwords fail verification."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = auth._hash_password(password)
        
        assert auth._verify_password(wrong_password, hashed) is False


class TestAccountLockout:
    """Test account lockout after failed login attempts."""
    
    def test_account_locks_after_max_failed_attempts(self):
        """Verify account locks after 5 failed attempts."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        # Create a test user
        conn = cm.get_write_connection()
        auth.create_user(
            username="locktest",
            password="testpass123",
            full_name="Lock Test User",
            role="cashier",
            conn=conn
        )
        conn.close()
        
        # Simulate 5 failed attempts
        for i in range(5):
            with pytest.raises(AuthenticationError):
                auth.login("locktest", "wrongpassword")
        
        # 6th attempt should raise AccountLockedError
        with pytest.raises(AccountLockedError):
            auth.login("locktest", "testpass123")
    
    def test_successful_login_clears_failed_attempts(self):
        """Verify successful login resets failed attempt counter."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        # Create a test user
        conn = cm.get_write_connection()
        auth.create_user(
            username="cleartest",
            password="testpass123",
            full_name="Clear Test User",
            role="cashier",
            conn=conn
        )
        conn.close()
        
        # 3 failed attempts
        for i in range(3):
            with pytest.raises(AuthenticationError):
                auth.login("cleartest", "wrongpassword")
        
        # Successful login
        session = auth.login("cleartest", "testpass123")
        assert session is not None
        
        # Should still be able to login (attempts cleared)
        auth.logout(session.token)
        session2 = auth.login("cleartest", "testpass123")
        assert session2 is not None


class TestSessionManagement:
    """Test session creation, validation, and expiration."""
    
    def test_session_created_on_login(self):
        """Verify session is created with correct properties on login."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        # Create a test user
        conn = cm.get_write_connection()
        auth.create_user(
            username="sessiontest",
            password="testpass123",
            full_name="Session Test User",
            role="admin",
            conn=conn
        )
        conn.close()
        
        # Login
        session = auth.login("sessiontest", "testpass123")
        
        assert session.username == "sessiontest"
        assert session.full_name == "Session Test User"
        assert session.role == "admin"
        assert session.token is not None
        assert len(session.token) == 64  # 32 bytes hex = 64 chars
        assert session.expires_at > datetime.now()
    
    def test_session_validation(self):
        """Test session validation returns session if valid."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        # Create and login
        conn = cm.get_write_connection()
        auth.create_user(
            username="validatetest",
            password="testpass123",
            full_name="Validate Test",
            role="cashier",
            conn=conn
        )
        conn.close()
        
        session = auth.login("validatetest", "testpass123")
        
        # Validate should return same session
        validated = auth.validate_session(session.token)
        assert validated.user_id == session.user_id
        assert validated.token == session.token
    
    def test_invalid_token_raises_error(self):
        """Test that invalid token raises AuthenticationError."""
        cm = ConnectionManager()
        auth = AuthService(cm)
        
        with pytest.raises(AuthenticationError):
            auth.validate_session("invalid_token_12345")


class TestAuditTriggers:
    """Test automatic audit logging via database triggers."""
    
    @pytest.fixture
    def db_with_triggers(self):
        """Create in-memory database with audit triggers."""
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        create_all_tables(conn)
        conn.executescript(CREATE_AUDIT_TRIGGERS)
        conn.commit()
        
        # Insert test data
        conn.execute('''INSERT INTO styles (style_code, name, category_id, base_sale_price)
                        VALUES ('TEST-001', 'Test Shirt', 1, 220000)''')
        conn.commit()
        
        yield conn
        conn.close()
    
    def test_variant_insert_triggers_audit_log(self, db_with_triggers):
        """Verify INSERT on variants creates audit log entry."""
        conn = db_with_triggers
        
        # Insert variant
        conn.execute('''INSERT INTO variants (style_id, size, color, barcode, quantity)
                        VALUES (1, 'M', 'Blue', 'TEST-BC-001', 10)''')
        conn.commit()
        
        # Check audit log
        cursor = conn.execute('SELECT * FROM audit_log WHERE table_name = "variants" AND action = "INSERT"')
        row = cursor.fetchone()
        
        assert row is not None
        assert row['record_id'] == 1
        assert row['action'] == 'INSERT'
        assert row['old_values'] is None
        assert row['new_values'] is not None
        assert 'quantity' in row['new_values']
    
    def test_variant_update_triggers_audit_log(self, db_with_triggers):
        """Verify UPDATE on variants creates audit log entry."""
        conn = db_with_triggers
        
        # Insert then update
        conn.execute('''INSERT INTO variants (style_id, size, color, barcode, quantity)
                        VALUES (1, 'L', 'Black', 'TEST-BC-002', 5)''')
        conn.execute('UPDATE variants SET quantity = 8 WHERE barcode = "TEST-BC-002"')
        conn.commit()
        
        # Check audit log for UPDATE
        cursor = conn.execute('SELECT * FROM audit_log WHERE table_name = "variants" AND action = "UPDATE"')
        row = cursor.fetchone()
        
        assert row is not None
        assert 'OLD' in row['old_values'] or 'quantity' in row['old_values']
        assert 'NEW' in row['new_values'] or 'quantity' in row['new_values']
    
    def test_sales_insert_triggers_audit_log(self, db_with_triggers):
        """Verify INSERT on sales creates audit log entry."""
        conn = db_with_triggers
        
        # Create customer first
        conn.execute('''INSERT INTO customers (name, phone)
                        VALUES ('Test Customer', '0300-1234567')''')
        
        # Insert sale (all required fields)
        conn.execute('''INSERT INTO sales (invoice_number, subtotal, tax_amount, discount_amount, 
                                          grand_total, payment_type, paid_amount, due_amount, user_id)
                        VALUES ('INV-TEST-001', 500000, 0, 0, 500000, 'cash', 500000, 0, 1)''')
        conn.commit()
        
        # Check audit log
        cursor = conn.execute('SELECT * FROM audit_log WHERE table_name = "sales" AND action = "INSERT"')
        row = cursor.fetchone()
        
        assert row is not None
        assert row['action'] == 'INSERT'
        assert 'invoice_number' in row['new_values']
    
    def test_customer_credit_update_triggers_audit_log(self, db_with_triggers):
        """Verify UPDATE on customer credit creates audit log entry."""
        conn = db_with_triggers
        
        # Insert customer
        conn.execute('''INSERT INTO customers (name, phone, total_due)
                        VALUES ('Credit Customer', '0300-7654321', 100000)''')
        
        # Update credit
        conn.execute('UPDATE customers SET total_due = 150000 WHERE phone = "0300-7654321"')
        conn.commit()
        
        # Check audit log
        cursor = conn.execute('SELECT * FROM audit_log WHERE table_name = "customers" AND action = "UPDATE"')
        row = cursor.fetchone()
        
        assert row is not None
        assert 'total_due' in row['old_values']
        assert 'total_due' in row['new_values']


class TestAuditIntegrity:
    """Test audit log integrity verification with HMAC."""
    
    def test_audit_logger_creates_valid_hmac(self):
        """Verify AuditLogger creates valid HMAC for logged actions."""
        logger = AuditLogger(secret_key="test_secret_key_2026")
        
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        create_all_tables(conn)
        conn.commit()
        
        # Log an action through the logger (not trigger)
        logger.log_action(
            conn=conn,
            table_name='variants',
            record_id=1,
            action='UPDATE',
            old_values={'quantity': 10},
            new_values={'quantity': 8},
            user_id=1
        )
        conn.commit()
        
        # Verify the log entry
        cursor = conn.execute('SELECT * FROM audit_log LIMIT 1')
        row = cursor.fetchone()
        
        assert row is not None
        assert row['hmac_hash'] is not None
        assert len(row['hmac_hash']) == 64  # SHA256 hex length
        
        # Verify integrity
        is_valid = logger.verify_log_integrity(conn, row['id'])
        assert is_valid is True
    
    def test_tampered_audit_log_fails_verification(self):
        """Verify that modified audit log entries fail integrity check."""
        logger = AuditLogger(secret_key="test_secret_key_2026")
        
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        create_all_tables(conn)
        conn.commit()
        
        # Log an action
        logger.log_action(
            conn=conn,
            table_name='sales',
            record_id=1,
            action='INSERT',
            new_values={'invoice_number': 'INV-001'},
            user_id=1
        )
        conn.commit()
        
        # Get the log ID
        cursor = conn.execute('SELECT id FROM audit_log LIMIT 1')
        log_id = cursor.fetchone()['id']
        
        # Tamper with the record
        conn.execute('UPDATE audit_log SET new_values = ? WHERE id = ?',
                    ('{"invoice_number": "INV-TAMPERED"}', log_id))
        conn.commit()
        
        # Verification should fail
        is_valid = logger.verify_log_integrity(conn, log_id)
        assert is_valid is False
    
    def test_verify_all_logs_returns_counts(self):
        """Test verify_all_logs returns valid and invalid counts."""
        logger = AuditLogger(secret_key="test_secret_key_2026")
        
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        create_all_tables(conn)
        conn.commit()
        
        # Log multiple actions
        for i in range(5):
            logger.log_action(
                conn=conn,
                table_name='variants',
                record_id=i,
                action='UPDATE',
                new_values={'quantity': i * 10},
                user_id=1
            )
        conn.commit()
        
        # Verify all
        valid_count, invalid_count = logger.verify_all_logs(conn)
        
        assert valid_count == 5
        assert invalid_count == 0


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def test_admin_has_full_permissions(self):
        """Verify admin role has all permissions."""
        from config import UserRole, ROLE_PERMISSIONS
        
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        
        assert 'products:create' in admin_perms
        assert 'products:edit' in admin_perms
        assert 'products:delete' in admin_perms
        assert 'sales:view' in admin_perms
        assert 'sales:create' in admin_perms
        assert 'settings:edit' in admin_perms
        assert 'backup:restore' in admin_perms
    
    def test_cashier_has_limited_permissions(self):
        """Verify cashier role has restricted permissions."""
        from config import UserRole, ROLE_PERMISSIONS
        
        cashier_perms = ROLE_PERMISSIONS[UserRole.CASHIER]
        
        assert 'sales:create' in cashier_perms
        assert 'sales:view' in cashier_perms
        assert 'returns:create' in cashier_perms
        assert 'products:edit' not in cashier_perms
        assert 'settings:edit' not in cashier_perms
        assert 'backup:restore' not in cashier_perms


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
