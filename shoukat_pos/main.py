"""
Shoukat Sons Garments POS - Main Entry Point

This is the application entry point that initializes the database,
loads configuration, and starts the CustomTkinter GUI.
"""
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

import customtkinter as ctk
from config import APP_NAME, APP_VERSION, DATA_DIR, DIR_PERMISSIONS
from database.connection import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DATA_DIR / "pos.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def initialize_application() -> ConnectionManager:
    """
    Initialize the application: create directories, database, and seed data.
    
    This function runs once on first launch to set up the application environment.
    
    Returns:
        ConnectionManager: Initialized database connection manager instance.
    """
    logger.info(f"Initializing {APP_NAME} v{APP_VERSION}")
    
    # Ensure data directory exists with secure permissions
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, mode=DIR_PERMISSIONS)
        logger.info(f"Created data directory: {DATA_DIR}")
    
    # Initialize database (creates tables and seeds default data if needed)
    connection_manager = ConnectionManager.get_instance()
    connection_manager.initialize_database()
    
    logger.info("Application initialization complete")
    return connection_manager


def main() -> None:
    """
    Main application entry point.
    
    Initializes the application and starts the CustomTkinter event loop.
    """
    # Initialize application (database, directories, etc.)
    connection_manager = initialize_application()
    
    # Configure CustomTkinter appearance
    ctk.set_appearance_mode("light")  # 'light' or 'dark'
    ctk.set_default_color_theme("blue")  # 'blue', 'green', 'dark-blue'
    
    # Create login application window (shows login first, then main app on success)
    from ui.app import LoginApp
    login_app = LoginApp(connection_manager)
    
    # Start the event loop
    try:
        login_app.mainloop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    finally:
        # Cleanup: close database connections
        connection_manager.close_all()
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
