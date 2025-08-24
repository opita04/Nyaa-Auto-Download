# Building Executable and Distribution Guide

This guide explains how to create an executable version of Nyaa Auto Download for distribution.

## Quick Start

### Method 1: Using the Build Script (Recommended)
```bash
# Double-click build.bat or run:
python build_exe.py
```

### Method 2: Manual PyInstaller
```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --name=NyaaAutoDownload --add-data=modules;modules --add-data=utils;utils main.py
```

## What Gets Included vs Excluded

### ✅ **INCLUDED in executable:**
- All Python code (.py files)
- Required dependencies (requests, beautifulsoup4, tkinter)
- Python interpreter
- Application modules and utilities

### ❌ **EXCLUDED from executable:**
- `tracker.json` (your anime list)
- `settings.json` (your qBittorrent credentials)
- `logs/` folder (your application logs)
- Personal cache and temporary files

### 🔒 **Privacy Protection:**
Your personal data is **NEVER** included in the executable. Each user creates their own settings and tracker files when they first run the app.

## Distribution via GitHub

### Step 1: Create the Executable
```bash
python build_exe.py
```
This creates `dist/NyaaAutoDownload.exe` (typically 15-30 MB)

### Step 2: Test the Executable
1. Copy the .exe to a different folder
2. Run it to ensure it works independently
3. Test on a clean system if possible

### Step 3: Create GitHub Release
1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version (e.g., `v1.0.0`)
4. Upload the executable as an asset

### Step 4: Release Files Structure
```
Your Release Assets:
├── NyaaAutoDownload-v1.0.0.exe (Windows executable)
├── README.md (usage instructions)
└── checksums.txt (optional - file verification)
```

## Advanced: Creating an Installer

If you want a proper installer instead of just an .exe:

### Using Inno Setup (Windows)
1. Download Inno Setup from https://jrsoftware.org/isinfo.php
2. Create an installer script that:
   - Installs the .exe to Program Files
   - Creates desktop shortcut
   - Adds to Start Menu
   - Handles uninstallation

### Sample Inno Setup Script
```inno
[Setup]
AppName=Nyaa Auto Download
AppVersion=1.0.0
DefaultDirName={pf}\NyaaAutoDownload
DefaultGroupName=Nyaa Auto Download
OutputBaseFilename=NyaaAutoDownload-Setup-v1.0.0

[Files]
Source: "dist\NyaaAutoDownload.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\Nyaa Auto Download"; Filename: "{app}\NyaaAutoDownload.exe"
Name: "{desktop}\Nyaa Auto Download"; Filename: "{app}\NyaaAutoDownload.exe"
```

## File Size Optimization

Your executable will be approximately:
- **Basic build**: ~15-25 MB
- **With all dependencies**: ~20-35 MB

To reduce size:
```bash
# Use UPX compression (optional)
pyinstaller --onefile --windowed --upx-dir=/path/to/upx main.py
```

## Troubleshooting

### Common Issues:
1. **"Module not found"** - Add `--hidden-import=module_name`
2. **Large file size** - Use `--exclude-module` for unused packages
3. **Antivirus warnings** - Normal for PyInstaller executables, submit for allowlisting

### Testing Checklist:
- [ ] Executable runs without Python installed
- [ ] Creates its own settings.json and tracker.json
- [ ] Connects to qBittorrent properly
- [ ] All GUI elements function correctly
- [ ] No personal data embedded in file

## Automated Builds (Advanced)

Create a GitHub Action to automatically build releases:

```yaml
# .github/workflows/build-release.yml
name: Build Release
on:
  release:
    types: [created]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build executable
        run: python build_exe.py
      - name: Upload Release Asset
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: ./dist/NyaaAutoDownload.exe
          asset_name: NyaaAutoDownload-${{ github.event.release.tag_name }}.exe
          asset_content_type: application/octet-stream
```

---

## Summary

✅ **Safe to distribute**: Your executable contains NO personal data  
✅ **Easy to build**: Just run `python build_exe.py`  
✅ **GitHub ready**: Upload .exe directly to releases  
✅ **User-friendly**: Each user gets their own clean setup  

The executable is completely self-contained and safe to share publicly!
