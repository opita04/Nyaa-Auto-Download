# Nyaa Auto Download

A Python-based desktop application that automatically monitors and downloads anime episodes from Nyaa.si using qBittorrent. The application provides a user-friendly GUI for managing anime series, tracking episode releases, and automating the download process.

## Features

- **Anime Tracking**: Add and manage anime series with Nyaa.si URLs
- **Automatic Episode Detection**: Smart parsing of episode numbers and season information
- **qBittorrent Integration**: Seamless integration with qBittorrent for downloads
- **Search Functionality**: Built-in search panel for finding anime series
- **Settings Management**: Configurable download intervals and qBittorrent settings
- **Episode Management**: View and manage individual episodes for each series
- **Logging System**: Comprehensive logging for debugging and monitoring
- **Cross-platform**: Works on Windows, macOS, and Linux

## Screenshots

![Nyaa Auto Downloader Interface](images/nya-auto-downloader-screenshot.png)

*The main interface showing tracked anime management and Nyaa.si search functionality*

## Download Options

### 🚀 **Windows Executable (Recommended)**

**No Python installation required!**

1. **Download**: Go to [Releases](https://github.com/opita04/Nyaa-Auto-Download/releases) and download `NyaaAutoDownload.exe`
2. **Run**: Double-click the executable - that's it!
3. **Configure**: Set up qBittorrent connection in the app settings

**Requirements for executable:**
- Windows 10/11
- qBittorrent (with Web UI enabled)
- Internet connection

### 📝 **Source Code Installation**

**For developers or advanced users:**

**Requirements:**
- Python 3.7+
- qBittorrent (with Web UI enabled)
- Internet connection

## Installation (Source Code)

### 1. Clone the Repository

```bash
git clone https://github.com/opita04/Nyaa-Auto-Download.git
cd Nyaa-Auto-Download
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure qBittorrent

1. Open qBittorrent
2. Go to **Tools** → **Options** → **Web UI**
3. Enable the Web UI
4. Set a username and password
5. Note the port number (default: 8080)

### 4. Configure Settings

Edit `settings.py` to match your qBittorrent configuration:

```python
# qBittorrent Configuration
QBITTORRENT_HOST = "localhost"
QBITTORRENT_PORT = 8080
QBITTORRENT_USERNAME = "your_username"
QBITTORRENT_PASSWORD = "your_password"
```

## Usage

### Starting the Application

```bash
python main.py
```

### Adding Anime Series

1. Enter the anime title in the "Title" field
2. Paste the Nyaa.si URL in the "Nyaa.si URL" field
3. Click "Add Series"

### Managing Downloads

- The application automatically checks for new episodes at the configured interval
- Episodes are automatically downloaded to your qBittorrent client
- Use the settings panel (⚙️) to configure download intervals and qBittorrent settings
- Use the search panel (🔍) to find anime series

### Episode Management

- Click on a series to view its episodes
- Episodes are automatically parsed and categorized
- Multi-episode releases are properly handled
- Season information is extracted when available

## Project Structure

```
Nyaa-Auto-Download/
├── main.py                 # Main application entry point
├── settings.py            # Configuration settings
├── requirements.txt       # Python dependencies
├── modules/
│   ├── anime_tracker.py   # Anime series management
│   ├── nyaa_scraper.py   # Nyaa.si scraping and parsing
│   ├── qbittorrent_client.py # qBittorrent API integration
│   └── settings_panel.py # Settings management GUI
├── utils/
│   └── logging_utils.py  # Logging configuration
└── documentation/         # Project documentation
```

## Configuration Options

### Download Intervals

- **Default Interval**: 5 minutes
- **Configurable**: Adjustable through the settings panel
- **Real-time**: Immediate checking available

### qBittorrent Settings

- **Host**: qBittorrent server address
- **Port**: Web UI port number
- **Authentication**: Username and password
- **Download Path**: Default download directory

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check qBittorrent Web UI settings and firewall
2. **Authentication Error**: Verify username/password in settings
3. **No Episodes Found**: Check Nyaa.si URL format and series availability
4. **Download Not Starting**: Ensure qBittorrent is running and accessible

### Logs

The application creates detailed logs in the `backup/logs/` directory. Check these files for debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This application is for educational and personal use only. Please respect copyright laws and only download content you have the right to access. The developers are not responsible for any misuse of this software.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/opita04/Nyaa-Auto-Download/issues) page
2. Create a new issue with detailed information
3. Include logs and error messages when possible

## Changelog

### Version 1.0.0
- Initial release
- Basic anime tracking functionality
- qBittorrent integration
- GUI interface
- Episode parsing and management

---

**Note**: This application requires qBittorrent to be running with the Web UI enabled for proper functionality.
