# Nyaa Auto Download - Current Context

## Current Features
- **Anime Tracking**: Add and manage anime series with Nyaa.si URLs
- **Context Menu Interface**: Right-click anime entries for actions (Remove, Edit, Toggle Multi-Episode)
- **Automatic Episode Detection**: Smart parsing of episode numbers and season information
- **Multi-Client Torrent Support**: Supports qBittorrent, system default, and custom torrent clients with automatic fallback
- **Search Functionality**: Built-in search panel for finding anime series
- **Settings Management**: Configurable download intervals and torrent client settings
- **Episode Management**: View and manage individual episodes for each series
- **Logging System**: Comprehensive logging for debugging and monitoring
- **Cross-platform Support**: Works on Windows, macOS, and Linux

## In-Progress Work
- **Project Documentation**: Creating proper context files for development workflow
- **Code Quality**: Implementing logging guidelines and development standards
- **Warp Terminal Integration**: Adapting project rules for terminal-based development

## Dependencies
### Core Dependencies
- Python 3.7+
- tkinter (GUI framework)
- requests (HTTP requests)
- qBittorrent (with Web UI enabled)

### Python Packages (from requirements.txt)
- requests
- Other dependencies as specified in requirements.txt

### External Services
- Nyaa.si (torrent indexer)
- qBittorrent Web API

## Known Issues
- Context documentation files were missing (being created now)
- Need to ensure all logging follows the established guidelines
- Project structure documentation needs to be updated

## Current Development Environment
- **Platform**: Windows
- **Shell**: PowerShell (pwsh) 7.5.2
- **Working Directory**: C:\AI\Nyaa-Auto-Download
- **Terminal**: Warp Terminal

## Recent Changes
- **UI Improvement**: Moved anime management from buttons to right-click context menu (2025-08-23)
- **Interface Cleanup**: Removed visual clutter by consolidating actions into context menu
- Created warp.md rules file for development standards
- Setting up cursor-docs directory structure
- Implementing project context management system
