#!/usr/bin/env python3
"""
Build script for Nyaa Auto Download executable using PyInstaller
This script creates a single executable file without including personal data
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_directories():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            try:
                shutil.rmtree(dir_name)
                print(f"✅ Cleaned {dir_name}")
            except PermissionError as e:
                print(f"⚠️  Warning: Could not clean {dir_name} - {e}")
                print(f"   This is usually fine - PyInstaller will overwrite files")
            except Exception as e:
                print(f"⚠️  Warning: Error cleaning {dir_name} - {e}")

def create_executable():
    """Create the executable using PyInstaller"""
    print("Creating executable with PyInstaller...")
    
    # PyInstaller command with all necessary options
    cmd = [
        'pyinstaller',
        '--onefile',                    # Create single executable
        '--windowed',                   # No console window (GUI app)
        '--name=NyaaAutoDownload',      # Executable name
        '--add-data=modules;modules',   # Include modules folder
        '--add-data=utils;utils',       # Include utils folder
        '--hidden-import=tkinter',      # Ensure tkinter is included
        '--hidden-import=requests',     # Ensure requests is included
        '--hidden-import=beautifulsoup4', # Ensure beautifulsoup4 is included
        '--exclude-module=pytest',      # Exclude test modules
        '--exclude-module=unittest',    # Exclude test modules
        'main.py'                       # Main entry point
    ]
    
    # Add icon if it exists
    icon_path = 'app_icon.ico'
    if os.path.exists(icon_path):
        cmd.extend(['--icon', icon_path])
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executable created successfully!")
        print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create executable: {e}")
        print(f"Error output: {e.stderr}")
        return False

def verify_executable():
    """Verify the executable was created"""
    exe_path = os.path.join('dist', 'NyaaAutoDownload.exe')
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✅ Executable found: {exe_path}")
        print(f"📦 Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ Executable not found at: {exe_path}")
        return False

def main():
    """Main build process"""
    print("🚀 Building Nyaa Auto Download executable...")
    print("=" * 50)
    
    # Check if PyInstaller is installed
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
        print("✅ PyInstaller found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("✅ PyInstaller installed")
    
    # Clean previous builds
    clean_build_directories()
    
    # Create executable
    if create_executable():
        if verify_executable():
            print("\n🎉 Build completed successfully!")
            print("📁 Your executable is in the 'dist' folder")
            print("💡 You can now distribute this .exe file without worrying about personal data")
            print("\n📋 Next steps:")
            print("1. Test the executable on a different computer")
            print("2. Create a GitHub release")
            print("3. Upload the .exe as a release asset")
        else:
            print("\n❌ Build failed - executable not found")
    else:
        print("\n❌ Build failed")

if __name__ == '__main__':
    main()
