# ui_components.py
import tkinter as tk
from tkinter import ttk

# Make sure this import is correct
# from .archive_viewer import ArchiveViewer

def set_dark_theme(self):
    self.style = ttk.Style(self)
    self.style.theme_use('clam')

    self.bg_color = '#2E2E2E'
    self.fg_color = '#FFFFFF'
    self.button_bg = '#4A4A4A'
    self.button_fg = '#FFFFFF'
    self.treeview_bg = '#3E3E3E'
    self.treeview_fg = '#FFFFFF'
    self.treeview_selected_bg = '#5A5A5A'

    self.style.configure('TButton', background=self.button_bg, foreground=self.button_fg)
    self.style.map('TButton', background=[('active', '#5A5A5A')])
    
    self.style.configure('Treeview', 
                         background=self.treeview_bg, 
                         foreground=self.treeview_fg, 
                         fieldbackground=self.treeview_bg)
    self.style.map('Treeview', background=[('selected', self.treeview_selected_bg)])
    
    self.style.configure('TProgressbar', background='#4CAF50')
    
    self.configure(bg=self.bg_color)

def create_widgets(self):
    # Create a frame for the top buttons
    top_button_frame = ttk.Frame(self)
    top_button_frame.pack(pady=10)

    # Add 'New Archive' and 'Select Archive' buttons at the top
    self.new_archive_button = ttk.Button(top_button_frame, text="New Archive", command=self.create_new_archive)
    self.new_archive_button.pack(side=tk.LEFT, padx=5)

    self.select_button = ttk.Button(top_button_frame, text="Select Archive", command=self.select_file)
    self.select_button.pack(side=tk.LEFT, padx=5)

    self.tree = ttk.Treeview(self, columns=("Extract", "Filename", "Size"), show="headings")
    self.tree.heading("Extract", text="Extract")
    self.tree.heading("Filename", text="Filename")
    self.tree.heading("Size", text="Size")
    self.tree.column("Extract", width=50, anchor="center")
    self.tree.pack(expand=True, fill="both", padx=10, pady=10)

    self.tree.bind("<ButtonRelease-1>", self.on_click)

    # Create a frame for the search bar
    search_frame = ttk.Frame(self)
    search_frame.pack(pady=5)

    self.search_entry = ttk.Entry(search_frame)
    self.search_entry.pack(side=tk.LEFT)

    self.search_button = ttk.Button(search_frame, text="Search", command=self.search_files)
    self.search_button.pack(side=tk.LEFT)

    self.tree.bind("<Button-3>", self.show_right_click_menu)

    # Add sorting functionality
    self.tree.heading("Extract", text="Extract", command=lambda: self.sort_by_column("#1", False))
    self.tree.heading("Filename", text="Filename", command=lambda: self.sort_by_column("#2", False))
    self.tree.heading("Size", text="Size", command=lambda: self.sort_by_column("#3", False))

    # Create a frame to hold the action buttons
    button_frame = ttk.Frame(self)
    button_frame.pack(pady=10)

    # Place all action buttons side by side
    self.add_button = ttk.Button(button_frame, text="Add Files", command=self.add_files)
    self.add_button.pack(side=tk.LEFT, padx=5)

    self.extract_button = ttk.Button(button_frame, text="Extract Files", command=self.extract_files)
    self.extract_button.pack(side=tk.LEFT, padx=5)
    
    self.delete_button = ttk.Button(button_frame, text="Delete Files", command=self.delete_files)
    self.delete_button.pack(side=tk.LEFT, padx=5)

    self.rename_button = ttk.Button(button_frame, text="Rename File", command=self.rename_file)
    self.rename_button.pack(side=tk.LEFT, padx=5)

    self.encrypt_button = ttk.Button(button_frame, text="Encrypt", command=self.encrypt_files)
    self.encrypt_button.pack(side=tk.LEFT, padx=5)

    self.status_var = tk.StringVar()
    self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, 
                                background=self.bg_color, foreground=self.fg_color)
    self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    self.progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='determinate')
    self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    # Right-click menu
    self.right_click_menu = tk.Menu(self, tearoff=0)
    self.right_click_menu.add_command(label="Delete", command=self.delete_files)
    self.right_click_menu.add_command(label="Rename", command=self.rename_file)
    self.right_click_menu.add_command(label="Encrypt", command=self.encrypt_files)

    def show_right_click_menu(self, event):
        self.right_click_menu.post(event.x_root, event.y_root)