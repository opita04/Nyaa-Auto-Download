"""
Nyaa Auto Download - Refactored Architecture

A clean, modular anime torrent downloader with separate business logic and UI layers.

Package Structure:
- core/: Business logic controllers (app, torrent, tracker)
- gui/: GUI framework and main window
- panels/: Individual UI panel components
"""

__version__ = "1.1.0-refactor"
__author__ = "Nyaa Auto Download Team"

from . import core
from . import gui
from . import panels

__all__ = ['core', 'gui', 'panels']
