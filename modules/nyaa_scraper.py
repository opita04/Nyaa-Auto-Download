import re
import requests
import logging
from bs4 import BeautifulSoup


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
            return None, None, None
        except Exception as e:
            logging.error(f"An unexpected error occurred during scraping {url}: {e}", exc_info=True)
            return None, None, None
