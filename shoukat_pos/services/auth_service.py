"""
Authentication Service for Shoukat POS.

Handles user login, password hashing, session management, and role-based access control.
Uses bcrypt for secure password storage with 12 rounds of hashing.
"""

import sqlite3
import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass, asdict
import bcrypt

from database.connection import ConnectionManager
from utils.validators import validate_text


@dataclass
class User:
    """User account data class."""
    id: int
    username: str
    password_hash: str  # Should not be accessed directly
    full_name: str
    role: str  # 'admin' or 'cashier'
    is_active: bool
    created_at: str
    last_login: Optional[str] = None
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary, excluding password hash by default."""
        data = {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data


@dataclass
class Session:
    """Active user session."""
    user_id: int
    username: str
    full_name: str
    role: str
    login_time: datetime
    expires_at: datetime
    token: str
    
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        return datetime.now() < self.expires_at
    
    def time_remaining(self) -> timedelta:
        """Get time remaining before session expires."""
        remaining = self.expires_at - datetime.now()
        return max(remaining, timedelta(0))


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AccountLockedError(AuthenticationError):
    """Raised when account is temporarily locked due to failed attempts."""
    pass


class SessionExpiredError(AuthenticationError):
    """Raised when session has expired."""
    pass


class AuthService:
    """
    Authentication service managing user login, sessions, and access control.
    
    Features:
    - Bcrypt password hashing with 12 rounds
    - Session management with 30-minute timeout
    - Account lockout after 5 failed attempts (15-minute lock)
    - Role-based access control (admin/cashier)
    - Secure token generation for session validation
    """
    
    # Configuration constants
    BCRYPT_ROUNDS = 12
    SESSION_TIMEOUT_MINUTES = 30
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    TOKEN_LENGTH = 32
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize authentication service.
        
        Args:
            connection_manager: Database connection manager instance
        """
        self.connection_manager = connection_manager
        self._active_sessions: Dict[str, Session] = {}
        self._failed_attempts: Dict[str, list] = {}  # username -> [timestamps]
    
    def _generate_token(self) -> str:
        """
        Generate a secure random session token.
        
        Returns:
            Hex-encoded random token string
        """
        return os.urandom(self.TOKEN_LENGTH).hex()
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with configured rounds.
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hash string
        """
        assert len(password) >= 6, "Password must be at least 6 characters"
        salt = bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Stored bcrypt hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    def _check_lockout(self, username: str) -> Tuple[bool, Optional[float]]:
        """
        Check if account is locked due to failed attempts.
        
        Args:
            username: Username to check
            
        Returns:
            Tuple of (is_locked, unlock_time_timestamp)
        """
        if username not in self._failed_attempts:
            return False, None
        
        # Clean old attempts (older than lockout window)
        current_time = time.time()
        cutoff_time = current_time - (self.LOCKOUT_DURATION_MINUTES * 60)
        self._failed_attempts[username] = [
            ts for ts in self._failed_attempts[username]
            if ts > cutoff_time
        ]
        
        # Check if locked
        if len(self._failed_attempts[username]) >= self.MAX_FAILED_ATTEMPTS:
            oldest_attempt = min(self._failed_attempts[username])
            unlock_time = oldest_attempt + (self.LOCKOUT_DURATION_MINUTES * 60)
            return True, unlock_time
        
        return False, None
    
    def _record_failed_attempt(self, username: str) -> None:
        """
        Record a failed login attempt.
        
        Args:
            username: Username that failed authentication
        """
        current_time = time.time()
        if username not in self._failed_attempts:
            self._failed_attempts[username] = []
        self._failed_attempts[username].append(current_time)
    
    def _clear_failed_attempts(self, username: str) -> None:
        """
        Clear failed attempt history after successful login.
        
        Args:
            username: Username to clear
        """
        if username in self._failed_attempts:
            del self._failed_attempts[username]
    
    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str = 'cashier',
        conn: Optional[sqlite3.Connection] = None
    ) -> User:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            full_name: User's full name
            role: User role ('admin' or 'cashier')
            conn: Optional existing database connection
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username already exists or validation fails
        """
        # Validate inputs
        is_valid, error_msg = validate_text(username, min_len=3, max_len=50, field_name="Username")
        if not is_valid:
            raise ValueError(error_msg)
        
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        if role not in ('admin', 'cashier'):
            raise ValueError("Role must be 'admin' or 'cashier'")
        
        # Hash password
        password_hash = self._hash_password(password)
        created_at = datetime.now().isoformat()
        
        # Close connection if we opened it
        close_conn = False
        if conn is None:
            conn = self.connection_manager.get_write_connection()
            close_conn = True
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, full_name, role, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (username, password_hash, full_name, role, created_at)
            )
            conn.commit()
            
            user_id = cursor.lastrowid
            return User(
                id=user_id,
                username=username,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
                is_active=True,
                created_at=created_at
            )
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                raise ValueError(f"Username '{username}' already exists")
            raise
        finally:
            if close_conn:
                conn.close()
    
    def get_user_by_username(
        self,
        username: str,
        conn: Optional[sqlite3.Connection] = None
    ) -> Optional[User]:
        """
        Retrieve user by username.
        
        Args:
            username: Username to look up
            conn: Optional existing database connection
            
        Returns:
            User object if found, None otherwise
        """
        close_conn = False
        if conn is None:
            conn = self.connection_manager.get_read_connection()
            close_conn = True
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, password_hash, full_name, role, is_active, 
                       created_at, last_login
                FROM users
                WHERE username = ?
                """,
                (username,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                full_name=row['full_name'],
                role=row['role'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                last_login=row['last_login']
            )
        finally:
            if close_conn:
                conn.close()
    
    def login(self, username: str, password: str) -> Session:
        """
        Authenticate user and create session.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Session object with user info and expiration
            
        Raises:
            AuthenticationError: If credentials are invalid
            AccountLockedError: If account is temporarily locked
        """
        # Check for lockout
        is_locked, unlock_time = self._check_lockout(username)
        if is_locked:
            unlock_datetime = datetime.fromtimestamp(unlock_time)
            wait_minutes = int((unlock_datetime - datetime.now()).total_seconds() / 60) + 1
            raise AccountLockedError(
                f"Account locked due to too many failed attempts. Try again in {wait_minutes} minutes."
            )
        
        # Get user from database
        user = self.get_user_by_username(username)
        
        if user is None:
            self._record_failed_attempt(username)
            raise AuthenticationError("Invalid username or password")
        
        if not user.is_active:
            raise AuthenticationError("Account is disabled. Contact administrator.")
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._record_failed_attempt(username)
            raise AuthenticationError("Invalid username or password")
        
        # Clear failed attempts on successful login
        self._clear_failed_attempts(username)
        
        # Update last login time
        now = datetime.now()
        now_str = now.isoformat()
        
        with self.connection_manager.execute_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (now_str, user.id)
            )
        
        # Create session
        token = self._generate_token()
        expires_at = now + timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        
        session = Session(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            login_time=now,
            expires_at=expires_at,
            token=token
        )
        
        # Store active session
        self._active_sessions[token] = session
        
        return session
    
    def logout(self, token: str) -> None:
        """
        End user session.
        
        Args:
            token: Session token to invalidate
        """
        if token in self._active_sessions:
            del self._active_sessions[token]
    
    def validate_session(self, token: str) -> Session:
        """
        Validate session token and return session if valid.
        
        Args:
            token: Session token to validate
            
        Returns:
            Session object if valid
            
        Raises:
            SessionExpiredError: If session has expired
            AuthenticationError: If token is invalid
        """
        if token not in self._active_sessions:
            raise AuthenticationError("Invalid session token")
        
        session = self._active_sessions[token]
        
        if not session.is_valid():
            # Remove expired session
            del self._active_sessions[token]
            raise SessionExpiredError("Session has expired. Please login again.")
        
        return session
    
    def extend_session(self, token: str) -> Session:
        """
        Extend session expiration time.
        
        Args:
            token: Session token to extend
            
        Returns:
            Updated Session object
            
        Raises:
            AuthenticationError: If token is invalid
        """
        session = self.validate_session(token)
        
        # Extend expiration
        session.expires_at = datetime.now() + timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        self._active_sessions[token] = session
        
        return session
    
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        token: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            token: Session token for authorization
            
        Returns:
            True if password changed successfully
            
        Raises:
            AuthenticationError: If old password is incorrect or session invalid
            ValueError: If new password doesn't meet requirements
        """
        # Validate session
        session = self.validate_session(token)
        
        # Verify session belongs to user
        if session.user_id != user_id:
            raise AuthenticationError("Cannot change password for another user")
        
        # Verify old password
        user = self.get_user_by_username(session.username)
        if user is None or not self._verify_password(old_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters")
        
        # Hash new password
        new_hash = self._hash_password(new_password)
        
        # Update database
        with self.connection_manager.execute_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user_id)
            )
        
        return True
    
    def has_permission(self, token: str, required_role: str) -> bool:
        """
        Check if session has required permission level.
        
        Args:
            token: Session token
            required_role: Minimum required role ('admin' or 'cashier')
            
        Returns:
            True if user has required permission
        """
        try:
            session = self.validate_session(token)
            
            # Admin has all permissions
            if session.role == 'admin':
                return True
            
            # Cashier can access cashier resources
            if required_role == 'cashier':
                return True
            
            # Cashier cannot access admin-only resources
            return False
        except AuthenticationError:
            return False
    
    def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from session token.
        
        Args:
            token: Session token
            
        Returns:
            User object if session valid, None otherwise
        """
        try:
            session = self.validate_session(token)
            return self.get_user_by_username(session.username)
        except AuthenticationError:
            return None
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from memory.
        
        Returns:
            Number of sessions removed
        """
        current_time = datetime.now()
        expired_tokens = [
            token for token, session in self._active_sessions.items()
            if session.expires_at < current_time
        ]
        
        for token in expired_tokens:
            del self._active_sessions[token]
        
        return len(expired_tokens)
    
    def get_active_session_count(self) -> int:
        """
        Get number of currently active sessions.
        
        Returns:
            Count of active sessions
        """
        # First cleanup expired
        self.cleanup_expired_sessions()
        return len(self._active_sessions)


# Global auth service instance (initialized by main app)
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """
    Get global auth service instance.
    
    Returns:
        AuthService instance
        
    Raises:
        RuntimeError: If service not initialized
    """
    if _auth_service is None:
        raise RuntimeError("AuthService not initialized. Call init_auth_service() first.")
    return _auth_service


def init_auth_service(connection_manager: ConnectionManager) -> AuthService:
    """
    Initialize global auth service.
    
    Args:
        connection_manager: Database connection manager
        
    Returns:
        Initialized AuthService instance
    """
    global _auth_service
    _auth_service = AuthService(connection_manager)
    return _auth_service