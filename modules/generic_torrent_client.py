import subprocess
import webbrowser
import platform
import os
from settings import TorrentClientConfig

class GenericTorrentClient:
    """Generic torrent client launcher that works with any torrent client"""

    def __init__(self, config: TorrentClientConfig = None):
        self.config = config or TorrentClientConfig()

    def launch_magnet(self, magnet_link, category=None):
        """
        Launch a magnet link using the configured torrent client

        Args:
            magnet_link (str): The magnet link to launch
            category (str, optional): Category for qBittorrent (ignored for other clients)

        Returns:
            tuple: (success: bool, error_message: str)
        """
        try:
            if self.config.preferred_client == 'qbittorrent':
                return self._launch_with_qbittorrent(magnet_link, category)
            elif self.config.preferred_client == 'custom':
                return self._launch_with_custom_command(magnet_link)
            elif self.config.preferred_client == 'default':
                return self._launch_with_system_default(magnet_link)
            else:
                return False, f"Unsupported torrent client: {self.config.preferred_client}"

        except Exception as e:
            error_msg = f"Failed to launch magnet link: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg

    def _launch_with_qbittorrent(self, magnet_link, category=None):
        """Launch magnet link using qBittorrent"""
        try:
            from modules.qbittorrent_client import QBittorrentClient
            from settings import QBittorrentConfig

            qb_config = QBittorrentConfig()
            qb = QBittorrentClient(qb_config)
            connected, err = qb.connect()

            if connected:
                ok, err = qb.add_magnet(magnet_link, category)
                if ok:
                    return True, ""
                else:
                    return False, f"qBittorrent error: {err}"
            else:
                if self.config.fallback_to_default:
                    print(f"[INFO] qBittorrent not available, falling back to system default")
                    return self._launch_with_system_default(magnet_link)
                else:
                    return False, f"qBittorrent connection failed: {err}"

        except Exception as e:
            if self.config.fallback_to_default:
                print(f"[INFO] qBittorrent failed, falling back to system default: {e}")
                return self._launch_with_system_default(magnet_link)
            else:
                return False, f"qBittorrent error: {str(e)}"

    def _launch_with_custom_command(self, magnet_link):
        """Launch magnet link using a custom command"""
        try:
            if not self.config.custom_command:
                return False, "No custom command configured"

            # Replace placeholders in custom command
            command = self.config.custom_command.replace("{magnet}", magnet_link)

            # Execute the command
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                return True, ""
            else:
                return False, f"Custom command failed: {result.stderr}"

        except Exception as e:
            return False, f"Custom command error: {str(e)}"

    def _launch_with_system_default(self, magnet_link):
        """Launch magnet link using the system's default application"""
        try:
            # Try to open the magnet link with the default system application
            if platform.system() == "Windows":
                # On Windows, use os.startfile
                os.startfile(magnet_link)
                return True, ""
            elif platform.system() == "Darwin":  # macOS
                # On macOS, use the 'open' command
                result = subprocess.run(['open', magnet_link], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, ""
                else:
                    return False, f"macOS open command failed: {result.stderr}"
            else:  # Linux and other Unix-like systems
                # Try xdg-open first, then fall back to webbrowser
                try:
                    result = subprocess.run(['xdg-open', magnet_link], capture_output=True, text=True)
                    if result.returncode == 0:
                        return True, ""
                    else:
                        raise Exception("xdg-open failed")
                except (FileNotFoundError, Exception):
                    # Fallback to webbrowser module
                    webbrowser.open(magnet_link)
                    return True, ""

        except Exception as e:
            return False, f"System default launcher error: {str(e)}"

    def test_connection(self):
        """
        Test if the preferred torrent client is available

        Returns:
            tuple: (available: bool, error_message: str)
        """
        try:
            if self.config.preferred_client == 'qbittorrent':
                return self._test_qbittorrent_connection()
            elif self.config.preferred_client == 'custom':
                return self._test_custom_command()
            elif self.config.preferred_client == 'default':
                return True, ""  # System default is always "available"
            else:
                return False, f"Unsupported torrent client: {self.config.preferred_client}"

        except Exception as e:
            return False, f"Connection test error: {str(e)}"

    def _test_qbittorrent_connection(self):
        """Test qBittorrent connection"""
        try:
            from modules.qbittorrent_client import QBittorrentClient
            from settings import QBittorrentConfig

            qb_config = QBittorrentConfig()
            qb = QBittorrentClient(qb_config)
            connected, err = qb.connect()

            if connected:
                return True, ""
            else:
                if self.config.fallback_to_default:
                    return True, "qBittorrent not available, will fallback to system default"
                else:
                    return False, f"qBittorrent connection failed: {err}"

        except Exception as e:
            if self.config.fallback_to_default:
                return True, "qBittorrent not available, will fallback to system default"
            else:
                return False, f"qBittorrent error: {str(e)}"

    def _test_custom_command(self):
        """Test custom command (basic validation)"""
        try:
            if not self.config.custom_command:
                return False, "No custom command configured"

            # Basic validation - check if command contains required placeholder
            if "{magnet}" not in self.config.custom_command:
                return False, "Custom command must contain {magnet} placeholder"

            return True, ""

        except Exception as e:
            return False, f"Custom command validation error: {str(e)}"
