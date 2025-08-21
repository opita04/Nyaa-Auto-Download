import tkinter as tk
from tkinter import ttk, messagebox
from settings import DEFAULT_INTERVAL, TorrentClientConfig, QualitySettings


class SettingsPanel:
    def __init__(self, parent, qb_config, check_interval, on_save_callback, torrent_config=None, quality_settings=None):
        self.parent = parent
        self.qb_config = qb_config
        self.torrent_config = torrent_config or TorrentClientConfig()
        self.quality_settings = quality_settings or QualitySettings()
        self.check_interval = check_interval
        self.on_save_callback = on_save_callback
        self.visible = False
        self.frame = None
        self._create_panel()
        
    def _create_panel(self):
        """Create the settings panel frame"""
        self.frame = ttk.LabelFrame(self.parent, text='Settings')

        # Settings panel header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill='x', padx=5, pady=5)

        settings_title_label = ttk.Label(header_frame, text='Application Settings', font=('TkDefaultFont', 12, 'bold'))
        settings_title_label.pack(side='left')

        close_btn = ttk.Button(header_frame, text='×', width=3, command=self.hide)
        close_btn.pack(side='right')

        # Create scrollable content area
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # qBittorrent Settings section
        qb_frame = ttk.LabelFrame(content_frame, text='qBittorrent Settings')
        qb_frame.pack(fill='x', pady=5)

        # Host and Port row
        host_port_frame = ttk.Frame(qb_frame)
        host_port_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(host_port_frame, text='Host:').pack(side='left')
        self.qb_host = ttk.Entry(host_port_frame, width=15)
        self.qb_host.insert(0, self.qb_config.host)
        self.qb_host.pack(side='left', padx=5)

        ttk.Label(host_port_frame, text='Port:').pack(side='left', padx=5)
        self.qb_port = ttk.Entry(host_port_frame, width=6)
        self.qb_port.insert(0, str(self.qb_config.port))
        self.qb_port.pack(side='left')
        
        # Username and Password row
        user_pass_frame = ttk.Frame(qb_frame)
        user_pass_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(user_pass_frame, text='Username:').pack(side='left')
        self.qb_user = ttk.Entry(user_pass_frame, width=15)
        self.qb_user.insert(0, self.qb_config.username)
        self.qb_user.pack(side='left', padx=5)

        ttk.Label(user_pass_frame, text='Password:').pack(side='left', padx=5)
        self.qb_pass = ttk.Entry(user_pass_frame, width=15, show='*')
        self.qb_pass.insert(0, self.qb_config.password)
        self.qb_pass.pack(side='left')
        
        # Category and Interval row
        cat_interval_frame = ttk.Frame(qb_frame)
        cat_interval_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(cat_interval_frame, text='Category:').pack(side='left')
        self.qb_cat = ttk.Entry(cat_interval_frame, width=15)
        self.qb_cat.insert(0, self.qb_config.category)
        self.qb_cat.pack(side='left', padx=5)

        ttk.Label(cat_interval_frame, text='Check Interval (hours):').pack(side='left', padx=5)
        self.interval_entry = ttk.Entry(cat_interval_frame, width=6)
        self.interval_entry.insert(0, str(self.check_interval // 3600))
        self.interval_entry.pack(side='left')

        # Torrent Client Selection section
        torrent_frame = ttk.LabelFrame(content_frame, text='Torrent Client Settings')
        torrent_frame.pack(fill='x', pady=5)

        torrent_client_frame = ttk.Frame(torrent_frame)
        torrent_client_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(torrent_client_frame, text='Torrent Client:').pack(side='left')
        self.torrent_client_combo = ttk.Combobox(torrent_client_frame, width=15, state='readonly')
        self.torrent_client_combo['values'] = list(TorrentClientConfig.SUPPORTED_CLIENTS.values())
        current_client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(self.torrent_config.preferred_client, 'qBittorrent')
        self.torrent_client_combo.set(current_client_name)
        self.torrent_client_combo.pack(side='left', padx=5)
        self.torrent_client_combo.bind('<<ComboboxSelected>>', self._on_torrent_client_changed)

        # Custom Command row (initially hidden)
        self.custom_command_frame = ttk.Frame(torrent_frame)

        ttk.Label(self.custom_command_frame, text='Custom Command:').pack(side='left')
        self.custom_command_entry = ttk.Entry(self.custom_command_frame, width=30)
        self.custom_command_entry.insert(0, self.torrent_config.custom_command)
        self.custom_command_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Fallback checkbox row
        self.fallback_var = tk.BooleanVar(value=self.torrent_config.fallback_to_default)
        self.fallback_check = ttk.Checkbutton(torrent_frame, text='Fallback to system default if qBittorrent fails',
                                           variable=self.fallback_var)
        self.fallback_check.pack(anchor='w', padx=5, pady=2)

        # Quality Filter Settings section
        quality_frame = ttk.LabelFrame(content_frame, text='Quality Filter Settings')
        quality_frame.pack(fill='x', pady=5)

        # Quality filter mode
        quality_mode_frame = ttk.Frame(quality_frame)
        quality_mode_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(quality_mode_frame, text='Filter Mode:').pack(side='left')
        self.quality_mode_var = tk.StringVar(value=self.quality_settings.quality_filter_mode)
        self.quality_mode_combo = ttk.Combobox(quality_mode_frame, textvariable=self.quality_mode_var, state='readonly', width=15)
        self.quality_mode_combo['values'] = ['preferred', 'blocked', 'both', 'disabled']
        self.quality_mode_combo.pack(side='left', padx=5)

        # Preferred qualities
        preferred_frame = ttk.Frame(quality_frame)
        preferred_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(preferred_frame, text='Preferred:').pack(anchor='w')
        self.preferred_qualities_text = tk.Text(preferred_frame, height=3, width=30)
        self.preferred_qualities_text.insert('1.0', '\n'.join(self.quality_settings.preferred_qualities))
        self.preferred_qualities_text.pack(fill='x', pady=2)

        # Blocked qualities
        blocked_frame = ttk.Frame(quality_frame)
        blocked_frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(blocked_frame, text='Blocked:').pack(anchor='w')
        self.blocked_qualities_text = tk.Text(blocked_frame, height=3, width=30)
        self.blocked_qualities_text.insert('1.0', '\n'.join(self.quality_settings.blocked_qualities))
        self.blocked_qualities_text.pack(fill='x', pady=2)

        # Help text
        help_text = "Enter one quality per line (e.g., 720p, 1080p, BluRay)\nLeave empty for no filtering"
        ttk.Label(quality_frame, text=help_text, font=('TkDefaultFont', 8), foreground='gray').pack(
            anchor='w', padx=5, pady=2)

                # Save button and connection status
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill='x', pady=10)

        # Save button
        save_btn = ttk.Button(button_frame, text='Save Config', command=self.save_config)
        save_btn.pack(side='left', padx=5)

        # Test connection button
        test_btn = ttk.Button(button_frame, text='Test Connection', command=self.test_connection)
        test_btn.pack(side='left', padx=5)

        # Connection status
        status_frame = ttk.Frame(button_frame)
        status_frame.pack(side='right', fill='x', expand=True)

        ttk.Label(status_frame, text='Connection Status:').pack(side='left')
        self.connection_status = ttk.Label(status_frame, text='Not tested', foreground='gray')
        self.connection_status.pack(side='left', padx=5)

        # Initialize custom command visibility
        self._update_custom_command_visibility()

        # Initially hidden
        self.hide()

    def _on_torrent_client_changed(self, event):
        """Handle torrent client selection change"""
        self._update_custom_command_visibility()

    def _update_custom_command_visibility(self):
        """Show/hide custom command field based on selected client"""
        selected_client_name = self.torrent_client_combo.get()
        # Find the key for the selected client name
        selected_client_key = None
        for key, name in TorrentClientConfig.SUPPORTED_CLIENTS.items():
            if name == selected_client_name:
                selected_client_key = key
                break

        # Show custom command field only for custom client
        if selected_client_key == 'custom':
            self.custom_command_frame.pack(fill='x', padx=5, pady=2)
        else:
            self.custom_command_frame.pack_forget()

    def test_connection(self):
        """Test the selected torrent client connection with current settings"""
        try:
            # Import here to avoid circular imports
            from modules.generic_torrent_client import GenericTorrentClient

            # Create a temporary qBittorrent config
            qb_temp_config = type('TempConfig', (), {
                'host': self.qb_host.get().strip(),
                'port': int(self.qb_port.get().strip()),
                'username': self.qb_user.get().strip(),
                'password': self.qb_pass.get().strip(),
                'category': self.qb_cat.get().strip()
            })()

            # Create a temporary torrent client config
            selected_client_name = self.torrent_client_combo.get()
            selected_client_key = None
            for key, name in TorrentClientConfig.SUPPORTED_CLIENTS.items():
                if name == selected_client_name:
                    selected_client_key = key
                    break

            torrent_temp_config = type('TempConfig', (), {
                'preferred_client': selected_client_key,
                'custom_command': self.custom_command_entry.get().strip(),
                'fallback_to_default': self.fallback_var.get()
            })()

            # Test connection
            torrent_client = GenericTorrentClient(torrent_temp_config)
            available, err = torrent_client.test_connection()

            if available:
                client_name = TorrentClientConfig.SUPPORTED_CLIENTS.get(selected_client_key, "Torrent client")
                self.connection_status.config(text='✅ Connected', foreground='green')
                messagebox.showinfo("Connection Test", f"Successfully configured {client_name}!")
            else:
                self.connection_status.config(text='❌ Failed', foreground='red')
                messagebox.showerror("Connection Test Failed",
                                   f"Cannot configure torrent client:\n\n{err}")

        except ValueError as e:
            self.connection_status.config(text='❌ Invalid Config', foreground='red')
            messagebox.showerror("Configuration Error",
                               f"Invalid configuration values:\n\n{str(e)}")
        except Exception as e:
            self.connection_status.config(text='❌ Test Error', foreground='red')
            messagebox.showerror("Test Error",
                               f"Error testing connection:\n\n{str(e)}")
        
    def show(self):
        """Show the settings panel"""
        if not self.visible:
            self.frame.pack(fill='both', expand=True, padx=5, pady=5)
            self.visible = True

    def hide(self):
        """Hide the settings panel"""
        if self.visible:
            self.frame.pack_forget()
            self.visible = False
            
    def toggle(self):
        """Toggle the visibility of the settings panel"""
        if self.visible:
            self.hide()
        else:
            self.show()
            
    def save_config(self):
        """Save the configuration"""
        try:
            # Save qBittorrent config
            self.qb_config.host = self.qb_host.get().strip()
            self.qb_config.port = int(self.qb_port.get().strip())
            self.qb_config.username = self.qb_user.get().strip()
            self.qb_config.password = self.qb_pass.get().strip()
            self.qb_config.category = self.qb_cat.get().strip()

            try:
                interval = int(self.interval_entry.get().strip())
                self.check_interval = max(1, interval) * 3600  # Convert hours to seconds
            except Exception:
                self.check_interval = DEFAULT_INTERVAL

            # Save torrent client config
            selected_client_name = self.torrent_client_combo.get()
            selected_client_key = None
            for key, name in TorrentClientConfig.SUPPORTED_CLIENTS.items():
                if name == selected_client_name:
                    selected_client_key = key
                    break

            self.torrent_config.preferred_client = selected_client_key
            self.torrent_config.custom_command = self.custom_command_entry.get().strip()
            self.torrent_config.fallback_to_default = self.fallback_var.get()

            # Save quality settings
            self.quality_settings.quality_filter_mode = self.quality_mode_var.get()
            preferred_text = self.preferred_qualities_text.get('1.0', 'end-1c').strip()
            self.quality_settings.preferred_qualities = [q.strip() for q in preferred_text.split('\n') if q.strip()]
            blocked_text = self.blocked_qualities_text.get('1.0', 'end-1c').strip()
            self.quality_settings.blocked_qualities = [q.strip() for q in blocked_text.split('\n') if q.strip()]

            # Call the callback function with the new configs
            self.on_save_callback(self.qb_config, self.check_interval, self.torrent_config, self.quality_settings)

            # Test the connection after saving
            self.test_connection()

        except ValueError as e:
            # Handle invalid port number
            if hasattr(self.parent, 'master'):
                messagebox.showerror("Error", f"Invalid configuration: {e}")
            else:
                print(f"Configuration error: {e}")
                
    def get_config(self):
        """Get the current configuration"""
        return {
            'host': self.qb_host.get().strip(),
            'port': self.qb_port.get().strip(),
            'username': self.qb_user.get().strip(), 
            'password': self.qb_pass.get().strip(),
            'category': self.qb_cat.get().strip(),
            'interval': self.interval_entry.get().strip()
        }
