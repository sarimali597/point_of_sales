# Shoukat Sons Garments POS

A modern, production-ready Python-based Point of Sale (POS) system designed specifically for garment retail stores. Built 
with CustomTkinter for a beautiful, responsive UI and SQLite with WAL mode for reliable data storage.

## Features

### Core POS Functionality
- **Sales Processing**: Fast barcode scanning, cart management, multiple payment types (cash, credit, split)
- **Inventory Management**: Style-variant-batch architecture for size/color matrix tracking
- **Customer Management**: Credit tracking, purchase history, loyalty points
- **Returns & Exchanges**: Full support for garment-specific variant swaps
- **Held Sales**: Pause and resume transactions

### Hardware Integration
- **Label Printing**: Native TSPL command support for BlackCopper BC-LP-1300 (203 DPI)
- **Receipt Printing**: ESC/POS protocol for 80mm thermal receipt printers
- **Barcode Scanning**: USB HID keyboard-wedge scanner support

### Security & Reliability
- **ACID Transactions**: Atomic sale processing with automatic rollback on errors
- **Audit Logging**: Tamper-evident audit trail with HMAC chain verification
- **Encrypted Backups**: SQLCipher-compatible encrypted backups with PBKDF2 key derivation
- **Role-Based Access**: Admin and Cashier roles with granular permissions

### Modern UI/UX
- **CustomTkinter**: Beautiful, modern interface with dark/light themes
- **Responsive Design**: Adapts to different screen sizes (tablet to desktop)
- **Animations**: Smooth transitions, toast notifications, loading indicators
- **Variant Grid View**: Size-color matrix display for quick product selection

## Project Structure

```
shoukat_pos/
├── main.py                          # Application entry point
├── config.py                        # Constants, paths, default settings
├── requirements.txt                 # Python dependencies
│
├── database/
│   ├── connection.py                # Singleton ConnectionManager with WAL
│   ├── schema.py                    # Table definitions and migrations
│   ├── models.py                    # Dataclass entities
│   └── queries.py                   # SQL query constants
│
├── services/
│   ├── auth_service.py              # Authentication and session management
│   ├── product_service.py           # Product CRUD and variant operations
│   ├── sale_engine.py               # ACID sale processing
│   ├── inventory_service.py         # Stock management and alerts
│   ├── customer_service.py          # Customer and credit management
│   ├── report_service.py            # Report generation
│   └── backup_service.py            # Encrypted backup and restore
│
├── ui/
│   ├── app.py                       # Main application window
│   ├── theme.py                     # Color palette and styling
│   ├── animations.py                # UI animations
│   ├── components.py                # Reusable widgets
│   ├── screens/                     # Application screens
│   └── dialogs/                     # Modal dialogs
│
├── hardware/
│   ├── label_printer.py             # TSPL command builder
│   ├── receipt_printer.py           # ESC/POS command builder
│   └── barcode_scanner.py           # Scanner input handler
│
├── utils/
│   ├── validators.py                # Input validation
│   ├── formatters.py                # Currency and date formatting
│   ├── barcode_generator.py         # Code 128 generation
│   ├── tspl_builder.py              # TSPL command assembly
│   ├── pdf_generator.py             # PDF report generation
│   └── audit_logger.py              # Audit trail with HMAC
│
├── tests/
│   ├── conftest.py                  # pytest fixtures
│   ├── test_validators.py
│   ├── test_sale_engine.py
│   └── ...
│
└── assets/
    ├── icons/
    ├── fonts/
    ├── logo.png
    └── barcode_templates/
```

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Step 1: Clone or Download
```bash
cd /path/to/shoukat_pos
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python main.py
```

On first run, the application will:
1. Create the `data/` directory with secure permissions (0o700)
2. Initialize the SQLite database with all tables
3. Seed default data (admin user, categories, settings)
4. Display the login screen

### Default Login Credentials
- **Username**: `admin`
- **Password**: `admin123`

**Important**: Change the default password immediately after first login!

## Database Architecture

### Style-Variant-Batch Model

The database uses a three-level hierarchy optimized for garment retail:

