"""
Shoukat Sons Garments POS - Configuration Constants

This module contains all application constants, default settings, and path configurations.
"""
from pathlib import Path
from typing import Dict, List, Tuple
from enum import Enum


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
ASSETS_DIR = BASE_DIR / "assets"
DATABASE_PATH = DATA_DIR / "shoukat_pos.db"
LOG_FILE = DATA_DIR / "pos.log"

# Directory permissions (owner-only access)
DIR_PERMISSIONS = 0o700
FILE_PERMISSIONS = 0o600


# =============================================================================
# COLOR PALETTE
# =============================================================================

class Colors:
    """Primary color palette for the POS system."""
    
    # Primary colors
    PRIMARY = "#1A237E"       # Deep blue
    SECONDARY = "#0D47A1"     # Dark blue
    ACCENT = "#00BCD4"        # Cyan
    
    # Semantic colors
    SUCCESS = "#2E7D32"       # Green
    WARNING = "#F57C00"       # Orange
    DANGER = "#C62828"        # Red
    INFO = "#1976D2"          # Light blue
    
    # Neutral colors
    BACKGROUND = "#F5F5F5"    # Light gray
    CARD = "#FFFFFF"          # White
    TEXT_PRIMARY = "#263238"  # Dark gray
    TEXT_SECONDARY = "#546E7A"  # Medium gray
    BORDER = "#CFD8DC"        # Light border
    
    # Status colors
    LOW_STOCK = "#FF9800"     # Orange for low stock
    OUT_OF_STOCK = "#F44336"  # Red for out of stock
    IN_STOCK = "#4CAF50"      # Green for in stock


# =============================================================================
# RESPONSIVE BREAKPOINTS
# =============================================================================

class Breakpoints:
    """Screen width breakpoints for responsive design."""
    COMPACT = 1024    # < 1024: single column, collapsible sidebar
    STANDARD = 1440   # 1024-1440: two columns, visible sidebar
    WIDE = 1920       # > 1440: three columns, expanded tables


# =============================================================================
# DATABASE PRAGMAS (Production Configuration)
# =============================================================================

DATABASE_PRAGMAS = {
    "journal_mode": "WAL",           # Write-Ahead Logging for concurrent reads
    "synchronous": "NORMAL",         # 3x faster than FULL, safe with WAL
    "busy_timeout": 30000,           # 30 seconds to handle peak contention
    "cache_size": -64000,            # 64MB cache for frequent lookups
    "mmap_size": 268435456,          # 256MB memory-mapped I/O
    "foreign_keys": "ON",            # Enforce foreign key constraints
    "temp_store": "MEMORY",          # Keep temp tables in RAM
    "secure_delete": "ON",           # Overwrite deleted sensitive data
    "wal_autocheckpoint": 1000,      # Checkpoint every 1000 pages
}


# =============================================================================
# DEFAULT SETTINGS
# =============================================================================

DEFAULT_SHOP_NAME = "SHOUKAT SONS GARMENTS"
DEFAULT_TAX_RATE = 0.0               # 0% tax by default (configurable)
DEFAULT_CURRENCY = "Rs."
DEFAULT_LANGUAGE = "en"

# Sticker sizes (width x height in mm)
STICKER_SIZES: Dict[str, Tuple[int, int]] = {
    "28x19": (28, 19),
    "32x25": (32, 25),
    "32x19": (32, 19),
    "34x24": (34, 24),
}

DEFAULT_STICKER_SIZE = "28x19"
DEFAULT_GAP_MM = 2

# Receipt configuration
RECEIPT_WIDTHS = {
    "58mm": 58,
    "80mm": 80,
}
DEFAULT_RECEIPT_WIDTH = "80mm"

# Printer DPI (BlackCopper BC-LP-1300)
PRINTER_DPI = 203
PRINTER_DPMM = 8  # Dots per mm at 203 DPI


# =============================================================================
# SIZE & COLOR OPTIONS
# =============================================================================

SIZE_OPTIONS: List[str] = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]
COLOR_OPTIONS: List[str] = ["Black", "White", "Blue", "Red", "Green", 
                            "Navy", "Grey", "Brown", "Pink", "Yellow", 
                            "Orange", "Purple", "Beige", "Maroon"]

# Default reorder point for inventory alerts
DEFAULT_REORDER_POINT = 5

# Stock level thresholds for color coding
STOCK_THRESHOLD_LOW = 5
STOCK_THRESHOLD_MEDIUM = 10


# =============================================================================
# SECRET CODE DEFAULT MAPPING
# =============================================================================

DEFAULT_SECRET_CODE_MAP: Dict[str, str] = {
    "0": "L",
    "1": "R",
    "2": "K",
    "3": "B",
    "4": "S",
    "5": "M",
    "6": "N",
    "7": "T",
    "8": "H",
    "9": "W",
}


# =============================================================================
# SEASON OPTIONS
# =============================================================================

SEASON_OPTIONS: List[str] = ["Summer", "Winter", "Festive", "Spring", "Fall", "All Season"]


# =============================================================================
# CATEGORY OPTIONS
# =============================================================================

DEFAULT_CATEGORIES: List[str] = [
    "Shirts",
    "Pants",
    "T-Shirts",
    "Jeans",
    "Kurta",
    "Waistcoat",
    "Blazer",
    "Ties",
    "Accessories",
]


# =============================================================================
# USER ROLES
# =============================================================================

class UserRole(Enum):
    ADMIN = "admin"
    CASHIER = "cashier"


ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    UserRole.ADMIN: [
        "products:create", "products:edit", "products:delete",
        "sales:view", "sales:create", "sales:void",
        "customers:view", "customers:edit",
        "reports:view", "reports:export",
        "settings:view", "settings:edit",
        "backup:create", "backup:restore",
    ],
    UserRole.CASHIER: [
        "sales:view", "sales:create",
        "customers:view",
        "returns:create",
        "reports:view",
    ],
}


# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


# =============================================================================
# BACKUP CONFIGURATION
# =============================================================================

DEFAULT_BACKUP_RETENTION = 30
DEFAULT_BACKUP_FREQUENCY = "daily"
DEFAULT_BACKUP_TIME = "02:00"  # 2 AM
BACKUP_ENCRYPTION_ENABLED = True


# =============================================================================
# APPLICATION METADATA
# =============================================================================

APP_NAME = "Shoukat POS"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Shoukat Sons Garments"
COPYRIGHT_YEAR = 2026
