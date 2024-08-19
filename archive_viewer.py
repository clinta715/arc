# archive_viewer.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
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
                populate_tree(self, self.archive_filename)  # Refresh the file list
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete files: {str(e)}")

    def rename_file(self):
        if not self.archive_filename:
            messagebox.showerror("Error", "No archive file selected.")
            return

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "No file selected for renaming.")
            return

        handler = get_archive_handler(self.archive_filename)
        if not handler:
            messagebox.showerror("Error", f"Unsupported file format: {os.path.splitext(self.archive_filename)[1]}")
            return

        if not handler.supports_renaming:
            messagebox.showerror("Error", "Renaming is not supported for this archive format.")
            return

        renamed_files = 0
        skipped_files = 0

        for item in selected_items:
            old_name = self.tree.item(item)['values'][1]
            new_name = simpledialog.askstring("Rename File", f"Enter new name for {old_name}:", parent=self)

            if new_name:
                if new_name == old_name:
                    skipped_files += 1
                    continue

                try:
                    handler.rename_file(self.archive_filename, old_name, new_name)
                    renamed_files += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename {old_name}: {str(e)}")
                    skipped_files += 1
            else:
                skipped_files += 1

        if renamed_files > 0:
            messagebox.showinfo("Success", f"Successfully renamed {renamed_files} file(s).")
            populate_tree(self, self.archive_filename)  # Refresh the file list

        if skipped_files > 0:
            messagebox.showinfo("Information", f"{skipped_files} file(s) were not renamed.")

    def encrypt_files(self):
        if not self.archive_filename:
            messagebox.showerror("Error", "No archive file selected.")
            return

        handler = get_archive_handler(self.archive_filename)
        if not handler:
            messagebox.showerror("Error", f"Unsupported file format: {os.path.splitext(self.archive_filename)[1]}")
            return

        if not handler.supports_encryption:
            messagebox.showerror("Error", "Encryption is not supported for this archive format.")
            return

        selected_items = self.tree.selection()
        if not selected_items:
            # Encrypt entire archive
            password = simpledialog.askstring("Encrypt Archive", "Enter master password for the archive:", show='*')
            if password:
                try:
                    handler.encrypt_archive(self.archive_filename, password)
                    messagebox.showinfo("Success", "Archive encrypted successfully.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to encrypt archive: {str(e)}")
        else:
            # Encrypt selected files
            files_to_encrypt = {}
            for item in selected_items:
                file_name = self.tree.item(item)['values'][1]
                password = simpledialog.askstring("Encrypt File", f"Enter password for {file_name}:", show='*')
                if password:
                    files_to_encrypt[file_name] = password

            if files_to_encrypt:
                try:
                    handler.encrypt_files(self.archive_filename, files_to_encrypt, files_to_encrypt)
                    messagebox.showinfo("Success", f"Successfully encrypted {len(files_to_encrypt)} file(s).")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to encrypt files: {str(e)}")

        # Refresh the file list
        populate_tree(self, self.archive_filename)
    
    def create_new_archive(self):
        filetypes = [(f.upper() + " files", f"*.{f}") for f in self.supported_formats]
        filetypes.append(("All files", "*.*"))
        
        new_archive_path = filedialog.asksaveasfilename(
            title="Create New Archive",
            filetypes=filetypes,
            initialdir=self.last_extraction_path
        )
        
        if new_archive_path:
            _, extension = os.path.splitext(new_archive_path)
            extension = extension[1:].lower()  # Remove the dot and convert to lowercase
            
            handler = get_archive_handler(new_archive_path)
            if not handler:
                messagebox.showerror("Error", f"Unsupported file format: {extension}")
                return
            
            if not handler.supports_creation:
                messagebox.showerror("Error", f"Creation of {extension} archives is not supported.")
                return
            
            try:
                handler.create_archive(new_archive_path)
                messagebox.showinfo("Success", f"New {extension} archive created successfully.")
                self.archive_filename = new_archive_path
                populate_tree(self, new_archive_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create archive: {str(e)}")

    def add_files(self):
        if not self.archive_filename:
            messagebox.showerror("Error", "No archive file selected. Please create or open an archive first.")
            return

        handler = get_archive_handler(self.archive_filename)
        if not handler:
            messagebox.showerror("Error", f"Unsupported file format: {os.path.splitext(self.archive_filename)[1]}")
            return

        if not handler.supports_adding:
            messagebox.showerror("Error", "Adding files is not supported for this archive format.")
            return

        files_to_add = filedialog.askopenfilenames(
            title="Select Files to Add",
            initialdir=self.last_extraction_path
        )

        if files_to_add:
            try:
                handler.add_files(self.archive_filename, files_to_add)
                messagebox.showinfo("Success", f"Successfully added {len(files_to_add)} file(s) to the archive.")
                populate_tree(self, self.archive_filename)  # Refresh the file list
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add files: {str(e)}")
                