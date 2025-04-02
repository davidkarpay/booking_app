"""
Debug panel for the PBSO Booking Blotter
"""
from datetime import datetime
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog
)

from logger import logger

class DebugPanel(QGroupBox):
    """Debug panel widget for logging and debugging information"""
    def __init__(self, parent=None):
        super().__init__("Debug Log", parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Text area for debug logs
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setMinimumHeight(200)
        self.debug_text.setStyleSheet("font-family: Consolas, monospace; font-size: 9pt;")
        layout.addWidget(self.debug_text)
        
        # Debug action buttons
        buttons_layout = QHBoxLayout()
        
        self.dump_button = QPushButton("Dump Raw Data Structure")
        self.dump_button.clicked.connect(self.dump_data)
        buttons_layout.addWidget(self.dump_button)
        
        self.count_button = QPushButton("Count Records by Name")
        self.count_button.clicked.connect(self.count_records)
        buttons_layout.addWidget(self.count_button)
        
        self.save_button = QPushButton("Save Debug Log")
        self.save_button.clicked.connect(self.save_log)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
    
    def log_debug(self, message):
        """Add a message to the debug log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_text.append(f"[{timestamp}] {message}")
        # Also log to console/file for terminal debugging
        logger.debug(message)
    
    def dump_data(self):
        """Dump the data structure to the debug panel"""
        if not hasattr(self.parent, 'booking_data') or not self.parent.booking_data:
            self.log_debug("No booking data available")
            return
        
        data = self.parent.booking_data
        self.log_debug(f"Data structure contains {len(data)} total records")
        
        # Dump the first record structure as an example
        self.log_debug("\nExample record structure:")
        for key, value in data[0].items():
            self.log_debug(f"  {key}: {value}")
        
        # Count and log different types of data
        statuses = {}
        for record in data:
            status = record.get("Status", "Unknown")
            if status not in statuses:
                statuses[status] = 0
            statuses[status] += 1
        
        self.log_debug("\nStatus counts:")
        for status, count in statuses.items():
            self.log_debug(f"  {status}: {count}")
    
    def count_records(self):
        """Count and display records by name"""
        if not hasattr(self.parent, 'booking_data') or not self.parent.booking_data:
            self.log_debug("No booking data available")
            return
        
        data = self.parent.booking_data
        
        # Group by name
        names_dict = {}
        for entry in data:
            name = entry.get("Name", "Unknown")
            if name not in names_dict:
                names_dict[name] = []
            names_dict[name].append(entry)
        
        # Sort by name for consistent output
        self.log_debug(f"\nFound records for {len(names_dict)} unique names:")
        for name, records in sorted(names_dict.items()):
            in_custody = sum(1 for r in records if r.get("Status") == "In Custody")
            released = sum(1 for r in records if r.get("Status") == "Released")
            self.log_debug(f"  {name}: {len(records)} records (In Custody: {in_custody}, Released: {released})")
    
    def save_log(self):
        """Save the debug log to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Debug Log", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.debug_text.toPlainText())
                if hasattr(self.parent, 'status_label'):
                    self.parent.status_label.setText(f"Status: Debug log saved to {file_path}")
                self.log_debug(f"Debug log saved to {file_path}")
            except Exception as e:
                if hasattr(self.parent, 'status_label'):
                    self.parent.status_label.setText(f"Status: Failed to save debug log - {str(e)}")
                self.log_debug(f"Error saving debug log: {str(e)}")