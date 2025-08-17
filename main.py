import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import scrolledtext
import threading
import re
import requests
from datetime import datetime
import argparse
import time

# Import modules
from modules.nyaa_scraper import NyaaScraper
from modules.anime_tracker import AnimeTracker
from modules.qbittorrent_client import QBittorrentClient
from modules.settings_panel import SettingsPanel
from utils.logging_utils import setup_logging, create_trace_file
from settings import *

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
        self.qb_config = QBittorrentConfig()
        self.check_interval = DEFAULT_INTERVAL
        self.check_thread = None
        self.stop_event = threading.Event()
        self._setup_gui()
        self._load_tracker()
        self._log('Application started.')
        self._start_periodic_check()

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
        self.settings_panel = SettingsPanel(self.left_frame, self.qb_config, self.check_interval, self.on_settings_save)

        # Status Log
        log_frame = ttk.LabelFrame(self.left_frame, text='Status Log')
        log_frame.grid(row=3, column=0, sticky='nsew', padx=5, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=GUISettings.LOG_TEXT_HEIGHT, 
                                                state='disabled', wrap='word')
        self.log_text.pack(fill='both', expand=True)

        self.left_frame.rowconfigure(1, weight=1)
        self.left_frame.rowconfigure(3, weight=1)
        self.left_frame.columnconfigure(0, weight=1)
        
        # Setup episodes panel
        self._setup_episodes_panel()
        
        # Setup search panel
        self._setup_search_panel()
    
    def on_settings_save(self, qb_config, check_interval):
        """Callback for when settings are saved"""
        self.qb_config = qb_config
        self.check_interval = check_interval
        self._log('Configuration saved.')
    
    def toggle_settings_panel(self):
        """Toggle the visibility of the settings panel"""
        self.settings_panel.toggle()
    
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
            results = NyaaScraper.search(query)
            
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
            
            self.search_results_tree.insert('', 'end', 
                                           text=result['title'][:60] + ('...' if len(result['title']) > 60 else ''),
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
        
        # Download using qBittorrent
        qb = QBittorrentClient(self.qb_config)
        connected, err = qb.connect()
        if not connected:
            self._log(f'qBittorrent connection failed: {err}')
            return
        
        ok, err = qb.add_magnet(magnet, self.qb_config.category)
        if ok:
            self._log(f'Search result "{episode_title}" sent to qBittorrent.')
        else:
            self._log(f'Failed to add search result to qBittorrent: {err}')
    
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
        
        # Download using qBittorrent
        qb = QBittorrentClient(self.qb_config)
        connected, err = qb.connect()
        if not connected:
            self._log(f'qBittorrent connection failed: {err}')
            return
        
        ok, err = qb.add_magnet(magnet, self.qb_config.category)
        if ok:
            self._log(f'Episode "{episode_title}" sent to qBittorrent.')
        else:
            self._log(f'Failed to add episode to qBittorrent: {err}')
    
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

    def _periodic_check(self):
        while not self.stop_event.is_set():
            self._check_all()
            for _ in range(self.check_interval):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def _check_all(self):
        self._log('Checking for new episodes...')
        qb = QBittorrentClient(self.qb_config)
        connected, err = qb.connect()
        if not connected:
            self._log(f'qBittorrent connection failed: {err}')
            return
        for title, info in self.tracker.get_all():
            url = info['url']
            last_s, last_ep = self.tracker.get_last_season_and_episode(title)
            try:
                latest_s, latest_ep, magnet = NyaaScraper.get_latest_episode_and_magnet(url, title, self.tracker)
                if latest_ep is None or magnet is None:
                    self._log(f'Failed to scrape: {title}')
                    continue
                if latest_s > last_s or (latest_s == last_s and latest_ep > last_ep):
                    ok, err = qb.add_magnet(magnet, self.qb_config.category)
                    if ok:
                        self.tracker.update_episode(title, latest_s, latest_ep)
                        self._update_tree_episode(title, latest_s, latest_ep)
                        self._log(f'New episode {latest_ep} for {title} sent to qBittorrent.')
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
                    latest_s, latest_ep, magnet = NyaaScraper.get_latest_episode_and_magnet(url, title, tracker)
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
