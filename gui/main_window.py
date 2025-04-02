"""
Main application window for the PBSO Booking Blotter
"""
import csv
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextEdit, QHBoxLayout,
    QSpinBox, QFrame, QGridLayout, QGroupBox, QSplitter, QListWidget, QListWidgetItem,
    QStackedWidget, QTabWidget, QRadioButton, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

from gui.data_view import DataView
from gui.debug_panel import DebugPanel
from gui.details_view import DetailsView
from scrapers.parallel_scraper import PBSOParallelScraper
from utils.export import export_to_csv, export_to_excel
from logger import logger
from config import DEFAULT_MAX_WORKERS, DEFAULT_MIN_DELAY, DEFAULT_MAX_DELAY


class PBSOBookingBlotter(QWidget):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.booking_data = []  # Store scraped data for export
        self.initUI()
    
    def initUI(self):
        """Initialize the user interface"""
        self.setWindowTitle("PBSO Booking Blotter")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create a tab widget to separate the main interface from debug tools
        self.tab_widget = QTabWidget()
        
        # Create the main interface tab
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout()
        
        # Header with title
        header_layout = QHBoxLayout()
        title_label = QLabel("PBSO Booking Blotter")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #003366;")
        header_layout.addWidget(title_label, 1)
        header_layout.setAlignment(Qt.AlignLeft)
        
        main_tab_layout.addLayout(header_layout)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #cccccc;")
        main_tab_layout.addWidget(line)
        
        # Login section
        login_group = QGroupBox("Login Information")
        login_layout = QGridLayout()
        
        self.label_user = QLabel("Username:")
        self.input_user = QLineEdit()
        login_layout.addWidget(self.label_user, 0, 0)
        login_layout.addWidget(self.input_user, 0, 1)
        
        self.label_pass = QLabel("Password:")
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.Password)
        login_layout.addWidget(self.label_pass, 1, 0)
        login_layout.addWidget(self.input_pass, 1, 1)
        
        login_group.setLayout(login_layout)
        main_tab_layout.addWidget(login_group)
        
        # Search settings
        settings_group = QGroupBox("Search Settings")
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("Max Concurrent Searches:"), 0, 0)
        self.worker_spinner = QSpinBox()
        self.worker_spinner.setRange(1, 10)
        self.worker_spinner.setValue(DEFAULT_MAX_WORKERS)
        self.worker_spinner.setStyleSheet("padding: 5px;")
        settings_layout.addWidget(self.worker_spinner, 0, 1)
        
        settings_layout.addWidget(QLabel("Request Delay Range:"), 1, 0)
        delay_layout = QHBoxLayout()
        self.min_delay_spinner = QSpinBox()
        self.min_delay_spinner.setRange(1, 10)
        self.min_delay_spinner.setValue(DEFAULT_MIN_DELAY)
        self.min_delay_spinner.setStyleSheet("padding: 5px;")
        delay_layout.addWidget(self.min_delay_spinner)
        
        delay_layout.addWidget(QLabel("to"))
        
        self.max_delay_spinner = QSpinBox()
        self.max_delay_spinner.setRange(2, 15)
        self.max_delay_spinner.setValue(DEFAULT_MAX_DELAY)
        self.max_delay_spinner.setStyleSheet("padding: 5px;")
        delay_layout.addWidget(self.max_delay_spinner)
        delay_layout.addWidget(QLabel("seconds"))
        
        settings_layout.addLayout(delay_layout, 1, 1)
        settings_group.setLayout(settings_layout)
        main_tab_layout.addWidget(settings_group)
        
        # Names input section
        names_group = QGroupBox("Search Names")
        names_layout = QVBoxLayout()
        
        self.label_names = QLabel("Enter Names (Lastname, Firstname - one per line):")
        names_layout.addWidget(self.label_names)
        
        self.input_names = QTextEdit()
        self.input_names.setMinimumHeight(120)
        names_layout.addWidget(self.input_names)
        
        csv_button_layout = QHBoxLayout()
        self.load_csv_button = QPushButton("Load Names from CSV")
        self.load_csv_button.setIcon(QIcon.fromTheme("document-open"))
        self.load_csv_button.clicked.connect(self.load_csv)
        csv_button_layout.addWidget(self.load_csv_button)
        csv_button_layout.addStretch()
        
        names_layout.addLayout(csv_button_layout)
        names_group.setLayout(names_layout)
        main_tab_layout.addWidget(names_group)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.search_button = QPushButton("Start Parallel Search")
        self.search_button.setMinimumHeight(36)
        self.search_button.clicked.connect(self.run_search)
        buttons_layout.addWidget(self.search_button)
        
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.setMinimumHeight(36)
        self.clear_button.clicked.connect(self.clear_results)
        buttons_layout.addWidget(self.clear_button)
        
        main_tab_layout.addLayout(buttons_layout)
        
        # Export buttons
        export_group = QGroupBox("Export Results")
        export_layout = QHBoxLayout()
        
        self.export_csv_button = QPushButton("Export to CSV")
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.export_csv_button.setEnabled(False)
        export_layout.addWidget(self.export_csv_button)
        
        self.export_excel_button = QPushButton("Export to Excel")
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setEnabled(False)
        export_layout.addWidget(self.export_excel_button)
        
        export_group.setLayout(export_layout)
        main_tab_layout.addWidget(export_group)
        
        # Status section
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #666666;")
        status_layout.addWidget(self.status_label)
        
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setStyleSheet("color: #666666;")
        status_layout.addWidget(self.progress_label)
        
        main_tab_layout.addLayout(status_layout)
        
        # Results area - using a stacked widget for summary and details views
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout()
        
        # Use a stacked widget for summary and details views
        self.results_stack = QStackedWidget()
        
        # Summary view contains a list widget for the results
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                font-family: Arial;
                font-size: 10pt;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eaeaea;
            }
            QListWidget::item:selected {
                background-color: #e0f0ff;
                border: none;
            }
        """)
        self.results_list.itemClicked.connect(self.show_details)
        
        # Create details view
        self.details_widget = DetailsView(self)
        self.details_widget.back_button.clicked.connect(lambda: self.results_stack.setCurrentIndex(0))
        
        # Add both views to the stack
        self.results_stack.addWidget(self.results_list)
        self.results_stack.addWidget(self.details_widget)
        
        results_layout.addWidget(self.results_stack)
        results_group.setLayout(results_layout)
        
        main_tab_layout.addWidget(results_group)
        
        # Copyright footer
        footer = QLabel("© Copyright David Karpay " + str(datetime.now().year))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #666666; font-size: 9pt;")
        main_tab_layout.addWidget(footer)
        
        # Set the main tab layout
        main_tab.setLayout(main_tab_layout)
        self.tab_widget.addTab(main_tab, "Main Interface")
        
        # Create a debug tab with debug panel and data view
        debug_tab = QWidget()
        debug_tab_layout = QVBoxLayout()
        
        # Add a label for the debug tab
        debug_heading = QLabel("Debugging Tools")
        debug_heading.setStyleSheet("font-size: 18px; color: #003366; font-weight: bold;")
        debug_tab_layout.addWidget(debug_heading)
        
        # Add the debug panel
        self.debug_panel = DebugPanel(self)
        debug_tab_layout.addWidget(self.debug_panel)
        
        # Add data diagnostic view
        self.data_view = DataView(self)
        debug_tab_layout.addWidget(self.data_view)
        
        debug_tab.setLayout(debug_tab_layout)
        self.tab_widget.addTab(debug_tab, "Debug Tools")
        
        # Add the tab widget to the main layout
        self.main_layout.addWidget(self.tab_widget)
        
        # Initialize debug log
        self.log_debug("Debug interface initialized")
        
        # Set the main layout
        self.setLayout(self.main_layout)
        
        # Add style sheet
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                color: #333333;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-weight: bold;
                color: #003366;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QPushButton {
                background-color: #003366;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #004080;
            }
            QPushButton:pressed {
                background-color: #002040;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
    
    def log_debug(self, message):
        """Add a message to the debug log"""
        self.debug_panel.log_debug(message)
    
    def load_csv(self):
        """Load names from a CSV file"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")
        if file_name:
            try:
                names = []
                with open(file_name, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if len(row) >= 2:
                            last = row[0].strip()
                            first = row[1].strip()
                            names.append(f"{last}, {first}")
                if names:
                    self.input_names.setPlainText("\n".join(names))
                    self.status_label.setText(f"Status: CSV loaded successfully with {len(names)} names.")
                    self.log_debug(f"CSV loaded with {len(names)} names")
                else:
                    self.status_label.setText("⚠️ CSV file is empty or not in the expected format.")
                    self.log_debug("CSV file was empty or in wrong format")
            except Exception as e:
                self.status_label.setText(f"Error loading CSV file: {str(e)}")
                self.log_debug(f"Error loading CSV: {str(e)}")

    def run_search(self):
        """Run the search with the provided names"""
        username = self.input_user.text().strip()
        password = self.input_pass.text().strip()
        raw_text = self.input_names.toPlainText().strip()
        
        if not raw_text:
            self.status_label.setText("⚠️ Please enter at least one name!")
            return
        
        names_list = []
        for line in raw_text.splitlines():
            if "," in line:
                parts = line.split(",")
                if len(parts) >= 2:
                    # Use only the first word of the last name and first name
                    last = parts[0].strip().split()[0]
                    first = parts[1].strip().split()[0]
                    names_list.append((last, first))
        
        if not names_list:
            self.status_label.setText("⚠️ Invalid format! Use 'Lastname, Firstname' per line.")
            return
        
        # Get user settings
        max_workers = self.worker_spinner.value()
        min_delay = self.min_delay_spinner.value()
        max_delay = self.max_delay_spinner.value()
        
        # Check if max_delay is greater than min_delay
        if max_delay <= min_delay:
            self.max_delay_spinner.setValue(min_delay + 1)
            max_delay = min_delay + 1
        
        # Count total names
        total_names = len(names_list)
        
        # Log search parameters
        self.log_debug(f"Starting search for {total_names} names with {max_workers} workers")
        self.log_debug(f"Delay range: {min_delay}-{max_delay} seconds")
        
        # Warning if too many names
        if total_names > 50:
            self.status_label.setText(f"⚠️ Warning: You are about to search for {total_names} names. This may put significant load on the website.")
            self.search_button.setText("Confirm Search")
            self.search_button.setStyleSheet("background-color: #ffcccc;")
            
            # Create a one-time reset function
            def reset_button():
                self.search_button.setText("Start Parallel Search")
                self.search_button.setStyleSheet("")
                self.search_button.clicked.disconnect(reset_button)
                self.search_button.clicked.connect(self.run_search)
            
            self.search_button.clicked.disconnect(self.run_search)
            self.search_button.clicked.connect(reset_button)
            return
        
        # Start the search
        self.status_label.setText("Status: Initializing parallel searches...")
        self.progress_label.setText(f"Progress: 0% (0/{total_names})")
        
        # Clear previous results and show searching message
        self.results_list.clear()
        searching_item = QListWidgetItem(f"Searching for {total_names} names with {max_workers} concurrent workers...\n\nPlease wait. This could take some time depending on the number of names and concurrent searches.\n\nUsing {min_delay}-{max_delay} second delays between requests to avoid overloading the website.")
        self.results_list.addItem(searching_item)
        
        # Make sure we're on the summary view
        self.results_stack.setCurrentIndex(0)
        
        # Create and start the scraper
        self.scraper = PBSOParallelScraper(
            username, 
            password, 
            names_list, 
            max_workers,
            min_delay,
            max_delay
        )
        self.scraper.search_complete.connect(self.display_results)
        self.scraper.status_update.connect(self.update_status)
        self.scraper.progress_update.connect(self.update_progress)
        self.scraper.data_ready.connect(self.handle_data_ready)
        self.scraper.start()
    
    def update_status(self, status):
        """Update the status label with the current status"""
        self.status_label.setText(f"Status: {status}")
        # Log important status updates
        if "complete" in status.lower() or "error" in status.lower():
            self.log_debug(status)
    
    def update_progress(self, completed, total):
        """Update the progress label with the current progress"""
        percentage = int((completed / total) * 100)
        self.progress_label.setText(f"Progress: {percentage}% ({completed}/{total})")
    
    def show_details(self, item):
        """Show the detailed view for a booking entry"""
        entry_data = item.data(Qt.UserRole)
        
        # If there's no data or it's a header item, do nothing
        if not entry_data:
            return
        
        # Update the details view
        self.details_widget.show_details(entry_data)
        
        # Switch to details view
        self.results_stack.setCurrentIndex(1)
    
    def handle_data_ready(self, data):
        """Store data for export when search is complete"""
        self.booking_data = data
        self.log_debug(f"Received {len(data)} booking records from search")
        
        # Update the data view
        if hasattr(self, 'data_view'):
            self.data_view.set_data(data)
        
        if data:
            self.export_csv_button.setEnabled(True)
            self.export_excel_button.setEnabled(True)
            
            # Show a summary of the time served analysis in the status bar
            if len(data) > 0:
                try:
                    # Calculate statistics
                    in_custody_count = sum(1 for item in data if item.get("Status") == "In Custody")
                    released_count = sum(1 for item in data if item.get("Status") == "Released")
                    
                    # Update status with quick summary
                    self.status_label.setText(f"Status: Found {len(data)} booking records. In custody: {in_custody_count}, Released: {released_count}")
                    self.log_debug(f"Statistics - Total: {len(data)}, In custody: {in_custody_count}, Released: {released_count}")
                except Exception as e:
                    logger.error(f"Error generating statistics: {str(e)}")
                    self.log_debug(f"Error calculating statistics: {str(e)}")
    
    def export_to_csv(self):
        """Export booking data to CSV file"""
        if export_to_csv(self.booking_data):
            self.status_label.setText("Status: Data exported to CSV successfully")
    
    def export_to_excel(self):
        """Export booking data to Excel file with formatting"""
        if export_to_excel(self.booking_data):
            self.status_label.setText("Status: Data exported to Excel successfully")
    
    def clear_results(self):
        """Clear all results and reset the UI"""
        self.input_names.clear()
        self.results_list.clear()
        self.booking_data = []
        self.status_label.setText("Status: Ready")
        self.progress_label.setText("Progress: 0%")
        self.export_csv_button.setEnabled(False)
        self.export_excel_button.setEnabled(False)
        self.results_stack.setCurrentIndex(0)
        
        # Also clear data view if it exists
        if hasattr(self, 'data_view'):
            self.data_view.clear_data()
            
        self.log_debug("Results cleared")

    def display_results(self, results):
        """Display search results in the UI"""
        self.status_label.setText("Status: Search Complete")
        
        # Clear the list widget
        self.results_list.clear()
        
        # Reset to the summary view
        self.results_stack.setCurrentIndex(0)
        
        # Log debug information
        self.log_debug(f"Search complete. Processing {len(self.booking_data)} booking records.")
        
        # Check if we have data
        if not self.booking_data:
            # No results found
            self.log_debug("No booking data available to display")
            item = QListWidgetItem("No results found for any of the searches.")
            item.setData(Qt.UserRole, None)
            self.results_list.addItem(item)
            return
        
        # Group data by name
        names_dict = {}
        for entry in self.booking_data:
            name = entry.get("Name", "Unknown")
            if name not in names_dict:
                names_dict[name] = []
            names_dict[name].append(entry)
        
        self.log_debug(f"Displaying results for {len(names_dict)} unique names")
        
        # Add each person's summary to the list
        for name, entries in sorted(names_dict.items()):
            self.log_debug(f"Processing {len(entries)} records for {name}")
            
            # Create a header item for the person
            person_item = QListWidgetItem(f"📋 {name}")
            person_item.setData(Qt.UserRole, None)
            person_item.setBackground(QColor("#f0f0f0"))
            person_item.setForeground(QColor("#000066"))
            font = person_item.font()
            font.setBold(True)
            font.setPointSize(11)
            person_item.setFont(font)
            self.results_list.addItem(person_item)
            
            # Add booking entries for this person
            for i, entry in enumerate(entries):
                try:
                    booking_num = entry.get("Booking Number", "Unknown")
                    status = entry.get("Status", "Unknown")
                    days = entry.get("Time Served (Days)", 0)
                    
                    # Create nicely formatted summary text
                    if status == "In Custody":
                        # For in-custody, highlight with red and show cell location
                        cell = entry.get("Cell Location", "Unknown")
                        charges = entry.get("Charges", "None specified")
                        
                        summary = f"🔴 BOOKING #{i+1} ({booking_num}) - CURRENTLY IN CUSTODY - {days} days\n"
                        summary += f"📍 Location: {cell}\n"
                        summary += f"⚖️ Charges: {charges}"
                        
                        item = QListWidgetItem(summary)
                        item.setBackground(QColor("#fff0f0"))  # Light red background
                    else:
                        # For released individuals, use neutral styling
                        summary = f"✓ BOOKING #{i+1} ({booking_num}) - Released - Served {days} days"
                        item = QListWidgetItem(summary)
                    
                    # Store the data for this entry to be used in detail view
                    item.setData(Qt.UserRole, entry)
                    
                    # Add to list
                    self.results_list.addItem(item)
                    
                    # Add a "View Details" button for this entry
                    details_item = QListWidgetItem("    👁️ View Complete Details")
                    details_item.setData(Qt.UserRole, entry)
                    # The section around line 576 should look like this:
                    details_item = QListWidgetItem("    👁️ View Complete Details")
                    details_item.setData(Qt.UserRole, entry)
                    details_item.setForeground(QColor("#0066cc"))
                    font = details_item.font()
                    font.setUnderline(True)
                    details_item.setFont(font)
                    self.results_list.addItem(details_item)
                    self.results_list.addItem(details_item)
                except Exception as e:
                    self.log_debug(f"Error displaying record {i} for {name}: {str(e)}")
                    error_item = QListWidgetItem(f"⚠️ Error displaying booking #{i+1}: {str(e)}")
                    self.results_list.addItem(error_item)
            
            # Add a separator
            separator = QListWidgetItem("")
            separator.setFlags(Qt.NoItemFlags)
            self.results_list.addItem(separator)
        
        # Enable export buttons if we have data
        if self.booking_data:
            self.export_csv_button.setEnabled(True)
            self.export_excel_button.setEnabled(True)
            
        self.log_debug("Finished displaying search results")