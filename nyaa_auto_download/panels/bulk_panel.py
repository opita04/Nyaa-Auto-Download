"""
Bulk Panel for Nyaa Auto Download.
Provides bulk torrent download functionality for all tracked series.
"""

import tkinter as tk
from tkinter import ttk
import threading
from typing import Optional, List, Dict, Any, Callable

from settings import GUISettings


class BulkPanel:
    """
    Bulk torrents panel component for downloading multiple torrents at once.
    Shows latest episodes from all tracked series with selection capabilities.
    """
    
    def __init__(self, parent_paned_window, app_controller):
        """Initialize the bulk panel."""
        self.parent_paned = parent_paned_window
        self.app_controller = app_controller
        self.visible = False
        
        # UI components
        self.frame = None
        self.bulk_torrents_tree = None
        
        # Create the panel
        self._create_panel()
        
    def _create_panel(self):
        """Create the bulk panel frame with proper layout."""
        # Main panel frame
        self.frame = ttk.Frame(self.parent_paned)
        
        # Header section
        self._create_header()
        
        # Content area
        self._create_content_area()
        
    def _create_header(self):
        """Create the panel header with title and controls."""
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(header_frame, text='All Latest Torrents', 
                              font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(side='left')
        
        # Refresh button
        refresh_btn = ttk.Button(header_frame, text='🔄 Refresh', command=self.refresh)
        refresh_btn.pack(side='right', padx=5)
        
        # Close button
        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide)
        close_btn.pack(side='right')
        
    def _create_content_area(self):
        """Create the main content area with torrent list."""
        # List frame
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for bulk torrents
        self.bulk_torrents_tree = ttk.Treeview(list_frame,
                                              columns=('Series', 'Episode', 'Status'),
                                              show='tree headings', 
                                              height=GUISettings.EPISODES_TREE_HEIGHT)
        
        # Configure headers
        self.bulk_torrents_tree.heading('#0', text='Title')
        self.bulk_torrents_tree.heading('Series', text='Series')
        self.bulk_torrents_tree.heading('Episode', text='Episode')  
        self.bulk_torrents_tree.heading('Status', text='Status')
        
        # Set column widths
        self.bulk_torrents_tree.column('#0', width=300)
        self.bulk_torrents_tree.column('Series', width=150)
        self.bulk_torrents_tree.column('Episode', width=80)
        self.bulk_torrents_tree.column('Status', width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.bulk_torrents_tree.yview)
        self.bulk_torrents_tree.configure(yscrollcommand=scrollbar.set)
        
        self.bulk_torrents_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click to toggle selection
        self.bulk_torrents_tree.bind('<Double-1>', self._on_double_click)
        
        # Buttons frame
        self._create_buttons()
        
    def _create_buttons(self):
        """Create action buttons."""
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(pady=5)
        
        # Selection buttons
        ttk.Button(buttons_frame, text='Select All', 
                  command=self.select_all).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text='Deselect All', 
                  command=self.deselect_all).pack(side='left', padx=5)
                  
        # Download buttons
        ttk.Button(buttons_frame, text='Download Selected', 
                  command=self.download_selected).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text='Download All', 
                  command=self.download_all).pack(side='left', padx=5)
                  
    def refresh(self):
        """Refresh the bulk torrents list."""
        # Clear existing items
        for item in self.bulk_torrents_tree.get_children():
            self.bulk_torrents_tree.delete(item)
            
        # Show loading message
        loading_item = self.bulk_torrents_tree.insert('', 'end', 
                                                    text='Loading latest torrents...', 
                                                    values=('', '', ''))
        self.bulk_torrents_tree.update()
        
        # Load torrents in background thread
        def load_torrents():
            try:
                # Get all tracked series data
                all_series = self.app_controller.tracker_controller.get_all_series()
                
                # Use torrent controller to gather latest torrents
                torrents = self.app_controller.torrent_controller.gather_all_latest_torrents(all_series)
                
                # Update UI in main thread
                self.frame.after(0, lambda: self._populate_torrents(torrents, loading_item))
                
            except Exception as e:
                self.frame.after(0, lambda: self._handle_load_error(str(e), loading_item))
                
        threading.Thread(target=load_torrents, daemon=True).start()
        
    def _populate_torrents(self, torrents: List[Dict[str, Any]], loading_item):
        """Populate the torrents tree with fetched torrents."""
        # Remove loading message
        if loading_item and self.bulk_torrents_tree.exists(loading_item):
            self.bulk_torrents_tree.delete(loading_item)
            
        if not torrents:
            self.bulk_torrents_tree.insert('', 'end', text='No torrents found', 
                                         values=('', '', ''))
            return
            
        # Add torrents to tree
        for torrent in torrents:
            # Determine status and color
            status = 'NEW' if torrent.get('is_new', False) else 'Current'
            
            # Extract quality info
            quality_info = self.app_controller.torrent_controller.extract_quality_from_title(
                torrent.get('title', ''))
                
            # Create display status
            display_status = f"{status} ({quality_info})" if quality_info != 'Unknown' else status
            
            # Truncate long titles
            display_title = torrent.get('title', '')[:55]
            if len(torrent.get('title', '')) > 55:
                display_title += '...'
                
            # Insert item
            item = self.bulk_torrents_tree.insert('', 'end',
                                                text=display_title,
                                                values=(torrent.get('series_title', ''),
                                                       torrent.get('episode_info', ''),
                                                       display_status),
                                                tags=(torrent.get('magnet', ''),))
            
            # Color code NEW items
            if status == 'NEW':
                self.bulk_torrents_tree.set(item, 'Status', f"🆕 {display_status}")
                
        # Log completion
        series_count = len(set(t.get('series_title', '') for t in torrents))
        self.app_controller._log(f'Loaded {len(torrents)} torrents from {series_count} series')
        
    def _handle_load_error(self, error_msg: str, loading_item):
        """Handle errors during torrent loading."""
        if loading_item and self.bulk_torrents_tree.exists(loading_item):
            self.bulk_torrents_tree.delete(loading_item)
            
        self.bulk_torrents_tree.insert('', 'end', 
                                     text=f'Error loading torrents: {error_msg}', 
                                     values=('', '', ''))
        self.app_controller._log(f'Error loading bulk torrents: {error_msg}')
        
    def _on_double_click(self, event):
        """Handle double-click on torrent to toggle selection."""
        item = self.bulk_torrents_tree.identify_row(event.y)
        if item:
            # Toggle selection
            if item in self.bulk_torrents_tree.selection():
                self.bulk_torrents_tree.selection_remove(item)
            else:
                self.bulk_torrents_tree.selection_add(item)
                
    def select_all(self):
        """Select all torrents in the list."""
        all_items = self.bulk_torrents_tree.get_children()
        self.bulk_torrents_tree.selection_set(all_items)
        
    def deselect_all(self):
        """Deselect all torrents in the list."""
        self.bulk_torrents_tree.selection_remove(self.bulk_torrents_tree.selection())
        
    def download_selected(self):
        """Download selected torrents from bulk list."""
        selection = self.bulk_torrents_tree.selection()
        if not selection:
            self.app_controller._log('No torrents selected for download.')
            return
            
        downloaded_count = 0
        failed_count = 0
        
        for item in selection:
            try:
                tags = self.bulk_torrents_tree.item(item, 'tags')
                if tags and tags[0]:
                    magnet = tags[0]
                    title = self.bulk_torrents_tree.item(item, 'text')
                    
                    # Use torrent controller to download
                    success, error_msg = self.app_controller.torrent_controller.launch_magnet_system_default(magnet)
                    
                    if success:
                        self.app_controller._log(f'Launched torrent: {title}')
                        downloaded_count += 1
                    else:
                        self.app_controller._log(f'Failed to launch torrent: {title[:30]}... - {error_msg}')
                        failed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                self.app_controller._log(f'Error processing torrent: {e}')
                failed_count += 1
                
        # Summary message
        total = len(selection)
        if downloaded_count > 0:
            self.app_controller._log(f'Successfully launched {downloaded_count} out of {total} selected torrents.')
        if failed_count > 0:
            self.app_controller._log(f'Failed to launch {failed_count} torrents.')
            
    def download_all(self):
        """Download all torrents from bulk list."""
        all_items = self.bulk_torrents_tree.get_children()
        if not all_items:
            self.app_controller._log('No torrents available for download.')
            return
            
        # Select all items first
        self.select_all()
        
        # Then download them
        self.download_selected()
        
    def show(self):
        """Show the bulk panel."""
        if not self.visible:
            # Add to parent paned window
            self.parent_paned.add(self.frame, weight=1)
            self.visible = True
            
            # Load torrents when shown
            self.refresh()
            
    def hide(self):
        """Hide the bulk panel."""
        if self.visible:
            self.parent_paned.remove(self.frame)
            self.visible = False
            
    def toggle(self):
        """Toggle the visibility of the bulk panel."""
        if self.visible:
            self.hide()
        else:
            self.show()
            
    def is_visible(self) -> bool:
        """Check if the bulk panel is currently visible."""
        return self.visible
