"""
Scraper worker implementation for the PBSO Booking Blotter
"""
import time
import random
import re
from datetime import datetime, timedelta
from PyQt5.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from logger import logger

class ScraperWorker(QThread):
    """Individual worker thread that processes a single name search"""
    result_ready = pyqtSignal(str, str, list)  # Signal for name, result, and structured data
    status_update = pyqtSignal(str)
    
    def __init__(self, username, password, last_name, first_name, min_delay, max_delay):
        super().__init__()
        self.username = username
        self.password = password
        self.last_name = last_name
        self.first_name = first_name
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.booking_data = []  # To store structured data for export
    
    def extract_value(self, text, label):
        """
        Extract values from the text following a specified label.
        Enhanced to handle multi-line results and edge cases.
        """
        try:
            if not text or not label:
                return None
                
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if label in line:
                    # Special case for Cell Location
                    if label == "Cell Location:":
                        # First try direct Cell Location pattern
                        cell_match = re.search(r'Cell Location:([^\n]+)', text)
                        if cell_match and cell_match.group(1).strip():
                            return cell_match.group(1).strip()
                            
                        # Try alternate format
                        for j, check_line in enumerate(lines):
                            if "Cell Location:" in check_line:
                                # If cell location is on this line
                                cell_text = check_line.replace("Cell Location:", "").strip()
                                if cell_text:
                                    return cell_text
                                # If it's on the next line
                                elif j + 1 < len(lines) and lines[j + 1].strip():
                                    return lines[j + 1].strip()
                        
                        # As a backup, look for Facility line
                        for j, check_line in enumerate(lines):
                            if "Facility:" in check_line:
                                facility = check_line.replace("Facility:", "").strip()
                                if facility and not facility.lower() in ["no file", ""]:
                                    return facility
                    
                    # Handle special case for charges which can span multiple lines
                    if label == "Charges:":
                        # First look for the "Charges" section header
                        charges_section = -1
                        for j, check_line in enumerate(lines):
                            if check_line.strip() == "Charges":
                                charges_section = j
                                break
                        
                        if charges_section >= 0:
                            # Collect all charge lines until we hit a section that starts with keywords
                            charges = []
                            j = charges_section + 1
                            while j < len(lines) and not any(keyword in lines[j] for keyword in 
                                  ["Bond:", "Original Bond:", "Current Bond:", "Bond Information", "Release Date:"]):
                                if lines[j].strip():
                                    charges.append(lines[j].strip())
                                j += 1
                            
                            return " | ".join(charges) if charges else None
                        
                        # Alternate approach - look for lines between "Charges:" and next section
                        for j, check_line in enumerate(lines):
                            if "Charges:" in check_line:
                                charges = []
                                k = j + 1
                                while k < len(lines) and not any(keyword in lines[k] for keyword in 
                                      ["Bond:", "Original Bond:", "Current Bond:", "Bond Information", "Release Date:"]):
                                    if lines[k].strip():
                                        charges.append(lines[k].strip())
                                    k += 1
                                
                                return " | ".join(charges) if charges else None
                    
                    # For booking number, use regex to extract the exact number
                    if label == "Booking Number:":
                        booking_match = re.search(r'Booking Number:\s*(\d+)', text)
                        if booking_match:
                            return booking_match.group(1)
                    
                    # For booking date, first try regex then fallback to next line
                    if label == "Booking Date/Time:":
                        date_match = re.search(r'Booking Date/Time:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})', text)
                        if date_match:
                            return date_match.group(1)
                        
                        # Try alternate format
                        alt_match = re.search(r'Booking Date/Time:(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})', text)
                        if alt_match:
                            return alt_match.group(1)
                    
                    # For release date, use regex
                    if label == "Release Date:":
                        release_match = re.search(r'Release Date:\s*([^\n]+)', text)
                        if release_match:
                            return release_match.group(1).strip()
                    
                    # For regular fields, check next line
                    if i + 1 < len(lines):
                        return lines[i + 1].strip()
                    else:
                        return None
        except Exception as e:
            logger.error(f"Error extracting value for {label}: {str(e)}")
            return None
        
        # If we got here, the label wasn't found
        return None
    
    def determine_status(self, release_date_str, cell_location):
        """
        Determine the custody status with more robust logic
        
        Args:
            release_date_str (str): Release date string
            cell_location (str): Cell location string
        
        Returns:
            str: Status ('In Custody', 'Released', or 'Unknown')
        """
        # Logging details for debugging
        logger.debug(f"Status Determination Debug:")
        logger.debug(f"Release Date String: {release_date_str}")
        logger.debug(f"Cell Location: {cell_location}")
        
        # Normalize input strings
        release_date_str = str(release_date_str).strip().lower() if release_date_str else ""
        cell_location = str(cell_location).strip().lower() if cell_location else ""
        
        # Check release date first
        if release_date_str and release_date_str not in ['', 'n/a', 'unknown', 'still in custody']:
            try:
                # Remove any text like "Time:"
                clean_date = re.sub(r'\s*time:.*', '', release_date_str, flags=re.IGNORECASE)
                release_date = self.parse_date(clean_date)
                
                if release_date and release_date <= datetime.now():
                    return "Released"
            except Exception as e:
                logger.warning(f"Date parsing error: {e}")
        
        # Check cell location for custody indicators
        custody_indicators = [
            'jail', 'prison', 'facility', 'block', 'pod', 'cell', 
            'detention', 'surety bond', 'bonds', 'holding', 'center'
        ]
        
        if cell_location and any(indicator in cell_location for indicator in custody_indicators):
            return "In Custody"
        
        # If N/A is specified for release date, assume in custody
        if release_date_str == "n/a":
            return "In Custody"
            
        # Default to Unknown if we can't determine status
        return "Unknown"
    
    def parse_date(self, date_str):
        """
        Parse date string to datetime object with improved handling of different date formats.
        """
        if not date_str or date_str == "N/A" or date_str == "Still in custody":
            return None
            
        # Clean up the date string
        date_str = date_str.strip()
        
        # Try multiple date formats
        formats = [
            "%m/%d/%Y %H:%M", 
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y", 
            "%m/%d/%y %H:%M",
            "%m/%d/%y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # If we got here, log the failure but don't crash
        logger.warning(f"Failed to parse date: {date_str}")
        return None
    
    def run(self):
        driver = None
        try:
            # Add jitter to prevent all workers from starting at the exact same time
            jitter = random.uniform(0.5, 3.0)
            time.sleep(jitter)
            
            # Setup Chrome options
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")
            
            # Initialize WebDriver with a unique session
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
            # Random delay between requests to avoid fingerprinting
            delay = random.uniform(self.min_delay, self.max_delay)
            time.sleep(delay)
            
            self.status_update.emit(f"Worker starting for {self.last_name}, {self.first_name}")
            driver.get("https://www3.pbso.org/mediablotter/index.cfm?fa=search1")
            wait = WebDriverWait(driver, 60)
            
            # Login Process
            self.status_update.emit(f"Logging in for {self.last_name}, {self.first_name}")
            username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
            password_input = driver.find_element(By.ID, "password")
            username_input.send_keys(self.username)
            password_input.send_keys(self.password)
            password_input.send_keys(Keys.RETURN)
            time.sleep(delay)
            
            wait.until(EC.presence_of_element_located((By.ID, "firstName")))
            self.status_update.emit(f"Login successful for {self.last_name}, {self.first_name}")
            
            # Perform search
            first_name_input = wait.until(EC.presence_of_element_located((By.ID, "firstName")))
            last_name_input = driver.find_element(By.ID, "lastName")
            first_name_input.clear()
            last_name_input.clear()
            first_name_input.send_keys(self.first_name)
            last_name_input.send_keys(self.last_name)
            
            # Set start date to two years ago
            try:
                start_date_input = wait.until(EC.presence_of_element_located((By.NAME, "start_date")))
                start_date = (datetime.now() - timedelta(days=730)).strftime("%m/%d/%Y")
                logger.info(f"Start date updated to: {start_date}")
                driver.execute_script("arguments[0].value = '';", start_date_input)
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", start_date_input, start_date)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error setting start date: {str(e)}")
                error_msg = f"Error setting start date: {str(e)}"
                self.result_ready.emit(f"{self.last_name}, {self.first_name}", error_msg, [])
                driver.quit()
                return
            
            # Click search button
            self.status_update.emit(f"Searching for {self.last_name}, {self.first_name}")
            search_button = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.vc_btn3.vc_btn3-shape-rounded.btn.btn-md.btn-primary")
            ))
            search_button.click()
            
            # Wait for results with randomized delay to prevent timing fingerprinting
            time.sleep(random.uniform(2, 4))
            
            # Try to get results container
            try:
                results_container = wait.until(EC.presence_of_element_located((By.ID, "resultspage")))
                self.status_update.emit(f"Results loaded for {self.last_name}, {self.first_name}")
            except Exception:
                self.status_update.emit(f"Using page source fallback for {self.last_name}, {self.first_name}")
                results_container = None
                time.sleep(random.uniform(3, 5))
            
            # Extract booking entries
            if results_container:
                booking_entries = results_container.find_elements(By.CSS_SELECTOR, "div[id^='allresults_']")
            else:
                booking_entries = driver.find_elements(By.CSS_SELECTOR, "div[id^='allresults_']")
            
            if not booking_entries:
                result = f"No results for {self.last_name}, {self.first_name}.\n"
                self.status_update.emit(f"No results for {self.last_name}, {self.first_name}")
                self.result_ready.emit(f"{self.last_name}, {self.first_name}", result, [])
            else:
                results = []
                self.booking_data = []  # Reset booking data list
                
                for entry in booking_entries:
                    text = entry.text
                    results.append(text)
                    
                    # Extract structured data
                    booking_number = self.extract_value(text, "Booking Number:") or "Unknown"
                    booking_date_str = self.extract_value(text, "Booking Date/Time:") or "Unknown"
                    release_date_str = self.extract_value(text, "Release Date:") or "N/A"
                    charges = self.extract_value(text, "Charges:") or "Not specified"
                    cell_location = self.extract_value(text, "Cell Location:") or "Not specified"
                    
                    # Parse dates with improved parsing
                    booking_date = self.parse_date(booking_date_str)
                    release_date = self.parse_date(release_date_str) if release_date_str != "N/A" else None
                    
                    # Determine status with more robust logic
                    status = self.determine_status(release_date_str, cell_location)
                    
                    # Calculate time served with better handling
                    if booking_date:
                        if release_date and release_date > booking_date:
                            time_served = (release_date - booking_date).days
                            if time_served < 1:  # Ensure at least 1 day
                                time_served = 1
                        else:
                            # Still in custody, calculate from booking date to today
                            time_served = (datetime.now() - booking_date).days
                            if time_served < 0:  # Sanity check
                                time_served = 0
                    else:
                        time_served = 0
                    
                    # Add structured data for this booking
                    structured_data = {
                        "Name": f"{self.last_name}, {self.first_name}",
                        "Booking Number": booking_number,
                        "Booking Date": booking_date_str,
                        "Release Date": release_date_str if status == "Released" else "Still in custody",
                        "Status": status,
                        "Time Served (Days)": time_served,
                        "Charges": charges,
                        "Cell Location": cell_location,
                        "Raw Data": text
                    }
                    
                    self.booking_data.append(structured_data)
                    
                # Combine results into a single string
                result_text = f"Results for {self.last_name}, {self.first_name}:\n" + "\n\n".join(results) + "\n"
                
                # Log the number of results
                self.status_update.emit(f"Found {len(booking_entries)} results for {self.last_name}, {self.first_name}")
                
                # Send both the text result and structured data
                self.result_ready.emit(f"{self.last_name}, {self.first_name}", result_text, self.booking_data)
                
            # Close this driver instance
            driver.quit()
                
        except Exception as e:
            error_message = f"Error processing {self.last_name}, {self.first_name}: {str(e)}"
            logger.error(error_message)
            import traceback
            logger.error(traceback.format_exc())
            self.result_ready.emit(f"{self.last_name}, {self.first_name}", error_message, [])
            try:
                if driver:
                    driver.quit()
            except:
                pass