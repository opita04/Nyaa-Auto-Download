# Torrent Client Compatibility Enhancement

This enhancement adds support for multiple torrent clients beyond qBittorrent, allowing users to launch magnet links with their preferred torrent application.

## Supported Torrent Clients

The application now supports three types of torrent client configurations:

### 1. qBittorrent (Default)
- **Description**: The original qBittorrent integration with full API support
- **Features**: Category support, connection testing, detailed error reporting
- **Requirements**: qBittorrent running with Web UI enabled

### 2. System Default
- **Description**: Uses the system's default application for magnet links
- **Features**: Works with any torrent client set as default
- **Platform Support**:
  - **Windows**: Uses `os.startfile()`
  - **macOS**: Uses `open` command
  - **Linux**: Uses `xdg-open` with fallback to `webbrowser` module

### 3. Custom Command
- **Description**: Allows custom commands for launching magnet links
- **Features**: Full flexibility for custom torrent client setups
- **Requirements**: Command must contain `{magnet}` placeholder

## Configuration Options

### In Settings Panel
1. **Torrent Client Dropdown**: Choose between qBittorrent, System Default, or Custom Command
2. **Custom Command Field**: Appears only when "Custom Command" is selected
3. **Fallback Option**: Automatically fall back to system default if qBittorrent fails

### Custom Command Examples

#### Windows (uTorrent)
```bash
"C:\Program Files (x86)\uTorrent\uTorrent.exe" "{magnet}"
```

#### Windows (Deluge)
```bash
"C:\Program Files\Deluge\deluge.exe" "{magnet}"
```

#### macOS (Transmission)
```bash
open -a Transmission "{magnet}"
```

#### Linux (Transmission)
```bash
transmission-remote --add "{magnet}"
```

## Fallback Behavior

When qBittorrent is selected as the preferred client but connection fails:

1. **With Fallback Enabled**: Automatically tries system default
2. **Without Fallback**: Shows error message and stops

## Error Handling

The system provides comprehensive error handling:

- **Connection Tests**: Test any configured torrent client
- **Graceful Fallbacks**: Seamless fallback to system default
- **Detailed Error Messages**: Specific error reporting for each client type
- **Platform Detection**: Automatic platform-specific handling

## Benefits

1. **Universal Compatibility**: Works with any torrent client that supports magnet links
2. **No Vendor Lock-in**: Users aren't forced to use qBittorrent
3. **Flexibility**: Custom commands for specialized setups
4. **Reliability**: Fallback mechanisms ensure downloads always work
5. **User Choice**: Choose the torrent client that best fits your needs

## Migration Guide

Existing users will continue to use qBittorrent by default. To change torrent clients:

1. Open the settings panel (⚙️ button)
2. Select your preferred torrent client from the dropdown
3. Configure custom command if needed
4. Enable/disable fallback as desired
5. Click "Save Config"
6. Test the connection

## Troubleshooting

### System Default Issues
- **Windows**: Ensure a default magnet link handler is set
- **macOS**: Check default application settings for magnet links
- **Linux**: Verify xdg-open is configured for magnet links

### Custom Command Issues
- Ensure the command contains `{magnet}` placeholder
- Test the command manually in terminal first
- Check file paths and permissions
- Verify the torrent client accepts command-line arguments

### Connection Test Failures
- For qBittorrent: Verify Web UI is enabled and credentials are correct
- For System Default: Ensure a torrent client is installed and set as default
- For Custom Command: Verify the command is valid and executable

## Security Considerations

- Custom commands are executed as the current user
- Only use trusted torrent client executables
- Avoid commands that could be exploited
- The application validates custom commands contain the `{magnet}` placeholder

## Future Enhancements

Potential improvements for future versions:

1. **More Built-in Clients**: Direct support for popular clients like Deluge, Transmission, etc.
2. **Client Detection**: Automatic detection of installed torrent clients
3. **Advanced Configuration**: Per-client configuration options
4. **Batch Operations**: Support for multiple magnet links simultaneously
