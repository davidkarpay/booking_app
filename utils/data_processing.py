"""
Data processing utilities for the PBSO Booking Blotter
"""
from datetime import datetime

def validate_record(record):
    """
    Validate and clean a booking record
    
    Args:
        record: A booking record dictionary
        
    Returns:
        dict: Cleaned and validated record, or None if invalid
    """
    if not isinstance(record, dict):
        return None
    
    # Check for required fields
    required_fields = ["Name", "Booking Number", "Status"]
    for field in required_fields:
        if field not in record:
            return None
    
    # Clean and validate fields
    clean_record = {}
    
    # Copy all fields
    for key, value in record.items():
        clean_record[key] = value
    
    # Handle time served calculation
    if "Time Served (Days)" not in clean_record:
        booking_date_str = clean_record.get("Booking Date")
        release_date_str = clean_record.get("Release Date")
        
        booking_date = parse_date(booking_date_str)
        release_date = parse_date(release_date_str)
        
        if booking_date:
            if release_date:
                time_served = (release_date - booking_date).days + 1
            else:
                time_served = (datetime.now() - booking_date).days + 1
            
            clean_record["Time Served (Days)"] = time_served
    
    return clean_record

def parse_date(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return None
    
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y", "%m/%d/%y %H:%M", "%m/%d/%y"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    
    return None

def group_by_name(records):
    """
    Group records by name
    
    Args:
        records: List of booking record dictionaries
        
    Returns:
        dict: Dictionary with names as keys and lists of records as values
    """
    name_groups = {}
    
    for record in records:
        if not isinstance(record, dict):
            continue
            
        name = record.get("Name", "Unknown")
        if name not in name_groups:
            name_groups[name] = []
        
        name_groups[name].append(record)
    
    return name_groups

def get_statistics(records):
    """
    Calculate statistics from booking records
    
    Args:
        records: List of booking record dictionaries
        
    Returns:
        dict: Dictionary with statistical information
    """
    if not records:
        return {
            "total": 0,
            "in_custody": 0,
            "released": 0,
            "avg_days": 0,
            "max_days": 0,
            "min_days": 0,
            "unique_names": 0
        }
    
    # Basic counts
    total = len(records)
    in_custody_count = sum(1 for r in records if r.get("Status") == "In Custody")
    released_count = sum(1 for r in records if r.get("Status") == "Released")
    
    # Time served statistics
    days_served = []
    for record in records:
        days = record.get("Time Served (Days)")
        if isinstance(days, (int, float)) and days > 0:
            days_served.append(days)
    
    avg_days = sum(days_served) / len(days_served) if days_served else 0
    max_days = max(days_served) if days_served else 0
    min_days = min(days_served) if days_served else 0
    
    # Count unique names
    unique_names = len(group_by_name(records))
    
    return {
        "total": total,
        "in_custody": in_custody_count,
        "released": released_count,
        "avg_days": round(avg_days, 1),
        "max_days": max_days,
        "min_days": min_days,
        "unique_names": unique_names
    }

def filter_records(records, text_filter=None, filter_field=None, status_filter=None):
    """
    Filter records based on criteria
    
    Args:
        records: List of booking record dictionaries
        text_filter: Text to filter by (case-insensitive)
        filter_field: Field to apply text filter to, or None for all fields
        status_filter: Status to filter by (In Custody, Released, or None for all)
        
    Returns:
        list: Filtered list of records
    """
    if not records:
        return []
    
    # Convert text filter to lowercase for case-insensitive comparison
    if text_filter:
        text_filter = text_filter.lower()
    
    filtered_records = []
    
    for record in records:
        # Skip invalid records
        if not isinstance(record, dict):
            continue
        
        # Apply status filter if specified
        if status_filter and record.get("Status") != status_filter:
            continue
        
        # Apply text filter if specified
        if text_filter:
            if filter_field:
                # Filter specific field
                field_value = record.get(filter_field, "")
                if not field_value or text_filter not in str(field_value).lower():
                    continue
            else:
                # Filter all fields
                field_match = False
                for key, value in record.items():
                    if key == "Raw Data":  # Skip raw data, too large
                        continue
                    if text_filter in str(value).lower():
                        field_match = True
                        break
                if not field_match:
                    continue
        
        # If we got here, the record passed all filters
        filtered_records.append(record)
    
    return filtered_records

def sort_records(records, sort_field, ascending=True):
    """
    Sort records by a specified field
    
    Args:
        records: List of booking record dictionaries
        sort_field: Field to sort by
        ascending: True for ascending order, False for descending
        
    Returns:
        list: Sorted list of records
    """
    if not records or not sort_field:
        return records
    
    # Define a key function that handles missing values and different types
    def sort_key(record):
        value = record.get(sort_field)
        
        # Handle missing values - they should come last in sorting
        if value is None:
            return "" if ascending else "zzzzzzz"
        
        # Handle days served as numbers
        if sort_field == "Time Served (Days)" and isinstance(value, (int, float)):
            return value
        
        # Handle dates (convert to datetime objects)
        if sort_field in ["Booking Date", "Release Date"]:
            date_obj = parse_date(value)
            if date_obj:
                return date_obj
        
        # Default to string comparison
        return str(value).lower()
    
    # Sort the records
    sorted_records = sorted(records, key=sort_key, reverse=not ascending)
    return sorted_records