```
Style (e.g., "Premium Cotton Shirt")
├── Variant (M / Blue) - Barcode: SSG001-M-BLU
│   └── Batch 1 - Purchase: Rs. 1,000, Qty: 20, Remaining: 15
│   └── Batch 2 - Purchase: Rs. 1,050, Qty: 10, Remaining: 10
├── Variant (L / Blue) - Barcode: SSG001-L-BLU
│   └── Batch 1 - Purchase: Rs. 1,000, Qty: 20, Remaining: 5
└── Variant (XL / Black) - Barcode: SSG001-XL-BLK
    └── Batch 1 - Purchase: Rs. 1,000, Qty: 15, Remaining: 0
```

This architecture enables:
- **FIFO Inventory Valuation**: Track which purchase batches are being sold
- **Secret Code Encoding**: Hide purchase prices using configurable digit mapping
- **Size-Color Matrix**: Quick view of all variants for a style
- **Accurate Profit Reports**: Calculate profit per sale using actual batch costs

### SQLite Production Configuration

The database is configured with production-ready pragmas:

| PRAGMA | Value | Purpose |
|--------|-------|---------|
| journal_mode | WAL | Concurrent reads during writes |
| synchronous | NORMAL | 3x faster writes, safe with WAL |
| busy_timeout | 30000 | Handle peak-hour contention |
| cache_size | -64000 | 64MB RAM cache for lookups |
| foreign_keys | ON | Prevent orphaned records |
| secure_delete | ON | Overwrite deleted sensitive data |

## Development Workflow

### Spec + TDD Approach

This project follows a Specification + Test-Driven Development workflow:

1. **Spec**: Write detailed specification before any code
2. **RED**: Write failing tests that encode the spec
3. **GREEN**: Write minimum implementation to pass tests
4. **REFACTOR**: Clean up code while keeping tests green
5. **VALIDATE**: Run full test suite + type checking + linting

### Running Tests
```bash
pytest tests/ -v --cov=shoukat_pos
```

### Type Checking
```bash
mypy shoukat_pos/
```

### Code Formatting
```bash
ruff check shoukat_pos/
ruff format shoukat_pos/
```

## Configuration

### Printer Settings

Configure printers in Settings > Printer Settings:

**Label Printer (BlackCopper BC-LP-1300)**
- Sticker size: 28x19mm (default), 32x25mm, 32x19mm, 34x24mm
- Gap between stickers: 2mm (default)
- Print density: Light/Normal/Dark

**Receipt Printer**
- Width: 80mm (default) or 58mm
- Header: Shop name, address, phone
- Footer: Thank you message, return policy

### Secret Code Mapping

Configure in Settings > Secret Code:

Default mapping (configurable):
- 0→L, 1→R, 2→K, 3→B, 4→S, 5→M, 6→N, 7→T, 8→H, 9→W

Example: Rs. 1,250 → RKML

### Tax Configuration

Set default tax rate in Settings > General:
- GST rate (Pakistan): 17% (or as applicable)
- Per-category tax overrides available

## Backup & Restore

### Automatic Backups
- Enabled by default at 2:00 AM daily
- Retains last 30 backups
- Encrypted using admin password-derived key

### Manual Backup
Settings > Backup & Restore > Backup Now

### Restore from Backup
Settings > Backup & Restore > Select Backup File

**Warning**: Restore overwrites all current data!

## Security Features

### Password Security
- Bcrypt hashing with 12 rounds
- Account lockout after 5 failed attempts (15 minutes)
- Session timeout after 30 minutes of inactivity

### Audit Trail
Every data modification is logged with:
- Before/after values (JSON)
- User who made the change
- Timestamp
- HMAC-SHA256 hash chain for tamper detection

### Data Encryption
- Backups encrypted with Fernet (AES-128-CBC)
- Key derived from admin password via PBKDF2 (100,000 iterations)
- Database file permissions: 0o600 (owner read/write only)

## Troubleshooting

### Database Locked Errors
If you see "database is locked" errors:
1. Check if another instance is running
2. Verify no uncommitted transactions
3. Increase `busy_timeout` in config.py (default: 30s)

### Printer Not Working
1. Verify printer is installed and set as default
2. Test print from Settings > Printer Settings
3. Check USB connection and printer power
4. For Windows: Install printer drivers from manufacturer

### Barcode Scanner Issues
1. Ensure scanner is in keyboard-wedge mode (USB HID)
2. Test by scanning into a text editor
3. Configure scanner prefix/suffix if needed

## License

Proprietary - All rights reserved to Shoukat Sons Garments.

## Support

For technical support, contact the development team.

---

**Version**: 1.0.0  
**Build Date**: 2026  
**Author**: Shoukat Sons Garments Development Team
