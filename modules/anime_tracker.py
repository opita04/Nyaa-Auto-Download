import json
import os
import logging
from settings import TRACKER_FILE


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
