"""
Data view panel for displaying and filtering booking data
"""
import json
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QRadioButton, QPushButton, QTableWidget, QTableWidgetItem, QMenu,
    QDialog, QTextEdit, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from utils.export import export_filtered_data  # Added import for export utility

class DataView(QGroupBox):
    """Data view panel for displaying and filtering booking data"""
    def __init__(self, parent=None):
        super().__init__("Data Diagnostic View", parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by:"))
        
        self.filter_field_combo = QComboBox()
        self.filter_field_combo.addItems(["All Fields", "Name", "Booking Number", "Status", "Charges"])
        self.filter_field_combo.currentIndexChanged.connect(lambda: self.apply_filter())
        filter_layout.addWidget(self.filter_field_combo)
        
        self.filter_field = QLineEdit()
        self.filter_field.setPlaceholderText("Enter filter text...")
        self.filter_field.textChanged.connect(lambda: self.apply_filter())
        filter_layout.addWidget(self.filter_field)
        
        controls_layout.addLayout(filter_layout, 3)
        
        # Status filters
        status_filter_layout = QHBoxLayout()
        status_filter_layout.addWidget(QLabel("Status:"))
        
        self.all_status_radio = QRadioButton("All")
        self.in_custody_radio = QRadioButton("In Custody")
        self.released_radio = QRadioButton("Released")
        self.all_status_radio.setChecked(True)
        
        self.all_status_radio.toggled.connect(lambda: self.apply_filter())
        self.in_custody_radio.toggled.connect(lambda: self.apply_filter())
        self.released_radio.toggled.connect(lambda: self.apply_filter())
        
        status_filter_layout.addWidget(self.all_status_radio)
        status_filter_layout.addWidget(self.in_custody_radio)
        status_filter_layout.addWidget(self.released_radio)
        
        controls_layout.addLayout(status_filter_layout, 1)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Data View")
        self.refresh_button.clicked.connect(self.refresh_view)
        controls_layout.addWidget(self.refresh_button)
        
        layout.addLayout(controls_layout)
        
        # Table for data
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SingleSelection)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.setSortingEnabled(True)
        
        # Set up a context menu for the table
        self.data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.data_table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.data_table)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("No data loaded")
        status_layout.addWidget(self.status_label)
        
        self.export_filtered_button = QPushButton("Export Filtered Data")
        self.export_filtered_button.clicked.connect(self.export_filtered_data)
        self.export_filtered_button.setEnabled(False)
        status_layout.addWidget(self.export_filtered_button)
        
        layout.addLayout(status_layout)
    
    def set_data(self, data):
        """Set the data for the view"""
        if hasattr(self.parent, 'booking_data'):
            self.refresh_view()
    
    def clear_data(self):
        """Clear the data from the view"""
        self.data_table.clear()
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(0)
        self.status_label.setText("No data loaded")
        self.export_filtered_button.setEnabled(False)
    
    def refresh_view(self):
        """Refresh the data view with current data"""
        if not hasattr(self.parent, 'booking_data'):
            return
            
        data = self.parent.booking_data
        
        # Clear current table
        self.data_table.clear()
        self.data_table.setRowCount(0)
        
        if not data:
            self.status_label.setText("No data available")
            self.export_filtered_button.setEnabled(False)
            return
        
        # Determine columns based on data
        all_columns = set()
        for record in data:
            if isinstance(record, dict):
                all_columns.update(record.keys())
        
        # Order columns - put important ones first
        ordered_columns = ["Name", "Status", "Booking Number", "Booking Date", "Release Date", 
                         "Time Served (Days)", "Cell Location", "Charges"]
        
        # Add any remaining columns to the end
        for col in sorted(all_columns):
            if col not in ordered_columns and col != "Raw Data":  # Skip raw data, too large
                ordered_columns.append(col)
        
        # Set up table
        self.data_table.setColumnCount(len(ordered_columns))
        self.data_table.setHorizontalHeaderLabels(ordered_columns)
        
        # Populate table with data
        for row_idx, record in enumerate(data):
            if not isinstance(record, dict):
                continue
                
            self.data_table.insertRow(row_idx)
            
            for col_idx, column in enumerate(ordered_columns):
                value = record.get(column, "")
                if column == "Status":
                    # Color-code status cells
                    item = QTableWidgetItem(str(value))
                    if value == "In Custody":
                        item.setBackground(QColor("#ffcccc"))  # Light red for in custody
                        item.setForeground(QColor("#cc0000"))  # Dark red text
                    elif value == "Released":
                        item.setBackground(QColor("#ccffcc"))  # Light green for released
                        item.setForeground(QColor("#006600"))  # Dark green text
                else:
                    # Regular cells
                    item = QTableWidgetItem(str(value))
                
                self.data_table.setItem(row_idx, col_idx, item)
        
        # Auto-resize columns to content
        self.data_table.resizeColumnsToContents()
        
        # Update status
        self.status_label.setText(f"Showing {self.data_table.rowCount()} of {len(data)} records")
        self.export_filtered_button.setEnabled(True)
        
        # Apply any active filters
        self.apply_filter()
    
    def apply_filter(self):
        """Apply filters to the data view"""
        if self.data_table.rowCount() == 0:
            return
            
        filter_text = self.filter_field.text().lower()
        filter_column = self.filter_field_combo.currentText()
        
        # Determine status filter
        status_filter = None
        if self.in_custody_radio.isChecked():
            status_filter = "In Custody"
        elif self.released_radio.isChecked():
            status_filter = "Released"
        
        # Get column index for status
        status_col_idx = -1
        for i in range(self.data_table.columnCount()):
            if self.data_table.horizontalHeaderItem(i).text() == "Status":
                status_col_idx = i
                break
        
        # Get column index for filter field
        filter_col_idx = -1
        if filter_column != "All Fields":
            for i in range(self.data_table.columnCount()):
                if self.data_table.horizontalHeaderItem(i).text() == filter_column:
                    filter_col_idx = i
                    break
        
        # Apply filters row by row
        visible_count = 0
        for row in range(self.data_table.rowCount()):
            # Check status filter first
            if status_filter and status_col_idx >= 0:
                status_item = self.data_table.item(row, status_col_idx)
                if not status_item or status_item.text() != status_filter:
                    self.data_table.setRowHidden(row, True)
                    continue
            
            # Then check text filter
            if filter_text:
                if filter_col_idx >= 0:
                    # Filter specific column
                    item = self.data_table.item(row, filter_col_idx)
                    if not item or filter_text not in item.text().lower():
                        self.data_table.setRowHidden(row, True)
                        continue
                else:
                    # Filter all columns
                    row_matches = False
                    for col in range(self.data_table.columnCount()):
                        item = self.data_table.item(row, col)
                        if item and filter_text in item.text().lower():
                            row_matches = True
                            break
                    if not row_matches:
                        self.data_table.setRowHidden(row, True)
                        continue
            
            # If we get here, show the row
            self.data_table.setRowHidden(row, False)
            visible_count += 1
        
        # Update status
        self.status_label.setText(f"Showing {visible_count} of {len(self.parent.booking_data)} records")
    
    def show_context_menu(self, position):
        """Show context menu for table items"""
        menu = QMenu()
        
        # Get selected row
        row = self.data_table.currentRow()
        if row >= 0:
            view_action = menu.addAction("View Details")
            export_action = menu.addAction("Export This Record")
            
            # Add a separator
            menu.addSeparator()
            
            # Add debugging actions
            debug_action = menu.addAction("Debug This Record")
            
            # Show the menu and get the selected action
            action = menu.exec_(self.data_table.mapToGlobal(position))
            
            if action == view_action:
                self.view_record_details(row)
            elif action == export_action:
                self.export_single_record(row)
            elif action == debug_action:
                self.debug_record(row)
    
    def get_record_index_from_row(self, table_row):
        """Find the index in booking_data that corresponds to this table row"""
        if table_row < 0 or table_row >= self.data_table.rowCount() or not hasattr(self.parent, 'booking_data'):
            return -1
        
        # Get identifying information from the row
        booking_num = None
        name = None
        
        for col in range(self.data_table.columnCount()):
            header = self.data_table.horizontalHeaderItem(col).text()
            if header == "Booking Number":
                item = self.data_table.item(table_row, col)
                if item:
                    booking_num = item.text()
            elif header == "Name":
                item = self.data_table.item(table_row, col)
                if item:
                    name = item.text()
        
        # Find matching record
        for idx, record in enumerate(self.parent.booking_data):
            if not isinstance(record, dict):
                continue
                
            if (booking_num and record.get("Booking Number") == booking_num and 
                name and record.get("Name") == name):
                return idx
        
        return -1
    
    def view_record_details(self, row):
        """Show details for the selected record"""
        record_idx = self.get_record_index_from_row(row)
        if record_idx >= 0:
            self.parent.show_details(self.data_table.item(row, 0))
    
    def debug_record(self, row):
        """Debug a specific record"""
        record_idx = self.get_record_index_from_row(row)
        if record_idx >= 0 and hasattr(self.parent, 'booking_data'):
            record = self.parent.booking_data[record_idx]
            
            # Create a dialog with the record data in a text area
            dialog = QDialog(self)
            dialog.setWindowTitle("Record Debug Information")
            dialog.resize(700, 500)
            
            layout = QVBoxLayout()
            
            # Add text area with record info
            debug_text = QTextEdit()
            debug_text.setReadOnly(True)
            debug_text.setFont(QFont("Consolas", 9))
            
            # Format as pretty-printed JSON
            record_json = json.dumps(record, indent=2, default=str)
            debug_text.setText(record_json)
            
            layout.addWidget(debug_text)
            
            # Add copy button
            copy_button = QPushButton("Copy to Clipboard")
            copy_button.clicked.connect(lambda: QApplication.clipboard().setText(record_json))
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            
            button_layout = QHBoxLayout()
            button_layout.addWidget(copy_button)
            button_layout.addWidget(close_button)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            dialog.exec_()
    
    def export_single_record(self, row):
        """Export a single record to a file"""
        record_idx = self.get_record_index_from_row(row)
        if record_idx < 0 or not hasattr(self.parent, 'booking_data'):
            return
            
        record = self.parent.booking_data[record_idx]
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Record", "", "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                if file_path.lower().endswith('.json'):
                    # Export as JSON
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(record, f, indent=2, default=str)
                else:
                    # Export as formatted text
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"Record Details for {record.get('Name', 'Unknown')}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for key, value in sorted(record.items()):
                            if key != "Raw Data":  # Handle raw data separately
                                f.write(f"{key}: {value}\n")
                        
                        if "Raw Data" in record and record["Raw Data"]:
                            f.write("\nRaw Data:\n")
                            f.write("-" * 50 + "\n")
                            f.write(record["Raw Data"])
                
                self.status_label.setText(f"Record exported to {file_path}")
            except Exception as e:
                self.status_label.setText(f"Export error: {str(e)}")
    
    def export_filtered_data(self):
        """Export only the currently visible (filtered) data"""
        # Collect visible records
        visible_records = []
        
        # Get data and check if booking_data exists
        if not hasattr(self.parent, 'booking_data') or not self.parent.booking_data:
            self.status_label.setText("No data to export")
            return
        
        total_data = self.parent.booking_data
        
        # Collect records that are not hidden
        for row in range(self.data_table.rowCount()):
            if not self.data_table.isRowHidden(row):
                # Find the corresponding record in the original data
                for record in total_data:
                    # Match based on booking number and name if possible
                    booking_num = None
                    name = None
                    
                    for col in range(self.data_table.columnCount()):
                        header = self.data_table.horizontalHeaderItem(col).text()
                        item = self.data_table.item(row, col)
                        
                        if header == "Booking Number" and item:
                            booking_num = item.text()
                        elif header == "Name" and item:
                            name = item.text()
                    
                    # If we can match the record, add it to visible records
                    if (booking_num and record.get("Booking Number") == booking_num and 
                        name and record.get("Name") == name):
                        visible_records.append(record)
                        break
        
        # Use the utility export function
        export_filtered_data(visible_records, self)