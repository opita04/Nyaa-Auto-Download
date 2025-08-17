import tkinter as tk
from tkinter import ttk, messagebox
from settings import DEFAULT_INTERVAL


class SettingsPanel:
    def __init__(self, parent, qb_config, check_interval, on_save_callback):
        self.parent = parent
        self.qb_config = qb_config
        self.check_interval = check_interval
        self.on_save_callback = on_save_callback
        self.visible = False
        self.frame = None
        self._create_panel()
        
    def _create_panel(self):
        """Create the settings panel frame"""
        self.frame = ttk.LabelFrame(self.parent, text='qBittorrent Settings')
        
        # Host and Port row
        ttk.Label(self.frame, text='Host:').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.qb_host = ttk.Entry(self.frame, width=15)
        self.qb_host.insert(0, self.qb_config.host)
        self.qb_host.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.frame, text='Port:').grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.qb_port = ttk.Entry(self.frame, width=6)
        self.qb_port.insert(0, str(self.qb_config.port))
        self.qb_port.grid(row=0, column=3, padx=5, pady=2)
        
        # Username and Password row
        ttk.Label(self.frame, text='Username:').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.qb_user = ttk.Entry(self.frame, width=15)
        self.qb_user.insert(0, self.qb_config.username)
        self.qb_user.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(self.frame, text='Password:').grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.qb_pass = ttk.Entry(self.frame, width=15, show='*')
        self.qb_pass.insert(0, self.qb_config.password)
        self.qb_pass.grid(row=1, column=3, padx=5, pady=2)
        
        # Category and Interval row
        ttk.Label(self.frame, text='Category:').grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.qb_cat = ttk.Entry(self.frame, width=15)
        self.qb_cat.insert(0, self.qb_config.category)
        self.qb_cat.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(self.frame, text='Check Interval (hours):').grid(row=2, column=2, sticky='w', padx=5, pady=2)
        self.interval_entry = ttk.Entry(self.frame, width=6)
        self.interval_entry.insert(0, str(self.check_interval // 3600))
        self.interval_entry.grid(row=2, column=3, padx=5, pady=2)
        
        # Save button
        save_btn = ttk.Button(self.frame, text='Save Config', command=self.save_config)
        save_btn.grid(row=3, column=0, columnspan=4, sticky='ew', padx=5, pady=5)
        
        # Initially hidden
        self.hide()
        
    def show(self):
        """Show the settings panel"""
        if not self.visible:
            self.frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
            self.visible = True
            
    def hide(self):
        """Hide the settings panel"""
        if self.visible:
            self.frame.grid_remove()
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
                
            # Call the callback function with the new config
            self.on_save_callback(self.qb_config, self.check_interval)
            
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
