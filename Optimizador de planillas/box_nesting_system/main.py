"""
Main entry point for the Box Nesting Optimization System.

This module initializes the application and launches the main window
with all necessary components for box design and nesting optimization.
"""

import sys
import os
import logging

# Add the current directory to Python path for reliable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtWidgets import QApplication

from frontend.ui.main_window import MainWindow
from backend.utils.logging_config import setup_logging


def setup_application() -> QApplication:
    """
    Configure and initialize the QApplication.
    
    Returns:
        QApplication: Configured application instance
    """
    # Create application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Box Nesting Optimization System")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("BoxNestingOrg")
    app.setOrganizationDomain("boxnesting.org")
    
    # Set application-wide stylesheet if needed
    app.setStyle('Fusion')  # Modern style that works on all platforms
    
    return app


def initialize_environment():
    """
    Initialize application environment and dependencies.
    """
    # Ensure necessary directories exist
    log_dir = os.path.join(current_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join(log_dir, "box_nesting_system.log")
    setup_logging(level=logging.INFO, log_file=log_file, enable_console=True)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Box Nesting Optimization System - Starting Up")
    logger.info("Version: %s", __version__ if '__version__' in globals() else "1.0.0")
    logger.info("Python: %s", sys.version)
    logger.info("Working directory: %s", current_dir)
    logger.info("=" * 60)


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for uncaught exceptions.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow Ctrl+C to work normally
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    logger = logging.getLogger(__name__)
    logger.critical(
        "Uncaught exception:",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Show error message to user
    from PySide6.QtWidgets import QMessageBox, QApplication
    from PySide6.QtCore import Qt
    
    app = QApplication.instance()
    if app:
        error_msg = f"""
        <b>Critical Error</b><br><br>
        An unexpected error has occurred:<br>
        <code>{exc_type.__name__}: {exc_value}</code><br><br>
        Please check the log file for details.
        """
        QMessageBox.critical(
            None,
            "Critical Error",
            error_msg
        )


def main() -> int:
    """
    Application entry point.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    # Setup global exception handling
    sys.excepthook = handle_uncaught_exception
    
    # Initialize environment and logging
    initialize_environment()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing application...")
        
        # Setup and configure application
        app = setup_application()
        
        # Create and show main window
        logger.info("Creating main window...")
        window = MainWindow()
        window.show()
        
        logger.info("Application started successfully")
        logger.info("Main window displayed and ready for user interaction")
        
        # Execute application event loop
        exit_code = app.exec()
        
        logger.info("Application shutdown completed with exit code: %d", exit_code)
        return exit_code
        
    except ImportError as e:
        logger.critical("Import error - missing dependencies: %s", e)
        print(f"Import Error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install PySide6 pyclipper")
        return 1
        
    except Exception as e:
        logger.critical("Application failed to start: %s", e, exc_info=True)
        print(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    # Run the application
    exit_code = main()
    
    # Exit with appropriate code
    sys.exit(exit_code)