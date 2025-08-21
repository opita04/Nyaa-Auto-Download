"""
Settings module for Nyaa Auto Download application.
Centralizes all configuration settings and constants.
"""

import os
import sys
import json

# Application Constants
TRACKER_FILE = 'tracker.json'
SETTINGS_FILE = 'settings.json'
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

class TorrentClientConfig:
    """Configuration for torrent client selection"""

    SUPPORTED_CLIENTS = {
        'qbittorrent': 'qBittorrent',
        'default': 'System Default',
        'custom': 'Custom Command'
    }

    def __init__(self):
        self.preferred_client = 'qbittorrent'  # Default to qBittorrent
        self.custom_command = ''  # Custom command for opening magnet links
        self.fallback_to_default = True  # Fallback to system default if qBittorrent fails

    def as_dict(self):
        return {
            'preferred_client': self.preferred_client,
            'custom_command': self.custom_command,
            'fallback_to_default': self.fallback_to_default
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
class QualitySettings:
    """Settings for quality filtering preferences"""

    # Available quality options
    QUALITY_OPTIONS = [
        '360p', '480p', '720p', '1080p', '1440p', '2160p', '4K',
        'SD', 'HD', 'FHD', 'UHD', 'WEBRip', 'BluRay', 'DVD', 'HDTV'
    ]

    def __init__(self):
        # Default quality preferences (empty means no filtering)
        self.preferred_qualities = []  # List of preferred quality strings
        self.blocked_qualities = []    # List of blocked quality strings
        self.quality_filter_mode = 'preferred'  # 'preferred', 'blocked', or 'both'

    def matches_quality_filter(self, title):
        """Check if a title matches the quality filter settings"""
        if self.quality_filter_mode == 'disabled':
            return True

        title_lower = title.lower()

        # Check preferred qualities
        if self.quality_filter_mode in ['preferred', 'both'] and self.preferred_qualities:
            for quality in self.preferred_qualities:
                if quality.lower() in title_lower:
                    return True
            if self.quality_filter_mode == 'preferred':
                return False  # If preferred mode and no match, reject

        # Check blocked qualities
        if self.quality_filter_mode in ['blocked', 'both'] and self.blocked_qualities:
            for quality in self.blocked_qualities:
                if quality.lower() in title_lower:
                    return False  # Block this title

        # If we get here, either no filters or passed all checks
        return True

    def get_quality_score(self, title):
        """Get a quality score for sorting torrents (higher is better)"""
        title_lower = title.lower()
        score = 0

        # Higher scores for preferred qualities
        for preferred in self.preferred_qualities:
            if preferred.lower().strip() in title_lower:
                score += 10

        # Negative scores for blocked qualities (though these should be filtered out)
        for blocked in self.blocked_qualities:
            if blocked.lower().strip() in title_lower:
                score -= 100

        return score

    def filter_torrents(self, torrents):
        """Filter a list of torrents based on quality settings"""
        if self.quality_filter_mode == 'disabled':
            return torrents

        filtered = []
        for torrent in torrents:
            if self.matches_quality_filter(torrent.get('title', '')):
                # Add quality score for sorting
                torrent_copy = torrent.copy()
                torrent_copy['quality_score'] = self.get_quality_score(torrent.get('title', ''))
                filtered.append(torrent_copy)

        # Sort by quality score (descending) and then by row_index (more recent first)
        filtered.sort(key=lambda x: (-x.get('quality_score', 0), x.get('row_index', 999)))
        return filtered

class TestSettings:
    """Settings for testing and debugging"""

    HEADLESS_TEST_LIMIT = 2  # Limit number of entries processed in headless mode for testing


class SettingsManager:
    """Manages saving and loading of all application settings"""

    def __init__(self, settings_file=SETTINGS_FILE):
        self.settings_file = settings_file
        self._ensure_settings_directory()

    def _ensure_settings_directory(self):
        """Ensure the directory for settings file exists"""
        directory = os.path.dirname(os.path.abspath(self.settings_file))
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def save_settings(self, qb_config, torrent_config, quality_settings, check_interval):
        """Save all settings to file"""
        try:
            settings_data = {
                'qbittorrent': qb_config.as_dict(),
                'torrent_client': torrent_config.as_dict(),
                'quality_settings': {
                    'preferred_qualities': quality_settings.preferred_qualities,
                    'blocked_qualities': quality_settings.blocked_qualities,
                    'quality_filter_mode': quality_settings.quality_filter_mode
                },
                'check_interval': check_interval,
                'app_version': '1.0'  # For future compatibility checking
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)

            print(f"[INFO] Settings saved to {self.settings_file}")
            return True, ""

        except Exception as e:
            error_msg = f"Failed to save settings: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg

    def load_settings(self):
        """Load all settings from file"""
        try:
            if not os.path.exists(self.settings_file):
                print(f"[INFO] Settings file {self.settings_file} does not exist, using defaults")
                return self._get_default_settings()

            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

            # Create config objects from loaded data
            qb_config = QBittorrentConfig()
            if 'qbittorrent' in settings_data:
                qb_data = settings_data['qbittorrent']
                qb_config.host = qb_data.get('host', qb_config.host)
                qb_config.port = qb_data.get('port', qb_config.port)
                qb_config.username = qb_data.get('username', qb_config.username)
                qb_config.password = qb_data.get('password', qb_config.password)
                qb_config.category = qb_data.get('category', qb_config.category)

            torrent_config = TorrentClientConfig()
            if 'torrent_client' in settings_data:
                tc_data = settings_data['torrent_client']
                torrent_config.preferred_client = tc_data.get('preferred_client', torrent_config.preferred_client)
                torrent_config.custom_command = tc_data.get('custom_command', torrent_config.custom_command)
                torrent_config.fallback_to_default = tc_data.get('fallback_to_default', torrent_config.fallback_to_default)

            quality_settings = QualitySettings()
            if 'quality_settings' in settings_data:
                qs_data = settings_data['quality_settings']
                quality_settings.preferred_qualities = qs_data.get('preferred_qualities', quality_settings.preferred_qualities)
                quality_settings.blocked_qualities = qs_data.get('blocked_qualities', quality_settings.blocked_qualities)
                quality_settings.quality_filter_mode = qs_data.get('quality_filter_mode', quality_settings.quality_filter_mode)

            check_interval = settings_data.get('check_interval', DEFAULT_INTERVAL)

            print(f"[INFO] Settings loaded from {self.settings_file}")
            return qb_config, torrent_config, quality_settings, check_interval

        except Exception as e:
            error_msg = f"Failed to load settings: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return self._get_default_settings()

    def _get_default_settings(self):
        """Get default settings when file doesn't exist or is corrupted"""
        return (
            QBittorrentConfig(),
            TorrentClientConfig(),
            QualitySettings(),
            DEFAULT_INTERVAL
        )

    def backup_settings(self, backup_path=None):
        """Create a backup of current settings"""
        try:
            if backup_path is None:
                backup_path = f"{self.settings_file}.backup"

            if os.path.exists(self.settings_file):
                import shutil
                shutil.copy2(self.settings_file, backup_path)
                print(f"[INFO] Settings backup created: {backup_path}")
                return True, backup_path
            else:
                return False, "No settings file to backup"

        except Exception as e:
            return False, f"Backup failed: {str(e)}"

    def restore_settings(self, backup_path=None):
        """Restore settings from backup"""
        try:
            if backup_path is None:
                backup_path = f"{self.settings_file}.backup"

            if not os.path.exists(backup_path):
                return False, f"Backup file not found: {backup_path}"

            import shutil
            shutil.copy2(backup_path, self.settings_file)
            print(f"[INFO] Settings restored from: {backup_path}")
            return True, backup_path

        except Exception as e:
            return False, f"Restore failed: {str(e)}"

    def export_settings(self, export_path):
        """Export settings to a specific path"""
        try:
            if os.path.exists(self.settings_file):
                import shutil
                shutil.copy2(self.settings_file, export_path)
                print(f"[INFO] Settings exported to: {export_path}")
                return True, export_path
            else:
                return False, "No settings file to export"

        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def import_settings(self, import_path):
        """Import settings from a specific path"""
        try:
            if not os.path.exists(import_path):
                return False, f"Import file not found: {import_path}"

            import shutil
            shutil.copy2(import_path, self.settings_file)
            print(f"[INFO] Settings imported from: {import_path}")
            return True, import_path

        except Exception as e:
            return False, f"Import failed: {str(e)}"
