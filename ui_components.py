# ui_components.py
import tkinter as tk
from tkinter import ttk

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
    self.select_button = ttk.Button(self, text="Select Archive File", command=self.select_file)
    self.select_button.pack(pady=10)

    self.tree = ttk.Treeview(self, columns=("Extract", "Filename", "Size"), show="headings")
    self.tree.heading("Extract", text="Extract")
    self.tree.heading("Filename", text="Filename")
    self.tree.heading("Size", text="Size")
    self.tree.column("Extract", width=50, anchor="center")
    self.tree.pack(expand=True, fill="both", padx=10, pady=10)

    self.tree.bind("<ButtonRelease-1>", self.on_click)

    self.extract_button = ttk.Button(self, text="Extract Files", command=self.extract_files)
    self.extract_button.pack(pady=10)
    self.delete_button = ttk.Button(self, text="Delete Files", command=self.delete_files)
    self.delete_button.pack(pady=10)

    self.status_var = tk.StringVar()
    self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, 
                                background=self.bg_color, foreground=self.fg_color)
    self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    self.progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='determinate')
    self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)