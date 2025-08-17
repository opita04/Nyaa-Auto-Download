import logging
import sys
import os
from settings import LOG_DIRECTORY


def setup_logging():
    """Set up logging for both console and file"""
    
    # Ensure log directory exists
    os.makedirs(LOG_DIRECTORY, exist_ok=True)
    
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File logger
    log_file = os.path.join(LOG_DIRECTORY, 'nyaa_scraper_debug.log')
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Console logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_file


def create_trace_file():
    """Create and return the trace file path"""
    os.makedirs(LOG_DIRECTORY, exist_ok=True)
    trace_path = os.path.join(LOG_DIRECTORY, 'log_trace.txt')
    with open(trace_path, 'a') as f:
        f.write('TOP OF FILE\n')
    return trace_path
