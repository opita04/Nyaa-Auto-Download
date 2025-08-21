import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import scrolledtext
import threading
import re
import requests
from datetime import datetime
import argparse
import time
import os

# Import modules
from modules.nyaa_scraper import NyaaScraper
from modules.anime_tracker import AnimeTracker
from modules.qbittorrent_client import QBittorrentClient
from modules.settings_panel import SettingsPanel
from modules.generic_torrent_client import GenericTorrentClient
from utils.logging_utils import setup_logging, create_trace_file
from settings import *
from settings import SettingsManager

# Initialize trace file
TRACE_PATH = create_trace_file()

with open(TRACE_PATH, 'a') as f:
    f.write('TOP OF FILE\n')


class App:
    def __init__(self, root):
        with open(TRACE_PATH, 'a') as f:
            f.write('IN APP INIT\n')
        self.root = root
        self.root.title(GUISettings.WINDOW_TITLE)
        self.tracker = AnimeTracker()
        self.settings_manager = SettingsManager()

        # Initialize torrent client with default settings first
        self.qb_config = QBittorrentConfig()
        self.torrent_config = TorrentClientConfig()
        self.quality_settings = QualitySettings()
        self.check_interval = DEFAULT_INTERVAL
        self.torrent_client = GenericTorrentClient(self.torrent_config)

        self.check_thread = None
        self.stop_event = threading.Event()
        self.qb_health_check_thread = None
        self._setup_gui()
        self._load_tracker()

        # Load settings after GUI is set up (so we can log)
        self._load_settings()

        self._log('Application started.')
        self._start_periodic_check()
        self._start_qb_health_check()

    def _load_settings(self):
        """Load all settings from file"""
        try:
            self.qb_config, self.torrent_config, self.quality_settings, self.check_interval = \
                self.settings_manager.load_settings()

            # Reinitialize torrent client with loaded settings
            self.torrent_client = GenericTorrentClient(self.torrent_config)

            self._log('Settings loaded successfully.')
            self._update_settings_status('Settings loaded!')
        except Exception as e:
            self._log(f'Failed to load settings: {e}. Using defaults.')
            self._update_settings_status('Using default settings', error=True)

    def _save_settings(self):
        """Save all current settings"""
        try:
            success, error_msg = self.settings_manager.save_settings(
                self.qb_config, self.torrent_config, self.quality_settings, self.check_interval
            )
            if success:
                self._log('Settings saved successfully.')
                self._update_settings_status('Settings saved!')
            else:
                self._log(f'Failed to save settings: {error_msg}')
                self._update_settings_status(f'Failed to save settings: {error_msg}', error=True)
        except Exception as e:
            self._log(f'Failed to save settings: {e}')
            self._update_settings_status(f'Failed to save settings: {e}', error=True)

    def _add_settings_status_indicator(self):
        """Add a settings status indicator to the GUI"""
        # Create a small frame for settings status
        self.settings_status_frame = ttk.Frame(self.left_frame)
        self.settings_status_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=2)

        # Settings status label
        ttk.Label(self.settings_status_frame, text='Settings:', font=('TkDefaultFont', 8)).pack(side='left')
        self.settings_status_label = ttk.Label(self.settings_status_frame, text='Loaded', font=('TkDefaultFont', 8), foreground='green')
        self.settings_status_label.pack(side='left', padx=5)

        # Settings info button
        info_btn = ttk.Button(self.settings_status_frame, text='ℹ️', width=3,
                             command=self._show_settings_info)
        info_btn.pack(side='right')

    def _add_qbittorrent_status(self):
        """Add qBittorrent status indicator at the bottom of the GUI"""
        # Create a frame for qBittorrent status at the very bottom
        self.qb_status_frame = ttk.Frame(self.left_frame)
        self.qb_status_frame.grid(row=4, column=0, sticky='ew', padx=5, pady=5)

        self.qb_status_label = ttk.Label(self.qb_status_frame, text="qBittorrent Status:")
        self.qb_status_label.pack(side='left')

        self.qb_status_indicator = ttk.Label(self.qb_status_frame, text="🔄 Checking...", font=('TkDefaultFont', 10, 'bold'))
        self.qb_status_indicator.pack(side='left', padx=5)

        self.qb_status_message = ttk.Label(self.qb_status_frame, text="", foreground="gray")
        self.qb_status_message.pack(side='left', padx=5, fill='x', expand=True)

        # Add manual connection check button
        self.qb_check_btn = ttk.Button(self.qb_status_frame, text="🔄 Check", width=8,
                                      command=self._check_qb_connection)
        self.qb_check_btn.pack(side='right', padx=5)

    def _update_settings_status(self, message, error=False):
        """Update the settings status indicator"""
        color = 'red' if error else 'green'
        self.settings_status_label.config(text=message, foreground=color)

        # Auto-hide the message after 3 seconds
        def clear_status():
            self.settings_status_label.config(text='Ready', foreground='gray')

        self.root.after(3000, clear_status)

    def _show_settings_info(self):
        """Show settings information dialog"""
        info_msg = f"""Settings Information:

📁 Settings File: {SETTINGS_FILE}
📂 Anime List: {TRACKER_FILE}

Current Status:
• Settings: {'Loaded' if os.path.exists(SETTINGS_FILE) else 'Using defaults'}
• Anime List: {'Loaded' if os.path.exists(TRACKER_FILE) else 'Empty'}

Settings are automatically saved when you close the settings panel.
Anime list is automatically saved when modified.

Backup: {SETTINGS_FILE}.backup"""

        messagebox.showinfo("Settings Info", info_msg)

    def _setup_gui(self):
        with open(TRACE_PATH, 'a') as f: f.write('IN SETUP GUI\n')
        mainframe = ttk.Frame(self.root, padding=GUISettings.MAIN_PADDING)
        mainframe.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create main paned window for side panels
        self.main_paned = ttk.PanedWindow(mainframe, orient='horizontal')
        self.main_paned.grid(row=0, column=0, sticky='nsew')
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        
        # Left panel (main content)
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=3)
        
        # Right panel (episodes - initially hidden)
        self.right_frame = ttk.Frame(self.main_paned)
        self.episodes_visible = False

        # Add Anime Section
        add_frame = ttk.LabelFrame(self.left_frame, text='Add New Anime')
        add_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        ttk.Label(add_frame, text='Title:').grid(row=0, column=0, sticky='w')
        self.title_entry = ttk.Entry(add_frame, width=GUISettings.TITLE_ENTRY_WIDTH)
        self.title_entry.grid(row=0, column=1, sticky='ew')
        ttk.Label(add_frame, text='Nyaa.si URL:').grid(row=1, column=0, sticky='w')
        self.url_entry = ttk.Entry(add_frame, width=GUISettings.URL_ENTRY_WIDTH)
        self.url_entry.grid(row=1, column=1, sticky='ew')
        add_btn = ttk.Button(add_frame, text='Add Series', command=self.add_series)
        add_btn.grid(row=0, column=2, rowspan=2, padx=5)
        
        # Control buttons frame
        controls_frame = ttk.Frame(add_frame)
        controls_frame.grid(row=0, column=3, rowspan=2, padx=5)
        
        # Search Button (Magnifying Glass)
        search_btn = tk.Button(controls_frame, text="🔍", width=3, command=self.toggle_search_panel, 
                             font=('TkDefaultFont', 12))
        search_btn.pack(side='top', fill='x', pady=(0, 2))
        
        # Settings Button (Gear)
        self.settings_btn = tk.Button(controls_frame, text="⚙️", width=3, command=self.toggle_settings_panel,
                                    font=('TkDefaultFont', 12))
        self.settings_btn.pack(side='top', fill='x')

        # Bulk Torrents Button (List icon)
        self.bulk_btn = tk.Button(controls_frame, text="📋", width=3, command=self.show_bulk_torrents_panel,
                                font=('TkDefaultFont', 12))
        self.bulk_btn.pack(side='top', fill='x')

        # Hidden panels
        self.search_panel_visible = False

        # Anime List Section
        list_frame = ttk.LabelFrame(self.left_frame, text='Tracked Anime')
        list_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.anime_tree = ttk.Treeview(list_frame, columns=GUISettings.ANIME_TREE_COLUMNS, 
                                     show='headings', height=GUISettings.ANIME_TREE_HEIGHT)
        
        # Configure anime tree headers and widths
        for col, header in GUISettings.ANIME_TREE_HEADINGS.items():
            self.anime_tree.heading(col, text=header)
            self.anime_tree.column(col, width=GUISettings.ANIME_TREE_WIDTHS[col])
            
        self.anime_tree.grid(row=0, column=0, sticky='nsew')
        
        # Bind double-click event to show episodes
        self.anime_tree.bind('<Double-1>', self.on_anime_double_click)
        
        # Bind right-click for context menu
        self.anime_tree.bind('<Button-3>', self.on_anime_right_click)
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Toggle Multi-Episode Downloads", command=self.toggle_multi_episode)
        
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        remove_btn = ttk.Button(list_frame, text='Remove Series', command=self.remove_series)
        remove_btn.grid(row=1, column=0, sticky='ew', pady=3)
        edit_btn = ttk.Button(list_frame, text='Edit Title', command=self.edit_series)
        edit_btn.grid(row=2, column=0, sticky='ew', pady=3)
        multi_episode_btn = ttk.Button(list_frame, text='Toggle Multi-Episode', command=self.toggle_multi_episode)
        multi_episode_btn.grid(row=3, column=0, sticky='ew', pady=3)
        force_btn = ttk.Button(list_frame, text='Force Check Now', command=self.force_check)
        force_btn.grid(row=4, column=0, sticky='ew', pady=3)

        # Initialize Settings Panel (hidden by default)
        self.settings_frame = ttk.Frame(self.main_paned)
        self.settings_panel = SettingsPanel(self.settings_frame, self.qb_config, self.check_interval, self.on_settings_save, self.torrent_config, self.quality_settings)

        # Status Log
        log_frame = ttk.LabelFrame(self.left_frame, text='Status Log')
        log_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=GUISettings.LOG_TEXT_HEIGHT,
                                                state='disabled', wrap='word')
        self.log_text.pack(fill='both', expand=True)

        self.left_frame.columnconfigure(0, weight=1)

        # Setup episodes panel
        self._setup_episodes_panel()

        # Setup search panel
        self._setup_search_panel()

        # Setup bulk torrents panel
        self._setup_bulk_torrents_panel()

        # Add settings status indicator
        self._add_settings_status_indicator()

        # Add qBittorrent status at the bottom
        self._add_qbittorrent_status()

        # Configure row weights for proper expansion
        self.left_frame.rowconfigure(1, weight=1)  # Tracked Anime List expands
        self.left_frame.rowconfigure(2, weight=1)  # Status Log expands

        # Check torrent client connection on startup (moved after log_text is created)
        self._check_torrent_connection()

    def on_settings_save(self, qb_config, check_interval, torrent_config=None, quality_settings=None):
        """Callback for when settings are saved"""
        self.qb_config = qb_config
        self.check_interval = check_interval
        if torrent_config:
            self.torrent_config = torrent_config
            self.torrent_client = GenericTorrentClient(self.torrent_config)
        if quality_settings:
            self.quality_settings = quality_settings

        # Save all settings to file
        self._save_settings()

        # Re-check torrent client connection after settings change
        self._check_torrent_connection()
    
    def toggle_settings_panel(self):
        """Toggle the visibility of the settings panel"""
        if hasattr(self, 'settings_panel_visible') and self.settings_panel_visible:
            self.hide_settings_panel()
        else:
            self.show_settings_panel()

    def show_settings_panel(self):
        """Show the settings panel"""
        if not hasattr(self, 'settings_panel_visible'):
            self.settings_panel_visible = False

        if not self.settings_panel_visible:
            # Hide other panels if they're visible
            if self.episodes_visible:
                self.hide_episodes_panel()
            if self.search_panel_visible:
                self.hide_search_panel()
            if hasattr(self, 'bulk_torrents_panel_visible') and self.bulk_torrents_panel_visible:
                self.hide_bulk_torrents_panel()

            # Add the settings panel to the main paned window
            self.main_paned.add(self.settings_frame, weight=1)
            self.settings_panel_visible = True
            # Focus on the first entry field in the settings panel
            if hasattr(self.settings_panel, 'qb_host'):
                self.settings_panel.qb_host.focus()

    def hide_settings_panel(self):
        """Hide the settings panel"""
        if hasattr(self, 'settings_panel_visible') and self.settings_panel_visible:
            self.main_paned.remove(self.settings_frame)
            self.settings_panel_visible = False

    def _check_qb_connection(self):
        """Check qBittorrent connection and update status indicator"""
        try:
            qb = QBittorrentClient(self.qb_config)
            connected, err = qb.connect()

            if connected:
                self.qb_status_indicator.config(text="✅ Connected", foreground="green")
                self.qb_status_message.config(text="qBittorrent is running and accessible", foreground="green")
                self._log('qBittorrent connection successful')
            else:
                self.qb_status_indicator.config(text="❌ Disconnected", foreground="red")
                self.qb_status_message.config(text=f"Connection failed: {err}", foreground="red")
                self._log(f'qBittorrent connection failed: {err}')

                # Show warning dialog for connection failure
                messagebox.showwarning(
                    "qBittorrent Connection Warning",
                    f"qBittorrent is not accessible at {self.qb_config.host}:{self.qb_config.port}\n\n"
                    f"Error: {err}\n\n"
                    "Please ensure qBittorrent is running and the connection settings are correct.\n"
                    "You can check/update settings via the ⚙️ button."
                )

        except Exception as e:
            self.qb_status_indicator.config(text="❌ Error", foreground="red")
            self.qb_status_message.config(text=f"Connection check failed: {str(e)}", foreground="red")
            self._log(f'qBittorrent connection check error: {e}')

    def _check_torrent_connection(self):
        """Check torrent client connection and update status indicator"""
        try:
            available, err = self.torrent_client.test_connection()

            if available:
                client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(self.torrent_config.preferred_client, "Unknown")
                self.qb_status_indicator.config(text="✅ Connected", foreground="green")
                if self.torrent_config.preferred_client == 'qbittorrent':
                    self.qb_status_message.config(text=f"{client_name} is running and accessible", foreground="green")
                else:
                    self.qb_status_message.config(text=f"{client_name} client configured", foreground="green")
                self._log(f'{client_name} connection successful')
            else:
                client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(self.torrent_config.preferred_client, "Unknown")
                self.qb_status_indicator.config(text="❌ Disconnected", foreground="red")
                self.qb_status_message.config(text=f"{client_name} connection failed: {err}", foreground="red")
                self._log(f'{client_name} connection failed: {err}')

        except Exception as e:
            client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(self.torrent_config.preferred_client, "Unknown")
            self.qb_status_indicator.config(text="❌ Error", foreground="red")
            self.qb_status_message.config(text=f"{client_name} check failed: {str(e)}", foreground="red")
            self._log(f'{client_name} connection check error: {e}')

    def _update_qb_status(self, connected, error_msg=""):
        """Update qBittorrent status indicator without performing connection check"""
        if connected:
            self.qb_status_indicator.config(text="✅ Connected", foreground="green")
            self.qb_status_message.config(text="qBittorrent is running and accessible", foreground="green")
        else:
            self.qb_status_indicator.config(text="❌ Disconnected", foreground="red")
            self.qb_status_message.config(text=f"Connection failed: {error_msg}", foreground="red")
    
    def _setup_episodes_panel(self):
        """Setup the episodes side panel"""
        # Episodes panel header
        header_frame = ttk.Frame(self.right_frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        self.episodes_title_label = ttk.Label(header_frame, text='Episodes', font=('TkDefaultFont', 12, 'bold'))
        self.episodes_title_label.pack(side='left')
        
        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide_episodes_panel)
        close_btn.pack(side='right')
        
        # Episodes list
        episodes_list_frame = ttk.Frame(self.right_frame)
        episodes_list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for episodes
        self.episodes_tree = ttk.Treeview(episodes_list_frame, 
                                         columns=GUISettings.EPISODES_TREE_COLUMNS, 
                                         show='tree headings', height=GUISettings.EPISODES_TREE_HEIGHT)
        
        # Configure episodes tree headers and widths
        for col, header in GUISettings.EPISODES_TREE_HEADINGS.items():
            if col == '#0':
                self.episodes_tree.heading('#0', text=header, command=lambda: self.sort_treeview('#0', False, 'text'))
            else:
                sort_type = {'Episode': 'episode', 'Size': 'size', 'DateTime': 'datetime', 
                           'Seeders': 'seeders', 'Leechers': 'leechers'}.get(col, 'text')
                self.episodes_tree.heading(col, text=header, command=lambda c=col, st=sort_type: self.sort_treeview(c, False, st))
                
        # Set column widths
        for col, width in GUISettings.EPISODES_TREE_WIDTHS.items():
            self.episodes_tree.column(col, width=width)
        
        # Store current sort state
        self.current_sort_column = None
        self.current_sort_reverse = False
        
        # Scrollbar for episodes
        episodes_scrollbar = ttk.Scrollbar(episodes_list_frame, orient='vertical', command=self.episodes_tree.yview)
        self.episodes_tree.configure(yscrollcommand=episodes_scrollbar.set)
        
        self.episodes_tree.pack(side='left', fill='both', expand=True)
        episodes_scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to download episode
        self.episodes_tree.bind('<Double-1>', self.on_episode_double_click)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.right_frame)
        buttons_frame.pack(pady=5)
        
        # Download button
        download_btn = ttk.Button(buttons_frame, text='Download Selected', 
                                 command=self.download_selected_episode)
        download_btn.pack(side='left', padx=5)
        
        # Add to tracked button
        add_to_tracked_btn = ttk.Button(buttons_frame, text='Add to Tracked', 
                                      command=self.add_search_result_to_tracked)
        add_to_tracked_btn.pack(side='left', padx=5)
    
    def _setup_search_panel(self):
        """Setup the search panel"""
        # Create a frame for the search panel that's properly managed
        self.search_frame = ttk.Frame(self.main_paned)
        
        # Search panel header
        header_frame = ttk.Frame(self.search_frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        search_title_label = ttk.Label(header_frame, text='Search Nyaa.si', font=('TkDefaultFont', 12, 'bold'))
        search_title_label.pack(side='left')
        
        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide_search_panel)
        close_btn.pack(side='right')
        
        # Search input area
        search_input_frame = ttk.Frame(self.search_frame)
        search_input_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_input_frame, text='Search:').pack(side='left')
        self.search_entry = ttk.Entry(search_input_frame, width=GUISettings.SEARCH_ENTRY_WIDTH)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_nyaa())
        
        search_btn = ttk.Button(search_input_frame, text='Search', command=self.search_nyaa)
        search_btn.pack(side='left')
        
        # Add search results area to the search panel
        self.search_results_frame = ttk.Frame(self.search_frame)
        self.search_results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for search results within the search panel
        self.search_results_tree = ttk.Treeview(self.search_results_frame, 
                                              columns=GUISettings.EPISODES_TREE_COLUMNS, 
                                              show='tree headings', height=GUISettings.EPISODES_TREE_HEIGHT)
        
        # Configure search results tree headers and widths
        for col, header in GUISettings.EPISODES_TREE_HEADINGS.items():
            if col == '#0':
                self.search_results_tree.heading('#0', text=header)
            else:
                self.search_results_tree.heading(col, text=header)
                
        # Set column widths
        for col, width in GUISettings.EPISODES_TREE_WIDTHS.items():
            self.search_results_tree.column(col, width=width)
        
        # Scrollbar for search results
        search_scrollbar = ttk.Scrollbar(self.search_results_frame, orient='vertical', command=self.search_results_tree.yview)
        self.search_results_tree.configure(yscrollcommand=search_scrollbar.set)
        
        self.search_results_tree.pack(side='left', fill='both', expand=True)
        search_scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to download episode from search results
        self.search_results_tree.bind('<Double-1>', self.on_search_result_double_click)
        
        # Search results buttons frame
        search_buttons_frame = ttk.Frame(self.search_frame)
        search_buttons_frame.pack(pady=5)
        
        # Download button
        download_search_btn = ttk.Button(search_buttons_frame, text='Download Selected', 
                                       command=self.download_selected_search_result)
        download_search_btn.pack(side='left', padx=5)
        
        # Add to tracked button
        add_to_tracked_search_btn = ttk.Button(search_buttons_frame, text='Add to Tracked',
                                             command=self.add_search_result_to_tracked)
        add_to_tracked_search_btn.pack(side='left', padx=5)

    def _setup_bulk_torrents_panel(self):
        """Setup the bulk torrents panel"""
        # Create a frame for the bulk torrents panel
        self.bulk_torrents_frame = ttk.Frame(self.main_paned)

        # Bulk torrents panel header
        header_frame = ttk.Frame(self.bulk_torrents_frame)
        header_frame.pack(fill='x', padx=5, pady=5)

        bulk_title_label = ttk.Label(header_frame, text='All Latest Torrents', font=('TkDefaultFont', 12, 'bold'))
        bulk_title_label.pack(side='left')

        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide_bulk_torrents_panel)
        close_btn.pack(side='right')

        # Refresh button
        refresh_btn = ttk.Button(header_frame, text='🔄 Refresh', command=self.refresh_bulk_torrents)
        refresh_btn.pack(side='right', padx=5)

        # Bulk torrents list area
        self.bulk_torrents_list_frame = ttk.Frame(self.bulk_torrents_frame)
        self.bulk_torrents_list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create treeview for bulk torrents with checkboxes
        self.bulk_torrents_tree = ttk.Treeview(self.bulk_torrents_list_frame,
                                              columns=('Series', 'Episode', 'Status'),
                                              show='tree headings', height=GUISettings.EPISODES_TREE_HEIGHT)

        # Configure bulk torrents tree headers
        self.bulk_torrents_tree.heading('#0', text='Title')
        self.bulk_torrents_tree.heading('Series', text='Series')
        self.bulk_torrents_tree.heading('Episode', text='Episode')
        self.bulk_torrents_tree.heading('Status', text='Status')

        # Set column widths
        self.bulk_torrents_tree.column('#0', width=300)
        self.bulk_torrents_tree.column('Series', width=150)
        self.bulk_torrents_tree.column('Episode', width=80)
        self.bulk_torrents_tree.column('Status', width=100)

        # Scrollbar for bulk torrents
        bulk_scrollbar = ttk.Scrollbar(self.bulk_torrents_list_frame, orient='vertical', command=self.bulk_torrents_tree.yview)
        self.bulk_torrents_tree.configure(yscrollcommand=bulk_scrollbar.set)

        self.bulk_torrents_tree.pack(side='left', fill='both', expand=True)
        bulk_scrollbar.pack(side='right', fill='y')

        # Bind double-click to toggle selection
        self.bulk_torrents_tree.bind('<Double-1>', self.on_bulk_torrent_double_click)

        # Buttons frame
        buttons_frame = ttk.Frame(self.bulk_torrents_frame)
        buttons_frame.pack(pady=5)

        # Select All button
        select_all_btn = ttk.Button(buttons_frame, text='Select All',
                                   command=self.select_all_bulk_torrents)
        select_all_btn.pack(side='left', padx=5)

        # Deselect All button
        deselect_all_btn = ttk.Button(buttons_frame, text='Deselect All',
                                     command=self.deselect_all_bulk_torrents)
        deselect_all_btn.pack(side='left', padx=5)

        # Download Selected button
        download_selected_btn = ttk.Button(buttons_frame, text='Download Selected',
                                          command=self.download_selected_bulk_torrents)
        download_selected_btn.pack(side='left', padx=5)

        # Download All button
        download_all_btn = ttk.Button(buttons_frame, text='Download All',
                                     command=self.download_all_bulk_torrents)
        download_all_btn.pack(side='left', padx=5)

    def toggle_search_panel(self):
        """Toggle the search panel visibility"""
        if self.search_panel_visible:
            self.hide_search_panel()
        else:
            self.show_search_panel()
    
    def show_search_panel(self):
        """Show the search panel"""
        if not self.search_panel_visible:
            # Hide episodes panel if it's visible
            if self.episodes_visible:
                self.hide_episodes_panel()
            
            # Add the search panel to the main paned window
            self.main_paned.add(self.search_frame, weight=1)
            self.search_panel_visible = True
            self.search_entry.focus()
    
    def hide_search_panel(self):
        """Hide the search panel"""
        if self.search_panel_visible:
            self.main_paned.remove(self.search_frame)
            self.search_panel_visible = False
    
    def search_nyaa(self):
        """Search Nyaa.si for the given query"""
        query = self.search_entry.get().strip()
        if not query:
            self._log('Please enter a search query.')
            return
            
        self._log(f'Searching Nyaa.si for: {query}')
        
        # Clear existing search results
        for item in self.search_results_tree.get_children():
            self.search_results_tree.delete(item)
        
        # Show loading message
        loading_item = self.search_results_tree.insert('', 'end', text='Searching...', values=('', '', '', '', ''))
        self.search_results_tree.update()
        
        # Fetch search results in background thread
        def fetch_results():
            results = NyaaScraper.search(query, self.quality_settings)

            # Apply quality filtering
            if self.quality_settings.quality_filter_mode != 'disabled':
                results = self.quality_settings.filter_torrents(results)

            # Update UI in main thread
            self.root.after(0, lambda: self._populate_search_panel_results(results, loading_item))
        
        threading.Thread(target=fetch_results, daemon=True).start()
    
    def _populate_search_panel_results(self, results, loading_item):
        """Populate the search panel tree with search results"""
        # Remove loading message
        self.search_results_tree.delete(loading_item)
        
        if not results:
            self.search_results_tree.insert('', 'end', text='No results found', values=('', '', '', '', ''))
            return
        
        for result in results:
            # Format episode info for display
            if result['season']:
                ep_text = f"S{result['season']}E{result['episode_text']}"
            else:
                ep_text = f"Ep {result['episode_text']}"
                
            # Combine date and time into a single value
            datetime_value = self.combine_date_time(result['date'], result['time'])
            
            # Extract quality info for display
            quality_info = self._extract_quality_from_title(result['title'])
            display_title = result['title'][:55] + ('...' if len(result['title']) > 55 else '')
            if quality_info and quality_info != 'Unknown':
                display_title += f" [{quality_info}]"

            self.search_results_tree.insert('', 'end',
                                           text=display_title,
                                           values=(ep_text, result['size'], datetime_value, result['seeders'], result['leechers']),
                                           tags=(result['magnet'],))  # Store magnet link in tags
        
        self._log(f'Found {len(results)} results for: {self.search_entry.get().strip()}')
    
    def on_search_result_double_click(self, event):
        """Handle double-click on search result to download"""
        self.download_selected_search_result()
    
    def download_selected_search_result(self):
        """Download the selected search result"""
        selection = self.search_results_tree.selection()
        if not selection:
            self._log('No search result selected.')
            return

        item = selection[0]
        tags = self.search_results_tree.item(item, 'tags')
        if not tags or not tags[0]:
            self._log('No magnet link available for this search result.')
            return

        magnet = tags[0]
        episode_title = self.search_results_tree.item(item, 'text')

        # Download using the configured torrent client
        ok, err = self.torrent_client.launch_magnet(magnet, self.qb_config.category)
        if ok:
            client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(self.torrent_config.preferred_client, "Torrent client")
            self._log(f'Search result "{episode_title}" sent to {client_name}.')
        else:
            self._log(f'Failed to add search result to torrent client: {err}')
            messagebox.showerror(
                "Download Error",
                f"Cannot download search result. {err}\n\n"
                "Please check your torrent client settings and ensure it's running."
            )
    
    def show_episodes_panel(self, anime_title, url):
        """Show the episodes panel with episodes from the given URL"""
        if not self.episodes_visible:
            self.main_paned.add(self.right_frame, weight=2)
            self.episodes_visible = True
        
        self.episodes_title_label.config(text=f'Episodes - {anime_title}')
        
        # Clear existing episodes
        for item in self.episodes_tree.get_children():
            self.episodes_tree.delete(item)
        
        # Show loading message
        loading_item = self.episodes_tree.insert('', 'end', text='Loading episodes...', values=('', '', '', '', ''))
        self.episodes_tree.update()
        
        # Fetch episodes in background thread
        def fetch_episodes():
            episodes = NyaaScraper.get_all_episodes(url, anime_title, self.tracker)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._populate_episodes(episodes, loading_item))
        
        threading.Thread(target=fetch_episodes, daemon=True).start()
    
    def _populate_episodes(self, episodes, loading_item):
        """Populate the episodes tree with fetched episodes"""
        # Remove loading message
        self.episodes_tree.delete(loading_item)
        
        if not episodes:
            self.episodes_tree.insert('', 'end', text='No episodes found', values=('', '', '', '', ''))
            return
        
        for episode in episodes:
            season_num = episode.get('season')
            ep_num = episode.get('episode')
            if ep_num:
                if season_num:
                    ep_text = f"S{season_num:02d}E{ep_num:02d}"
                else:
                    ep_text = f"Ep {ep_num}"
            else:
                ep_text = 'Unknown'
            # Combine date and time into a single value
            datetime_value = self.combine_date_time(episode.get('date', ''), episode.get('time', ''))
            
            self.episodes_tree.insert('', 'end', 
                                     text=episode['title'][:60] + ('...' if len(episode['title']) > 60 else ''),
                                     values=(ep_text, episode['size'], datetime_value, episode['seeders'], episode['leechers']),
                                     tags=(episode['magnet'],))  # Store magnet link in tags
    
    def hide_episodes_panel(self):
        """Hide the episodes panel"""
        if self.episodes_visible:
            self.main_paned.remove(self.right_frame)
            self.episodes_visible = False
    
    def on_episode_double_click(self, event):
        """Handle double-click on episode to download"""
        self.download_selected_episode()
    
    def download_selected_episode(self):
        """Download the selected episode"""
        selection = self.episodes_tree.selection()
        if not selection:
            self._log('No episode selected.')
            return

        item = selection[0]
        tags = self.episodes_tree.item(item, 'tags')
        if not tags or not tags[0]:
            self._log('No magnet link available for this episode.')
            return

        magnet = tags[0]
        episode_title = self.episodes_tree.item(item, 'text')

        # Download using the configured torrent client
        ok, err = self.torrent_client.launch_magnet(magnet, self.qb_config.category)
        if ok:
            client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(self.torrent_config.preferred_client, "Torrent client")
            self._log(f'Episode "{episode_title}" sent to {client_name}.')
        else:
            self._log(f'Failed to add episode to torrent client: {err}')
            messagebox.showerror(
                "Download Error",
                f"Cannot download episode. {err}\n\n"
                "Please check your torrent client settings and ensure it's running."
            )
    
    def add_search_result_to_tracked(self):
        """Add the selected search result to the tracked anime list"""
        # Implementation simplified - use episodes_tree for now as it's the main content area
        selection = self.episodes_tree.selection()
        if not selection:
            self._log('No result selected.')
            return
        
        item = selection[0]
        episode_title = self.episodes_tree.item(item, 'text')
        
        # Extract the base anime title by removing episode information
        base_title = episode_title
        # Try to remove common episode markers
        for pattern in [r'\s+-\s+\d+', r'\s+EP\s*\d+', r'\s+Episode\s*\d+', r'\s+E\d+', r'\s+S\d+E\d+']:
            base_title = re.sub(pattern, '', base_title, flags=re.IGNORECASE)
        
        # Remove common suffixes like [1080p], [720p], etc.
        base_title = re.sub(r'\s*\[[^\]]+\]', '', base_title)
        base_title = base_title.strip()
        
        # Get the URL for the search result
        search_query = self.search_entry.get().strip()
        url = f"https://nyaa.si/?f=0&c=0_0&q={requests.utils.quote(search_query)}&s=seeders&o=desc"
        
        # Ask user to confirm or modify the title
        dialog = tk.Toplevel(self.root)
        dialog.title('Add to Tracked Anime')
        dialog.geometry(DialogSettings.ADD_DIALOG_SIZE)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text='Anime Title:').pack(pady=5)
        title_entry = ttk.Entry(dialog, width=50)
        title_entry.insert(0, base_title)
        title_entry.pack(pady=5)
        title_entry.select_range(0, tk.END)
        title_entry.focus()
        
        ttk.Label(dialog, text='Nyaa.si URL:').pack(pady=5)
        url_entry = ttk.Entry(dialog, width=50)
        url_entry.insert(0, url)
        url_entry.pack(pady=5)
        
        def save_anime():
            title = title_entry.get().strip()
            url = url_entry.get().strip()
            if not title or not url:
                messagebox.showerror('Error', 'Title and URL cannot be empty.')
                return
            
            if self.tracker.add(title, url):
                self.anime_tree.insert('', 'end', iid=title, values=(title, 1, 0, url))
                self._log(f'Added series: {title}')
                dialog.destroy()
            else:
                messagebox.showerror('Error', f'Series already exists: {title}')
        
        def cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text='Add', command=save_anime).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Cancel', command=cancel).pack(side='left', padx=5)
        
        dialog.bind('<Return>', lambda e: save_anime())
        dialog.bind('<Escape>', lambda e: cancel())

    def launch_magnet_system_default(self, magnet_link):
        """Launch magnet link using system default (bypassing qBittorrent)"""
        try:
            import webbrowser
            import platform
            import subprocess
            import os

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
            return False, f"Failed to launch magnet with system default: {str(e)}"

    def gather_all_latest_torrents(self, quality_settings=None):
        """Gather all latest available torrents from all tracked series"""
        all_torrents = []

        for title, info in self.tracker.get_all():
            url = info['url']
            last_season = info.get('last_season', 1)
            last_episode = info.get('last_episode', 0)

            try:
                self._log(f'Checking latest torrents for: {title}')
                latest_season, latest_episode, magnet = NyaaScraper.get_latest_episode_and_magnet(url, title, self.tracker, quality_settings)

                if latest_episode is not None and magnet is not None:
                    # Check if this is newer than what we have
                    if latest_season > last_season or (latest_season == last_season and latest_episode > last_episode):
                        all_torrents.append({
                            'title': title,
                            'series_title': title,
                            'episode_info': f'S{latest_season:02d}E{latest_episode:02d}',
                            'magnet': magnet,
                            'season': latest_season,
                            'episode': latest_episode,
                            'current_season': last_season,
                            'current_episode': last_episode
                        })
                    else:
                        # Even if not newer, include it as an option
                        all_torrents.append({
                            'title': f'{title} - S{latest_season:02d}E{latest_episode:02d} (Current)',
                            'series_title': title,
                            'episode_info': f'S{latest_season:02d}E{latest_episode:02d}',
                            'magnet': magnet,
                            'season': latest_season,
                            'episode': latest_episode,
                            'current_season': last_season,
                            'current_episode': last_episode
                        })

            except Exception as e:
                self._log(f'Error checking {title}: {e}')

        return all_torrents

    def _extract_quality_from_title(self, title):
        """Extract quality information from torrent title"""
        title_lower = title.lower()

        # Check for common quality indicators
        qualities = []

        # Resolution qualities
        if '360p' in title_lower:
            qualities.append('360p')
        if '480p' in title_lower:
            qualities.append('480p')
        if '720p' in title_lower:
            qualities.append('720p')
        if '1080p' in title_lower:
            qualities.append('1080p')
        if '1440p' in title_lower:
            qualities.append('1440p')
        if '2160p' in title_lower or '4k' in title_lower:
            qualities.append('4K')

        # Source qualities
        if 'webrip' in title_lower:
            qualities.append('WEBRip')
        if 'bluray' in title_lower or 'bdrip' in title_lower:
            qualities.append('BluRay')
        if 'dvd' in title_lower:
            qualities.append('DVD')
        if 'hdtv' in title_lower:
            qualities.append('HDTV')

        # Overall quality
        if 'sd' in title_lower and '480p' not in qualities:
            qualities.append('SD')
        if 'hd' in title_lower and not any(q in ['720p', '1080p', '1440p', '4K'] for q in qualities):
            qualities.append('HD')

        return ', '.join(qualities) if qualities else 'Unknown'

    def show_bulk_torrents_panel(self):
        """Show the bulk torrents panel"""
        if not hasattr(self, 'bulk_torrents_panel_visible'):
            self.bulk_torrents_panel_visible = False

        if not self.bulk_torrents_panel_visible:
            # Hide other panels if they're visible
            if self.episodes_visible:
                self.hide_episodes_panel()
            if self.search_panel_visible:
                self.hide_search_panel()

            # Add the bulk torrents panel to the main paned window
            self.main_paned.add(self.bulk_torrents_frame, weight=1)
            self.bulk_torrents_panel_visible = True

            # Load the torrents
            self.refresh_bulk_torrents()

    def hide_bulk_torrents_panel(self):
        """Hide the bulk torrents panel"""
        if hasattr(self, 'bulk_torrents_panel_visible') and self.bulk_torrents_panel_visible:
            self.main_paned.remove(self.bulk_torrents_frame)
            self.bulk_torrents_panel_visible = False

    def refresh_bulk_torrents(self):
        """Refresh the bulk torrents list"""
        # Clear existing items
        for item in self.bulk_torrents_tree.get_children():
            self.bulk_torrents_tree.delete(item)

        # Show loading message
        loading_item = self.bulk_torrents_tree.insert('', 'end', text='Loading latest torrents...', values=('', '', ''))

        # Load torrents in background thread
        def load_torrents():
            torrents = self.gather_all_latest_torrents(self.quality_settings)
            self.root.after(0, lambda: self._populate_bulk_torrents(torrents, loading_item))

        threading.Thread(target=load_torrents, daemon=True).start()

    def _populate_bulk_torrents(self, torrents, loading_item):
        """Populate the bulk torrents tree with fetched torrents"""
        # Remove loading message
        self.bulk_torrents_tree.delete(loading_item)

        if not torrents:
            self.bulk_torrents_tree.insert('', 'end', text='No torrents found', values=('', '', ''))
            return

        for torrent in torrents:
            # Determine status
            if torrent['season'] > torrent['current_season'] or \
               (torrent['season'] == torrent['current_season'] and torrent['episode'] > torrent['current_episode']):
                status = 'NEW'
                status_color = 'green'
            else:
                status = 'Current'
                status_color = 'blue'

            # Extract quality info from title
            quality_info = self._extract_quality_from_title(torrent['title'])

            # Insert item
            item = self.bulk_torrents_tree.insert('', 'end',
                                                text=torrent['title'],
                                                values=(torrent['series_title'],
                                                       torrent['episode_info'],
                                                       f"{status} ({quality_info})" if quality_info else status),
                                                tags=(torrent['magnet'],))

            # Color code the status
            self.bulk_torrents_tree.tag_configure(f'status_{status}', foreground=status_color)

        self._log(f'Loaded {len(torrents)} torrents from {len(set(t["series_title"] for t in torrents))} series')

    def on_bulk_torrent_double_click(self, event):
        """Handle double-click on bulk torrent to toggle selection"""
        item = self.bulk_torrents_tree.identify_row(event.y)
        if item:
            # Toggle selection (you could also implement checkbox-like behavior here)
            if self.bulk_torrents_tree.selection() and item in self.bulk_torrents_tree.selection():
                self.bulk_torrents_tree.selection_remove(item)
            else:
                self.bulk_torrents_tree.selection_add(item)

    def select_all_bulk_torrents(self):
        """Select all torrents in the bulk list"""
        all_items = self.bulk_torrents_tree.get_children()
        self.bulk_torrents_tree.selection_set(all_items)

    def deselect_all_bulk_torrents(self):
        """Deselect all torrents in the bulk list"""
        self.bulk_torrents_tree.selection_remove(self.bulk_torrents_tree.selection())

    def download_selected_bulk_torrents(self):
        """Download selected torrents from bulk list"""
        selection = self.bulk_torrents_tree.selection()
        if not selection:
            self._log('No torrents selected for download.')
            return

        downloaded_count = 0
        for item in selection:
            tags = self.bulk_torrents_tree.item(item, 'tags')
            if tags and tags[0]:
                magnet = tags[0]
                title = self.bulk_torrents_tree.item(item, 'text')

                success, error_msg = self.launch_magnet_system_default(magnet)
                if success:
                    self._log(f'Launched torrent: {title[:50]}...')
                    downloaded_count += 1
                else:
                    self._log(f'Failed to launch torrent {title[:30]}...: {error_msg}')

        self._log(f'Successfully launched {downloaded_count} out of {len(selection)} selected torrents.')

    def download_all_bulk_torrents(self):
        """Download all torrents from bulk list"""
        all_items = self.bulk_torrents_tree.get_children()
        if not all_items:
            self._log('No torrents available for download.')
            return

        # Select all items first
        self.select_all_bulk_torrents()

        # Then download them
        self.download_selected_bulk_torrents()

    def on_anime_double_click(self, event):
        """Handle double-click on anime in the main list"""
        selection = self.anime_tree.selection()
        if not selection:
            return
            
        title = selection[0]
        values = self.anime_tree.item(title, 'values')
        url = values[3]  # URL is the fourth column
        
        self.show_episodes_panel(title, url)
    
    def on_anime_right_click(self, event):
        """Handle right-click on anime list"""
        # Select the item under cursor
        item = self.anime_tree.identify_row(event.y)
        if item:
            self.anime_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def toggle_multi_episode(self):
        """Toggle multi-episode downloads for selected anime"""
        selected = self.anime_tree.selection()
        if not selected:
            self._log('No series selected.')
            return
        
        title = selected[0]
        current_flag = self.tracker.allows_multi_episode(title)
        new_flag = not current_flag
        
        self.tracker.set_multi_episode_flag(title, new_flag)
        
        status = "enabled" if new_flag else "disabled"
        self._log(f'Multi-episode downloads {status} for "{title}"')
        
        # Update the display to show the current status
        self._refresh_anime_display()
    
    def _refresh_anime_display(self):
        """Refresh the anime list display"""
        self._load_tracker()

    def _load_tracker(self):
        self.anime_tree.delete(*self.anime_tree.get_children())
        
        for title, info in self.tracker.get_all():
            multi_ep_status = " [Multi-Ep]" if info.get('allow_multi_episode', False) else ""
            display_title = title + multi_ep_status
            last_season = info.get('last_season', 1)
            last_episode = info.get('last_episode', 0)
            self.anime_tree.insert('', 'end', iid=title, values=(display_title, last_season, last_episode, info['url']))

    def add_series(self):
        title = self.title_entry.get().strip()
        url = self.url_entry.get().strip()
        if not title or not url:
            self._log('Title and URL required.')
            return
        if self.tracker.add(title, url):
            self.anime_tree.insert('', 'end', iid=title, values=(title, 1, 0, url))
            self._log(f'Added series: {title}')
            self.title_entry.delete(0, 'end')
            self.url_entry.delete(0, 'end')
        else:
            self._log(f'Series already exists: {title}')

    def remove_series(self):
        selected = self.anime_tree.selection()
        if not selected:
            self._log('No series selected.')
            return
        for title in selected:
            self.tracker.remove(title)
            self.anime_tree.delete(title)
            self._log(f'Removed series: {title}')
    
    def edit_series(self):
        selected = self.anime_tree.selection()
        if not selected:
            self._log('No series selected.')
            return
        if len(selected) > 1:
            self._log('Please select only one series to edit.')
            return
            
        old_title = selected[0]
        current_values = self.anime_tree.item(old_title, 'values')
        current_url = current_values[3]
        
        dialog = tk.Toplevel(self.root)
        dialog.title('Edit Anime Series')
        dialog.geometry(DialogSettings.EDIT_DIALOG_SIZE)
        dialog.transient(self.root)
        dialog.grab_set()
        DialogSettings.center_dialog(dialog)
        
        ttk.Label(dialog, text='Current Title:').pack(pady=5)
        ttk.Label(dialog, text=old_title, font=('TkDefaultFont', 9, 'bold')).pack(pady=5)
        ttk.Label(dialog, text='New Title:').pack(pady=5)
        new_title_entry = ttk.Entry(dialog, width=50)
        new_title_entry.insert(0, old_title)
        new_title_entry.pack(pady=5)
        new_title_entry.select_range(0, tk.END)
        new_title_entry.focus()
        ttk.Label(dialog, text='New URL:').pack(pady=5)
        new_url_entry = ttk.Entry(dialog, width=50)
        new_url_entry.insert(0, current_url)
        new_url_entry.pack(pady=5)
        
        def save_edit():
            new_title = new_title_entry.get().strip()
            new_url = new_url_entry.get().strip()
            if not new_title or not new_url:
                messagebox.showerror('Error', 'Title and URL cannot be empty.')
                return
            if new_title == old_title and new_url == current_url:
                dialog.destroy()
                return
                
            # If title changed, use edit_title; if only URL changed, just update URL
            if new_title != old_title:
                if self.tracker.edit_title(old_title, new_title):
                     self.tracker.data[new_title]['url'] = new_url
                     self.tracker.save()
                     self._load_tracker()
                     self._log(f'Renamed series from "{old_title}" to "{new_title}" and updated URL.')
                     dialog.destroy()
                else:
                    messagebox.showerror('Error', f'Failed to rename series. Title "{new_title}" may already exist.')
            else:
                # Only URL changed
                self.tracker.data[old_title]['url'] = new_url
                self.tracker.save()
                self._load_tracker()
                self._log(f'Updated URL for "{old_title}".')
                dialog.destroy()
                
        def cancel_edit():
            dialog.destroy()
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text='Save', command=save_edit).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Cancel', command=cancel_edit).pack(side='left', padx=5)
        
        dialog.bind('<Return>', lambda e: save_edit())
        dialog.bind('<Escape>', lambda e: cancel_edit())

    def force_check(self):
        self._log('Manual check triggered.')
        threading.Thread(target=self._check_all, daemon=True).start()

    def _log(self, msg):
        timestamp = datetime.now().strftime(LoggingSettings.TIMESTAMP_FORMAT)
        self.log_text.configure(state='normal')
        self.log_text.insert('end', f'[{timestamp}] {msg}\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def _start_periodic_check(self):
        self.check_thread = threading.Thread(target=self._periodic_check, daemon=True)
        self.check_thread.start()

    def _start_qb_health_check(self):
        """Start the qBittorrent health check thread"""
        self.qb_health_check_thread = threading.Thread(target=self._qb_health_check_loop, daemon=True)
        self.qb_health_check_thread.start()

    def _qb_health_check_loop(self):
        """Background loop to periodically check qBittorrent connection"""
        while not self.stop_event.is_set():
            try:
                # Only check if the window is still open
                if self.root.winfo_exists():
                    self._check_qb_connection()
                else:
                    break
            except Exception as e:
                print(f"[DEBUG] qBittorrent health check error: {e}")

            # Check every 5 minutes (300 seconds)
            for _ in range(300):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def _periodic_check(self):
        while not self.stop_event.is_set():
            self._check_all()
            for _ in range(self.check_interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def _check_all(self):
        self._log('Checking for new episodes...')
        available, err = self.torrent_client.test_connection()
        if not available:
            self._log(f'Torrent client connection failed: {err}')
            self._update_qb_status(False, err)
            # Don't show dialog for periodic checks to avoid spam, just update status
            return
        for title, info in self.tracker.get_all():
            url = info['url']
            last_s, last_ep = self.tracker.get_last_season_and_episode(title)
            try:
                latest_s, latest_ep, magnet = NyaaScraper.get_latest_episode_and_magnet(url, title, self.tracker, self.quality_settings)
                if latest_ep is None or magnet is None:
                    self._log(f'Failed to scrape: {title}')
                    continue
                if latest_s > last_s or (latest_s == last_s and latest_ep > last_ep):
                    ok, err = self.torrent_client.launch_magnet(magnet, self.qb_config.category)
                    if ok:
                        self.tracker.update_episode(title, latest_s, latest_ep)
                        self._update_tree_episode(title, latest_s, latest_ep)
                        client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(self.torrent_config.preferred_client, "Torrent client")
                        self._log(f'New episode {latest_ep} for {title} sent to {client_name}.')
                    else:
                        self._log(f'Failed to add magnet for {title}: {err}')
                else:
                    self._log(f'No new episode for {title}.')
            except Exception as e:
                self._log(f'Error checking {title}: {e}')

    def _update_tree_episode(self, title, season, episode):
        if self.anime_tree.exists(title):
            vals = list(self.anime_tree.item(title, 'values'))
            vals[1] = season
            vals[2] = episode
            self.anime_tree.item(title, values=vals)

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()
    
    # Utility methods
    def sort_treeview(self, column, reverse, sort_type):
        """Sort treeview by column"""
        # Get all items
        items = [(self.episodes_tree.set(item, column), item) for item in self.episodes_tree.get_children('')]
        
        # Determine if we should reverse the sort
        if self.current_sort_column == column:
            reverse = not self.current_sort_reverse
        else:
            reverse = False
        
        # Sort items
        items.sort(key=lambda x: self.get_sort_key(x[0], sort_type), reverse=reverse)
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            self.episodes_tree.move(item, '', index)
        
        # Update sort state
        self.current_sort_column = column
        self.current_sort_reverse = reverse
        
        # Update column header to show sort direction
        self.update_sort_indicator(column, reverse)
    
    def get_sort_key(self, value, sort_type):
        """Convert value to appropriate type for sorting"""
        if not value:
            return (0, 0) if sort_type in ['seeders', 'leechers', 'episode'] else ''
        
        if sort_type == 'episode':
            # Extract episode number from text like "Ep 01", "S01E01", etc.
            try:
                if 'E' in value and 'S' in value:
                    # Format like "S01E01"
                    ep_part = value.split('E')[-1]
                    return (0, int(ep_part))
                elif 'Ep' in value:
                    # Format like "Ep 01"
                    ep_part = value.split()[-1]
                    return (0, int(ep_part))
                else:
                    # Try to extract any number from the value
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        return (0, int(numbers[-1]))
                    return (0, 0)
            except (ValueError, IndexError):
                return (0, 0)
        
        elif sort_type in ['seeders', 'leechers']:
            try:
                return (0, int(value))
            except ValueError:
                return (0, 0)
        
        elif sort_type == 'size':
            # Convert size to bytes for sorting (e.g., "1.2 GB" -> 1288490188)
            return self.parse_size_for_sort(value)
        
        elif sort_type == 'datetime':
            # Convert combined datetime to sortable format
            return value
        
        else:
            # Text sorting
            return value.lower()
    
    def parse_size_for_sort(self, size_str):
        """Convert size string to bytes for sorting"""
        if not size_str or size_str == 'Unknown':
            return 0
        
        try:
            size_str = size_str.strip().upper()
            for unit, multiplier in ScraperSettings.SIZE_UNITS.items():
                if unit in size_str:
                    num = float(size_str.replace(unit, '').strip())
                    return int(num * multiplier)
            # Assume bytes if no unit found
            return int(float(size_str))
        except (ValueError, AttributeError):
            return 0
    
    def combine_date_time(self, date_str, time_str):
        """Combine date and time strings into a single display string"""
        if not date_str and not time_str:
            return ''
        elif not date_str:
            return time_str
        elif not time_str:
            return date_str
        else:
            return f"{date_str} {time_str}"
    
    def update_sort_indicator(self, column, reverse):
        """Update column header to show sort direction"""
        # Reset all headers
        for col in ['#0', 'Episode', 'Size', 'DateTime', 'Seeders', 'Leechers']:
            header_text = GUISettings.EPISODES_TREE_HEADINGS.get(col, col)
            self.episodes_tree.heading(col, text=header_text)
        
        # Update the sorted column header
        base_text = GUISettings.EPISODES_TREE_HEADINGS.get(column, column)
        arrow = ' ▼' if reverse else ' ▲'
        self.episodes_tree.heading(column, text=base_text + arrow)


def run_headless():
    """Run the scraper in headless mode (command-line only)"""
    print("[DEBUG] Starting headless mode...")
    
    try:
        # Initialize components
        print("[DEBUG] Initializing AnimeTracker...")
        tracker = AnimeTracker()
        print(f"[DEBUG] Tracker loaded with {len(tracker.data)} entries")
        
        if len(tracker.data) == 0:
            print("[INFO] No anime entries found in tracker. Exiting.")
            return
        
        print("[DEBUG] Initializing QBittorrentConfig...")
        qb_config = QBittorrentConfig()
        print(f"[DEBUG] QB Config: {qb_config.host}:{qb_config.port}")
        
        # Test qBittorrent connection with timeout
        print("[DEBUG] Creating QBittorrentClient...")
        qb = QBittorrentClient(qb_config)
        
        print("[DEBUG] Attempting to connect to qBittorrent...")
        try:
            connected, err = qb.connect()
            if not connected:
                print(f'[ERROR] qBittorrent connection failed: {err}')
                print("[INFO] Continuing without qBittorrent connection for testing...")
                # Continue without qBittorrent for testing
                qb = None
            else:
                print("[DEBUG] Successfully connected to qBittorrent")
        except Exception as e:
            print(f"[ERROR] Exception during qBittorrent connection: {e}")
            print("[INFO] Continuing without qBittorrent connection for testing...")
            qb = None
        
        anime_list = list(tracker.get_all())
        print(f"[DEBUG] Processing {len(anime_list)} anime entries")
        
        # Limit to first entries for testing
        test_limit = min(TestSettings.HEADLESS_TEST_LIMIT, len(anime_list))
        print(f"[DEBUG] Testing with first {test_limit} entries only")
        
        for i, (title, info) in enumerate(anime_list[:test_limit]):
            print(f"[DEBUG] Processing {i+1}/{test_limit}: {title}")
            url = info['url']
            last_s = info.get('last_season', 1)
            last_ep = info.get('last_episode', 0)
            print(f"[DEBUG] URL: {url}, Last tracked: S{last_s}E{last_ep}")

            try:
                print(f"[DEBUG] Scraping latest episode for {title}...")
                try:
                    latest_s, latest_ep, magnet = NyaaScraper.get_latest_episode_and_magnet(url, title, tracker, self.quality_settings)
                    print(f"[DEBUG] Scrape result - Season: {latest_s}, Episode: {latest_ep}, Magnet: {'Found' if magnet else 'None'}")
                except Exception as scrape_error:
                    print(f"[WARNING] Scraping failed for {title}: {scrape_error}")
                    continue

                if latest_ep is None or magnet is None:
                    print(f'[WARNING] Failed to scrape: {title}')
                    continue

                if latest_s > last_s or (latest_s == last_s and latest_ep > last_ep):
                    print(f"[DEBUG] New episode found: S{latest_s}E{latest_ep} > S{last_s}E{last_ep}")
                    if qb:
                        ok, err = qb.add_magnet(magnet, qb_config.category)
                        if ok:
                            tracker.update_episode(title, latest_s, latest_ep)
                            print(f'[SUCCESS] New episode S{latest_s}E{latest_ep} for {title} sent to qBittorrent.')
                        else:
                            print(f'[ERROR] Failed to add magnet for {title}: {err}')
                    else:
                        print(f'[INFO] Would download episode S{latest_s}E{latest_ep} for {title} (qBittorrent not connected)')
                        # Update tracker anyway for testing
                        tracker.update_episode(title, latest_s, latest_ep)
                else:
                    print(f'[INFO] No new episode for {title} (current: S{latest_s}E{latest_ep}, last: S{last_s}E{last_ep}).')
            except Exception as e:
                print(f'[ERROR] Exception checking {title}: {e}')
                import traceback
                traceback.print_exc()
        
        print("[DEBUG] Headless check completed successfully.")
        
    except Exception as e:
        print(f"[FATAL ERROR] Exception in run_headless: {e}")
        import traceback
        traceback.print_exc()


def main():
    try:
        # Setup logging
        log_file = setup_logging()
        print(f'Logging initialized. Log file: {log_file}')
        
        # Check for tracker file
        import os
        if not os.path.exists(TRACKER_FILE):
            print(f'ERROR: {TRACKER_FILE} not found!')
            return
        
        parser = argparse.ArgumentParser(description='Nyaa Auto Downloader')
        parser.add_argument('--headless', action='store_true', 
                           help='Run in headless mode (no GUI, single check)')
        parser.add_argument('--no-gui', action='store_true', 
                           help='Alias for --headless')

        args = parser.parse_args()
        
        if args.headless or args.no_gui:
            run_headless()
        else:
            # Run GUI mode
            try:
                root = tk.Tk()
                app = App(root)
                root.protocol("WM_DELETE_WINDOW", app.on_close)
                root.mainloop()
            except Exception as gui_error:
                print(f'GUI ERROR: {gui_error}')
                import traceback
                traceback.print_exc()
                
    except Exception as main_error:
        print(f'MAIN ERROR: {main_error}')
        import traceback
        traceback.print_exc()
        input('Press Enter to exit...')


if __name__ == '__main__':
    main()
