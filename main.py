import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import scrolledtext
import threading
import json
import os
import re
import requests
from bs4 import BeautifulSoup
import qbittorrentapi
from datetime import datetime
import logging
import sys
import sys
import argparse
import time
import builtins
log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
trace_path = os.path.join(log_dir, 'log_trace.txt')
with open(trace_path, 'a') as f:
    f.write('TOP OF FILE\n')
TRACKER_FILE = 'tracker.json'
DEFAULT_INTERVAL = 24 * 60 * 60  # 24 hours (once a day)

class AnimeTracker:
    def __init__(self, tracker_file=TRACKER_FILE):
        self.tracker_file = tracker_file
        self.data = self.load()

    def load(self):
        logging.debug(f'[DEBUG] AnimeTracker.load called, tracker_file: {self.tracker_file}')
        if not os.path.exists(self.tracker_file):
            logging.debug('[DEBUG] Tracker file does not exist, returning empty dict')
            return {}
        try:
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logging.debug(f'[DEBUG] Loaded tracker data with {len(data)} entries: {list(data.keys())}')
                return data
        except Exception as e:
            logging.debug(f'[DEBUG] Exception loading tracker file: {e}')
            return {}

    def save(self):
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get_all(self):
        logging.debug(f'[DEBUG] AnimeTracker.get_all called, data keys: {list(self.data.keys())}')
        return self.data.items()

    def add(self, title, url, allow_multi_episode=False):
        if title in self.data:
            return False
        self.data[title] = {'url': url, 'last_season': 1, 'last_episode': 0, 'allow_multi_episode': allow_multi_episode}
        self.save()
        return True

    def remove(self, title):
        if title in self.data:
            del self.data[title]
            self.save()
            return True
        return False

    def update_episode(self, title, season, episode):
        if title in self.data:
            self.data[title]['last_season'] = season
            self.data[title]['last_episode'] = episode
            self.save()
    
    def edit_title(self, old_title, new_title):
        if old_title in self.data and new_title not in self.data:
            self.data[new_title] = self.data.pop(old_title)
            self.save()
            return True
        return False

    def get_url(self, title):
        return self.data[title]['url'] if title in self.data else None

    def get_last_season_and_episode(self, title):
        if title in self.data:
            return self.data[title].get('last_season', 1), self.data[title]['last_episode']
        return 1, 0
    
    def allows_multi_episode(self, title):
        return self.data[title].get('allow_multi_episode', False) if title in self.data else False
    
    def set_multi_episode_flag(self, title, allow_multi_episode):
        if title in self.data:
            self.data[title]['allow_multi_episode'] = allow_multi_episode
            self.save()

class QBittorrentConfig:
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

