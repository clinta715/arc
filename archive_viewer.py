# archive_viewer.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading

from ui_components import create_widgets, set_dark_theme
from archive_handlers import populate_tree, extract_files, get_archive_handler
from utils import SUPPORTED_FORMATS

class ArchiveViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Archive Viewer")
        self.geometry("600x400")

        self.supported_formats = SUPPORTED_FORMATS
        self.last_extraction_path = os.path.expanduser("~")
        self.archive_filename = None

        set_dark_theme(self)
        create_widgets(self)

    def select_file(self):
        filetypes = [("All supported archives", f"*.{' *.'.join(self.supported_formats)}")]
        filetypes.extend([(f.upper() + " files", f"*.{f}") for f in self.supported_formats])
        filetypes.append(("All files", "*.*"))

        filename = filedialog.askopenfilename(
            filetypes=filetypes,
            initialdir=self.last_extraction_path
        )
        if filename:
            self.archive_filename = filename
            self.last_extraction_path = os.path.dirname(filename)
            populate_tree(self, filename)

    def on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":  # Extract column
                item = self.tree.identify_row(event.y)
                current_value = self.tree.item(item, "values")
                new_value = list(current_value)
                new_value[0] = "☑" if current_value[0] == "☐" else "☐"
                self.tree.item(item, values=new_value)

    def extract_files(self):
        extract_files(self)

    def delete_files(self):
        if not self.archive_filename:
            messagebox.showerror("Error", "No archive file selected.")
            return

        selected_files = [self.tree.item(item)['values'][1] for item in self.tree.get_children() 
                            if self.tree.item(item)['values'][0] == "☑"]

        if not selected_files:
            messagebox.showerror("Error", "No files selected for deletion.")
            return

        handler = get_archive_handler(self.archive_filename)
        if not handler:
            messagebox.showerror("Error", f"Unsupported file format: {os.path.splitext(self.archive_filename)[1]}")
            return

        if not handler.supports_deletion:
            messagebox.showerror("Error", "Deletion is not supported for this archive format.")
            return
        
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(selected_files)} file(s) from the archive?"):
            try:
                handler.delete_files(self.archive_filename, selected_files)
                messagebox.showinfo("Success", f"Successfully deleted {len(selected_files)} file(s) from the archive.")
                self.populate_tree(self.archive_filename)  # Refresh the file list
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete files: {str(e)}")
