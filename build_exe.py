#!/usr/bin/env python3
"""
Build script for Nyaa Auto Downloader executable.
Automatically removes old build artifacts and creates a new executable.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_artifacts():
    """Remove existing build artifacts"""
    print("🧹 Cleaning existing build artifacts...")

    # Remove executable
    exe_path = Path("dist/Nyaa.si Anime Auto Downloader.exe")
    if exe_path.exists():
        print(f"Removing {exe_path}")
        exe_path.unlink()

    # Remove build directory
    build_dir = Path("build")
    if build_dir.exists():
        print(f"Removing {build_dir}")
        shutil.rmtree(build_dir)

    # Clean __pycache__ directories
    for pycache_dir in Path(".").rglob("__pycache__"):
        if pycache_dir.is_dir():
            print(f"Removing {pycache_dir}")
            shutil.rmtree(pycache_dir)

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")

    # Try to use existing spec file first
    spec_files = ["NyaaAutoDownloader.spec", "Nyaa.si Anime Auto Downloader.spec"]

    spec_file = None
    for spec in spec_files:
        if Path(spec).exists():
            spec_file = spec
            break

    if spec_file:
        print(f"Using spec file: {spec_file}")
        cmd = ["pyinstaller", spec_file]
    else:
        print("No spec file found, using default PyInstaller command")
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name", "Nyaa.si Anime Auto Downloader",
            "--icon", "dist/Icon.ico",
            "--hidden-import", "PIL._tkinter_finder",
            "--add-data", "settings.py;.",
            "--add-data", "tracker.json;.",
            "main.py"
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Build successful!")
        exe_path = Path("dist/Nyaa.si Anime Auto Downloader.exe")
        if exe_path.exists():
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 File size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    else:
        print("❌ Build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False

def verify_build():
    """Verify the build was successful"""
    exe_path = Path("dist/Nyaa.si Anime Auto Downloader.exe")
    return exe_path.exists()

def main():
    """Main build function"""
    print("🚀 Starting Nyaa Auto Downloader build process...")

    try:
        # Clean old artifacts
        clean_build_artifacts()

        # Build new executable
        success = build_executable()

        # Verify build
        if success and verify_build():
            print("\n🎉 Build completed successfully!")
            return 0
        else:
            print("\n💥 Build failed!")
            return 1

    except Exception as e:
        print(f"\n💥 Build error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


