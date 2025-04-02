# PBSO Booking Blotter

A Python application for searching and analyzing booking records from the Palm Beach Sheriff's Office.

## Project Structure

The application is organized into the following modules:

```
pbso_booking_app/
├── main.py                     # Main entry point
├── config.py                   # Configuration settings
├── logger.py                   # Logging setup
├── gui/                        # GUI components
│   ├── __init__.py
│   ├── main_window.py          # Main application window
│   ├── details_view.py         # Details view code
│   ├── debug_panel.py          # Debug panel code
│   └── data_view.py            # Data view/table code
├── scrapers/                   # Web scraping functionality
│   ├── __init__.py
│   ├── worker.py               # Scraper worker implementation
│   └── parallel_scraper.py     # Parallel scraper implementation
└── utils/                      # Utility functions
    ├── __init__.py
    └── export.py               # Export functionality
```

## Requirements

- Python 3.6+
- PyQt5
- Selenium
- pandas
- openpyxl

## Installation

1. Clone this repository
2. Install dependencies:
```
pip install PyQt5 selenium pandas openpyxl webdriver-manager
```

## Usage

Run the application:

```
python main.py
```

### Instructions

1. Enter your login credentials
2. Adjust search settings if needed
3. Enter names in the format "Lastname, Firstname" (one per line)
4. Click "Start Parallel Search"
5. View results and export data as needed

## Features

- Parallel searching for multiple names
- Detailed booking information display
- Data filtering and sorting
- Export to CSV and Excel
- Debug tools for troubleshooting

## License

This project is licensed under the MIT License - see the LICENSE file for details.