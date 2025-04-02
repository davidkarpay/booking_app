"""
Logging configuration for the PBSO Booking Blotter application
"""
import logging
import os
from datetime import datetime

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

# Set up logging
log_file = os.path.join(log_dir, f"pbso_app_{datetime.now().strftime('%Y%m%d')}.log")

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Create logger
logger = logging.getLogger("pbso_app")