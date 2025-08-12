import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import time
import threading
from datetime import datetime
from pathlib import Path
import re
import configparser
import webbrowser

class TraderMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Trader Sales Monitor")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        
        # Configuration file path
        self.config_file = "trader_monitor_config.ini"
        
        # Data storage
        self.character_name = ""
        self.root_directory = ""
        self.bzr_file = ""
        self.inventory_file = ""
        self.item_prices = {}
        self.last_inventory = {}
        self.monitoring = False
        self.monitor_thread = None
        
        # Load configuration before setting up UI
        self.load_config()
        
        self.setup_ui()
        
        # Apply loaded configuration to UI
        self.apply_config_to_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        main_frame.rowconfigure(6, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # Character name input
        ttk.Label(main_frame, text="Character Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.char_entry = ttk.Entry(main_frame, width=20)
        self.char_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        self.char_entry.bind('<KeyRelease>', self.on_character_change)
        
        # Root directory selection
        ttk.Label(main_frame, text="Root Directory:").grid(row=1, column=0, sticky=tk.W, pady=2)
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_label = ttk.Label(dir_frame, text="Select directory containing your files", foreground="gray")
        self.dir_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(row=0, column=1, padx=(5, 0))
        
        # File status display
        ttk.Label(main_frame, text="Files:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.file_status_label = ttk.Label(main_frame, text="No files detected", foreground="gray")
        self.file_status_label.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Verify Files", command=self.verify_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Load Character Data", command=self.load_character_data).pack(side=tk.LEFT)
        
        # Items for sale list
        ttk.Label(main_frame, text="Items for Sale:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(0, 5))
        
        # Treeview for items
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=4, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.items_tree = ttk.Treeview(tree_frame, columns=('price', 'pqdi'), show='tree headings', height=6)
        self.items_tree.heading('#0', text='Item Name')
        self.items_tree.heading('price', text='Price')
        self.items_tree.heading('pqdi', text='PQDI')
        self.items_tree.column('#0', width=350)
        self.items_tree.column('price', width=100)
        self.items_tree.column('pqdi', width=50)
        
        # Configure alternating row colors
        self.items_tree.tag_configure('oddrow', background='#f0f0f0')
        self.items_tree.tag_configure('evenrow', background='white')
        
        # Bind click event for PQDI links
        self.items_tree.bind('<Button-1>', self.on_tree_click)
        # Change cursor to hand when hovering over PQDI column
        self.items_tree.bind('<Motion>', self.on_tree_motion)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.items_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Monitor buttons
        monitor_frame = ttk.Frame(main_frame)
        monitor_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.monitor_button = ttk.Button(monitor_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.monitor_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(monitor_frame, text="Manual Check", command=self.manual_check).pack(side=tk.LEFT)
        
        # Sales log
        ttk.Label(main_frame, text="Sales Log:").grid(row=6, column=0, sticky=(tk.W, tk.N), pady=(0, 5))
        
        self.sales_log = scrolledtext.ScrolledText(main_frame, height=6, state=tk.DISABLED)
        self.sales_log.grid(row=6, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Debug panel with toggle
        debug_frame = ttk.Frame(main_frame)
        debug_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        debug_frame.columnconfigure(1, weight=1)
        debug_frame.rowconfigure(1, weight=1)
        
        # Debug toggle button and label
        debug_header = ttk.Frame(debug_frame)
        debug_header.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(debug_header, text="Debug Log:").pack(side=tk.LEFT)
        self.debug_button = ttk.Button(debug_header, text="(d)", width=4, command=self.toggle_debug)
        self.debug_button.pack(side=tk.LEFT, padx=(5, 0))
        
        self.debug_log = scrolledtext.ScrolledText(debug_frame, height=6, state=tk.DISABLED)
        self.debug_log.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initially hide debug log
        self.debug_visible = False
        self.debug_log.grid_remove()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Enter character name and select directory to begin")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def debug_log_message(self, message):
        """Add a message to the debug log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.debug_log.config(state=tk.NORMAL)
            self.debug_log.insert(tk.END, log_message)
            self.debug_log.see(tk.END)
            self.debug_log.config(state=tk.DISABLED)
        
        # Schedule UI update on main thread
        self.root.after(0, update_log)
    
    def toggle_debug(self):
        """Toggle debug log visibility"""
        if self.debug_visible:
            self.debug_log.grid_remove()
            self.debug_visible = False
            self.debug_button.config(text="(d)")
        else:
            self.debug_log.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.debug_visible = True
            self.debug_button.config(text="(-)")
    
    def on_tree_click(self, event):
        """Handle clicks on the treeview"""
        region = self.items_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.items_tree.identify_column(event.x)
            if column == '#2':  # PQDI column (second value column)
                item = self.items_tree.identify_row(event.y)
                if item:
                    # Extract item ID from the item text
                    item_text = self.items_tree.item(item, 'text')
                    # Extract ID from format "Item Name (ID: 12345)"
                    match = re.search(r'ID: (\d+)', item_text)
                    if match:
                        item_id = match.group(1)
                        url = f"https://www.pqdi.cc/item/{item_id}"
                        webbrowser.open(url)
                        self.debug_log_message(f"Opened PQDI link for item ID {item_id}")
    
    def on_tree_motion(self, event):
        """Handle mouse motion over treeview to show hand cursor on PQDI column"""
        region = self.items_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.items_tree.identify_column(event.x)
            if column == '#2':  # PQDI column
                self.items_tree.config(cursor="hand2")
            else:
                self.items_tree.config(cursor="")
        else:
            self.items_tree.config(cursor="")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                config = configparser.ConfigParser()
                config.read(self.config_file)
                
                if 'Settings' in config:
                    self.character_name = config['Settings'].get('character_name', '')
                    self.root_directory = config['Settings'].get('root_directory', '')
            # If no config file exists, just use empty defaults (no error)
        except Exception as e:
            # If there's an error, just use empty defaults and continue
            self.character_name = ""
            self.root_directory = ""
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = configparser.ConfigParser()
            config['Settings'] = {
                'character_name': self.character_name,
                'root_directory': self.root_directory
            }
            
            with open(self.config_file, 'w') as f:
                config.write(f)
                
            if hasattr(self, 'debug_log'):  # Only log if debug_log exists
                self.debug_log_message("Configuration saved")
        except Exception as e:
            if hasattr(self, 'debug_log'):  # Only log if debug_log exists
                self.debug_log_message(f"Error saving config: {str(e)}")
    
    def apply_config_to_ui(self):
        """Apply loaded configuration to UI elements"""
        if self.character_name:
            self.char_entry.insert(0, self.character_name)
            
        if self.root_directory:
            self.dir_label.config(text=self.root_directory, foreground="black")
            
        # Update file paths and status if both are available
        if self.character_name and self.root_directory:
            self.update_file_paths()
            self.status_var.set(f"Loaded previous session: {self.character_name}")
            # Now it's safe to log
            self.debug_log_message(f"Restored session - Character: {self.character_name}")
        else:
            self.status_var.set("Enter character name and select directory to begin")
        
    def on_character_change(self, event=None):
        """Update file paths when character name changes"""
        char_name = self.char_entry.get().strip()
        if char_name:
            self.character_name = char_name
            self.save_config()  # Save immediately when character name changes
            self.update_file_paths()
        else:
            self.file_status_label.config(text="No files detected", foreground="gray")
            self.status_var.set("Enter character name and select directory to begin")
    
    def browse_directory(self):
        """Browse for root directory"""
        directory = filedialog.askdirectory(title="Select Directory Containing Your Files")
        if directory:
            self.root_directory = directory
            self.save_config()  # Save immediately when directory changes
            self.dir_label.config(text=directory, foreground="black")
            self.update_file_paths()
            
    def update_file_paths(self):
        """Update file paths based on character name and root directory"""
        if self.character_name and self.root_directory:
            self.bzr_file = os.path.join(self.root_directory, f"BZR_{self.character_name}_pq.proj.ini")
            self.inventory_file = os.path.join(self.root_directory, f"{self.character_name}-Inventory.txt")
            
            # Update file status
            bzr_exists = os.path.exists(self.bzr_file)
            inv_exists = os.path.exists(self.inventory_file)
            
            status_parts = []
            if bzr_exists:
                status_parts.append(f"BZR: ✓")
            else:
                status_parts.append(f"BZR: ✗")
                
            if inv_exists:
                status_parts.append(f"Inventory: ✓")
            else:
                status_parts.append(f"Inventory: ✗")
            
            status_text = " | ".join(status_parts)
            color = "darkgreen" if bzr_exists and inv_exists else "red"
            self.file_status_label.config(text=status_text, foreground=color)
            
            self.debug_log_message(f"Updated paths - BZR: {bzr_exists}, Inventory: {inv_exists}")
    
    def verify_files(self):
        """Verify that files exist and show detailed information"""
        if not self.character_name:
            messagebox.showerror("Error", "Please enter a character name first")
            return
            
        if not self.root_directory:
            messagebox.showerror("Error", "Please select a root directory first")
            return
        
        self.update_file_paths()
        
        bzr_exists = os.path.exists(self.bzr_file)
        inv_exists = os.path.exists(self.inventory_file)
        
        message = f"Character: {self.character_name}\n"
        message += f"Directory: {self.root_directory}\n\n"
        message += f"BZR File: {os.path.basename(self.bzr_file)}\n"
        message += f"  Status: {'✓ Found' if bzr_exists else '✗ Not Found'}\n"
        message += f"  Path: {self.bzr_file}\n\n"
        message += f"Inventory File: {os.path.basename(self.inventory_file)}\n"
        message += f"  Status: {'✓ Found' if inv_exists else '✗ Not Found'}\n"
        message += f"  Path: {self.inventory_file}"
        
        if bzr_exists and inv_exists:
            messagebox.showinfo("File Verification", message)
        else:
            messagebox.showerror("File Verification", message)
    
    def load_character_data(self):
        """Load character data from files"""
        if not self.character_name:
            messagebox.showerror("Error", "Please enter a character name first")
            return
            
        if not self.root_directory:
            messagebox.showerror("Error", "Please select a root directory first")
            return
        
        self.update_file_paths()
        
        # Check if files exist
        if not os.path.exists(self.bzr_file):
            messagebox.showerror("Error", f"BZR file not found: {os.path.basename(self.bzr_file)}")
            return
        
        if not os.path.exists(self.inventory_file):
            messagebox.showerror("Error", f"Inventory file not found: {os.path.basename(self.inventory_file)}")
            return
        
        try:
            # Load BZR file (item prices)
            self.item_prices = self.load_bzr_file()
            self.debug_log_message(f"Loaded {len(self.item_prices)} items from BZR file")
            
            # Load current inventory
            self.last_inventory = self.load_inventory_file()
            self.debug_log_message(f"Loaded {len(self.last_inventory)} items from inventory")
            
            # Update UI
            self.update_items_display()
            
            self.status_var.set(f"Loaded {len(self.item_prices)} prices from BZR file, found {len(self.last_inventory)} items in trader satchels")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load files: {str(e)}")
            self.debug_log_message(f"Error loading files: {str(e)}")
    
    def load_bzr_file(self):
        """Load item prices from BZR file"""
        prices = {}
        
        self.debug_log_message(f"Reading BZR file: {os.path.basename(self.bzr_file)}")
        
        with open(self.bzr_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        self.debug_log_message(f"BZR file content length: {len(content)} characters")
        
        # Find [Itemtosell] section
        itemtosell_match = re.search(r'\[Itemtosell\](.*?)(?:\[|$)', content, re.DOTALL | re.IGNORECASE)
        if itemtosell_match:
            section_content = itemtosell_match.group(1)
            self.debug_log_message("Found [Itemtosell] section")
            
            # Parse item=price lines
            lines = section_content.strip().split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line and '=' in line and not line.startswith('['):
                    try:
                        item, price = line.split('=', 1)
                        item = item.strip()
                        copper_price = int(price.strip())
                        # Convert copper to platinum (1000 copper = 1 platinum)
                        platinum_price = copper_price / 1000.0
                        prices[item] = platinum_price
                        if len(prices) <= 5:  # Debug first few items
                            self.debug_log_message(f"  Item: {item} = {copper_price} copper ({platinum_price:.3f} platinum)")
                    except ValueError as e:
                        self.debug_log_message(f"  Skipped malformed line {i}: {line[:50]}...")
        else:
            self.debug_log_message("No [Itemtosell] section found")
        
        return prices
    
    def load_inventory_file(self):
        """Load current inventory items from trader's satchels"""
        items = {}  # Changed to dict to store slot -> (item_name, item_id)
        
        self.debug_log_message(f"Reading inventory file: {os.path.basename(self.inventory_file)}")
        
        if os.path.exists(self.inventory_file):
            with open(self.inventory_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if line and '\t' in line:
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            slot = parts[0]
                            item_name = parts[1]
                            item_id = parts[2]
                            
                            # Track items in any General*-Slot* format (all trader satchel items)
                            if re.match(r'General\d+-Slot\d+', slot) and item_name != 'Empty':
                                items[slot] = (item_name, item_id)
                                if len(items) <= 10:  # Debug first 10 items
                                    self.debug_log_message(f"  {slot}: {item_name} (ID: {item_id})")
        
        self.debug_log_message(f"Found {len(items)} items in all trader satchels")
        return items
    
    def update_items_display(self):
        """Update the items for sale display"""
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        # Get current inventory items
        current_inventory = self.load_inventory_file()
        
        items_displayed = 0
        items_without_price = 0
        
        # Display items currently in trader satchel
        for i, (slot, (item_name, item_id)) in enumerate(current_inventory.items()):
            # Check if item has a price in BZR file
            if item_name in self.item_prices and self.item_prices[item_name] > 0:
                price = self.item_prices[item_name]
                price_str = f"{price:.1f} pp"  # Show platinum with 1 decimal place
                
                # Determine row tag for alternating colors
                row_tag = 'oddrow' if i % 2 == 1 else 'evenrow'
                
                # Insert item with alternating row colors
                self.items_tree.insert('', 'end', text=f"{item_name} (ID: {item_id})", 
                                     values=(price_str, 'pqdi'), tags=(row_tag,))
                items_displayed += 1
            else:
                items_without_price += 1
                if item_name in self.item_prices:
                    self.debug_log_message(f"Item has 0 price, ignoring: {item_name}")
                else:
                    self.debug_log_message(f"Item not in price list, ignoring: {item_name}")
        
        self.debug_log_message(f"Displayed {items_displayed} items for sale")
        if items_without_price > 0:
            self.debug_log_message(f"Ignored {items_without_price} items without valid prices")
    
    def toggle_monitoring(self):
        """Start or stop monitoring"""
        if not self.monitoring:
            if not self.item_prices:
                messagebox.showerror("Error", "Please load character data first")
                return
            
            self.monitoring = True
            self.monitor_button.config(text="Stop Monitoring")
            self.status_var.set("Monitoring inventory for changes...")
            self.debug_log_message("Started monitoring")
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self.monitor_inventory, daemon=True)
            self.monitor_thread.start()
            
        else:
            self.monitoring = False
            self.monitor_button.config(text="Start Monitoring")
            self.status_var.set("Monitoring stopped")
            self.debug_log_message("Stopped monitoring")
    
    def manual_check(self):
        """Manually check for changes"""
        if not self.item_prices:
            messagebox.showerror("Error", "Please load character data first")
            return
            
        self.debug_log_message("Manual check triggered")
        self.check_for_sales()
        self.update_items_display()
    
    def monitor_inventory(self):
        """Monitor inventory file for changes"""
        last_modified = os.path.getmtime(self.inventory_file) if os.path.exists(self.inventory_file) else 0
        self.debug_log_message(f"Monitoring started, file modified time: {last_modified}")
        
        while self.monitoring:
            try:
                if os.path.exists(self.inventory_file):
                    current_modified = os.path.getmtime(self.inventory_file)
                    
                    if current_modified > last_modified:
                        self.debug_log_message(f"File modified! Old: {last_modified}, New: {current_modified}")
                        # File was modified, check for sold items
                        self.check_for_sales()
                        self.root.after(0, self.update_items_display)
                        last_modified = current_modified
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                self.debug_log_message(f"Error monitoring file: {str(e)}")
                break
    
    def check_for_sales(self):
        """Check for items that were sold"""
        try:
            current_inventory = self.load_inventory_file()
            
            self.debug_log_message(f"Previous inventory: {len(self.last_inventory)} items")
            self.debug_log_message(f"Current inventory: {len(current_inventory)} items")
            
            # Find slots that had items but are now empty (sold items)
            sold_items = []
            
            for slot, (item_name, item_id) in self.last_inventory.items():
                if slot not in current_inventory:
                    # Item was removed from this slot (sold)
                    sold_items.append((item_name, item_id))
                    self.debug_log_message(f"Item sold from {slot}: {item_name} (ID: {item_id})")
            
            self.debug_log_message(f"Items sold: {len(sold_items)}")
            
            if sold_items:
                for item_name, item_id in sold_items:
                    if item_name in self.item_prices and self.item_prices[item_name] > 0:
                        price = self.item_prices[item_name]
                        self.log_sale(f"SOLD: {item_name} (ID: {item_id}) for {price:.1f} platinum")
                        self.debug_log_message(f"Sale logged: {item_name} for {price:.1f} platinum")
                    else:
                        if item_name in self.item_prices:
                            self.debug_log_message(f"Sold item has 0 price, ignoring: {item_name}")
                        else:
                            self.debug_log_message(f"Sold item not in price list, ignoring: {item_name}")
                
                # Update last inventory
                self.last_inventory = current_inventory.copy()
            else:
                self.debug_log_message("No sales detected")
                
        except Exception as e:
            error_msg = f"Error checking for sales: {str(e)}"
            self.log_sale(error_msg)
            self.debug_log_message(error_msg)
    
    def log_sale(self, message):
        """Add a message to the sales log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.sales_log.config(state=tk.NORMAL)
            self.sales_log.insert(tk.END, log_message)
            self.sales_log.see(tk.END)
            self.sales_log.config(state=tk.DISABLED)
        
        # Schedule UI update on main thread
        self.root.after(0, update_log)

def main():
    try:
        # Test basic imports first
        print("Starting Trader Monitor...")
        print("Testing imports...")
        
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox, scrolledtext
        print("Tkinter imports successful")
        
        import configparser
        print("ConfigParser import successful")
        
        print("Creating main window...")
        root = tk.Tk()
        print("Main window created")
        
        print("Initializing TraderMonitor...")
        app = TraderMonitor(root)
        print("TraderMonitor initialized")
        
        # Set window icon (optional)
        try:
            root.iconbitmap(default='icon.ico')  # Add your icon file if you have one
        except:
            pass
        
        # Save config on window close
        def on_closing():
            try:
                app.save_config()
            except Exception as e:
                print(f"Error saving config: {e}")
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        print("Starting main loop...")
        root.mainloop()
        
    except Exception as e:
        print(f"STARTUP ERROR: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to show error dialog if possible
        try:
            import tkinter.messagebox as mb
            mb.showerror("Startup Error", f"Failed to start application:\n{str(e)}")
        except:
            pass
        
        input("Press Enter to close...")  # Keep console open

if __name__ == "__main__":
    main()