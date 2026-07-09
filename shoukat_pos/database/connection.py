"""
Database Connection Manager with WAL Mode and Write Serialization

This module implements a singleton connection manager that:
1. Creates the database directory with secure permissions on first run
2. Applies all production pragmas for optimal performance
3. Provides separate read and write connections
4. Serializes all write operations using a threading lock
5. Implements atomic transaction context managers with rollback support
"""
import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional, Generator, Any
from contextlib import contextmanager

from config import (
    DATABASE_PATH,
    DATA_DIR,
    DIR_PERMISSIONS,
    FILE_PERMISSIONS,
    DATABASE_PRAGMAS,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Singleton database connection manager with WAL mode and write serialization.
    
    This class ensures thread-safe access to SQLite by maintaining a single
    write connection while allowing multiple concurrent read connections.
    All write operations are serialized through a threading lock to prevent
    "database is locked" errors during peak usage.
    
    Usage:
        manager = ConnectionManager.get_instance()
        manager.initialize_database()
        
        # Read operation
        with manager.get_read_connection() as conn:
            cursor = conn.execute("SELECT * FROM products")
            
        # Write operation with automatic serialization
        with manager.get_write_connection() as conn:
            conn.execute("INSERT INTO products (...) VALUES (...)")
            
        # Atomic transaction (all or nothing)
        with manager.execute_transaction() as conn:
            inventory_service.deduct_stock(conn, variant_id, qty)
            sale_engine.create_sale(conn, sale_data)
            # All committed atomically, or all rolled back on error
    """
    
    _instance: Optional["ConnectionManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "ConnectionManager":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the connection manager (called once due to singleton)."""
        if self._initialized:
            return
        
        self.db_path = DATABASE_PATH
        self.data_dir = DATA_DIR
        self._write_lock = threading.Lock()
        self._write_conn: Optional[sqlite3.Connection] = None
        self._initialized = True
        
        logger.info(f"ConnectionManager initialized for database: {self.db_path}")
    
    @classmethod
    def get_instance(cls) -> "ConnectionManager":
        """Get the singleton instance of the connection manager."""
        return cls()
    
    def _ensure_directories(self) -> None:
        """Create data directory with secure permissions if it doesn't exist."""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, mode=DIR_PERMISSIONS)
            logger.info(f"Created data directory: {self.data_dir}")
        
        # Set directory permissions even if it exists (in case they were changed)
        self.data_dir.chmod(DIR_PERMISSIONS)
        
        # Ensure backup directory exists
        backup_dir = self.data_dir / "backups"
        if not backup_dir.exists():
            backup_dir.mkdir(mode=DIR_PERMISSIONS)
    
    def _apply_pragmas(self, conn: sqlite3.Connection) -> None:
        """
        Apply production-ready SQLite pragmas for optimal performance.
        
        These settings transform SQLite from a development database into
        a production-capable storage engine for retail POS systems.
        """
        for pragma_name, pragma_value in DATABASE_PRAGMAS.items():
            try:
                conn.execute(f"PRAGMA {pragma_name} = {repr(pragma_value)}")
            except sqlite3.Error as e:
                logger.warning(f"Failed to set PRAGMA {pragma_name}: {e}")
        
        # Verify critical pragmas
        result = conn.execute("PRAGMA journal_mode").fetchone()
        if result[0] != "wal":
            logger.error("WAL mode not enabled - data integrity at risk!")
        
        logger.debug("Applied production SQLite pragmas")
    
    def _create_connection(self, readonly: bool = False) -> sqlite3.Connection:
        """
        Create a new database connection with all pragmas applied.
        
        Args:
            readonly: If True, open connection in read-only mode
            
        Returns:
            Configured sqlite3.Connection object
        """
        uri = f"file:{self.db_path}?mode=ro" if readonly else f"file:{self.db_path}"
        conn = sqlite3.connect(uri, uri=True, timeout=DATABASE_PRAGMAS["busy_timeout"])
        conn.row_factory = sqlite3.Row  # Dict-like row access
        self._apply_pragmas(conn)
        return conn
    
    def initialize_database(self) -> None:
        """
        Initialize the database: create directories, apply schema, seed data.
        
        This method should be called once on application startup. It ensures
        the database file exists with proper permissions and all tables are
        created according to the current schema.
        """
        self._ensure_directories()
        
        # Import schema here to avoid circular imports
        from database import schema
        
        # Create connection and apply schema
        conn = self._create_connection()
        try:
            schema.create_all_tables(conn)
            schema.seed_default_data(conn)
            logger.info("Database initialized successfully")
        finally:
            conn.close()
    
    def get_read_connection(self) -> sqlite3.Connection:
        """
        Get a read-only connection for SELECT queries.
        
        Multiple read connections can operate concurrently without blocking.
        The caller is responsible for closing the connection.
        
        Returns:
            sqlite3.Connection configured for read-only operations
        """
        return self._create_connection(readonly=True)
    
    @contextmanager
    def get_write_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a write connection with automatic serialization.
        
        This context manager ensures only one write operation executes at a time
        by acquiring a threading lock. The connection is automatically returned
        to the pool when the context exits.
        
        Usage:
            with manager.get_write_connection() as conn:
                conn.execute("UPDATE products SET quantity = ? WHERE id = ?", (qty, pid))
        
        Yields:
            sqlite3.Connection for write operations
        """
        with self._write_lock:
            if self._write_conn is None:
                self._write_conn = self._create_connection()
            yield self._write_conn
    
    @contextmanager
    def execute_transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Execute an atomic transaction with automatic commit/rollback.
        
        This is the recommended way to perform multi-step database operations
        that must succeed or fail together (ACID guarantee).
        
        Usage:
            with manager.execute_transaction() as conn:
                # Step 1: Deduct stock
                inventory_service.deduct_stock(conn, variant_id, qty)
                
                # Step 2: Create sale record
                sale_id = sale_engine.create_sale(conn, sale_data)
                
                # Step 3: Update customer credit
                if sale_data['is_credit']:
                    customer_service.add_due(conn, customer_id, due_amount)
                
                # All steps committed atomically, or all rolled back on error
        
        Raises:
            Exception: Re-raises any exception after rolling back the transaction
        
        Yields:
            sqlite3.Connection within an active transaction
        """
        conn = None
        try:
            with self.get_write_connection() as conn:
                # BEGIN IMMEDIATE acquires write lock immediately to prevent deadlocks
                conn.execute("BEGIN IMMEDIATE")
                yield conn
                conn.execute("COMMIT")
                logger.debug("Transaction committed successfully")
        except Exception as e:
            if conn is not None:
                try:
                    conn.execute("ROLLBACK")
                    logger.warning("Transaction rolled back due to error")
                except sqlite3.Error as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
            logger.error(f"Transaction failed: {e}")
            raise
    
    def integrity_check(self) -> tuple[bool, str]:
        """
        Run SQLite integrity check to detect database corruption.
        
        Returns:
            Tuple of (is_healthy, message) where is_healthy is True if no issues found
        """
        try:
            conn = self._create_connection(readonly=True)
            try:
                result = conn.execute("PRAGMA integrity_check").fetchone()
                is_healthy = result[0] == "ok"
                message = "Database integrity check passed" if is_healthy else f"Integrity issues: {result[0]}"
                return is_healthy, message
            finally:
                conn.close()
        except sqlite3.Error as e:
            return False, f"Integrity check failed: {e}"
    
    def get_database_size(self) -> int:
        """
        Get the current size of the database file in bytes.
        
        Returns:
            File size in bytes, or 0 if database doesn't exist
        """
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0
    
    def close_all(self) -> None:
        """
        Close all connections and release resources.
        
        Call this method during application shutdown to ensure all data
        is flushed to disk and connections are properly released.
        """
        if self._write_conn is not None:
            self._write_conn.close()
            self._write_conn = None
            logger.info("Write connection closed")
        
        logger.info("All database connections closed")


# Convenience function for getting the singleton instance
def get_connection_manager() -> ConnectionManager:
    """Get the singleton ConnectionManager instance."""
    return ConnectionManager.get_instance()
