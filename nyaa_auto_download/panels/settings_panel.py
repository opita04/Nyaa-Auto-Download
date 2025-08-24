"""
Settings Panel for Nyaa Auto Download.
Provides interface for configuring application settings with proper display handling.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from settings import DEFAULT_INTERVAL, TorrentClientConfig, QualitySettings


class SettingsPanel:
    """
    Settings panel component for configuring application settings.
    Handles torrent client, quality filters, and connection settings.
    """
    
    def __init__(self, parent_paned_window, app_controller):
        """Initialize the settings panel."""
        self.parent_paned = parent_paned_window
        self.app_controller = app_controller
        self.visible = False
        
        # Configuration objects (loaded from app controller)
        self.qb_config = app_controller.qb_config
        self.torrent_config = app_controller.torrent_config
        self.quality_settings = app_controller.quality_settings
        self.check_interval = app_controller.check_interval
        
        # UI components
        self.frame = None
        self.connection_status = None
        
        # Form fields
        self.qb_host = None
        self.qb_port = None
        self.qb_user = None
        self.qb_pass = None
        self.qb_cat = None
        self.interval_entry = None
        self.torrent_client_combo = None
        self.custom_command_entry = None
        self.custom_command_frame = None
        self.fallback_var = None
        self.quality_mode_var = None
        self.preferred_qualities_text = None
        self.blocked_qualities_text = None
        
        # Create the panel
        self._create_panel()
        
    def _create_panel(self):
        """Create the settings panel frame with proper layout."""
        # Main panel frame
        self.frame = ttk.Frame(self.parent_paned)
        
        # Header section
        self._create_header()
        
        # Scrollable content area
        self._create_content_area()
        
        # Initialize visibility and field states
        self._refresh_from_controller()
        
    def _create_header(self):
        """Create the panel header with title and close button."""
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(header_frame, text='Application Settings', 
                              font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(side='left')
        
        # Close button
        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide)
        close_btn.pack(side='right')
        
    def _create_content_area(self):
        """Create the main content area with all settings sections."""
        # Main content frame with proper scrolling setup
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # qBittorrent settings section
        self._create_qbittorrent_section(content_frame)
        
        # Torrent client section
        self._create_torrent_client_section(content_frame)
        
        # Quality settings section
        self._create_quality_section(content_frame)
        
        # Action buttons section
        self._create_buttons_section(content_frame)
        
    def _create_qbittorrent_section(self, parent):
        """Create qBittorrent configuration section."""
        qb_frame = ttk.LabelFrame(parent, text='qBittorrent Settings')
        qb_frame.pack(fill='x', pady=5)
        
        # Host and Port row
        host_port_frame = ttk.Frame(qb_frame)
        host_port_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(host_port_frame, text='Host:').grid(row=0, column=0, sticky='w')
        self.qb_host = ttk.Entry(host_port_frame, width=20)
        self.qb_host.grid(row=0, column=1, padx=5, sticky='w')
        
        ttk.Label(host_port_frame, text='Port:').grid(row=0, column=2, padx=(20,5), sticky='w')
        self.qb_port = ttk.Entry(host_port_frame, width=8)
        self.qb_port.grid(row=0, column=3, sticky='w')
        
        # Username and Password row
        user_pass_frame = ttk.Frame(qb_frame)
        user_pass_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(user_pass_frame, text='Username:').grid(row=0, column=0, sticky='w')
        self.qb_user = ttk.Entry(user_pass_frame, width=20)
        self.qb_user.grid(row=0, column=1, padx=5, sticky='w')
        
        ttk.Label(user_pass_frame, text='Password:').grid(row=0, column=2, padx=(20,5), sticky='w')
        self.qb_pass = ttk.Entry(user_pass_frame, width=20, show='*')
        self.qb_pass.grid(row=0, column=3, sticky='w')
        
        # Category and Interval row
        cat_interval_frame = ttk.Frame(qb_frame)
        cat_interval_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(cat_interval_frame, text='Category:').grid(row=0, column=0, sticky='w')
        self.qb_cat = ttk.Entry(cat_interval_frame, width=20)
        self.qb_cat.grid(row=0, column=1, padx=5, sticky='w')
        
        ttk.Label(cat_interval_frame, text='Check Interval (hours):').grid(row=0, column=2, padx=(20,5), sticky='w')
        self.interval_entry = ttk.Entry(cat_interval_frame, width=8)
        self.interval_entry.grid(row=0, column=3, sticky='w')
        
    def _create_torrent_client_section(self, parent):
        """Create torrent client configuration section."""
        torrent_frame = ttk.LabelFrame(parent, text='Torrent Client Settings')
        torrent_frame.pack(fill='x', pady=5)
        
        # Client selection
        client_frame = ttk.Frame(torrent_frame)
        client_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(client_frame, text='Torrent Client:').pack(side='left')
        self.torrent_client_combo = ttk.Combobox(client_frame, width=20, state='readonly')
        self.torrent_client_combo['values'] = list(TorrentClientConfig.SUPPORTED_CLIENTS.values())
        self.torrent_client_combo.pack(side='left', padx=5)
        self.torrent_client_combo.bind('<<ComboboxSelected>>', self._on_torrent_client_changed)
        
        # Custom command (hidden by default)
        self.custom_command_frame = ttk.Frame(torrent_frame)
        ttk.Label(self.custom_command_frame, text='Custom Command:').pack(side='left')
        self.custom_command_entry = ttk.Entry(self.custom_command_frame, width=50)
        self.custom_command_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # Fallback option
        self.fallback_var = tk.BooleanVar()
        fallback_check = ttk.Checkbutton(torrent_frame, 
                                       text='Fallback to system default if primary client fails',
                                       variable=self.fallback_var)
        fallback_check.pack(anchor='w', padx=5, pady=2)
        
    def _create_quality_section(self, parent):
        """Create quality filtering section."""
        quality_frame = ttk.LabelFrame(parent, text='Quality Filter Settings')
        quality_frame.pack(fill='x', pady=5)
        
        # Filter mode selection
        mode_frame = ttk.Frame(quality_frame)
        mode_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(mode_frame, text='Filter Mode:').pack(side='left')
        self.quality_mode_var = tk.StringVar()
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.quality_mode_var, 
                                state='readonly', width=15)
        mode_combo['values'] = ['disabled', 'preferred', 'blocked', 'both']
        mode_combo.pack(side='left', padx=5)
        
        # Quality lists in a two-column layout
        lists_frame = ttk.Frame(quality_frame)
        lists_frame.pack(fill='x', padx=5, pady=5)
        
        # Preferred qualities column
        preferred_frame = ttk.Frame(lists_frame)
        preferred_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        ttk.Label(preferred_frame, text='Preferred Qualities:').pack(anchor='w')
        self.preferred_qualities_text = tk.Text(preferred_frame, height=4, width=25)
        self.preferred_qualities_text.pack(fill='both', expand=True)
        
        # Blocked qualities column  
        blocked_frame = ttk.Frame(lists_frame)
        blocked_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        ttk.Label(blocked_frame, text='Blocked Qualities:').pack(anchor='w')
        self.blocked_qualities_text = tk.Text(blocked_frame, height=4, width=25)
        self.blocked_qualities_text.pack(fill='both', expand=True)
        
        # Help text
        help_text = ("Enter one quality per line (e.g., 720p, 1080p, BluRay)\\n"
                    "Leave empty for no filtering. Examples: 720p, 1080p, WEBRip, BluRay")
        help_label = ttk.Label(quality_frame, text=help_text, font=('TkDefaultFont', 8), 
                             foreground='gray')
        help_label.pack(anchor='w', padx=5, pady=2)
        
    def _create_buttons_section(self, parent):
        """Create action buttons and status section."""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill='x', pady=10)
        
        # Action buttons
        ttk.Button(buttons_frame, text='Save Settings', 
                  command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text='Test Connection', 
                  command=self.test_connection).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text='Reset to Defaults', 
                  command=self.reset_to_defaults).pack(side='left', padx=5)
        
        # Connection status
        status_frame = ttk.Frame(buttons_frame)
        status_frame.pack(side='right', fill='x', expand=True)
        
        ttk.Label(status_frame, text='Connection Status:').pack(side='left')
        self.connection_status = ttk.Label(status_frame, text='Not tested', foreground='gray')
        self.connection_status.pack(side='left', padx=5)
        
    def _on_torrent_client_changed(self, event):
        """Handle torrent client selection change."""
        self._update_custom_command_visibility()
        
    def _update_custom_command_visibility(self):
        """Show/hide custom command field based on selected client."""
        if not self.torrent_client_combo or not self.custom_command_frame:
            return
            
        selected_name = self.torrent_client_combo.get()
        
        # Find the corresponding key
        selected_key = None
        for key, name in TorrentClientConfig.SUPPORTED_CLIENTS.items():
            if name == selected_name:
                selected_key = key
                break
                
        # Show/hide custom command field
        if selected_key == 'custom':
            self.custom_command_frame.pack(fill='x', padx=5, pady=2, 
                                         before=self.custom_command_frame.master.winfo_children()[-1])
        else:
            self.custom_command_frame.pack_forget()
            
    def _refresh_from_controller(self):
        """Refresh form fields from the app controller's current settings."""
        if not self.app_controller:
            return
            
        # Update config references
        self.qb_config = self.app_controller.qb_config
        self.torrent_config = self.app_controller.torrent_config
        self.quality_settings = self.app_controller.quality_settings
        self.check_interval = self.app_controller.check_interval
        
        # Populate qBittorrent fields
        if self.qb_host:
            self.qb_host.delete(0, 'end')
            self.qb_host.insert(0, self.qb_config.host)
            
        if self.qb_port:
            self.qb_port.delete(0, 'end')
            self.qb_port.insert(0, str(self.qb_config.port))
            
        if self.qb_user:
            self.qb_user.delete(0, 'end')
            self.qb_user.insert(0, self.qb_config.username)
            
        if self.qb_pass:
            self.qb_pass.delete(0, 'end')
            self.qb_pass.insert(0, self.qb_config.password)
            
        if self.qb_cat:
            self.qb_cat.delete(0, 'end')
            self.qb_cat.insert(0, self.qb_config.category)
            
        if self.interval_entry:
            self.interval_entry.delete(0, 'end')
            self.interval_entry.insert(0, str(self.check_interval // 3600))
            
        # Populate torrent client fields
        if self.torrent_client_combo:
            client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(
                self.torrent_config.preferred_client, 'qBittorrent')
            self.torrent_client_combo.set(client_name)
            
        if self.custom_command_entry:
            self.custom_command_entry.delete(0, 'end')
            self.custom_command_entry.insert(0, self.torrent_config.custom_command)
            
        if self.fallback_var:
            self.fallback_var.set(self.torrent_config.fallback_to_default)
            
        # Populate quality settings
        if self.quality_mode_var:
            self.quality_mode_var.set(self.quality_settings.quality_filter_mode)
            
        if self.preferred_qualities_text:
            self.preferred_qualities_text.delete('1.0', 'end')
            self.preferred_qualities_text.insert('1.0', 
                '\\n'.join(self.quality_settings.preferred_qualities))
                
        if self.blocked_qualities_text:
            self.blocked_qualities_text.delete('1.0', 'end')
            self.blocked_qualities_text.insert('1.0', 
                '\\n'.join(self.quality_settings.blocked_qualities))
                
        # Update visibility
        self._update_custom_command_visibility()
        
    def save_settings(self):
        """Save current settings through the app controller."""
        try:
            # Collect values from form fields
            if not self._validate_inputs():
                return False
                
            # Update qBittorrent config
            self.qb_config.host = self.qb_host.get().strip()
            self.qb_config.port = int(self.qb_port.get().strip())
            self.qb_config.username = self.qb_user.get().strip()
            self.qb_config.password = self.qb_pass.get().strip()
            self.qb_config.category = self.qb_cat.get().strip()
            
            # Update check interval
            interval_hours = int(self.interval_entry.get().strip())
            self.check_interval = max(1, interval_hours) * 3600
            
            # Update torrent client config
            selected_name = self.torrent_client_combo.get()
            selected_key = None
            for key, name in TorrentClientConfig.SUPPORTED_CLIENTS.items():
                if name == selected_name:
                    selected_key = key
                    break
            
            self.torrent_config.preferred_client = selected_key or 'qbittorrent'
            self.torrent_config.custom_command = self.custom_command_entry.get().strip()
            self.torrent_config.fallback_to_default = self.fallback_var.get()
            
            # Update quality settings
            self.quality_settings.quality_filter_mode = self.quality_mode_var.get()
            
            preferred_text = self.preferred_qualities_text.get('1.0', 'end-1c').strip()
            self.quality_settings.preferred_qualities = [
                q.strip() for q in preferred_text.split('\\n') if q.strip()
            ]
            
            blocked_text = self.blocked_qualities_text.get('1.0', 'end-1c').strip()
            self.quality_settings.blocked_qualities = [
                q.strip() for q in blocked_text.split('\\n') if q.strip()
            ]
            
            # Save through app controller
            success, error_msg = self.app_controller.update_settings(
                self.qb_config, self.torrent_config, self.quality_settings, self.check_interval
            )
            
            if success:
                messagebox.showinfo("Success", "Settings saved successfully!")
                # Test connection after saving
                self.test_connection()
                return True
            else:
                messagebox.showerror("Error", f"Failed to save settings: {error_msg}")
                return False
                
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            return False
            
    def _validate_inputs(self):
        """Validate form inputs."""
        try:
            # Validate port
            port = int(self.qb_port.get().strip())
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
                
            # Validate interval
            interval = int(self.interval_entry.get().strip())
            if interval < 1:
                raise ValueError("Check interval must be at least 1 hour")
                
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False
            
    def test_connection(self):
        """Test the torrent client connection with current settings."""
        try:
            # Update status
            self.connection_status.config(text="🔄 Testing...", foreground="orange")
            self.frame.update()
            
            # Test connection through app controller
            available, error_msg = self.app_controller.test_connection()
            
            if available:
                self.connection_status.config(text="✅ Connected", foreground="green")
                messagebox.showinfo("Connection Test", "Connection successful!")
            else:
                self.connection_status.config(text="❌ Failed", foreground="red")
                messagebox.showerror("Connection Test", f"Connection failed:\\n{error_msg}")
                
        except Exception as e:
            self.connection_status.config(text="❌ Error", foreground="red")
            messagebox.showerror("Test Error", f"Connection test failed: {e}")
            
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset Settings", 
                             "Reset all settings to defaults? This cannot be undone."):
            try:
                # Create new default configs
                from settings import QBittorrentConfig, TorrentClientConfig, QualitySettings, DEFAULT_INTERVAL
                
                self.qb_config = QBittorrentConfig()
                self.torrent_config = TorrentClientConfig()
                self.quality_settings = QualitySettings()
                self.check_interval = DEFAULT_INTERVAL
                
                # Update the app controller
                success, error_msg = self.app_controller.update_settings(
                    self.qb_config, self.torrent_config, self.quality_settings, self.check_interval
                )
                
                if success:
                    # Refresh the form
                    self._refresh_from_controller()
                    messagebox.showinfo("Reset Complete", "Settings reset to defaults.")
                else:
                    messagebox.showerror("Reset Error", f"Failed to reset settings: {error_msg}")
                    
            except Exception as e:
                messagebox.showerror("Reset Error", f"Failed to reset settings: {e}")
                
    def show(self):
        """Show the settings panel."""
        if not self.visible:
            # Refresh settings from controller before showing
            self._refresh_from_controller()
            
            # Add to parent paned window
            self.parent_paned.add(self.frame, weight=1)
            self.visible = True
            
            # Focus on first field
            if self.qb_host:
                self.qb_host.focus()
                
    def hide(self):
        """Hide the settings panel."""
        if self.visible:
            self.parent_paned.remove(self.frame)
            self.visible = False
            
    def toggle(self):
        """Toggle the visibility of the settings panel."""
        if self.visible:
            self.hide()
        else:
            self.show()
            
    def is_visible(self) -> bool:
        """Check if the settings panel is currently visible."""
        return self.visible
