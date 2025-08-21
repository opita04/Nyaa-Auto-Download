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
        except qbittorrentapi.exceptions.APIConnectionError as e:
            error_msg = (f"Cannot connect to qBittorrent at {self.config.host}:{self.config.port}. "
                        "Please ensure qBittorrent is running and the Web UI is enabled. "
                        "Check that the IP address and port are correct.")
            print(f"[DEBUG] Connection failed: {error_msg}")
            return False, error_msg
        except qbittorrentapi.exceptions.LoginFailed as e:
            error_msg = (f"Authentication failed for qBittorrent. Please check your username and password. "
                        f"Make sure Web UI authentication is enabled in qBittorrent settings.")
            print(f"[DEBUG] Login failed: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"qBittorrent connection error: {str(e)}. Please check your settings and ensure qBittorrent is running."
            print(f"[DEBUG] Connection failed: {error_msg}")
            return False, error_msg

    def add_magnet(self, magnet, category=None):
        try:
            kwargs = {'urls': magnet}
            if category:
                kwargs['category'] = category
            self.client.torrents_add(**kwargs)
            return True, ''
        except qbittorrentapi.exceptions.Conflict409Error as e:
            error_msg = "Torrent already exists in qBittorrent or the magnet link is invalid."
            return False, error_msg
        except qbittorrentapi.exceptions.Forbidden403Error as e:
            error_msg = "Access denied. Please check your qBittorrent permissions."
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to add torrent to qBittorrent: {str(e)}"
            return False, error_msg
