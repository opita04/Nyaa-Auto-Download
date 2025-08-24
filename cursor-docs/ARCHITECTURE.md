# Nyaa Auto Download - Architecture Documentation

## Project Structure

```
Nyaa-Auto-Download/
├── main.py                         # Main application entry point
├── main_new.py                     # New version of main application
├── settings.py                     # Configuration settings and classes
├── requirements.txt                # Python dependencies
├── warp.md                        # Warp Terminal development rules
├── .cursorrules                   # Cursor IDE rules
├── .gitignore                     # Git ignore file
├── .gitattributes                 # Git attributes
├── LICENSE                        # MIT License
├── README.md                      # Project documentation
├── build_exe.py                   # Executable build script
├── rebuild_exe.bat                # Windows batch script for rebuilding
├── tatus                         # Status file (possibly temp)
├── nyaa_auto_download/           # Main package directory
│   └── __init__.py               # Package initialization
├── modules/                       # Core application modules
│   ├── __init__.py               # Package initialization
│   ├── anime_tracker.py          # Anime series management and tracking
│   ├── generic_torrent_client.py # Generic torrent client interface
│   ├── nyaa_scraper.py           # Nyaa.si scraping and parsing
│   ├── qbittorrent_client.py     # qBittorrent API integration
│   └── settings_panel.py         # Settings management GUI
├── utils/                         # Utility functions
│   ├── __init__.py               # Package initialization
│   └── logging_utils.py          # Logging configuration and utilities
├── cursor-docs/                   # Project context documentation
│   ├── ARCHITECTURE.md           # This file - project architecture
│   ├── CHANGELOG.md              # Change history and updates
│   └── CURSOR-CONTEXT.md         # Current project context and status
└── images/                       # Image assets
    └── .gitkeep                  # Keep directory in git
```

## Core Components

### Main Application (`main.py`)
- **Purpose**: Primary entry point for the GUI application
- **Key Classes**: `App` class manages the entire application lifecycle
- **Dependencies**: All modules and utilities
- **Functionality**: 
  - GUI setup and management
  - Thread management for periodic checks
  - Settings loading/saving
  - qBittorrent health monitoring

### Modules Directory
#### `anime_tracker.py`
- **Purpose**: Manages anime series data and tracking
- **Key Classes**: `AnimeTracker`
- **Functionality**: Series management, episode tracking, data persistence

#### `nyaa_scraper.py`
- **Purpose**: Web scraping and parsing for Nyaa.si
- **Key Classes**: `NyaaScraper`
- **Functionality**: URL parsing, episode detection, torrent link extraction

#### `qbittorrent_client.py`
- **Purpose**: qBittorrent Web API integration
- **Key Classes**: `QBittorrentClient`
- **Functionality**: Torrent management, download initiation, connection handling

#### `generic_torrent_client.py`
- **Purpose**: Generic interface for torrent clients
- **Key Classes**: `GenericTorrentClient`
- **Functionality**: Abstraction layer for different torrent clients

#### `settings_panel.py`
- **Purpose**: GUI for settings management
- **Key Classes**: Settings panel components
- **Functionality**: Settings UI, configuration management

### Utilities Directory
#### `logging_utils.py`
- **Purpose**: Centralized logging configuration
- **Functionality**: Log setup, trace file creation, logging utilities

### Configuration (`settings.py`)
- **Purpose**: Application configuration and settings classes
- **Key Classes**: 
  - `QBittorrentConfig`
  - `TorrentClientConfig`
  - `QualitySettings`
  - `SettingsManager`
  - `GUISettings`

## Data Flow

1. **User Input** → GUI (main.py)
2. **Series Management** → AnimeTracker → Data persistence
3. **Episode Detection** → NyaaScraper → Episode parsing
4. **Download Initiation** → Generic/QBittorrent Client → qBittorrent API
5. **Logging** → LoggingUtils → Log files

## Key Design Patterns

- **Modular Architecture**: Separated concerns into distinct modules
- **Configuration Management**: Centralized settings with dedicated classes
- **Generic Client Interface**: Abstraction for different torrent clients
- **Thread-based Operations**: Non-blocking periodic checks and health monitoring
- **GUI Separation**: Clear separation between business logic and presentation

## External Dependencies

- **qBittorrent**: External torrent client with Web API
- **Nyaa.si**: External torrent indexer website
- **Python Standard Library**: tkinter, threading, requests, etc.

## Torrent Client Compatibility

The application supports multiple torrent client configurations to provide flexibility in user setups:

### Supported Client Types

#### 1. qBittorrent (Default)
- **Description**: Full API integration with connection testing and error reporting
- **Features**: Category support, detailed status monitoring, Web UI integration
- **Requirements**: qBittorrent running with Web UI enabled
- **Configuration**: Host, port, username, password in settings

#### 2. System Default
- **Description**: Uses system's default magnet link handler
- **Platform Support**:
  - **Windows**: Uses `os.startfile()` to launch default handler
  - **macOS**: Uses `open` command for default application
  - **Linux**: Uses `xdg-open` with browser fallback
- **Benefits**: Works with any installed torrent client set as system default

#### 3. Custom Command
- **Description**: User-defined commands for launching magnet links
- **Requirements**: Command must contain `{magnet}` placeholder for link substitution
- **Examples**:
  - Windows uTorrent: `"C:\Program Files (x86)\uTorrent\uTorrent.exe" "{magnet}"`
  - macOS Transmission: `open -a Transmission "{magnet}"`
  - Linux Transmission: `transmission-remote --add "{magnet}"`

### Fallback Behavior
- **Automatic Fallback**: When qBittorrent connection fails, can automatically try system default
- **User Control**: Fallback behavior configurable in settings
- **Error Handling**: Comprehensive error reporting for each client type
- **Platform Detection**: Automatic handling of platform-specific launch methods

### Client Selection
- **Settings Panel**: Dropdown selection for preferred torrent client
- **Custom Command Field**: Appears when "Custom Command" option is selected
- **Connection Testing**: Test functionality available for all client types
- **Migration Support**: Existing users maintain qBittorrent as default

## Development Standards

- **Logging**: Follow guidelines in warp.md for targeted logging
- **Documentation**: Maintain cursor-docs files for context tracking
- **Code Quality**: Implement input validation, error handling, and rate limiting
