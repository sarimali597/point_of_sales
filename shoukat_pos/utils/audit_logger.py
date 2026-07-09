"""
Audit Logger for Tamper Detection

This module provides audit logging functionality to detect unauthorized
database modifications. All sensitive operations are logged with HMAC
verification to ensure log integrity.
"""

import sqlite3
import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Audit logger for tracking database changes and detecting tampering.
    
    This class logs all sensitive database operations with:
    - Timestamp
    - User ID
    - Table and record affected
    - Old and new values
    - HMAC hash for integrity verification
    
    The HMAC signature ensures that audit logs cannot be modified
    without detection.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize the audit logger.
        
        Args:
            secret_key: Secret key for HMAC signing. If None, uses a default.
                       In production, this should be stored securely.
        """
        self.secret_key = secret_key or "shoukat_pos_audit_secret_2026"
    
    def _generate_hmac(self, data: str) -> str:
        """
        Generate HMAC hash for audit log entry.
        
        Args:
            data: Data string to sign
            
        Returns:
            Hex-encoded HMAC-SHA256 hash
        """
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def log_action(
        self,
        conn: sqlite3.Connection,
        table_name: str,
        record_id: int,
        action: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> None:
        """
        Log an audit trail entry.
        
        Args:
            conn: Database connection
            table_name: Name of the affected table
            record_id: ID of the affected record
            action: Action type (INSERT, UPDATE, DELETE)
            old_values: Previous values (for UPDATE/DELETE)
            new_values: New values (for INSERT/UPDATE)
            user_id: ID of the user who performed the action
        """
        timestamp = datetime.now().isoformat()
        
        # Create data string for HMAC
        data_string = f"{table_name}:{record_id}:{action}:{timestamp}"
        if old_values:
            data_string += f":{json.dumps(old_values, sort_keys=True)}"
        if new_values:
            data_string += f":{json.dumps(new_values, sort_keys=True)}"
        
        hmac_hash = self._generate_hmac(data_string)
        
        # Insert audit log entry
        conn.execute(
            """INSERT INTO audit_log 
               (table_name, record_id, action, old_values, new_values, 
                user_id, timestamp, hmac_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                table_name,
                record_id,
                action,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                user_id,
                timestamp,
                hmac_hash
            )
        )
        
        logger.debug(
            f"Audit log: {action} on {table_name}:{record_id} by user {user_id}"
        )
    
    def verify_log_integrity(
        self,
        conn: sqlite3.Connection,
        log_id: int
    ) -> bool:
        """
        Verify integrity of an audit log entry.
        
        Args:
            conn: Database connection
            log_id: Audit log entry ID
            
        Returns:
            True if HMAC matches, False if tampering detected
        """
        cursor = conn.execute(
            """SELECT table_name, record_id, action, old_values, 
                      new_values, timestamp, hmac_hash
               FROM audit_log WHERE id = ?""",
            (log_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return False
        
        # Reconstruct data string
        data_string = f"{row['table_name']}:{row['record_id']}:{row['action']}:{row['timestamp']}"
        
        if row["old_values"]:
            data_string += f":{row['old_values']}"
        if row["new_values"]:
            data_string += f":{row['new_values']}"
        
        # Verify HMAC
        expected_hash = self._generate_hmac(data_string)
        
        return hmac.compare_digest(row["hmac_hash"], expected_hash)
    
    def verify_all_logs(
        self,
        conn: sqlite3.Connection
    ) -> tuple[int, int]:
        """
        Verify integrity of all audit log entries.
        
        Args:
            conn: Database connection
            
        Returns:
            Tuple of (valid_count, invalid_count)
        """
        cursor = conn.execute("SELECT id FROM audit_log ORDER BY id")
        log_ids = [row["id"] for row in cursor.fetchall()]
        
        valid = 0
        invalid = 0
        
        for log_id in log_ids:
            if self.verify_log_integrity(conn, log_id):
                valid += 1
            else:
                invalid += 1
                logger.error(f"Audit log entry {log_id} failed integrity check!")
        
        return valid, invalid