import qbittorrentapi
from settings import QBittorrentConfig


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
