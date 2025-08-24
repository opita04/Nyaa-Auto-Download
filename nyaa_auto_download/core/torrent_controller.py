"""
Torrent Controller for Nyaa Auto Download.
Handles torrent client interactions and magnet link processing.
"""

from typing import Optional, Tuple, List, Dict, Any

from settings import TorrentClientConfig, QBittorrentConfig, QualitySettings
from modules.generic_torrent_client import GenericTorrentClient
from modules.nyaa_scraper import NyaaScraper


class TorrentController:
    """
    Controller for torrent operations.
    Handles client interactions, magnet processing, and quality filtering.
    """
    
    def __init__(self, torrent_config: TorrentClientConfig, qb_config: QBittorrentConfig, quality_settings: QualitySettings):
        """Initialize the torrent controller with configuration."""
        self.torrent_config = torrent_config
        self.qb_config = qb_config
        self.quality_settings = quality_settings
        
        # Initialize generic torrent client
        self.torrent_client = GenericTorrentClient(self.torrent_config)
        
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to the configured torrent client."""
        try:
            return self.torrent_client.test_connection()
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
            
    def download_magnet(self, magnet_link: str, category: str = None) -> Tuple[bool, str]:
        """
        Download a torrent via magnet link using the configured client.
        
        Args:
            magnet_link: The magnet link to download
            category: Optional category for the torrent
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if category is None:
                category = self.qb_config.category
                
            return self.torrent_client.launch_magnet(magnet_link, category)
        except Exception as e:
            return False, f"Download failed: {str(e)}"
            
    def get_latest_episode(self, url: str, title: str, last_season: int, last_episode: int) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Get the latest episode and magnet link from a Nyaa.si URL.
        
        Args:
            url: Nyaa.si URL to scrape
            title: Anime title for filtering
            last_season: Last tracked season
            last_episode: Last tracked episode
            
        Returns:
            Tuple of (latest_season, latest_episode, magnet_link)
        """
        try:
            # Use existing scraper but with quality settings applied
            # TODO: This is a temporary bridge - the scraper will be refactored later
            # For now, we'll use the existing NyaaScraper directly
            
            # This is a placeholder that delegates to the existing scraper
            # The actual implementation will be moved here during full refactor
            from modules.anime_tracker import AnimeTracker
            temp_tracker = AnimeTracker()  # Temporary for compatibility
            
            latest_season, latest_episode, magnet = NyaaScraper.get_latest_episode_and_magnet(
                url, title, temp_tracker, self.quality_settings
            )
            
            return latest_season, latest_episode, magnet
            
        except Exception as e:
            print(f"Error getting latest episode for {title}: {e}")
            return None, None, None
            
    def get_all_episodes(self, url: str, title: str) -> List[Dict[str, Any]]:
        """
        Get all available episodes from a Nyaa.si URL.
        
        Args:
            url: Nyaa.si URL to scrape
            title: Anime title for filtering
            
        Returns:
            List of episode dictionaries with metadata
        """
        try:
            # Use existing scraper with quality filtering
            from modules.anime_tracker import AnimeTracker
            temp_tracker = AnimeTracker()  # Temporary for compatibility
            
            episodes = NyaaScraper.get_all_episodes(url, title, temp_tracker)
            
            # Apply quality filtering if enabled
            if self.quality_settings.quality_filter_mode != 'disabled':
                episodes = self.quality_settings.filter_torrents(episodes)
                
            return episodes
            
        except Exception as e:
            print(f"Error getting episodes for {title}: {e}")
            return []
            
    def search_nyaa(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Nyaa.si for torrents matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of search result dictionaries
        """
        try:
            results = NyaaScraper.search(query, self.quality_settings)
            
            # Apply quality filtering
            if self.quality_settings.quality_filter_mode != 'disabled':
                results = self.quality_settings.filter_torrents(results)
                
            return results
            
        except Exception as e:
            print(f"Error searching Nyaa.si: {e}")
            return []
            
    def gather_all_latest_torrents(self, tracker_data: List[Tuple[str, Dict]]) -> List[Dict[str, Any]]:
        """
        Gather latest torrents from all tracked series.
        
        Args:
            tracker_data: List of (title, info) tuples from tracker
            
        Returns:
            List of torrent dictionaries with metadata
        """
        all_torrents = []
        
        for title, info in tracker_data:
            try:
                url = info['url']
                last_season = info.get('last_season', 1)
                last_episode = info.get('last_episode', 0)
                
                latest_season, latest_episode, magnet = self.get_latest_episode(
                    url, title, last_season, last_episode
                )
                
                if latest_episode is not None and magnet is not None:
                    # Determine if this is a new episode
                    is_new = (latest_season > last_season or 
                             (latest_season == last_season and latest_episode > last_episode))
                    
                    status = "NEW" if is_new else "Current"
                    
                    torrent_info = {
                        'title': title,
                        'series_title': title,
                        'episode_info': f'S{latest_season:02d}E{latest_episode:02d}',
                        'magnet': magnet,
                        'season': latest_season,
                        'episode': latest_episode,
                        'current_season': last_season,
                        'current_episode': last_episode,
                        'status': status,
                        'is_new': is_new
                    }
                    
                    all_torrents.append(torrent_info)
                    
            except Exception as e:
                print(f'Error gathering torrents for {title}: {e}')
                continue
                
        return all_torrents
        
    def extract_quality_from_title(self, title: str) -> str:
        """
        Extract quality information from torrent title.
        
        Args:
            title: Torrent title to analyze
            
        Returns:
            Quality string or 'Unknown'
        """
        title_lower = title.lower()
        qualities = []
        
        # Resolution qualities
        resolution_map = {
            '360p': '360p', '480p': '480p', '720p': '720p', 
            '1080p': '1080p', '1440p': '1440p', '2160p': '4K', '4k': '4K'
        }
        
        for key, value in resolution_map.items():
            if key in title_lower:
                qualities.append(value)
                
        # Source qualities
        source_map = {
            'webrip': 'WEBRip', 'bluray': 'BluRay', 'bdrip': 'BluRay',
            'dvd': 'DVD', 'hdtv': 'HDTV'
        }
        
        for key, value in source_map.items():
            if key in title_lower:
                qualities.append(value)
                
        # General quality indicators
        if 'sd' in title_lower and '480p' not in qualities:
            qualities.append('SD')
        if 'hd' in title_lower and not any(q in ['720p', '1080p', '1440p', '4K'] for q in qualities):
            qualities.append('HD')
            
        return ', '.join(qualities) if qualities else 'Unknown'
        
    def launch_magnet_system_default(self, magnet_link: str) -> Tuple[bool, str]:
        """
        Launch magnet link using system default handler.
        
        Args:
            magnet_link: Magnet link to launch
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            import webbrowser
            import platform
            import subprocess
            import os
            
            system = platform.system()
            
            if system == "Windows":
                os.startfile(magnet_link)
                return True, ""
            elif system == "Darwin":  # macOS
                result = subprocess.run(['open', magnet_link], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, ""
                else:
                    return False, f"macOS open command failed: {result.stderr}"
            else:  # Linux and other Unix-like systems
                try:
                    result = subprocess.run(['xdg-open', magnet_link], capture_output=True, text=True)
                    if result.returncode == 0:
                        return True, ""
                    else:
                        raise Exception("xdg-open failed")
                except (FileNotFoundError, Exception):
                    # Fallback to webbrowser
                    webbrowser.open(magnet_link)
                    return True, ""
                    
        except Exception as e:
            return False, f"Failed to launch magnet with system default: {str(e)}"
            
    def update_configuration(self, torrent_config: TorrentClientConfig, qb_config: QBittorrentConfig, quality_settings: QualitySettings):
        """
        Update the controller's configuration.
        
        Args:
            torrent_config: New torrent client configuration
            qb_config: New qBittorrent configuration  
            quality_settings: New quality filter settings
        """
        self.torrent_config = torrent_config
        self.qb_config = qb_config
        self.quality_settings = quality_settings
        
        # Reinitialize the torrent client
        self.torrent_client = GenericTorrentClient(self.torrent_config)
