"""
Details view for displaying booking information
"""
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout
from PyQt5.QtGui import QFont

class DetailsView(QWidget):
    """Widget for displaying detailed booking information"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Header for the details view
        self.header = QLabel("Booking Details")
        self.header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #003366;")
        layout.addWidget(self.header)
        
        # Text edit for displaying details
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.details_text)
        
        # Back button
        self.back_button = QPushButton("Back to Summary")
        layout.addWidget(self.back_button)
    
    def show_details(self, entry_data):
        """Display details for the specified booking entry"""
        # Update the header
        self.header.setText(f"Booking Details for {entry_data.get('Name', 'Unknown')}")
        
        # Format details with rich formatting
        details_html = "<style>"
        details_html += "body { font-family: Arial, sans-serif; }"
        details_html += ".section { margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 5px; }"
        details_html += ".header { font-weight: bold; color: #003366; }"
        details_html += ".warning { color: #cc0000; font-weight: bold; }"
        details_html += ".label { font-weight: bold; }"
        details_html += "</style>"
        
        details_html += f"<h2>Booking #{entry_data.get('Booking Number', 'Unknown')}</h2>"
        
        # Status section with appropriate styling
        if entry_data.get("Status") == "In Custody":
            details_html += "<div class='section' style='background-color: #ffeeee;'>"
            details_html += "<p class='warning'>⚠️ CURRENTLY IN CUSTODY</p>"
            details_html += f"<p><span class='label'>Cell Location:</span> {entry_data.get('Cell Location', 'Unknown')}</p>"
        else:
            details_html += "<div class='section'>"
            details_html += "<p>✓ Released</p>"
        
        # Time served analysis
        details_html += f"<p><span class='label'>Time Served:</span> {entry_data.get('Time Served (Days)', 'Unknown')} days</p>"
        details_html += f"<p><span class='label'>Booking Date:</span> {entry_data.get('Booking Date', 'Unknown')}</p>"
        
        if entry_data.get("Status") == "Released":
            details_html += f"<p><span class='label'>Release Date:</span> {entry_data.get('Release Date', 'Unknown')}</p>"
        else:
            details_html += f"<p><span class='label'>Current as of:</span> {datetime.now().strftime('%m/%d/%Y')}</p>"
        details_html += "</div>"
        
        # Charges section
        details_html += "<div class='section'>"
        details_html += "<p class='header'>Charges:</p>"
        details_html += f"<p>{entry_data.get('Charges', 'None specified')}</p>"
        details_html += "</div>"
        
        # Raw data section - use pre-formatted text
        if "Raw Data" in entry_data and entry_data["Raw Data"]:
            details_html += "<div class='section'>"
            details_html += "<p class='header'>Complete Booking Information:</p>"
            details_html += f"<pre>{entry_data['Raw Data']}</pre>"
            details_html += "</div>"
        
        # Set the HTML content
        self.details_text.setHtml(details_html)