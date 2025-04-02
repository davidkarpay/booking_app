"""
Parallel scraper implementation for the PBSO Booking Blotter
"""
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtCore import QThread, pyqtSignal, QMutex

from scrapers.worker import ScraperWorker
from logger import logger

# Mutex for thread-safe result accumulation
result_mutex = QMutex()

class PBSOParallelScraper(QThread):
    """Main scraper controller that manages multiple worker threads"""
    search_complete = pyqtSignal(str)
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)  # completed, total
    data_ready = pyqtSignal(list)  # Signal for structured data ready for export
    
    def __init__(self, username, password, names_list, max_workers, min_delay, max_delay):
        super().__init__()
        self.username = username
        self.password = password
        self.names_list = names_list
        self.max_workers = max_workers
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.results = {}
        self.all_booking_data = []  # Consolidated data for export
        self.completed_count = 0
        self.total_count = len(names_list)
    
    def run(self):
        self.status_update.emit("Starting parallel searches...")
        logger.info(f"Starting parallel searches with {self.max_workers} workers")
        
        # Using ThreadPoolExecutor to limit the number of concurrent workers
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            workers = []
            
            # Create a worker for each name
            for last_name, first_name in self.names_list:
                worker = ScraperWorker(
                    self.username, 
                    self.password,
                    last_name,
                    first_name,
                    self.min_delay,
                    self.max_delay
                )
                worker.result_ready.connect(self.handle_result)
                worker.status_update.connect(self.relay_status)
                workers.append(worker)
                
            # Start all workers
            for worker in workers:
                worker.start()
            
            # Wait for all workers to complete
            for worker in workers:
                worker.wait()
        
        # Compile final results
        accumulated_results = ""
        for name in sorted(self.results.keys()):
            accumulated_results += self.results[name] + "\n" + "-"*50 + "\n\n"
        
        # Signal that search is complete and data is ready for export
        self.search_complete.emit(accumulated_results)
        self.data_ready.emit(self.all_booking_data)
        
        # Update status
        records_found = len(self.all_booking_data)
        self.status_update.emit(f"All searches complete. Found {records_found} booking records.")
        logger.info(f"All searches complete. Found {records_found} booking records.")
    
    def handle_result(self, name, result, booking_data):
        """
        Enhanced version of handle_result with better logging and data validation.
        Handles results from worker threads in a thread-safe manner.
        """
        # Log the incoming data
        logger.info(f"Received {len(booking_data)} records for {name}")
        
        if not booking_data:
            logger.warning(f"No booking data received for {name}")
        
        # Thread-safe update of results
        result_mutex.lock()
        try:
            self.results[name] = result
            
            # Add name to booking data if not present (data integrity check)
            for record in booking_data:
                if isinstance(record, dict) and "Name" not in record:
                    record["Name"] = name
            
            # Validate each record before adding it
            valid_records = []
            for i, record in enumerate(booking_data):
                if not isinstance(record, dict):
                    logger.error(f"Record {i} for {name} is not a dictionary: {type(record)}")
                    continue
                    
                # Check for required fields
                required_fields = ["Booking Number", "Status"]
                missing = [field for field in required_fields if field not in record]
                
                if missing:
                    logger.warning(f"Record {i} for {name} missing fields: {', '.join(missing)}")
                    # Try to repair record with minimum required fields
                    for field in missing:
                        if field == "Booking Number":
                            record[field] = f"Unknown-{i}"
                        elif field == "Status":
                            # Infer status based on Release Date presence
                            if "Release Date" in record and record["Release Date"] and record["Release Date"] != "N/A":
                                record["Status"] = "Released"
                            else:
                                record["Status"] = "In Custody"
                
                valid_records.append(record)
            
            # Add valid records
            self.all_booking_data.extend(valid_records)
            
            # Log a summary
            in_custody = sum(1 for r in valid_records if r.get("Status") == "In Custody")
            released = sum(1 for r in valid_records if r.get("Status") == "Released")
            logger.info(f"Added {len(valid_records)} records for {name} (In Custody: {in_custody}, Released: {released})")
            
            # Update completed count
            self.completed_count += 1
        except Exception as e:
            logger.error(f"Error processing results for {name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            result_mutex.unlock()
        
        # Update progress
        self.progress_update.emit(self.completed_count, self.total_count)
        
        completion_percentage = int((self.completed_count / self.total_count) * 100)
        self.status_update.emit(f"Progress: {completion_percentage}% ({self.completed_count}/{self.total_count}) - Total records: {len(self.all_booking_data)}")
    
    def relay_status(self, status):
        """Relay status messages from worker threads"""
        self.status_update.emit(status)