class NyaaScraper:
    # Improved regex that handles all episode formats correctly:
    # 1. Season/Episode format: S01E01, S1E12, etc.
    # 2. Episode ranges in parentheses: (31-32), (01-12) - identified as multi-episode
    # 3. Single episodes in parentheses: (01), (32)
    # 4. Dash-separated single episodes: - 01, - 32
    # 5. Explicit episode markers: Episode 1, Ep. 2
    # 6. Episode ranges without parentheses: 01-12, 1-24 - identified as multi-episode
    # Enhanced regex that captures both season and episode information
    EPISODE_REGEX = re.compile(
        r'(?:S(\d{1,2})E(\d{1,4}))|'  # Group 1,2: S01E01 format (season, episode)
        r'\((\d{1,4})-(\d{1,4})\)|'  # Group 3,4: Episode ranges in parentheses
        r'\b(\d{1,4})-(\d{1,4})\b(?!\d)|'  # Group 5,6: Episode ranges without parentheses
        r'\b(?:ep?\.?|episode)\s*(\d{1,4})-(\d{1,4})\b|'  # Group 7,8: Episode ranges with explicit markers
        r'\((\d{1,4})\)|'  # Group 9: Single episodes in parentheses
        r'- (\d{1,4})(?=\s|\.|\[|$)|'  # Group 10: Dash-separated episodes
        r'\b(?:ep?\.?|episode)\s*(\d{1,4})\b',  # Group 11: Explicit episode markers
        re.IGNORECASE
    )
    
    @staticmethod
    def search(query):
        """Search Nyaa.si for the given query and return the results"""
        logging.info(f"Searching Nyaa.si for: {query}")
        try:
            # Construct the search URL
            search_url = f"https://nyaa.si/?f=0&c=0_0&q={requests.utils.quote(query)}&s=seeders&o=desc"
            logging.debug(f"Search URL: {search_url}")
            
            # Send the request
            resp = requests.get(search_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find all torrent rows
            torrent_rows = soup.select('tbody tr')
            if not torrent_rows:
                torrent_rows = soup.select('tr')
            
            results = []
            
            for row in torrent_rows:
                # Find the title link (exclude comments links)
                title_link = None
                all_view_links = row.find_all('a', href=re.compile(r'/view/\d+'))
                for link in all_view_links:
                    href = link.get('href', '')
                    classes = link.get('class', [])
                    # Skip comment links
                    if '#comments' not in href and 'comments' not in classes:
                        title_link = link
                        break
                        
                if not title_link:
                    continue
                    
                title = title_link.get('title') or title_link.get_text().strip()
                
                # Get the torrent URL
                torrent_url = f"https://nyaa.si{title_link.get('href')}"
                
                # Find magnet link
                magnet_link_tag = row.find('a', href=re.compile(r'^magnet:'))
                magnet = magnet_link_tag['href'] if magnet_link_tag else None
                
                # Extract episode information
                episode_info, episode_type, matched_text, season_info = NyaaScraper.extract_episode_info(title)
                
                # Format episode number for display
                if episode_type == "range":
                    ep_text = f"{episode_info[0]}-{episode_info[1]}"
                elif episode_type == "single":
                    ep_text = str(episode_info)
                else:
                    ep_text = "Unknown"
                
                # Get file size
                size_cells = row.find_all('td')
                size = 'Unknown'
                if len(size_cells) >= 4:
                    size = size_cells[3].get_text().strip()
                
                # Get seeders/leechers
                seeders = leechers = 0
                if len(size_cells) >= 6:
                    try:
                        seeders = int(size_cells[5].get_text().strip())
                        leechers = int(size_cells[6].get_text().strip())
                    except (ValueError, IndexError):
                        pass
                
                # Get date information
                date = ''
                time = ''
                if len(size_cells) >= 5:  # Date is in column 4 (index 4)
                    date_text = size_cells[4].get_text().strip()
                    # Parse date and time from Nyaa.si format (e.g., "2024-01-15 14:30")
                    parsed_date, parsed_time = NyaaScraper.parse_date_time(date_text)
                    date = parsed_date
                    time = parsed_time
                
                results.append({
                    'title': title,
                    'episode': episode_info,
                    'episode_text': ep_text,
                    'season': season_info,
                    'magnet': magnet,
                    'url': torrent_url,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers,
                    'date': date,
                    'time': time
                })
            
            logging.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logging.error(f"Error searching Nyaa.si for {query}: {e}")
            return []
    
    @staticmethod
    def extract_episode_info(title):
        """Extract episode information and determine if it's a single episode or range
        Returns: (episode_info, episode_type, matched_text, season_info)
        """
        match = NyaaScraper.EPISODE_REGEX.search(title)
        if not match:
            return None, None, "No match", None
        
        groups = match.groups()
        
        # S01E01 format - now captures both season and episode
        if groups[0] and groups[1]:  # Groups 1,2
            season = int(groups[0])
            episode = int(groups[1])
            return episode, "single", f"S{groups[0]}E{groups[1]}", season
        
        # Episode ranges in parentheses (31-32)
        elif groups[2] and groups[3]:  # Groups 3,4
            start_ep = int(groups[2])
            end_ep = int(groups[3])
            return (start_ep, end_ep), "range", f"({groups[2]}-{groups[3]})", None
        
        # Episode ranges without parentheses 01-12
        elif groups[4] and groups[5]:  # Groups 5,6
            start_ep = int(groups[4])
            end_ep = int(groups[5])
            return (start_ep, end_ep), "range", f"{groups[4]}-{groups[5]}", None
        
        # Episode ranges with explicit markers Episode 05-08
        elif groups[6] and groups[7]:  # Groups 7,8
            start_ep = int(groups[6])
            end_ep = int(groups[7])
            return (start_ep, end_ep), "range", f"Episode {groups[6]}-{groups[7]}", None
        
        # Single episodes in parentheses (01)
        elif groups[8]:  # Group 9
            return int(groups[8]), "single", f"({groups[8]})", None
        
        # Dash-separated single episodes - 01
        elif groups[9]:  # Group 10
            return int(groups[9]), "single", f"- {groups[9]}", None
        
        # Explicit episode markers Episode 1
        elif groups[10]:  # Group 11
            return int(groups[10]), "single", f"Episode {groups[10]}", None
        
        return None, None, "No valid group", None
    
    @staticmethod
    def parse_date_time(date_text):
        """Parse date and time from Nyaa.si date format
        Returns: (date, time) tuple
        """
        if not date_text:
            return '', ''
        
        # Nyaa.si typically uses format like "2024-01-15 14:30" or "2024-01-15"
        # Try to split on space to separate date and time
        parts = date_text.strip().split()
        
        if len(parts) >= 2:
            # Has both date and time
            date = parts[0]
            time = parts[1]
        elif len(parts) == 1:
            # Only date, no time
            date = parts[0]
            time = ''
        else:
            # Empty or invalid
            date = ''
            time = ''
        
        return date, time
    
    @staticmethod
    def get_all_episodes(url, anime_title=None, tracker=None):
        """Get all episodes from a Nyaa.si page with their magnet links"""
        logging.info(f"Fetching all episodes from URL: {url}")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            torrent_rows = soup.select('tbody tr')
            if not torrent_rows:
                torrent_rows = soup.select('tr')
            
            episodes = []
            allow_multi_episode = tracker.allows_multi_episode(anime_title) if tracker and anime_title else False
            
            for row in torrent_rows:
                # Find the title link (exclude comments links)
                title_link = None
                all_view_links = row.find_all('a', href=re.compile(r'/view/\d+'))
                for link in all_view_links:
                    href = link.get('href', '')
                    classes = link.get('class', [])
                    # Skip comment links (either by href containing #comments or by having 'comments' class)
                    if '#comments' not in href and 'comments' not in classes:
                        title_link = link
                        break
                if not title_link:
                    continue
                    
                title = title_link.get('title') or title_link.get_text().strip()
                
                # Find magnet link
                magnet_link_tag = row.find('a', href=re.compile(r'^magnet:'))
                magnet = magnet_link_tag['href'] if magnet_link_tag else None
                
                # Extract episode information using new method
                episode_info, episode_type, matched_text, season_info = NyaaScraper.extract_episode_info(title)
                
                # Skip multi-episode files (ranges) unless allowed for this anime
                if episode_type == "range" and not allow_multi_episode:
                    logging.debug(f"Episode extraction - Title: '{title}' -> SKIPPED multi-episode range: {episode_info} (matched: '{matched_text}')")
                    continue
                
                # For multi-episode ranges, use the highest episode number
                if episode_type == "range" and allow_multi_episode:
                    episode_num = episode_info[1]  # Use the end episode of the range
                    logging.debug(f"Episode extraction - Title: '{title}' -> Multi-episode range allowed: {episode_info} -> Using episode {episode_num} (matched: '{matched_text}')")
                else:
                    episode_num = episode_info if episode_type == "single" else None
                
                if episode_num:
                    season_text = f" Season {season_info}" if season_info else ""
                    logging.debug(f"Episode extraction - Title: '{title}' -> Episode: {episode_num}{season_text} (matched: '{matched_text}')")
                else:
                    logging.debug(f"Episode extraction - Title: '{title}' -> No episode number found")
                
                # Get file size
                size_cells = row.find_all('td')
                size = 'Unknown'
                if len(size_cells) >= 4:
                    size = size_cells[3].get_text().strip()
                
                # Get seeders/leechers
                seeders = leechers = 0
                if len(size_cells) >= 6:
                    try:
                        seeders = int(size_cells[5].get_text().strip())
                        leechers = int(size_cells[6].get_text().strip())
                    except (ValueError, IndexError):
                        pass
                
                # Get date information
                date = ''
                time = ''
                if len(size_cells) >= 5:  # Date is in column 4 (index 4)
                    date_text = size_cells[4].get_text().strip()
                    # Parse date and time from Nyaa.si format
                    parsed_date, parsed_time = NyaaScraper.parse_date_time(date_text)
                    date = parsed_date
                    time = parsed_time
                
                episodes.append({
                    'title': title,
                    'episode': episode_num,
                    'magnet': magnet,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers,
                    'date': date,
                    'time': time
                })
            
            # Sort by episode number (descending)
            episodes.sort(key=lambda x: x['episode'] or 0, reverse=True)
            logging.info(f"Found {len(episodes)} episodes")
            return episodes
            
        except Exception as e:
            logging.error(f"Error fetching episodes from {url}: {e}")
            return []

    @staticmethod
    def get_latest_episode_and_magnet(url, anime_title=None, tracker=None):
        """Returns (season, episode, magnet)"""
        logging.info(f"Attempting to scrape URL: {url}")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Try different selectors to find torrent rows
            torrent_rows = soup.select('tbody tr')
            if not torrent_rows:
                torrent_rows = soup.select('tr')
            
            logging.debug(f"Found {len(torrent_rows)} potential torrent rows in the HTML.")
            
            allow_multi_episode = tracker.allows_multi_episode(anime_title) if tracker and anime_title else False
            
            # Collect all valid episodes with their metadata
            episodes = []
            
            for i, row in enumerate(torrent_rows):
                logging.debug(f"Processing row {i}")
                
                # Find the title link (exclude comments links)
                title_link = None
                all_view_links = row.find_all('a', href=re.compile(r'/view/\d+'))
                for link in all_view_links:
                    href = link.get('href', '')
                    classes = link.get('class', [])
                    if '#comments' not in href and 'comments' not in classes:
                        title_link = link
                        break
                        
                if not title_link:
                    logging.debug(f"No title link found in row {i}")
                    continue
                    
                torrent_title = title_link.get('title') or title_link.get_text().strip()
                logging.debug(f"Processing torrent title: {torrent_title}")

                # Extract episode information using enhanced method
                episode_info, episode_type, matched_text, season_info = NyaaScraper.extract_episode_info(torrent_title)
                
                # Skip multi-episode files (ranges) unless allowed for this anime
                if episode_type == "range" and not allow_multi_episode:
                    logging.debug(f"Episode extraction - Title: '{torrent_title}' -> SKIPPED multi-episode range: {episode_info} (matched: '{matched_text}')")
                    continue
                
                # For multi-episode ranges, use the highest episode number
                if episode_type == "range" and allow_multi_episode:
                    ep_num = episode_info[1]  # Use the end episode of the range
                    logging.debug(f"Episode extraction - Title: '{torrent_title}' -> Multi-episode range allowed: {episode_info} -> Using episode {ep_num} (matched: '{matched_text}')")
                else:
                    ep_num = episode_info if episode_type == "single" else None
                
                if ep_num:
                    # Find the magnet link within the current row
                    magnet_link_tag = row.find('a', href=re.compile(r'^magnet:'))
                    magnet = magnet_link_tag['href'] if magnet_link_tag else None
                    
                    season_text = f" Season {season_info}" if season_info else ""
                    logging.debug(f"Episode extraction - Title: '{torrent_title}' -> Episode: {ep_num}{season_text} (matched: '{matched_text}') - Row index: {i}")
                    
                    episodes.append({
                        'episode': ep_num,
                        'season': season_info,
                        'magnet': magnet,
                        'title': torrent_title,
                        'row_index': i,  # Lower index = more recent upload
                        'matched_text': matched_text
                    })
                else:
                    logging.debug(f"No episode number found in title: {torrent_title}")
            
            if not episodes:
                logging.info(f"No valid episodes found in {url}")
                return None, None, None
            
            # Smart episode selection logic:
            # 1. If we have season info, prioritize the highest season
            # 2. Within the same season (or no season), prioritize the highest episode
            # 3. If episodes are equal, prioritize the most recent upload (lower row_index)
            
            # Separate episodes with and without season info
            episodes_with_season = [ep for ep in episodes if ep['season'] is not None]
            episodes_without_season = [ep for ep in episodes if ep['season'] is None]
            
            latest_episode = None
            
            if episodes_with_season:
                # Find the highest season
                max_season = max(ep['season'] for ep in episodes_with_season)
                current_season_episodes = [ep for ep in episodes_with_season if ep['season'] == max_season]
                
                # Within the highest season, find the highest episode number
                # If tied, prefer the most recent upload (lower row_index)
                latest_episode = max(current_season_episodes, 
                                   key=lambda x: (x['episode'], -x['row_index']))
                
                logging.info(f"Found episodes with season info. Latest: Season {latest_episode['season']} Episode {latest_episode['episode']} (row {latest_episode['row_index']})")
            
            # If no season info available, or if episodes without season info have higher episode numbers
            # than the latest seasoned episode, consider them
            if episodes_without_season:
                # Find the highest episode number among non-seasoned episodes
                # If tied, prefer the most recent upload (lower row_index)
                latest_no_season = max(episodes_without_season, 
                                     key=lambda x: (x['episode'], -x['row_index']))
                
                # If we don't have a seasoned episode, or if the non-seasoned episode
                # appears more recent (lower row index) and has a reasonable episode number
                if (latest_episode is None or 
                    (latest_no_season['row_index'] < latest_episode['row_index'] and 
                     latest_no_season['episode'] >= latest_episode['episode'] - 5)):  # Allow some tolerance
                    
                    # Additional check: if the non-seasoned episode has a much higher number,
                    # it might be from an older season, so be more conservative
                    if (latest_episode is None or 
                        latest_no_season['episode'] <= latest_episode['episode'] + 10):
                        latest_episode = latest_no_season
                        logging.info(f"Selected non-seasoned episode: Episode {latest_episode['episode']} (row {latest_episode['row_index']})")
            
            if latest_episode:
                season_to_return = latest_episode.get('season') if latest_episode.get('season') is not None else 1
                logging.info(f"Final selection - Episode: {latest_episode['episode']}, Season: {season_to_return}, Title: {latest_episode['title'][:100]}...")
                return season_to_return, latest_episode['episode'], latest_episode['magnet']
            else:
                logging.info(f"No suitable episode found in {url}")
                return None, None, None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Network or HTTP error during scraping {url}: {e}")
            return None, None
        except Exception as e:
            logging.error(f"An unexpected error occurred during scraping {url}: {e}", exc_info=True)
            return None, None

class QBittorrentClient:
    def __init__(self, config: QBittorrentConfig):
        self.config = config
        self.client = None

    def connect(self):
        try:
            print(f"[DEBUG] Connecting to qBittorrent at {self.config.host}:{self.config.port}")
            self.client = qbittorrentapi.Client(
                host=f'http://{self.config.host}:{self.config.port}/',
                username=self.config.username,
                password=self.config.password,
                REQUESTS_ARGS={'timeout': (5, 10)}  # 5s connect, 10s read timeout
            )
            print("[DEBUG] Attempting authentication...")
            self.client.auth_log_in()
            print("[DEBUG] Authentication successful")
            return True, ''
        except Exception as e:
            print(f"[DEBUG] Connection failed: {e}")
            return False, str(e)

    def add_magnet(self, magnet, category=None):
        try:
            kwargs = {'urls': magnet}
            if category:
                kwargs['category'] = category
            self.client.torrents_add(**kwargs)
            return True, ''
        except Exception as e:
            return False, str(e)

class App:
    def __init__(self, root):
        logging.info('[DEBUG] MainWindow __init__ called')
        with open(trace_path, 'a') as f:
            f.write('IN APP INIT\n')
        self.root = root
        self.root.title('Nyaa.si Anime Auto Downloader')
        self.tracker = AnimeTracker()
        self.qb_config = QBittorrentConfig()
        self.check_interval = DEFAULT_INTERVAL
        self.check_thread = None
        self.stop_event = threading.Event()
        self._setup_gui()
        self._load_tracker()
        self._log('Application started.')
        self._start_periodic_check()

    def _setup_gui(self):
        with open(trace_path, 'a') as f: f.write('IN SETUP GUI\n')
        mainframe = ttk.Frame(self.root, padding='10')
        mainframe.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create main paned window for side panel
        self.main_paned = ttk.PanedWindow(mainframe, orient='horizontal')
        self.main_paned.grid(row=0, column=0, sticky='nsew')
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        
        # Left panel (main content)
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=3)
        
        # Right panel (episodes - initially hidden)
        self.right_frame = ttk.Frame(self.main_paned)
        self.episodes_visible = False

        # Add Anime Section
        add_frame = ttk.LabelFrame(self.left_frame, text='Add New Anime')
        add_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        ttk.Label(add_frame, text='Title:').grid(row=0, column=0, sticky='w')
        self.title_entry = ttk.Entry(add_frame, width=30)
        self.title_entry.grid(row=0, column=1, sticky='ew')
        ttk.Label(add_frame, text='Nyaa.si URL:').grid(row=1, column=0, sticky='w')
        self.url_entry = ttk.Entry(add_frame, width=50)
        self.url_entry.grid(row=1, column=1, sticky='ew')
        add_btn = ttk.Button(add_frame, text='Add Series', command=self.add_series)
        add_btn.grid(row=0, column=2, rowspan=2, padx=5)
        
        # Search Button (Magnifying Glass)
        search_btn_frame = ttk.Frame(add_frame)
        search_btn_frame.grid(row=0, column=3, rowspan=2, padx=5)
        search_btn = tk.Button(search_btn_frame, text="🔍", width=3, command=self.toggle_search_panel, 
                             font=('TkDefaultFont', 12))
        search_btn.pack(fill='both', expand=True)
        
        # Hidden Search Panel (will be shown when search button is clicked)
        self.search_panel_visible = False

        # Anime List Section
        list_frame = ttk.LabelFrame(self.left_frame, text='Tracked Anime')
        list_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.anime_tree = ttk.Treeview(list_frame, columns=('Title', 'Last Season', 'Last Episode', 'URL'), show='headings', height=8)
        self.anime_tree.heading('Title', text='Title')
        self.anime_tree.heading('Last Season', text='S')
        self.anime_tree.heading('Last Episode', text='Last Ep')
        self.anime_tree.heading('URL', text='Nyaa.si URL')
        self.anime_tree.column('Title', width=150)
        self.anime_tree.column('Last Season', width=40)
        self.anime_tree.column('Last Episode', width=80)
        self.anime_tree.column('URL', width=350)
        self.anime_tree.grid(row=0, column=0, sticky='nsew')
        
        # Bind double-click event to show episodes
        self.anime_tree.bind('<Double-1>', self.on_anime_double_click)
        
        # Bind right-click for context menu
        self.anime_tree.bind('<Button-3>', self.on_anime_right_click)
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Toggle Multi-Episode Downloads", command=self.toggle_multi_episode)
        
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        remove_btn = ttk.Button(list_frame, text='Remove Series', command=self.remove_series)
        remove_btn.grid(row=1, column=0, sticky='ew', pady=3)
        edit_btn = ttk.Button(list_frame, text='Edit Title', command=self.edit_series)
        edit_btn.grid(row=2, column=0, sticky='ew', pady=3)
        edit_btn.bind('<Button-1>', lambda e: logging.debug('[DEBUG] Edit Title button clicked'))
        multi_episode_btn = ttk.Button(list_frame, text='Toggle Multi-Episode', command=self.toggle_multi_episode)
        multi_episode_btn.grid(row=3, column=0, sticky='ew', pady=3)
        force_btn = ttk.Button(list_frame, text='Force Check Now', command=self.force_check)
        force_btn.grid(row=4, column=0, sticky='ew', pady=3)

        # qBittorrent Config Section
        config_frame = ttk.LabelFrame(self.left_frame, text='qBittorrent Settings')
        config_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        ttk.Label(config_frame, text='Host:').grid(row=0, column=0, sticky='w')
        self.qb_host = ttk.Entry(config_frame, width=15)
        self.qb_host.insert(0, self.qb_config.host)
        self.qb_host.grid(row=0, column=1)
        ttk.Label(config_frame, text='Port:').grid(row=0, column=2, sticky='w')
        self.qb_port = ttk.Entry(config_frame, width=6)
        self.qb_port.insert(0, str(self.qb_config.port))
        self.qb_port.grid(row=0, column=3)
        ttk.Label(config_frame, text='Username:').grid(row=1, column=0, sticky='w')
        self.qb_user = ttk.Entry(config_frame, width=15)
        self.qb_user.insert(0, self.qb_config.username)
        self.qb_user.grid(row=1, column=1)
        ttk.Label(config_frame, text='Password:').grid(row=1, column=2, sticky='w')
        self.qb_pass = ttk.Entry(config_frame, width=15, show='*')
        self.qb_pass.insert(0, self.qb_config.password)
        self.qb_pass.grid(row=1, column=3)
        ttk.Label(config_frame, text='Category:').grid(row=2, column=0, sticky='w')
        self.qb_cat = ttk.Entry(config_frame, width=15)
        self.qb_cat.insert(0, self.qb_config.category)
        self.qb_cat.grid(row=2, column=1)
        ttk.Label(config_frame, text='Check Interval (hours):').grid(row=2, column=2, sticky='w')
        self.interval_entry = ttk.Entry(config_frame, width=6)
        self.interval_entry.insert(0, str(DEFAULT_INTERVAL // 3600))
        self.interval_entry.grid(row=2, column=3)
        save_btn = ttk.Button(config_frame, text='Save Config', command=self.save_config)
        save_btn.grid(row=3, column=0, columnspan=4, sticky='ew', pady=3)

        # Status Log
        log_frame = ttk.LabelFrame(self.left_frame, text='Status Log')
        log_frame.grid(row=3, column=0, sticky='nsew', padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', wrap='word')
        self.log_text.pack(fill='both', expand=True)

        self.left_frame.rowconfigure(1, weight=1)
        self.left_frame.rowconfigure(3, weight=1)
        self.left_frame.columnconfigure(0, weight=1)
        
        # Setup episodes panel
        self._setup_episodes_panel()
    
    def _setup_episodes_panel(self):
        """Setup the episodes side panel"""
        # Episodes panel header
        header_frame = ttk.Frame(self.right_frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        self.episodes_title_label = ttk.Label(header_frame, text='Episodes', font=('TkDefaultFont', 12, 'bold'))
        self.episodes_title_label.pack(side='left')
        
        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide_episodes_panel)
        close_btn.pack(side='right')
        
        # Episodes list
        episodes_list_frame = ttk.Frame(self.right_frame)
        episodes_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for episodes
        self.episodes_tree = ttk.Treeview(episodes_list_frame, 
                                         columns=('Episode', 'Size', 'DateTime', 'Seeders', 'Leechers'), 
                                         show='tree headings', height=15)
        self.episodes_tree.heading('#0', text='Title', command=lambda: self.sort_treeview('#0', False, 'text'))
        self.episodes_tree.heading('Episode', text='Ep', command=lambda: self.sort_treeview('Episode', False, 'episode'))
        self.episodes_tree.heading('Size', text='Size', command=lambda: self.sort_treeview('Size', False, 'size'))
        self.episodes_tree.heading('DateTime', text='Date/Time', command=lambda: self.sort_treeview('DateTime', False, 'datetime'))
        self.episodes_tree.heading('Seeders', text='S', command=lambda: self.sort_treeview('Seeders', False, 'seeders'))
        self.episodes_tree.heading('Leechers', text='L', command=lambda: self.sort_treeview('Leechers', False, 'leechers'))
        
        # Store current sort state
        self.current_sort_column = None
        self.current_sort_reverse = False
        
        self.episodes_tree.column('#0', width=250)
        self.episodes_tree.column('Episode', width=50)
        self.episodes_tree.column('Size', width=80)
        self.episodes_tree.column('DateTime', width=120)
        self.episodes_tree.column('Seeders', width=40)
        self.episodes_tree.column('Leechers', width=40)
        
        # Scrollbar for episodes
        episodes_scrollbar = ttk.Scrollbar(episodes_list_frame, orient='vertical', command=self.episodes_tree.yview)
        self.episodes_tree.configure(yscrollcommand=episodes_scrollbar.set)
        
        self.episodes_tree.pack(side='left', fill='both', expand=True)
        episodes_scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to download episode
        self.episodes_tree.bind('<Double-1>', self.on_episode_double_click)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.right_frame)
        buttons_frame.pack(pady=5)
        
        # Download button
        download_btn = ttk.Button(buttons_frame, text='Download Selected', 
                                 command=self.download_selected_episode)
        download_btn.pack(side='left', padx=5)
        
        # Add to tracked button
        add_to_tracked_btn = ttk.Button(buttons_frame, text='Add to Tracked', 
                                      command=self.add_search_result_to_tracked)
        add_to_tracked_btn.pack(side='left', padx=5)
        
        # Search panel (initially hidden)
        self._setup_search_panel()
    
    def sort_treeview(self, column, reverse, sort_type):
        """Sort treeview by column"""
        # Get all items
        items = [(self.episodes_tree.set(item, column), item) for item in self.episodes_tree.get_children('')]
        
        # Determine if we should reverse the sort
        if self.current_sort_column == column:
            reverse = not self.current_sort_reverse
        else:
            reverse = False
        
        # Sort items
        items.sort(key=lambda x: self.get_sort_key(x[0], sort_type), reverse=reverse)
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            self.episodes_tree.move(item, '', index)
        
        # Update sort state
        self.current_sort_column = column
        self.current_sort_reverse = reverse
        
        # Update column header to show sort direction
        self.update_sort_indicator(column, reverse)
    
    def get_sort_key(self, value, sort_type):
        """Convert value to appropriate type for sorting"""
        if not value:
            return (0, 0) if sort_type in ['seeders', 'leechers', 'episode'] else ''
        
        if sort_type == 'episode':
            # Extract episode number from text like "Ep 01", "S01E01", etc.
            try:
                if 'E' in value and 'S' in value:
                    # Format like "S01E01"
                    ep_part = value.split('E')[-1]
                    return (0, int(ep_part))
                elif 'Ep' in value:
                    # Format like "Ep 01"
                    ep_part = value.split()[-1]
                    return (0, int(ep_part))
                else:
                    # Try to extract any number from the value
                    import re
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        return (0, int(numbers[-1]))
                    return (0, 0)
            except (ValueError, IndexError):
                return (0, 0)
        
        elif sort_type in ['seeders', 'leechers']:
            try:
                return (0, int(value))
            except ValueError:
                return (0, 0)
        
        elif sort_type == 'size':
            # Convert size to bytes for sorting (e.g., "1.2 GB" -> 1288490188)
            return self.parse_size_for_sort(value)
        
        elif sort_type == 'date':
            # Convert date to sortable format
            return self.parse_date_for_sort(value)
        
        elif sort_type == 'time':
            # Convert time to sortable format
            return self.parse_time_for_sort(value)
        
        elif sort_type == 'datetime':
            # Convert combined datetime to sortable format
            return self.parse_datetime_for_sort(value)
        
        else:
            # Text sorting
            return value.lower()
    
    def parse_size_for_sort(self, size_str):
        """Convert size string to bytes for sorting"""
        if not size_str or size_str == 'Unknown':
            return 0
        
        try:
            size_str = size_str.strip().upper()
            if 'GB' in size_str:
                num = float(size_str.replace('GB', '').strip())
                return int(num * 1024 * 1024 * 1024)
            elif 'MB' in size_str:
                num = float(size_str.replace('MB', '').strip())
                return int(num * 1024 * 1024)
            elif 'KB' in size_str:
                num = float(size_str.replace('KB', '').strip())
                return int(num * 1024)
            else:
                # Assume bytes
                return int(float(size_str))
        except (ValueError, AttributeError):
            return 0
    
    def parse_date_for_sort(self, date_str):
        """Convert date string to sortable format"""
        if not date_str:
            return ''
        
        try:
            # Assume format like "2024-01-15"
            return date_str
        except:
            return ''
    
    def parse_time_for_sort(self, time_str):
        """Convert time string to sortable format"""
        if not time_str:
            return ''
        
        try:
            # Assume format like "14:30"
            return time_str
        except:
            return ''
    
    def combine_date_time(self, date_str, time_str):
        """Combine date and time strings into a single display string"""
        if not date_str and not time_str:
            return ''
        elif not date_str:
            return time_str
        elif not time_str:
            return date_str
        else:
            return f"{date_str} {time_str}"
    
    def parse_datetime_for_sort(self, datetime_str):
        """Convert datetime string to sortable format"""
        if not datetime_str:
            return ''
        
        try:
            # Format like "2024-01-15 14:30" or "2024-01-15"
            return datetime_str
        except:
            return ''
    
    def update_sort_indicator(self, column, reverse):
        """Update column header to show sort direction"""
        # Reset all headers
        for col in ['#0', 'Episode', 'Size', 'DateTime', 'Seeders', 'Leechers']:
            if col == '#0':
                self.episodes_tree.heading(col, text='Title')
            elif col == 'Episode':
                self.episodes_tree.heading(col, text='Ep')
            elif col == 'Size':
                self.episodes_tree.heading(col, text='Size')
            elif col == 'DateTime':
                self.episodes_tree.heading(col, text='Date/Time')
            elif col == 'Seeders':
                self.episodes_tree.heading(col, text='S')
            elif col == 'Leechers':
                self.episodes_tree.heading(col, text='L')
        
        # Update the sorted column header
        if column == '#0':
            self.episodes_tree.heading(column, text='Title ▼' if reverse else 'Title ▲')
        elif column == 'Episode':
            self.episodes_tree.heading(column, text='Ep ▼' if reverse else 'Ep ▲')
        elif column == 'Size':
            self.episodes_tree.heading(column, text='Size ▼' if reverse else 'Size ▲')
        elif column == 'DateTime':
            self.episodes_tree.heading(column, text='Date/Time ▼' if reverse else 'Date/Time ▲')
        elif column == 'Seeders':
            self.episodes_tree.heading(column, text='S ▼' if reverse else 'S ▲')
        elif column == 'Leechers':
            self.episodes_tree.heading(column, text='L ▼' if reverse else 'L ▲')
    
    def on_anime_double_click(self, event):
        """Handle double-click on anime in the main list"""
        selection = self.anime_tree.selection()
        if not selection:
            return
            
        title = selection[0]
        values = self.anime_tree.item(title, 'values')
        url = values[3]  # URL is the fourth column
        
        self.show_episodes_panel(title, url)
    
    def _setup_search_panel(self):
        """Setup the search panel"""
        # Create a frame for the search panel
        self.search_frame = ttk.Frame(self.root)
        
        # Search panel header
        header_frame = ttk.Frame(self.search_frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        search_title_label = ttk.Label(header_frame, text='Search Nyaa.si', font=('TkDefaultFont', 12, 'bold'))
        search_title_label.pack(side='left')
        
        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide_search_panel)
        close_btn.pack(side='right')
        
        # Search input area
        search_input_frame = ttk.Frame(self.search_frame)
        search_input_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_input_frame, text='Search:').pack(side='left')
        self.search_entry = ttk.Entry(search_input_frame, width=30)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_nyaa())
        
        search_btn = ttk.Button(search_input_frame, text='Search', command=self.search_nyaa)
        search_btn.pack(side='left')
    
    def toggle_search_panel(self):
        """Toggle the search panel visibility"""
        if self.search_panel_visible:
            self.hide_search_panel()
        else:
            self.show_search_panel()
    
    def show_search_panel(self):
        """Show the search panel"""
        if not self.search_panel_visible:
            # Hide episodes panel if it's visible
            if self.episodes_visible:
                self.hide_episodes_panel()
            
            # Add the search panel to the main paned window
            self.main_paned.add(self.search_frame, weight=1)
            self.search_panel_visible = True
            self.search_entry.focus()
    
    def hide_search_panel(self):
        """Hide the search panel"""
        if self.search_panel_visible:
            self.main_paned.remove(self.search_frame)
            self.search_panel_visible = False
    
    def search_nyaa(self):
        """Search Nyaa.si for the given query"""
        query = self.search_entry.get().strip()
        if not query:
            self._log('Please enter a search query.')
            return
            
        self._log(f'Searching Nyaa.si for: {query}')
        
        # Show the episodes panel with search results
        self.show_search_results(query)
        
        # Hide the search panel after searching
        self.hide_search_panel()
    
    def show_search_results(self, query):
        """Show the episodes panel with search results"""
        if not self.episodes_visible:
            self.main_paned.add(self.right_frame, weight=2)
            self.episodes_visible = True
        
        self.episodes_title_label.config(text=f'Search Results - {query}')
        
        # Clear existing episodes
        for item in self.episodes_tree.get_children():
            self.episodes_tree.delete(item)
        
        # Show loading message
        loading_item = self.episodes_tree.insert('', 'end', text='Searching...', values=('', '', '', '', '', ''))
        self.episodes_tree.update()
        
        # Fetch search results in background thread
        def fetch_results():
            results = NyaaScraper.search(query)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._populate_search_results(results, loading_item))
        
        threading.Thread(target=fetch_results, daemon=True).start()
    
    def _populate_search_results(self, results, loading_item):
        """Populate the episodes tree with search results"""
        # Remove loading message
        self.episodes_tree.delete(loading_item)
        
        if not results:
            self.episodes_tree.insert('', 'end', text='No results found', values=('', '', '', '', ''))
            return
        
        for result in results:
            # Format episode info for display
            if result['season']:
                ep_text = f"S{result['season']}E{result['episode_text']}"
            else:
                ep_text = f"Ep {result['episode_text']}"
                
            # Combine date and time into a single value
            datetime_value = self.combine_date_time(result['date'], result['time'])
            
            self.episodes_tree.insert('', 'end', 
                                     text=result['title'][:60] + ('...' if len(result['title']) > 60 else ''),
                                     values=(ep_text, result['size'], datetime_value, result['seeders'], result['leechers']),
                                     tags=(result['magnet'],))  # Store magnet link in tags
        
        self._log(f'Found {len(results)} results for: {self.search_entry.get().strip()}')
    
    def show_episodes_panel(self, anime_title, url):
        """Show the episodes panel with episodes from the given URL"""
        if not self.episodes_visible:
            self.main_paned.add(self.right_frame, weight=2)
            self.episodes_visible = True
        
        self.episodes_title_label.config(text=f'Episodes - {anime_title}')
        
        # Clear existing episodes
        for item in self.episodes_tree.get_children():
            self.episodes_tree.delete(item)
        
        # Show loading message
        loading_item = self.episodes_tree.insert('', 'end', text='Loading episodes...', values=('', '', '', '', ''))
        self.episodes_tree.update()
        
        # Fetch episodes in background thread
        def fetch_episodes():
            episodes = NyaaScraper.get_all_episodes(url, anime_title, self.tracker)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._populate_episodes(episodes, loading_item))
        
        threading.Thread(target=fetch_episodes, daemon=True).start()
    
    def _populate_episodes(self, episodes, loading_item):
        """Populate the episodes tree with fetched episodes"""
        # Remove loading message
        self.episodes_tree.delete(loading_item)
        
        if not episodes:
            self.episodes_tree.insert('', 'end', text='No episodes found', values=('', '', '', '', ''))
            return
        
        for episode in episodes:
            season_num = episode.get('season')
            ep_num = episode.get('episode')
            if ep_num:
                if season_num:
                    ep_text = f"S{season_num:02d}E{ep_num:02d}"
                else:
                    ep_text = f"Ep {ep_num}"
            else:
                ep_text = 'Unknown'
            # Combine date and time into a single value
            datetime_value = self.combine_date_time(episode.get('date', ''), episode.get('time', ''))
            
            self.episodes_tree.insert('', 'end', 
                                     text=episode['title'][:60] + ('...' if len(episode['title']) > 60 else ''),
                                     values=(ep_text, episode['size'], datetime_value, episode['seeders'], episode['leechers']),
                                     tags=(episode['magnet'],))  # Store magnet link in tags
    
    def hide_episodes_panel(self):
        """Hide the episodes panel"""
        if self.episodes_visible:
            self.main_paned.remove(self.right_frame)
            self.episodes_visible = False
    
    def on_episode_double_click(self, event):
        """Handle double-click on episode to download"""
        self.download_selected_episode()
    
    def download_selected_episode(self):
        """Download the selected episode"""
        selection = self.episodes_tree.selection()
        if not selection:
            self._log('No episode selected.')
            return
        
        item = selection[0]
        tags = self.episodes_tree.item(item, 'tags')
        if not tags or not tags[0]:
            self._log('No magnet link available for this episode.')
            return
        
        magnet = tags[0]
        episode_title = self.episodes_tree.item(item, 'text')
        
        # Download using qBittorrent
        qb = QBittorrentClient(self.qb_config)
        connected, err = qb.connect()
        if not connected:
            self._log(f'qBittorrent connection failed: {err}')
            return
        
        ok, err = qb.add_magnet(magnet, self.qb_config.category)
        if ok:
            self._log(f'Episode "{episode_title}" sent to qBittorrent.')
        else:
            self._log(f'Failed to add episode to qBittorrent: {err}')
    
    def add_search_result_to_tracked(self):
        """Add the selected search result to the tracked anime list"""
        selection = self.episodes_tree.selection()
        if not selection:
            self._log('No result selected.')
            return
        
        item = selection[0]
        episode_title = self.episodes_tree.item(item, 'text')
        
        # Extract the base anime title by removing episode information
        # This is a simple approach - might need refinement for complex titles
        base_title = episode_title
        # Try to remove common episode markers
        for pattern in [r'\s+-\s+\d+', r'\s+EP\s*\d+', r'\s+Episode\s*\d+', r'\s+E\d+', r'\s+S\d+E\d+']:
            base_title = re.sub(pattern, '', base_title, flags=re.IGNORECASE)
        
        # Remove common suffixes like [1080p], [720p], etc.
        base_title = re.sub(r'\s*\[[^\]]+\]', '', base_title)
        base_title = base_title.strip()
        
        # Get the URL for the search result
        # For search results, we'll use the Nyaa.si URL with the search query
        search_query = self.search_entry.get().strip()
        url = f"https://nyaa.si/?f=0&c=0_0&q={requests.utils.quote(search_query)}&s=seeders&o=desc"
        
        # Ask user to confirm or modify the title
        dialog = tk.Toplevel(self.root)
        dialog.title('Add to Tracked Anime')
        dialog.geometry('400x220')
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text='Anime Title:').pack(pady=5)
        title_entry = ttk.Entry(dialog, width=50)
        title_entry.insert(0, base_title)
        title_entry.pack(pady=5)
        title_entry.select_range(0, tk.END)
        title_entry.focus()
        
        ttk.Label(dialog, text='Nyaa.si URL:').pack(pady=5)
        url_entry = ttk.Entry(dialog, width=50)
        url_entry.insert(0, url)
        url_entry.pack(pady=5)
        
        def save_anime():
            title = title_entry.get().strip()
            url = url_entry.get().strip()
            if not title or not url:
                messagebox.showerror('Error', 'Title and URL cannot be empty.')
                return
            
            if self.tracker.add(title, url):
                self.anime_tree.insert('', 'end', iid=title, values=(title, 1, 0, url))
                self._log(f'Added series: {title}')
                dialog.destroy()
            else:
                messagebox.showerror('Error', f'Series already exists: {title}')
        
        def cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text='Add', command=save_anime).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Cancel', command=cancel).pack(side='left', padx=5)
        
        dialog.bind('<Return>', lambda e: save_anime())
        dialog.bind('<Escape>', lambda e: cancel())
    
    def on_anime_right_click(self, event):
        """Handle right-click on anime list"""
        # Select the item under cursor
        item = self.anime_tree.identify_row(event.y)
        if item:
            self.anime_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def toggle_multi_episode(self):
        """Toggle multi-episode downloads for selected anime"""
        selected = self.anime_tree.selection()
        if not selected:
            self._log('No series selected.')
            return
        
        title = selected[0]
        current_flag = self.tracker.allows_multi_episode(title)
        new_flag = not current_flag
        
        self.tracker.set_multi_episode_flag(title, new_flag)
        
        status = "enabled" if new_flag else "disabled"
        self._log(f'Multi-episode downloads {status} for "{title}"')
        
        # Update the display to show the current status
        self._refresh_anime_display()
    
    def _refresh_anime_display(self):
        """Refresh the anime list display"""
        self._load_tracker()

    def _load_tracker(self):
        logging.debug('_load_tracker called')
        self.anime_tree.delete(*self.anime_tree.get_children())
        tracker_data = self.tracker.get_all()
        logging.debug(f'Tracker data count: {len(list(tracker_data))}')
        
        for title, info in self.tracker.get_all():
            logging.debug(f'Loading anime: {title} with info: {info}')
            multi_ep_status = " [Multi-Ep]" if info.get('allow_multi_episode', False) else ""
            display_title = title + multi_ep_status
            last_season = info.get('last_season', 1)
            last_episode = info.get('last_episode', 0)
            self.anime_tree.insert('', 'end', iid=title, values=(display_title, last_season, last_episode, info['url']))
            logging.debug(f'Inserted anime: {display_title}')
        
        logging.debug(f'_load_tracker completed. Tree children count: {len(self.anime_tree.get_children())}')

    def add_series(self):
        title = self.title_entry.get().strip()
        url = self.url_entry.get().strip()
        if not title or not url:
            self._log('Title and URL required.')
            return
        if self.tracker.add(title, url):
            self.anime_tree.insert('', 'end', iid=title, values=(title, 1, 0, url))
            self._log(f'Added series: {title}')
            self.title_entry.delete(0, 'end')
            self.url_entry.delete(0, 'end')
        else:
            self._log(f'Series already exists: {title}')

    def remove_series(self):
        selected = self.anime_tree.selection()
        if not selected:
            self._log('No series selected.')
            return
        for title in selected:
            self.tracker.remove(title)
            self.anime_tree.delete(title)
            self._log(f'Removed series: {title}')
    
    def edit_series(self):
        import logging
        try:
            logging.debug('[DEBUG] edit_series called')
            selected = self.anime_tree.selection()
            logging.debug('[DEBUG] anime_tree.selection: %s', selected)
            if not selected:
                logging.debug('[DEBUG] No selection in anime_tree when Edit Title pressed')
                self._log('No series selected.')
                return
            if len(selected) > 1:
                logging.debug('[DEBUG] Multiple selection in anime_tree when Edit Title pressed')
                self._log('Please select only one series to edit.')
                return
            old_title = selected[0]
            logging.debug('[DEBUG] Selected title: %s', old_title)
            current_values = self.anime_tree.item(old_title, 'values')
            logging.debug('[DEBUG] current_values: %s', current_values)
            current_url = current_values[2]
            print('[DEBUG] edit_series dialog opened for', old_title, 'with URL', current_url)
            dialog = tk.Toplevel(self.root)
            dialog.title('Edit Anime Series')
            dialog.geometry('400x220')
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f'+{x}+{y}')
            ttk.Label(dialog, text='Current Title:').pack(pady=5)
            ttk.Label(dialog, text=old_title, font=('TkDefaultFont', 9, 'bold')).pack(pady=5)
            ttk.Label(dialog, text='New Title:').pack(pady=5)
            new_title_entry = ttk.Entry(dialog, width=50)
            new_title_entry.insert(0, old_title)
            new_title_entry.pack(pady=5)
            new_title_entry.select_range(0, tk.END)
            new_title_entry.focus()
            ttk.Label(dialog, text='New URL:').pack(pady=5)
            new_url_entry = ttk.Entry(dialog, width=50)
            new_url_entry.insert(0, current_url)
            new_url_entry.pack(pady=5)
            print('[DEBUG] edit_series dialog URL entry created with value', new_url_entry.get())
            def save_edit():
                new_title = new_title_entry.get().strip()
                new_url = new_url_entry.get().strip()
                print('[DEBUG] edit_series save_edit called with', new_title, new_url)
                if not new_title or not new_url:
                    messagebox.showerror('Error', 'Title and URL cannot be empty.')
                    return
                if new_title == old_title and new_url == current_url:
                    dialog.destroy()
                    return
                # If title changed, use edit_title; if only URL changed, just update URL
                if new_title != old_title:
                    if self.tracker.edit_title(old_title, new_title):
                         self.tracker.data[new_title]['url'] = new_url
                         self.tracker.save()
                         self._load_tracker() # Easiest way to refresh correctly
                         self._log(f'Renamed series from "{old_title}" to "{new_title}" and updated URL.')
                         dialog.destroy()
                    else:
                        messagebox.showerror('Error', f'Failed to rename series. Title "{new_title}" may already exist.')
                else:
                    # Only URL changed
                    self.tracker.data[old_title]['url'] = new_url
                    self.tracker.save()
                    self._load_tracker() # Easiest way to refresh correctly
                    self._log(f'Updated URL for "{old_title}".')
                    dialog.destroy()
            def cancel_edit():
                dialog.destroy()
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            ttk.Button(button_frame, text='Save', command=save_edit).pack(side='left', padx=5)
            ttk.Button(button_frame, text='Cancel', command=cancel_edit).pack(side='left', padx=5)
            dialog.bind('<Return>', lambda e: save_edit())
            dialog.bind('<Escape>', lambda e: cancel_edit())
        except Exception as e:
            print('[DEBUG][ERROR] Exception in edit_series:', e)
            import traceback
            traceback.print_exc()

    def force_check(self):
        self._log('Manual check triggered.')
        threading.Thread(target=self._check_all, daemon=True).start()

    def save_config(self):
        self.qb_config.host = self.qb_host.get().strip()
        self.qb_config.port = int(self.qb_port.get().strip())
        self.qb_config.username = self.qb_user.get().strip()
        self.qb_config.password = self.qb_pass.get().strip()
        self.qb_config.category = self.qb_cat.get().strip()
        try:
            interval = int(self.interval_entry.get().strip())
            self.check_interval = max(1, interval) * 3600  # Convert hours to seconds
        except Exception:
            self.check_interval = DEFAULT_INTERVAL
        self._log('Configuration saved.')

    def _log(self, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.configure(state='normal')
        self.log_text.insert('end', f'[{timestamp}] {msg}\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def _start_periodic_check(self):
        self.check_thread = threading.Thread(target=self._periodic_check, daemon=True)
        self.check_thread.start()

    def _periodic_check(self):
        while not self.stop_event.is_set():
            self._check_all()
            for _ in range(self.check_interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def _check_all(self):
        self._log('Checking for new episodes...')
        qb = QBittorrentClient(self.qb_config)
        connected, err = qb.connect()
        if not connected:
            self._log(f'qBittorrent connection failed: {err}')
            return
        for title, info in self.tracker.get_all():
            url = info['url']
            last_s, last_ep = self.tracker.get_last_season_and_episode(title)
            try:
                latest_s, latest_ep, magnet = NyaaScraper.get_latest_episode_and_magnet(url, title, self.tracker)
                if latest_ep is None or magnet is None:
                    self._log(f'Failed to scrape: {title}')
                    continue
                if latest_s > last_s or (latest_s == last_s and latest_ep > last_ep):
                    ok, err = qb.add_magnet(magnet, self.qb_config.category)
                    if ok:
                        self.tracker.update_episode(title, latest_s, latest_ep)
                        self._update_tree_episode(title, latest_s, latest_ep)
                        self._log(f'New episode {latest_ep} for {title} sent to qBittorrent.')
                    else:
                        self._log(f'Failed to add magnet for {title}: {err}')
                else:
                    self._log(f'No new episode for {title}.')
            except Exception as e:
                self._log(f'Error checking {title}: {e}')

    def _update_tree_episode(self, title, season, episode):
        if self.anime_tree.exists(title):
            vals = list(self.anime_tree.item(title, 'values'))
            vals[1] = season
            vals[2] = episode
            self.anime_tree.item(title, values=vals)

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()

def run_headless():
    """Run the scraper in headless mode (command-line only)"""
    print("[DEBUG] Starting headless mode...")
    
    try:
        # Initialize components
        print("[DEBUG] Initializing AnimeTracker...")
        tracker = AnimeTracker()
        print(f"[DEBUG] Tracker loaded with {len(tracker.data)} entries")
        
        if len(tracker.data) == 0:
            print("[INFO] No anime entries found in tracker. Exiting.")
            return
        
        print("[DEBUG] Initializing QBittorrentConfig...")
        qb_config = QBittorrentConfig()
        print(f"[DEBUG] QB Config: {qb_config.host}:{qb_config.port}")
        
        # Test qBittorrent connection with timeout
        print("[DEBUG] Creating QBittorrentClient...")
        qb = QBittorrentClient(qb_config)
        
        print("[DEBUG] Attempting to connect to qBittorrent...")
        try:
            connected, err = qb.connect()
            if not connected:
                print(f'[ERROR] qBittorrent connection failed: {err}')
                print("[INFO] Continuing without qBittorrent connection for testing...")
                # Continue without qBittorrent for testing
                qb = None
            else:
                print("[DEBUG] Successfully connected to qBittorrent")
        except Exception as e:
            print(f"[ERROR] Exception during qBittorrent connection: {e}")
            print("[INFO] Continuing without qBittorrent connection for testing...")
            qb = None
        
        anime_list = list(tracker.get_all())
        print(f"[DEBUG] Processing {len(anime_list)} anime entries")
        
        # Limit to first 2 entries for testing
        test_limit = min(2, len(anime_list))
        print(f"[DEBUG] Testing with first {test_limit} entries only")
        
        for i, (title, info) in enumerate(anime_list[:test_limit]):
            print(f"[DEBUG] Processing {i+1}/{test_limit}: {title}")
            url = info['url']
            last_s = info.get('last_season', 1)
            last_ep = info.get('last_episode', 0)
            print(f"[DEBUG] URL: {url}, Last tracked: S{last_s}E{last_ep}")

            try:
                print(f"[DEBUG] Scraping latest episode for {title}...")
                # Simple scraping without timeout for Windows compatibility
                try:
                    latest_s, latest_ep, magnet = NyaaScraper.get_latest_episode_and_magnet(url, title, tracker)
                    print(f"[DEBUG] Scrape result - Season: {latest_s}, Episode: {latest_ep}, Magnet: {'Found' if magnet else 'None'}")
                except Exception as scrape_error:
                    print(f"[WARNING] Scraping failed for {title}: {scrape_error}")
                    continue

                if latest_ep is None or magnet is None:
                    print(f'[WARNING] Failed to scrape: {title}')
                    continue

                if latest_s > last_s or (latest_s == last_s and latest_ep > last_ep):
                    print(f"[DEBUG] New episode found: S{latest_s}E{latest_ep} > S{last_s}E{last_ep}")
                    if qb:
                        ok, err = qb.add_magnet(magnet, qb_config.category)
                        if ok:
                            tracker.update_episode(title, latest_s, latest_ep)
                            print(f'[SUCCESS] New episode S{latest_s}E{latest_ep} for {title} sent to qBittorrent.')
                        else:
                            print(f'[ERROR] Failed to add magnet for {title}: {err}')
                    else:
                        print(f'[INFO] Would download episode S{latest_s}E{latest_ep} for {title} (qBittorrent not connected)')
                        # Update tracker anyway for testing
                        tracker.update_episode(title, latest_s, latest_ep)
                else:
                    print(f'[INFO] No new episode for {title} (current: S{latest_s}E{latest_ep}, last: S{last_s}E{last_ep}).')
            except Exception as e:
                print(f'[ERROR] Exception checking {title}: {e}')
                import traceback
                traceback.print_exc()
        
        print("[DEBUG] Headless check completed successfully.")
        
    except Exception as e:
        print(f"[FATAL ERROR] Exception in run_headless: {e}")
        import traceback
        traceback.print_exc()



def setup_logging():
    """Set up logging for both console and file"""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File logger
    log_file = 'nyaa_scraper_debug.log'
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

def main():
    try:
        setup_logging()
        logging.info('Logging setup complete.')
        tracker_path = 'tracker.json'
        logging.info(f'Checking for tracker file at: {os.path.abspath(tracker_path)}')
        if not os.path.exists(tracker_path):
            logging.error('tracker.json not found!')
            return
        
        logging.debug('MAIN FUNCTION START')
        
        parser = argparse.ArgumentParser(description='Nyaa Auto Downloader')
        parser.add_argument('--headless', action='store_true', 
                           help='Run in headless mode (no GUI, single check)')
        parser.add_argument('--no-gui', action='store_true', 
                           help='Alias for --headless')

        
        args = parser.parse_args()
        
        logging.debug(f'ARGS PARSED: headless={args.headless}, no_gui={args.no_gui}')
        
        if args.headless or args.no_gui:
            logging.debug('RUNNING HEADLESS MODE')
            run_headless()
        else:
            logging.debug('STARTING GUI MODE')
            # Run GUI mode
            try:
                root = tk.Tk()
                logging.debug('TK ROOT CREATED')
                app = App(root)
                logging.debug('APP INSTANCE CREATED')
                root.protocol("WM_DELETE_WINDOW", app.on_close)
                logging.debug('STARTING MAINLOOP')
                root.mainloop()
                logging.debug('MAINLOOP ENDED')
            except Exception as gui_error:
                logging.exception(f'GUI ERROR: {gui_error}')
                
    except Exception as main_error:
        logging.exception(f'MAIN ERROR: {main_error}')
        input('Press Enter to exit...')

if __name__ == '__main__':
    main()