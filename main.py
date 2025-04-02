#!/usr/bin/env python3
"""
PBSO Booking Blotter - Main Application Entry
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import PBSOBookingBlotter
from logger import logger

def main():
    """Main application entry point"""
    logger.info("Launching GUI application...")
    
    # Create the application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and display the main window
    window = PBSOBookingBlotter()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()