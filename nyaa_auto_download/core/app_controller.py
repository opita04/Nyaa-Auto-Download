"""
Application Controller for Nyaa Auto Download.
Handles application lifecycle, settings management, and background tasks.
"""

import threading
import time
from datetime import datetime
from typing import Optional, Tuple, Any

from settings import SettingsManager, QBittorrentConfig, TorrentClientConfig, QualitySettings
from modules.qbittorrent_client import QBittorrentClient
from .torrent_controller import TorrentController
from .tracker_controller import TrackerController


class AppController:
    """
    Main application controller handling business logic coordination.
    Manages settings, background tasks, and client connections.
    """
    
    def __init__(self):
        """Initialize the application controller."""
        self.settings_manager = SettingsManager()
        self.tracker_controller = TrackerController()
        self.torrent_controller: Optional[TorrentController] = None
        
        # Configuration objects
        self.qb_config = QBittorrentConfig()
        self.torrent_config = TorrentClientConfig()
        self.quality_settings = QualitySettings()
        self.check_interval = 3600  # 1 hour default
        
        # Threading
        self.stop_event = threading.Event()
        self.check_thread: Optional[threading.Thread] = None
        self.health_check_thread: Optional[threading.Thread] = None
        
        # Callbacks for UI updates
        self.on_log_message: Optional[callable] = None
        self.on_connection_status_changed: Optional[callable] = None
        self.on_settings_status_changed: Optional[callable] = None
        
        # Initialize with default settings
        self._load_settings()
        self._initialize_torrent_controller()
        
    def _initialize_torrent_controller(self):
        """Initialize the torrent controller with current settings."""
        self.torrent_controller = TorrentController(
            self.torrent_config, 
            self.qb_config,
            self.quality_settings
        )
        
    def set_callbacks(self, log_callback=None, connection_callback=None, settings_callback=None):
        """Set callback functions for UI updates."""
        self.on_log_message = log_callback
        self.on_connection_status_changed = connection_callback
        self.on_settings_status_changed = settings_callback
        
    def _log(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f'[{timestamp}] {message}'
        
        if self.on_log_message:
            self.on_log_message(log_entry)
        else:
            print(log_entry)
            
    # Settings Management
    def _load_settings(self) -> bool:
        """Load settings from file. Returns True if successful."""
        try:
            self.qb_config, self.torrent_config, self.quality_settings, self.check_interval = \
                self.settings_manager.load_settings()
            
            self._log('Settings loaded successfully.')
            if self.on_settings_status_changed:
                self.on_settings_status_changed('Settings loaded!')
            return True
            
        except Exception as e:
            self._log(f'Failed to load settings: {e}. Using defaults.')
            if self.on_settings_status_changed:
                self.on_settings_status_changed('Using default settings', error=True)
            return False
            
    def save_settings(self) -> Tuple[bool, str]:
        """Save current settings to file. Returns (success, error_message)."""
        try:
            success, error_msg = self.settings_manager.save_settings(
                self.qb_config, self.torrent_config, self.quality_settings, self.check_interval
            )
            
            if success:
                self._log('Settings saved successfully.')
                if self.on_settings_status_changed:
                    self.on_settings_status_changed('Settings saved!')
                # Reinitialize torrent controller with new settings
                self._initialize_torrent_controller()
                return True, ""
            else:
                self._log(f'Failed to save settings: {error_msg}')
                if self.on_settings_status_changed:
                    self.on_settings_status_changed(f'Failed to save settings: {error_msg}', error=True)
                return False, error_msg
                
        except Exception as e:
            error_msg = str(e)
            self._log(f'Failed to save settings: {error_msg}')
            if self.on_settings_status_changed:
                self.on_settings_status_changed(f'Failed to save settings: {error_msg}', error=True)
            return False, error_msg
            
    def update_settings(self, qb_config, torrent_config, quality_settings, check_interval):
        """Update settings and reinitialize controllers."""
        self.qb_config = qb_config
        self.torrent_config = torrent_config
        self.quality_settings = quality_settings
        self.check_interval = check_interval
        
        # Reinitialize torrent controller
        self._initialize_torrent_controller()
        
        # Save settings
        return self.save_settings()
        
    # Connection Management
    def test_connection(self) -> Tuple[bool, str]:
        """Test the current torrent client connection."""
        if not self.torrent_controller:
            return False, "Torrent controller not initialized"
            
        return self.torrent_controller.test_connection()
        
    def _check_connection_health(self):
        """Check connection health and update status."""
        available, error_msg = self.test_connection()
        
        if self.on_connection_status_changed:
            self.on_connection_status_changed(available, error_msg)
            
    # Background Tasks
    def start_background_tasks(self):
        """Start periodic checking and health monitoring."""
        self.stop_event.clear()
        
        # Start periodic episode checking
        if not self.check_thread or not self.check_thread.is_alive():
            self.check_thread = threading.Thread(target=self._periodic_check_loop, daemon=True)
            self.check_thread.start()
            self._log("Started periodic checking.")
            
        # Start connection health monitoring
        if not self.health_check_thread or not self.health_check_thread.is_alive():
            self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_check_thread.start()
            self._log("Started connection health monitoring.")
            
    def stop_background_tasks(self):
        """Stop all background tasks."""
        self.stop_event.set()
        self._log("Background tasks stopped.")
        
    def _periodic_check_loop(self):
        """Background loop for periodic episode checking."""
        while not self.stop_event.is_set():
            try:
                self._check_all_series()
            except Exception as e:
                self._log(f'Error in periodic check: {e}')
                
            # Wait for check interval or until stopped
            for _ in range(self.check_interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
                
    def _health_check_loop(self):
        """Background loop for connection health monitoring."""
        while not self.stop_event.is_set():
            try:
                self._check_connection_health()
            except Exception as e:
                self._log(f'Error in health check: {e}')
                
            # Check every 5 minutes
            for _ in range(300):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
                
    # Episode Checking
    def force_check_all(self):
        """Manually trigger a check for all series."""
        self._log('Manual check triggered.')
        threading.Thread(target=self._check_all_series, daemon=True).start()
        
    def _check_all_series(self):
        """Check all tracked series for new episodes."""
        self._log('Checking for new episodes...')
        
        # Test connection first
        available, error_msg = self.test_connection()
        if not available:
            self._log(f'Torrent client connection failed: {error_msg}')
            self._check_connection_health()  # Update UI status
            return
            
        # Get all tracked series
        all_series = self.tracker_controller.get_all_series()
        
        for title, info in all_series:
            try:
                result = self._check_series(title, info)
                if result:
                    self._log(f'New episode for {title}: {result}')
                else:
                    self._log(f'No new episode for {title}.')
                    
            except Exception as e:
                self._log(f'Error checking {title}: {e}')
                
    def _check_series(self, title: str, info: dict) -> Optional[str]:
        """Check a single series for new episodes. Returns episode info if found."""
        url = info['url']
        last_season, last_episode = self.tracker_controller.get_last_episode(title)
        
        # Use torrent controller to check for new episodes
        latest_season, latest_episode, magnet = self.torrent_controller.get_latest_episode(
            url, title, last_season, last_episode
        )
        
        if latest_episode is None or magnet is None:
            return None
            
        # Check if this is a new episode
        if latest_season > last_season or (latest_season == last_season and latest_episode > last_episode):
            # Try to download the new episode
            success, error_msg = self.torrent_controller.download_magnet(magnet)
            
            if success:
                # Update tracker with new episode
                self.tracker_controller.update_episode(title, latest_season, latest_episode)
                return f'S{latest_season:02d}E{latest_episode:02d}'
            else:
                self._log(f'Failed to download {title}: {error_msg}')
                return None
                
        return None
        
    # Headless Mode Support
    def run_headless_check(self) -> bool:
        """Run a single check in headless mode. Returns True if successful."""
        try:
            self._log("Starting headless mode check...")
            
            # Load tracker data
            all_series = self.tracker_controller.get_all_series()
            if not all_series:
                self._log("No anime series found in tracker.")
                return True
                
            # Test connection (optional in headless mode)
            available, error_msg = self.test_connection()
            if not available:
                self._log(f"Warning: Torrent client not available: {error_msg}")
                
            # Check series (limit for testing)
            checked_count = 0
            max_check = min(5, len(all_series))  # Limit for safety
            
            for title, info in list(all_series)[:max_check]:
                try:
                    result = self._check_series(title, info)
                    checked_count += 1
                    
                    if result:
                        self._log(f"New episode found for {title}: {result}")
                    else:
                        self._log(f"No new episode for {title}")
                        
                except Exception as e:
                    self._log(f"Error checking {title}: {e}")
                    
            self._log(f"Headless check completed. Checked {checked_count} series.")
            return True
            
        except Exception as e:
            self._log(f"Fatal error in headless mode: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def shutdown(self):
        """Clean shutdown of the application controller."""
        self._log("Shutting down application controller...")
        self.stop_background_tasks()
        
        # Wait for threads to finish (with timeout)
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(timeout=2)
            
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=2)
            
        self._log("Application controller shutdown complete.")
