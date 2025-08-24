# Nyaa Auto Download - Changelog

## [2025-08-24] - Documentation Cleanup and Knowledge Consolidation

### Changed
- **cursor-docs/ARCHITECTURE.md**: Added comprehensive "Torrent Client Compatibility" section with detailed documentation of multi-client support
- **cursor-docs/CURSOR-CONTEXT.md**: Updated "Current Features" to reflect multi-client torrent support and automatic fallback capabilities
- **Project Structure**: Cleaned project structure in ARCHITECTURE.md to reflect removed files

### Removed
- **TORRENT_CLIENT_COMPATIBILITY.md**: Integrated content into cursor-docs/ARCHITECTURE.md for centralized knowledge management
- **docs/refactor_map.md**: Removed outdated refactoring planning documentation that is no longer relevant
- **documentation/REFACTOR_SUMMARY.md**: Removed completed historical refactoring documentation 
- **Empty directories**: Removed `docs/` and `documentation/` directories after file cleanup

### Improved
- **Knowledge Centralization**: All development-relevant documentation now consolidated in cursor-docs/ as required by warp.md rules
- **Project Clarity**: Removed loose markdown files that didn't serve current development needs
- **Documentation Consistency**: Torrent client information now integrated with architectural overview

### Technical Details
- Preserved README.md as standard project documentation for public repository
- Torrent client compatibility information moved to ARCHITECTURE.md under new dedicated section
- Updated project structure diagrams to reflect cleaned file structure
- Enhanced CURSOR-CONTEXT.md to include multi-client support in current features

### Files Modified
- `cursor-docs/ARCHITECTURE.md` - Added torrent client compatibility section, updated project structure
- `cursor-docs/CURSOR-CONTEXT.md` - Updated current features to include multi-client support

### Files Removed  
- `TORRENT_CLIENT_COMPATIBILITY.md` - Content integrated into ARCHITECTURE.md
- `docs/refactor_map.md` - Outdated refactoring plans
- `documentation/REFACTOR_SUMMARY.md` - Historical refactoring summary
- `docs/` directory - Empty after file cleanup
- `documentation/` directory - Empty after file cleanup

### Reason for Change
- **warp.md Compliance**: Follow project context management rules requiring knowledge consolidation in cursor-docs/
- **Maintainability**: Remove outdated documentation that could confuse future development
- **Organization**: Centralize all development-relevant documentation for easier maintenance
- **Clarity**: Eliminate redundant or obsolete files that don't serve current project needs

---

## [2025-08-23] - UI Improvement: Context Menu Implementation

### Changed
- **main.py**: Moved anime management actions from always-visible buttons to right-click context menu
- **UI Layout**: Removed individual "Remove Series", "Edit Title", and "Toggle Multi-Episode" buttons from main interface
- **Context Menu**: Enhanced right-click menu to include all anime-specific actions with separator for better organization
- **Space Efficiency**: Freed up vertical space by keeping only the global "Force Check Now" button

### Improved
- **User Experience**: More intuitive interface following standard UI patterns (right-click to act on specific items)
- **Visual Design**: Cleaner main interface with less visual clutter
- **Context Sensitivity**: Actions now only appear when relevant (when right-clicking on actual anime entries)

### Technical Details
- Modified context menu creation in _setup_gui() method
- Removed button grid layout (rows 1-3) and kept only Force Check Now button (row 1)
- All existing functionality preserved - only access method changed
- No changes to underlying anime management logic
- **Panel Consistency Fixes**:
  - Added proper visibility state initialization for all panels
  - Added missing `toggle_bulk_torrents_panel()` function for consistent behavior
  - Fixed mutual exclusion between panels (only one panel open at a time)
  - Standardized all panel toggle patterns for consistent user experience

### Files Modified
- `main.py` - Lines ~228-241: Context menu setup and button removal

### Executable Rebuild
- **Rebuilt**: Successfully rebuilt executable using PyInstaller 6.14.1 (Second build)
- **File Size**: 18.8 MB (`dist/NyaDownloader.exe`)
- **Build Time**: 2025-08-23 1:27 PM
- **Context Menu**: New executable includes the context menu functionality
- **Panel Fixes**: Updated executable includes consistent panel toggle behavior

### Documentation Update
- **warp.md**: Added comprehensive "EXECUTABLE BUILD LESSONS LEARNED" section
- **Build Process**: Documented spec file priority issues and reliable build methods
- **Troubleshooting**: Added common failure patterns and solutions
- **PowerShell Syntax**: Documented proper executable launch syntax

### Reason for Change
- **User Request**: Move anime-specific actions from buttons to right-click context menu
- **UI Best Practices**: Follow standard file manager / list view interaction patterns
- **Screen Real Estate**: Reduce visual clutter and make better use of available space
- **Process Improvement**: Document build lessons to prevent future issues

---

## [2025-08-23] - Executable Rebuild and Environment Fix

### Fixed
- **Build Environment**: Removed obsolete `typing` package (v3.7.4.3) that was causing PyInstaller incompatibility
- **Executable Generation**: Successfully rebuilt executable with updated dependencies
- **Spec File Usage**: Switched to `NyaDownloader.spec` for proper executable naming

### Changed
- **Executable**: Fresh build of `dist/NyaDownloader.exe` (18.8 MB)
- **Build Process**: Cleaned all build artifacts, __pycache__ directories, and previous executables
- **Settings Preservation**: All user settings (settings.json, tracker.json) preserved during rebuild

### Technical Details
- Build completed using PyInstaller 6.14.1 with Python 3.10.11
- Executable tested in both GUI and headless modes
- No data loss during rebuild process
- Clean build environment established

---

## [2025-08-23] - Project Documentation Setup

### Added
- **cursor-docs/CURSOR-CONTEXT.md**: Created comprehensive project context documentation
  - Current features overview
  - In-progress work tracking
  - Dependencies listing
  - Known issues documentation
  - Development environment details
  
- **cursor-docs/ARCHITECTURE.md**: Created detailed project architecture documentation
  - Complete project structure mapping
  - Core component descriptions
  - Data flow documentation
  - Design patterns overview
  - External dependencies listing
  - Development standards reference

- **cursor-docs/CHANGELOG.md**: Created this changelog for tracking project changes
  - Initial project history documentation
  - Future change tracking structure

- **warp.md**: Created Warp Terminal development rules
  - Project context management rules
  - Logging guidelines (3-5 logs per function max)
  - Development workflow standards
  - Warp-specific guidelines for PowerShell environment
  - Input validation, rate limiting, and security standards

### Purpose
Established proper project documentation structure following development workflow standards. These files enable:
- Consistent development practices across different environments
- Proper context tracking for all changes
- Architecture awareness for future modifications
- Change history preservation

### Technical Details
- Files created in Windows PowerShell environment
- Following Warp Terminal compatibility guidelines
- Documentation structure mirrors cursor IDE standards
- All files use Windows line endings (CRLF) for consistency

---

## Historical Context (Pre-Documentation)

### Version 1.0.0 - Initial Release
- Basic anime tracking functionality
- qBittorrent integration
- GUI interface with tkinter
- Episode parsing and management
- Nyaa.si scraping capabilities
- Settings management system
- Cross-platform support
- Comprehensive logging system

### Project Structure Establishment
- Modular architecture with separate modules/ directory
- Utility functions in utils/ directory  
- Configuration management in settings.py
- Documentation in multiple directories (docs/, documentation/)
- Build scripts and configuration files
- Git version control setup
