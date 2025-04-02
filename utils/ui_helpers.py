"""
UI helper functions for the PBSO Booking Blotter
"""
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem, QFileDialog
from PyQt5.QtGui import QColor, QFont

def show_error_dialog(parent, title, message):
    """
    Show an error dialog
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Error message
    """
    QMessageBox.critical(parent, title, message)

def show_info_dialog(parent, title, message):
    """
    Show an information dialog
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Information message
    """
    QMessageBox.information(parent, title, message)

def show_confirmation_dialog(parent, title, message):
    """
    Show a confirmation dialog
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Confirmation message
        
    Returns:
        bool: True if confirmed, False otherwise
    """
    reply = QMessageBox.question(parent, title, message, 
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return reply == QMessageBox.Yes

def create_list_item(text, data=None, background=None, foreground=None, bold=False, size=None, underline=False):
    """
    Create a styled list widget item
    
    Args:
        text: Item text
        data: Data to store with the item
        background: Background color (QColor or string)
        foreground: Foreground color (QColor or string)
        bold: Whether to use bold font
        size: Font size (int)
        underline: Whether to underline text
        
    Returns:
        QListWidgetItem: Styled list item
    """
    item = QListWidgetItem(text)
    
    if data is not None:
        item.setData(1, data)
    
    if background:
        if isinstance(background, str):
            background = QColor(background)
        item.setBackground(background)
    
    if foreground:
        if isinstance(foreground, str):
            foreground = QColor(foreground)
        item.setForeground(foreground)
    
    if bold or size or underline:
        font = item.font()
        if bold:
            font.setBold(True)
        if size:
            font.setPointSize(size)
        if underline:
            font.setUnderline(True)
        item.setFont(font)
    
    return item

def get_save_file_path(parent, title, initial_dir="", filter_str=""):
    """
    Show a save file dialog and return the selected path
    
    Args:
        parent: Parent widget
        title: Dialog title
        initial_dir: Initial directory
        filter_str: File type filter string
        
    Returns:
        str: Selected file path or empty string if canceled
    """
    file_path, _ = QFileDialog.getSaveFileName(parent, title, initial_dir, filter_str)
    return file_path

def get_open_file_path(parent, title, initial_dir="", filter_str=""):
    """
    Show an open file dialog and return the selected path
    
    Args:
        parent: Parent widget
        title: Dialog title
        initial_dir: Initial directory
        filter_str: File type filter string
        
    Returns:
        str: Selected file path or empty string if canceled
    """
    file_path, _ = QFileDialog.getOpenFileName(parent, title, initial_dir, filter_str)
    return file_path

def get_status_html(stats):
    """
    Generate HTML for status display
    
    Args:
        stats: Dictionary with statistics
        
    Returns:
        str: Formatted HTML for status display
    """
    html = """
    <style>
        .stat-table { border-collapse: collapse; width: 100%; }
        .stat-table td { padding: 4px; border-bottom: 1px solid #eee; }
        .stat-label { font-weight: bold; color: #003366; }
        .stat-value { text-align: right; }
        .stat-highlight { color: #cc0000; font-weight: bold; }
    </style>
    <table class="stat-table">
    """
    
    # Add rows for each statistic
    html += f'<tr><td class="stat-label">Total Records:</td><td class="stat-value">{stats["total"]}</td></tr>'
    html += f'<tr><td class="stat-label">In Custody:</td><td class="stat-value stat-highlight">{stats["in_custody"]}</td></tr>'
    html += f'<tr><td class="stat-label">Released:</td><td class="stat-value">{stats["released"]}</td></tr>'
    html += f'<tr><td class="stat-label">Unique Names:</td><td class="stat-value">{stats["unique_names"]}</td></tr>'
    html += f'<tr><td class="stat-label">Average Time Served:</td><td class="stat-value">{stats["avg_days"]} days</td></tr>'
    html += f'<tr><td class="stat-label">Longest Time Served:</td><td class="stat-value">{stats["max_days"]} days</td></tr>'
    
    html += "</table>"
    return html

def format_booking_html(booking_data):
    """
    Format booking data as HTML for display
    
    Args:
        booking_data: Dictionary with booking information
        
    Returns:
        str: Formatted HTML for display
    """
    html = """
    <style>
        body { font-family: Arial, sans-serif; }
        .section { margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 5px; }
        .header { font-weight: bold; color: #003366; }
        .warning { color: #cc0000; font-weight: bold; }
        .label { font-weight: bold; }
    </style>
    """
    
    html += f"<h2>Booking #{booking_data.get('Booking Number', 'Unknown')}</h2>"
    
    # Status section with appropriate styling
    if booking_data.get("Status") == "In Custody":
        html += "<div class='section' style='background-color: #ffeeee;'>"
        html += "<p class='warning'>⚠️ CURRENTLY IN CUSTODY</p>"
        html += f"<p><span class='label'>Cell Location:</span> {booking_data.get('Cell Location', 'Unknown')}</p>"
    else:
        html += "<div class='section'>"
        html += "<p>✓ Released</p>"
    
    # Time served analysis
    html += f"<p><span class='label'>Time Served:</span> {booking_data.get('Time Served (Days)', 'Unknown')} days</p>"
    html += f"<p><span class='label'>Booking Date:</span> {booking_data.get('Booking Date', 'Unknown')}</p>"
    
    if booking_data.get("Status") == "Released":
        html += f"<p><span class='label'>Release Date:</span> {booking_data.get('Release Date', 'Unknown')}</p>"
    html += "</div>"
    
    # Charges section
    charges = booking_data.get('Charges', 'None specified')
    html += "<div class='section'>"
    html += "<p class='header'>Charges:</p>"
    html += f"<p>{charges}</p>"
    html += "</div>"
    
    return html