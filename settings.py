"""
Settings module for Nyaa Auto Download application.
Centralizes all configuration settings and constants.
"""

import os
import sys

# Application Constants
TRACKER_FILE = 'tracker.json'
DEFAULT_INTERVAL = 1 * 60 * 60  # 1 hour (changed from 24 hours)

# Directory Configuration
def get_log_directory():
    """Get the appropriate log directory based on whether app is frozen or not"""
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'logs')

LOG_DIRECTORY = get_log_directory()

def get_trace_path():
    """Get the trace log file path"""
    return os.path.join(LOG_DIRECTORY, 'log_trace.txt')

TRACE_PATH = get_trace_path()

# GUI Configuration
class GUISettings:
    """GUI-related settings and constants"""
    
    # Main window
    WINDOW_TITLE = 'Nyaa.si Anime Auto Downloader'
    MAIN_PADDING = '10'
    
    # Treeview columns
    ANIME_TREE_COLUMNS = ('Title', 'Last Season', 'Last Episode', 'URL')
    ANIME_TREE_HEADINGS = {
        'Title': 'Title',
        'Last Season': 'S', 
        'Last Episode': 'Last Ep',
        'URL': 'Nyaa.si URL'
    }
    ANIME_TREE_WIDTHS = {
        'Title': 150,
        'Last Season': 40,
        'Last Episode': 80, 
        'URL': 350
    }
    
    # Episodes treeview
    EPISODES_TREE_COLUMNS = ('Episode', 'Size', 'DateTime', 'Seeders', 'Leechers')
    EPISODES_TREE_HEADINGS = {
        '#0': 'Title',
        'Episode': 'Ep',
        'Size': 'Size',
        'DateTime': 'Date/Time',
        'Seeders': 'S',
        'Leechers': 'L'
    }
    EPISODES_TREE_WIDTHS = {
        '#0': 250,
        'Episode': 50,
        'Size': 80,
        'DateTime': 120,
        'Seeders': 40,
        'Leechers': 40
    }
    
    # Entry field widths
    TITLE_ENTRY_WIDTH = 30
    URL_ENTRY_WIDTH = 50
    QB_HOST_WIDTH = 15
    QB_PORT_WIDTH = 6
    QB_USER_WIDTH = 15
    QB_PASS_WIDTH = 15
    QB_CAT_WIDTH = 15
    INTERVAL_WIDTH = 6
    SEARCH_ENTRY_WIDTH = 30
    
    # Log text height
    LOG_TEXT_HEIGHT = 10
    EPISODES_TREE_HEIGHT = 15
    ANIME_TREE_HEIGHT = 8

class QBittorrentConfig:
    """qBittorrent configuration settings"""
    
    def __init__(self):
        self.host = 'localhost'
        self.port = 8080
        self.username = 'admin'
        self.password = 'adminadmin'
        self.category = ''

    def as_dict(self):
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'category': self.category
        }

# Network Configuration
class NetworkSettings:
    """Network-related configuration"""
    
    REQUEST_TIMEOUT = 15
    QB_CONNECT_TIMEOUT = 5
    QB_READ_TIMEOUT = 10
    
    # Nyaa.si URLs and parameters
    NYAA_BASE_URL = "https://nyaa.si"
    NYAA_SEARCH_URL = "https://nyaa.si/?f=0&c=0_0&q={}&s=seeders&o=desc"

# Scraper Configuration  
class ScraperSettings:
    """Settings for web scraping functionality"""
    
    # Episode regex patterns and formats
    EPISODE_FORMATS = [
        r'(?:S(\d{1,2})E(\d{1,4}))',  # S01E01 format
        r'\((\d{1,4})-(\d{1,4})\)',   # Episode ranges in parentheses
        r'\b(\d{1,4})-(\d{1,4})\b(?!\d)',  # Episode ranges without parentheses
        r'\b(?:ep?\.?|episode)\s*(\d{1,4})-(\d{1,4})\b',  # Episode ranges with markers
        r'\((\d{1,4})\)',  # Single episodes in parentheses
        r'- (\d{1,4})(?=\s|\.|\[|$)',  # Dash-separated episodes
        r'\b(?:ep?\.?|episode)\s*(\d{1,4})\b',  # Explicit episode markers
    ]
    
    # Size units for parsing
    SIZE_UNITS = {
        'GB': 1024 * 1024 * 1024,
        'MB': 1024 * 1024,
        'KB': 1024,
    }

# Logging Settings
class LoggingSettings:
    """Logging configuration"""
    
    DEBUG_LOG_FILE = 'nyaa_scraper_debug.log'
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

# Dialog Settings
class DialogSettings:
    """Settings for dialog windows"""
    
    EDIT_DIALOG_SIZE = '400x220'
    ADD_DIALOG_SIZE = '400x220'
    
    @staticmethod
    def center_dialog(dialog):
        """Center a dialog window on screen"""
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

# Test Configuration
class TestSettings:
    """Settings for testing and debugging"""
    
    HEADLESS_TEST_LIMIT = 2  # Limit number of entries processed in headless mode for testing
