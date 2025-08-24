"""
Main Window for Nyaa Auto Download GUI.
Handles the primary user interface and coordinates with panels.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Callable

from settings import GUISettings, DialogSettings
from nyaa_auto_download.core import AppController
from nyaa_auto_download.panels import (
    EpisodesPanel, SearchPanel, BulkPanel, SettingsPanel
)


class MainWindow:
    """
    Main application window handling GUI layout and coordination.
    Manages panels and communicates with the AppController for business logic.
    """
    
    def __init__(self, root: tk.Tk, app_controller: AppController):
        """Initialize the main window."""
        self.root = root
        self.app_controller = app_controller
        
        # Set up window properties
        self.root.title(GUISettings.WINDOW_TITLE)
        
        # GUI components
        self.main_paned = None
        self.left_frame = None
        self.log_text = None
        self.anime_tree = None
        
        # Status indicators
        self.settings_status_label = None
        self.qb_status_indicator = None
        self.qb_status_message = None
        self.qb_check_btn = None
        
        # Panel instances
        self.episodes_panel: Optional[EpisodesPanel] = None
        self.search_panel: Optional[SearchPanel] = None
        self.bulk_panel: Optional[BulkPanel] = None
        self.settings_panel: Optional[SettingsPanel] = None
        
        # Panel visibility states
        self.episodes_visible = False
        self.search_panel_visible = False
        self.bulk_panel_visible = False
        self.settings_panel_visible = False
        
        # Set up callbacks with app controller
        self._setup_controller_callbacks()
        
        # Build the GUI
        self._setup_gui()
        
        # Load initial data
        self._load_initial_data()
        
    def _setup_controller_callbacks(self):
        """Set up callback functions for the app controller."""
        self.app_controller.set_callbacks(
            log_callback=self._handle_log_message,
            connection_callback=self._handle_connection_status,
            settings_callback=self._handle_settings_status
        )
        
    def _handle_log_message(self, message: str):
        """Handle log messages from the app controller."""
        if self.log_text:
            self.log_text.configure(state='normal')
            self.log_text.insert('end', f'{message}\n')
            self.log_text.see('end')
            self.log_text.configure(state='disabled')
            
    def _handle_connection_status(self, connected: bool, error_msg: str = ""):
        """Handle connection status updates from the app controller."""
        if not self.qb_status_indicator or not self.qb_status_message:
            return
            
        if connected:
            self.qb_status_indicator.config(text="✅ Connected", foreground="green")
            self.qb_status_message.config(text="Torrent client is available", foreground="green")
        else:
            self.qb_status_indicator.config(text="❌ Disconnected", foreground="red")
            self.qb_status_message.config(text=f"Connection failed: {error_msg}", foreground="red")
            
    def _handle_settings_status(self, message: str, error: bool = False):
        """Handle settings status updates from the app controller."""
        if not self.settings_status_label:
            return
            
        color = 'red' if error else 'green'
        self.settings_status_label.config(text=message, foreground=color)
        
        # Auto-clear after 3 seconds
        self.root.after(3000, lambda: self.settings_status_label.config(text='Ready', foreground='gray'))
        
    def _setup_gui(self):
        """Set up the main GUI layout."""
        # Main frame
        mainframe = ttk.Frame(self.root, padding=GUISettings.MAIN_PADDING)
        mainframe.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create main paned window
        self.main_paned = ttk.PanedWindow(mainframe, orient='horizontal')
        self.main_paned.grid(row=0, column=0, sticky='nsew')
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        
        # Left panel (main content)
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=3)
        
        # Set up main content sections
        self._setup_add_anime_section()
        self._setup_anime_list_section()
        self._setup_log_section()
        self._setup_status_indicators()
        
        # Initialize panels
        self._initialize_panels()
        
        # Configure layout weights
        self.left_frame.columnconfigure(0, weight=1)
        self.left_frame.rowconfigure(1, weight=1)  # Anime list expands
        self.left_frame.rowconfigure(2, weight=1)  # Log expands
        
    def _setup_add_anime_section(self):
        """Set up the add new anime section."""
        add_frame = ttk.LabelFrame(self.left_frame, text='Add New Anime')
        add_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        # Title and URL inputs
        ttk.Label(add_frame, text='Title:').grid(row=0, column=0, sticky='w')
        self.title_entry = ttk.Entry(add_frame, width=GUISettings.TITLE_ENTRY_WIDTH)
        self.title_entry.grid(row=0, column=1, sticky='ew')
        
        ttk.Label(add_frame, text='Nyaa.si URL:').grid(row=1, column=0, sticky='w')
        self.url_entry = ttk.Entry(add_frame, width=GUISettings.URL_ENTRY_WIDTH)
        self.url_entry.grid(row=1, column=1, sticky='ew')
        
        # Add button
        add_btn = ttk.Button(add_frame, text='Add Series', command=self._add_series)
        add_btn.grid(row=0, column=2, rowspan=2, padx=5)
        
        # Control buttons
        self._setup_control_buttons(add_frame)
        
        add_frame.columnconfigure(1, weight=1)
        
    def _setup_control_buttons(self, parent):
        """Set up the control buttons (search, settings, bulk)."""
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=0, column=3, rowspan=2, padx=5)
        
        # Search button
        search_btn = tk.Button(controls_frame, text="🔍", width=3, 
                             command=self.toggle_search_panel,
                             font=('TkDefaultFont', 12))
        search_btn.pack(side='top', fill='x', pady=(0, 2))
        
        # Settings button
        settings_btn = tk.Button(controls_frame, text="⚙️", width=3,
                               command=self.toggle_settings_panel,
                               font=('TkDefaultFont', 12))
        settings_btn.pack(side='top', fill='x', pady=(0, 2))
        
        # Bulk torrents button
        bulk_btn = tk.Button(controls_frame, text="📋", width=3,
                           command=self.toggle_bulk_panel,
                           font=('TkDefaultFont', 12))
        bulk_btn.pack(side='top', fill='x')
        
    def _setup_anime_list_section(self):
        """Set up the tracked anime list section."""
        list_frame = ttk.LabelFrame(self.left_frame, text='Tracked Anime')
        list_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        # Anime treeview
        self.anime_tree = ttk.Treeview(list_frame, columns=GUISettings.ANIME_TREE_COLUMNS,
                                     show='headings', height=GUISettings.ANIME_TREE_HEIGHT)
        
        # Configure headers and widths
        for col, header in GUISettings.ANIME_TREE_HEADINGS.items():
            self.anime_tree.heading(col, text=header)
            self.anime_tree.column(col, width=GUISettings.ANIME_TREE_WIDTHS[col])
            
        self.anime_tree.grid(row=0, column=0, sticky='nsew')
        
        # Bind events
        self.anime_tree.bind('<Double-1>', self._on_anime_double_click)
        self.anime_tree.bind('<Button-3>', self._on_anime_right_click)
        
        # Context menu
        self._setup_context_menu()
        
        # Buttons
        self._setup_list_buttons(list_frame)
        
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
    def _setup_context_menu(self):
        """Set up the right-click context menu."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Toggle Multi-Episode Downloads",
                                    command=self._toggle_multi_episode)
        
    def _setup_list_buttons(self, parent):
        """Set up buttons for the anime list."""
        remove_btn = ttk.Button(parent, text='Remove Series', command=self._remove_series)
        remove_btn.grid(row=1, column=0, sticky='ew', pady=3)
        
        edit_btn = ttk.Button(parent, text='Edit Title', command=self._edit_series)
        edit_btn.grid(row=2, column=0, sticky='ew', pady=3)
        
        multi_btn = ttk.Button(parent, text='Toggle Multi-Episode', command=self._toggle_multi_episode)
        multi_btn.grid(row=3, column=0, sticky='ew', pady=3)
        
        force_btn = ttk.Button(parent, text='Force Check Now', command=self._force_check)
        force_btn.grid(row=4, column=0, sticky='ew', pady=3)
        
    def _setup_log_section(self):
        """Set up the status log section."""
        log_frame = ttk.LabelFrame(self.left_frame, text='Status Log')
        log_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=GUISettings.LOG_TEXT_HEIGHT,
                                                state='disabled', wrap='word')
        self.log_text.pack(fill='both', expand=True)
        
    def _setup_status_indicators(self):
        """Set up status indicator sections."""
        # Settings status
        settings_frame = ttk.Frame(self.left_frame)
        settings_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=2)
        
        ttk.Label(settings_frame, text='Settings:', font=('TkDefaultFont', 8)).pack(side='left')
        self.settings_status_label = ttk.Label(settings_frame, text='Ready', 
                                             font=('TkDefaultFont', 8), foreground='gray')
        self.settings_status_label.pack(side='left', padx=5)
        
        info_btn = ttk.Button(settings_frame, text='ℹ️', width=3, command=self._show_settings_info)
        info_btn.pack(side='right')
        
        # Connection status
        conn_frame = ttk.Frame(self.left_frame)
        conn_frame.grid(row=4, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Label(conn_frame, text="Connection Status:").pack(side='left')
        
        self.qb_status_indicator = ttk.Label(conn_frame, text="🔄 Checking...", 
                                           font=('TkDefaultFont', 10, 'bold'))
        self.qb_status_indicator.pack(side='left', padx=5)
        
        self.qb_status_message = ttk.Label(conn_frame, text="", foreground="gray")
        self.qb_status_message.pack(side='left', padx=5, fill='x', expand=True)
        
        self.qb_check_btn = ttk.Button(conn_frame, text="🔄 Check", width=8,
                                     command=self._check_connection)
        self.qb_check_btn.pack(side='right', padx=5)
        
    def _initialize_panels(self):
        """Initialize all side panels."""
        # Initialize functional panels
        self.settings_panel = SettingsPanel(self.main_paned, self.app_controller)
        self.bulk_panel = BulkPanel(self.main_paned, self.app_controller)
        
        # TODO: Initialize other panels once they are implemented
        # self.episodes_panel = EpisodesPanel(...)
        # self.search_panel = SearchPanel(...)
        
    def _load_initial_data(self):
        """Load initial data and update the UI."""
        # Load tracked anime
        self._refresh_anime_list()
        
        # Test initial connection
        self._check_connection()
        
    # Event Handlers
    def _add_series(self):
        """Add a new anime series."""
        title = self.title_entry.get().strip()
        url = self.url_entry.get().strip()
        
        if not title or not url:
            self._log('Title and URL required.')
            return
            
        if self.app_controller.tracker_controller.add_series(title, url):
            self._refresh_anime_list()
            self._log(f'Added series: {title}')
            self.title_entry.delete(0, 'end')
            self.url_entry.delete(0, 'end')
        else:
            self._log(f'Series already exists: {title}')
            
    def _remove_series(self):
        """Remove selected anime series."""
        selected = self.anime_tree.selection()
        if not selected:
            self._log('No series selected.')
            return
            
        for title in selected:
            if self.app_controller.tracker_controller.remove_series(title):
                self._log(f'Removed series: {title}')
            else:
                self._log(f'Failed to remove series: {title}')
                
        self._refresh_anime_list()
        
    def _edit_series(self):
        """Edit selected anime series."""
        # TODO: Implement edit dialog
        # This will be a more complex dialog for editing series info
        self._log('Edit series functionality will be implemented in next phase.')
        
    def _toggle_multi_episode(self):
        """Toggle multi-episode downloads for selected series."""
        selected = self.anime_tree.selection()
        if not selected:
            self._log('No series selected.')
            return
            
        title = selected[0]
        current_flag = self.app_controller.tracker_controller.allows_multi_episode(title)
        new_flag = not current_flag
        
        if self.app_controller.tracker_controller.set_multi_episode_flag(title, new_flag):
            status = "enabled" if new_flag else "disabled"
            self._log(f'Multi-episode downloads {status} for "{title}"')
            self._refresh_anime_list()
        else:
            self._log(f'Failed to update multi-episode setting for "{title}"')
            
    def _force_check(self):
        """Force a manual check for all series."""
        self.app_controller.force_check_all()
        
    def _check_connection(self):
        """Check torrent client connection."""
        available, error_msg = self.app_controller.test_connection()
        self._handle_connection_status(available, error_msg)
        
    def _on_anime_double_click(self, event):
        """Handle double-click on anime list."""
        selected = self.anime_tree.selection()
        if not selected:
            return
            
        title = selected[0]
        series_info = self.app_controller.tracker_controller.get_series_info(title)
        if series_info:
            url = series_info['url']
            # TODO: Show episodes panel
            self._log(f'Would show episodes for: {title}')
            
    def _on_anime_right_click(self, event):
        """Handle right-click on anime list."""
        item = self.anime_tree.identify_row(event.y)
        if item:
            self.anime_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def _refresh_anime_list(self):
        """Refresh the anime list display."""
        # Clear existing items
        self.anime_tree.delete(*self.anime_tree.get_children())
        
        # Load current data
        all_series = self.app_controller.tracker_controller.get_all_series()
        
        for title, info in all_series:
            multi_status = " [Multi-Ep]" if info.get('allow_multi_episode', False) else ""
            display_title = title + multi_status
            last_season = info.get('last_season', 1)
            last_episode = info.get('last_episode', 0)
            
            self.anime_tree.insert('', 'end', iid=title, 
                                 values=(display_title, last_season, last_episode, info['url']))
                                 
    # Panel Management
    def toggle_search_panel(self):
        """Toggle the search panel."""
        # TODO: Implement when search panel is created
        self._log('Search panel toggle will be implemented in next phase.')
        
    def toggle_settings_panel(self):
        """Toggle the settings panel."""
        if self.settings_panel:
            # Hide other panels first
            if hasattr(self, 'episodes_panel') and self.episodes_panel and self.episodes_visible:
                self.episodes_panel.hide()
                self.episodes_visible = False
                
            # Toggle settings panel
            if self.settings_panel.is_visible():
                self.settings_panel.hide()
                self.settings_panel_visible = False
            else:
                self.settings_panel.show()
                self.settings_panel_visible = True
        else:
            self._log('Settings panel not available.')
        
    def toggle_bulk_panel(self):
        """Toggle the bulk torrents panel."""
        if self.bulk_panel:
            # Hide other panels first
            if self.settings_panel and self.settings_panel.is_visible():
                self.settings_panel.hide()
                self.settings_panel_visible = False
                
            if hasattr(self, 'episodes_panel') and self.episodes_panel and self.episodes_visible:
                self.episodes_panel.hide()
                self.episodes_visible = False
                
            # Toggle bulk panel
            if self.bulk_panel.is_visible():
                self.bulk_panel.hide()
                self.bulk_panel_visible = False
            else:
                self.bulk_panel.show()
                self.bulk_panel_visible = True
        else:
            self._log('Bulk panel not available.')
        
    # Utility Methods
    def _log(self, message: str):
        """Log a message (delegates to app controller)."""
        # This will trigger the callback which updates the UI
        self.app_controller._log(message)
        
    def _show_settings_info(self):
        """Show settings information dialog."""
        from settings import SETTINGS_FILE, TRACKER_FILE
        import os
        
        info_msg = f"""Settings Information:

📁 Settings File: {SETTINGS_FILE}
📂 Anime List: {TRACKER_FILE}

Current Status:
• Settings: {'Loaded' if os.path.exists(SETTINGS_FILE) else 'Using defaults'}
• Anime List: {'Loaded' if os.path.exists(TRACKER_FILE) else 'Empty'}

Settings are automatically saved when modified.
Anime list is automatically saved when changed."""
        
        messagebox.showinfo("Settings Info", info_msg)
        
    def on_closing(self):
        """Handle window closing."""
        self.app_controller.shutdown()
        self.root.destroy()
        
    def start_application(self):
        """Start the application (begin background tasks)."""
        self.app_controller.start_background_tasks()
        
    def get_root(self) -> tk.Tk:
        """Get the root window."""
        return self.root
