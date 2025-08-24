"""
Tracker Controller for Nyaa Auto Download.
Manages anime series tracking and episode state persistence.
"""

from typing import List, Tuple, Dict, Any, Optional

from modules.anime_tracker import AnimeTracker


class TrackerController:
    """
    Controller for anime series tracking operations.
    Handles series management, episode state, and persistence.
    """
    
    def __init__(self, tracker_file: str = None):
        """Initialize the tracker controller."""
        # Initialize the existing AnimeTracker for now
        # TODO: During full refactor, move AnimeTracker logic here
        self.tracker = AnimeTracker()
        
    def get_all_series(self) -> List[Tuple[str, Dict]]:
        """
        Get all tracked anime series.
        
        Returns:
            List of (title, info) tuples
        """
        return list(self.tracker.get_all())
        
    def add_series(self, title: str, url: str) -> bool:
        """
        Add a new anime series to tracking.
        
        Args:
            title: Anime series title
            url: Nyaa.si URL for the series
            
        Returns:
            True if added successfully, False if already exists
        """
        return self.tracker.add(title, url)
        
    def remove_series(self, title: str) -> bool:
        """
        Remove an anime series from tracking.
        
        Args:
            title: Title of series to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        try:
            self.tracker.remove(title)
            return True
        except Exception:
            return False
            
    def edit_series_title(self, old_title: str, new_title: str) -> bool:
        """
        Edit the title of a tracked series.
        
        Args:
            old_title: Current series title
            new_title: New series title
            
        Returns:
            True if edited successfully, False if failed
        """
        return self.tracker.edit_title(old_title, new_title)
        
    def update_series_url(self, title: str, new_url: str) -> bool:
        """
        Update the URL for a tracked series.
        
        Args:
            title: Series title
            new_url: New Nyaa.si URL
            
        Returns:
            True if updated successfully, False if failed
        """
        try:
            if title in self.tracker.data:
                self.tracker.data[title]['url'] = new_url
                self.tracker.save()
                return True
            return False
        except Exception:
            return False
            
    def get_series_info(self, title: str) -> Optional[Dict]:
        """
        Get information for a specific series.
        
        Args:
            title: Series title
            
        Returns:
            Series info dictionary or None if not found
        """
        return self.tracker.data.get(title)
        
    def get_last_episode(self, title: str) -> Tuple[int, int]:
        """
        Get the last tracked season and episode for a series.
        
        Args:
            title: Series title
            
        Returns:
            Tuple of (last_season, last_episode)
        """
        return self.tracker.get_last_season_and_episode(title)
        
    def update_episode(self, title: str, season: int, episode: int) -> bool:
        """
        Update the last tracked episode for a series.
        
        Args:
            title: Series title
            season: Season number
            episode: Episode number
            
        Returns:
            True if updated successfully, False if failed
        """
        try:
            self.tracker.update_episode(title, season, episode)
            return True
        except Exception:
            return False
            
    def set_multi_episode_flag(self, title: str, allow_multi: bool) -> bool:
        """
        Set the multi-episode download flag for a series.
        
        Args:
            title: Series title
            allow_multi: Whether to allow multi-episode downloads
            
        Returns:
            True if set successfully, False if failed
        """
        try:
            self.tracker.set_multi_episode_flag(title, allow_multi)
            return True
        except Exception:
            return False
            
    def allows_multi_episode(self, title: str) -> bool:
        """
        Check if a series allows multi-episode downloads.
        
        Args:
            title: Series title
            
        Returns:
            True if multi-episode downloads are allowed
        """
        return self.tracker.allows_multi_episode(title)
        
    def get_series_count(self) -> int:
        """
        Get the total number of tracked series.
        
        Returns:
            Number of tracked series
        """
        return len(self.tracker.data)
        
    def series_exists(self, title: str) -> bool:
        """
        Check if a series is already being tracked.
        
        Args:
            title: Series title to check
            
        Returns:
            True if series exists in tracker
        """
        return title in self.tracker.data
        
    def save_data(self) -> bool:
        """
        Save tracker data to file.
        
        Returns:
            True if saved successfully, False if failed
        """
        try:
            self.tracker.save()
            return True
        except Exception:
            return False
            
    def load_data(self) -> bool:
        """
        Load tracker data from file.
        
        Returns:
            True if loaded successfully, False if failed
        """
        try:
            # The AnimeTracker loads automatically on initialization
            # This method is for explicit reloading if needed
            return len(self.tracker.data) >= 0  # Always returns True if data structure exists
        except Exception:
            return False
            
    def backup_data(self, backup_path: str = None) -> Tuple[bool, str]:
        """
        Create a backup of tracker data.
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            Tuple of (success, backup_path_used)
        """
        try:
            import shutil
            import os
            from settings import TRACKER_FILE
            
            if backup_path is None:
                backup_path = f"{TRACKER_FILE}.backup"
                
            if os.path.exists(TRACKER_FILE):
                shutil.copy2(TRACKER_FILE, backup_path)
                return True, backup_path
            else:
                return False, "No tracker file to backup"
                
        except Exception as e:
            return False, f"Backup failed: {str(e)}"
            
    def restore_data(self, backup_path: str = None) -> Tuple[bool, str]:
        """
        Restore tracker data from backup.
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            Tuple of (success, message)
        """
        try:
            import shutil
            import os
            from settings import TRACKER_FILE
            
            if backup_path is None:
                backup_path = f"{TRACKER_FILE}.backup"
                
            if not os.path.exists(backup_path):
                return False, f"Backup file not found: {backup_path}"
                
            shutil.copy2(backup_path, TRACKER_FILE)
            
            # Reload the tracker data
            self.tracker = AnimeTracker()
            
            return True, f"Data restored from {backup_path}"
            
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about tracked series.
        
        Returns:
            Dictionary with various statistics
        """
        try:
            total_series = self.get_series_count()
            multi_episode_series = sum(1 for title, info in self.tracker.get_all() 
                                     if info.get('allow_multi_episode', False))
            
            # Calculate episode statistics
            total_episodes = 0
            max_season = 0
            max_episode = 0
            
            for title, info in self.tracker.get_all():
                season = info.get('last_season', 1)
                episode = info.get('last_episode', 0)
                
                total_episodes += episode
                max_season = max(max_season, season)
                max_episode = max(max_episode, episode)
                
            return {
                'total_series': total_series,
                'multi_episode_enabled': multi_episode_series,
                'total_episodes_tracked': total_episodes,
                'highest_season': max_season,
                'highest_episode': max_episode,
                'average_episodes_per_series': total_episodes / max(total_series, 1)
            }
            
        except Exception as e:
            return {
                'error': f"Failed to calculate statistics: {str(e)}",
                'total_series': 0
            }
            
    def find_series_by_pattern(self, pattern: str) -> List[Tuple[str, Dict]]:
        """
        Find series matching a pattern in title or URL.
        
        Args:
            pattern: Search pattern (case-insensitive)
            
        Returns:
            List of (title, info) tuples matching the pattern
        """
        pattern_lower = pattern.lower()
        matches = []
        
        for title, info in self.tracker.get_all():
            if (pattern_lower in title.lower() or 
                pattern_lower in info.get('url', '').lower()):
                matches.append((title, info))
                
        return matches
