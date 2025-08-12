import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import re
import glob
from collections import defaultdict

class BZRSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BZR File Price Synchronizer")
        self.root.geometry("800x600")
        
        # Variables
        self.folder_path = tk.StringVar()
        self.trader_name = tk.StringVar()
        self.bzr_files = []
        self.synchronized_items = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Folder selection
        ttk.Label(main_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        folder_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(folder_frame, textvariable=self.folder_path, state="readonly").grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Synchronize", command=self.synchronize_prices).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT)
        
        # New trader section
        trader_frame = ttk.Frame(main_frame)
        trader_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        trader_frame.columnconfigure(1, weight=1)
        
        ttk.Label(trader_frame, text="Trader name:").grid(row=0, column=0, padx=(0, 5))
        ttk.Entry(trader_frame, textvariable=self.trader_name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(trader_frame, text="Copy to new trader", command=self.copy_to_new_trader).grid(row=0, column=2)
        
        # File list
        ttk.Label(main_frame, text="Found BZR Files:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))
        list_frame.columnconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(list_frame, height=6)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        # Debug panel
        ttk.Label(main_frame, text="Debug Log:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(10, 5))
        
        self.debug_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15)
        self.debug_text.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log_message(f"Selected folder: {folder}")
    
    def log_message(self, message):
        self.debug_text.insert(tk.END, message + "\n")
        self.debug_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.debug_text.delete(1.0, tk.END)
    
    def scan_files(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder first.")
            return
        
        # Clear previous results
        self.file_listbox.delete(0, tk.END)
        self.bzr_files = []
        
        # Search for BZR files
        pattern = os.path.join(self.folder_path.get(), "BZR_*_pq.proj.ini")
        found_files = glob.glob(pattern)
        
        if not found_files:
            self.log_message("No BZR files found matching pattern: BZR_*_pq.proj.ini")
            return
        
        self.bzr_files = found_files
        self.log_message(f"Found {len(found_files)} BZR files:")
        
        for file_path in found_files:
            filename = os.path.basename(file_path)
            self.file_listbox.insert(tk.END, filename)
            self.log_message(f"  - {filename}")
    
    def parse_bzr_file(self, file_path):
        """Parse a BZR file and extract items from [ItemToSell] section"""
        items = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find [ItemToSell] section
            item_section_match = re.search(r'\[ItemToSell\](.*?)(?=\[|$)', content, re.DOTALL)
            if not item_section_match:
                return items
            
            item_section = item_section_match.group(1)
            
            # Parse item=price lines
            for line in item_section.strip().split('\n'):
                line = line.strip()
                if '=' in line and not line.startswith('['):
                    item_name, price_str = line.split('=', 1)
                    try:
                        price = int(price_str)
                        items[item_name.strip()] = price
                    except ValueError:
                        continue
            
            return items
        except Exception as e:
            self.log_message(f"Error parsing {os.path.basename(file_path)}: {str(e)}")
            return {}
    
    def write_bzr_file(self, file_path, items):
        """Update a BZR file with new item prices"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find [ItemToSell] section
            item_section_match = re.search(r'(\[ItemToSell\])(.*?)(?=(\[|$))', content, re.DOTALL)
            if not item_section_match:
                # If no [ItemToSell] section exists, create one at the end
                if not content.endswith('\n'):
                    content += '\n'
                content += '[ItemToSell]\n'
                for item, price in items.items():
                    content += f'{item}={price}\n'
            else:
                # Replace the existing section
                before_section = content[:item_section_match.start()]
                after_section = content[item_section_match.end():]
                
                new_section = '[ItemToSell]\n'
                for item, price in sorted(items.items()):
                    new_section += f'{item}={price}\n'
                
                # If there's content after, add a newline
                if after_section and not new_section.endswith('\n'):
                    new_section += '\n'
                
                content = before_section + new_section + after_section
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            self.log_message(f"Error writing {os.path.basename(file_path)}: {str(e)}")
            return False
    
    def synchronize_prices(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder first.")
            return
        
        # First scan for files
        self.scan_files()
        
        if not self.bzr_files:
            messagebox.showerror("Error", "No BZR files found in the selected folder.")
            return
        
        self.log_message("\n" + "="*50)
        self.log_message("Starting price synchronization...")
        self.log_message("="*50)
        
        # Parse all files and collect items
        all_items = defaultdict(list)  # item_name -> [(price, filename), ...]
        file_items = {}  # filename -> {item: price}
        
        for file_path in self.bzr_files:
            filename = os.path.basename(file_path)
            items = self.parse_bzr_file(file_path)
            file_items[file_path] = items
            
            self.log_message(f"\nParsed {filename}:")
            if items:
                for item, price in items.items():
                    all_items[item].append((price, filename))
                    self.log_message(f"  {item} = {price}")
            else:
                self.log_message("  No items found")
        
        if not all_items:
            self.log_message("\nNo items found in any files.")
            return
        
        # Calculate lowest non-zero prices
        self.log_message(f"\nCalculating lowest non-zero prices for {len(all_items)} unique items...")
        
        lowest_prices = {}
        for item, price_list in all_items.items():
            non_zero_prices = [(price, filename) for price, filename in price_list if price > 0]
            if non_zero_prices:
                lowest_price, source_file = min(non_zero_prices, key=lambda x: x[0])
                lowest_prices[item] = lowest_price
                
                # Log price comparison if item exists in multiple files
                if len(price_list) > 1:
                    price_info = ", ".join([f"{filename}={price}" for price, filename in price_list])
                    self.log_message(f"  {item}: {price_info} -> Using {lowest_price} from {source_file}")
        
        # Store synchronized items for potential new trader creation
        self.synchronized_items = lowest_prices
        
        # Update all files
        self.log_message(f"\nUpdating {len(self.bzr_files)} files...")
        
        updates_made = 0
        for file_path in self.bzr_files:
            filename = os.path.basename(file_path)
            current_items = file_items[file_path].copy()
            original_count = len(current_items)
            changes_made = False
            
            # Update existing items and add new ones
            for item, target_price in lowest_prices.items():
                if item in current_items:
                    if current_items[item] != target_price:
                        old_price = current_items[item]
                        current_items[item] = target_price
                        self.log_message(f"  {filename}: Updated {item} from {old_price} to {target_price}")
                        changes_made = True
                else:
                    current_items[item] = target_price
                    self.log_message(f"  {filename}: Added {item} = {target_price}")
                    changes_made = True
            
            if changes_made:
                if self.write_bzr_file(file_path, current_items):
                    updates_made += 1
                    new_count = len(current_items)
                    self.log_message(f"  {filename}: Successfully updated ({original_count} -> {new_count} items)")
                else:
                    self.log_message(f"  {filename}: Failed to write file")
            else:
                self.log_message(f"  {filename}: No changes needed")
        
        self.log_message(f"\nSynchronization complete!")
        self.log_message(f"Files processed: {len(self.bzr_files)}")
        self.log_message(f"Files updated: {updates_made}")
        self.log_message(f"Unique items synchronized: {len(lowest_prices)}")
        
        # Show concise summary message
        summary_msg = f"Found {len(lowest_prices)} items with prices in {len(self.bzr_files)} BZR files. All files updated with lowest prices and are now in sync."
        messagebox.showinfo("Synchronization Complete", summary_msg)
    
    def copy_to_new_trader(self):
        """Create a new BZR file for a new trader with all synchronized items"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder first.")
            return
        
        trader_name = self.trader_name.get().strip()
        if not trader_name:
            messagebox.showerror("Error", "Please enter a trader name.")
            return
        
        if not self.synchronized_items:
            messagebox.showerror("Error", "No synchronized items available. Please run synchronization first.")
            return
        
        # Create filename
        filename = f"BZR_{trader_name}_pq.proj.ini"
        file_path = os.path.join(self.folder_path.get(), filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            if not messagebox.askyesno("File Exists", f"{filename} already exists. Overwrite it?"):
                return
        
        self.log_message(f"\nCreating new trader file: {filename}")
        self.log_message(f"Adding {len(self.synchronized_items)} items with synchronized prices...")
        
        # Create the new file content
        content = "[ItemToSell]\n"
        for item, price in sorted(self.synchronized_items.items()):
            content += f"{item}={price}\n"
            self.log_message(f"  {item} = {price}")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log_message(f"\nSuccessfully created {filename}")
            messagebox.showinfo("Success", f"Created new trader file: {filename}\nAdded {len(self.synchronized_items)} items with synchronized prices.")
            
            # Clear the trader name field
            self.trader_name.set("")
            
            # Refresh the file list if we're in the same folder
            if self.folder_path.get():
                self.scan_files()
                
        except Exception as e:
            self.log_message(f"Error creating {filename}: {str(e)}")
            messagebox.showerror("Error", f"Failed to create {filename}:\n{str(e)}")

def main():
    root = tk.Tk()
    app = BZRSyncApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()