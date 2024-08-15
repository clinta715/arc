import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import py7zr
import zipfile
import rarfile

class ArchiveViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Archive Viewer")
        self.geometry("600x400")

        self.supported_formats = ["7z", "zip", "rar"]
        self.last_extraction_path = os.path.expanduser("~")

        self.set_dark_theme()
        self.create_widgets()

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
        # File selection
        self.select_button = ttk.Button(self, text="Select Archive File", command=self.select_file)
        self.select_button.pack(pady=10)

        # Treeview for file list
        self.tree = ttk.Treeview(self, columns=("Extract", "Filename", "Size"), show="headings")
        self.tree.heading("Extract", text="Extract")
        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Size", text="Size")
        self.tree.column("Extract", width=50, anchor="center")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        # Bind click event to the "Extract" column
        self.tree.bind("<ButtonRelease-1>", self.on_click)

        # Extract button
        self.extract_button = ttk.Button(self, text="Extract Files", command=self.extract_files)
        self.extract_button.pack(pady=10)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, 
                                    background=self.bg_color, foreground=self.fg_color)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

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
            self.populate_tree(filename)

    def populate_tree(self, filename):
        self.tree.delete(*self.tree.get_children())
        try:
            extension = os.path.splitext(filename)[1][1:].lower()
            
            if extension == '7z':
                with py7zr.SevenZipFile(filename, mode='r') as archive:
                    file_list = archive.getnames()
            elif extension == 'zip':
                with zipfile.ZipFile(filename, 'r') as archive:
                    file_list = archive.namelist()
            elif extension == 'rar':
                with rarfile.RarFile(filename, 'r') as archive:
                    file_list = archive.namelist()
            else:
                raise ValueError(f"Unsupported file format: {extension}")
            
            for file_path in file_list:
                self.tree.insert("", "end", values=(
                    "☐",  # Unchecked box
                    file_path,
                    ""  # Size information not available
                ))
            
            self.status_var.set(f"Loaded {len(file_list)} files from archive")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read archive: {str(e)}")

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
        selected_files = [self.tree.item(item)['values'][1] for item in self.tree.get_children() 
                          if self.tree.item(item)['values'][0] == "☑"]
        
        if not selected_files:
            files_to_extract = [self.tree.item(item)['values'][1] for item in self.tree.get_children()]
        else:
            files_to_extract = selected_files

        if not files_to_extract:
            messagebox.showinfo("Info", "No files to extract.")
            return

        extract_dir = filedialog.askdirectory(
            title="Select Extraction Directory",
            initialdir=self.last_extraction_path
        )
        if not extract_dir:
            return

        self.last_extraction_path = extract_dir

        total_files = len(files_to_extract)

        def extraction_thread():
            try:
                extension = os.path.splitext(self.archive_filename)[1][1:].lower()
                
                if extension == '7z':
                    with py7zr.SevenZipFile(self.archive_filename, mode='r') as archive:
                        for i, file in enumerate(files_to_extract, 1):
                            self.status_var.set(f"Extracting: {file}")
                            archive.extract(path=extract_dir, targets=[file])
                            self.progress_bar['value'] = (i / total_files) * 100
                            self.update_idletasks()
                elif extension == 'zip':
                    with zipfile.ZipFile(self.archive_filename, 'r') as archive:
                        for i, file in enumerate(files_to_extract, 1):
                            self.status_var.set(f"Extracting: {file}")
                            archive.extract(file, path=extract_dir)
                            self.progress_bar['value'] = (i / total_files) * 100
                            self.update_idletasks()
                elif extension == 'rar':
                    with rarfile.RarFile(self.archive_filename, 'r') as archive:
                        for i, file in enumerate(files_to_extract, 1):
                            self.status_var.set(f"Extracting: {file}")
                            archive.extract(file, path=extract_dir)
                            self.progress_bar['value'] = (i / total_files) * 100
                            self.update_idletasks()
                else:
                    raise ValueError(f"Unsupported file format: {extension}")

                self.status_var.set(f"Extraction completed. Files extracted to {extract_dir}")
                messagebox.showinfo("Success", f"Extraction completed. Files extracted to {extract_dir}")
            except Exception as e:
                self.status_var.set(f"Error during extraction: {str(e)}")
                messagebox.showerror("Error", f"Error during extraction: {str(e)}")
            finally:
                self.progress_bar['value'] = 0

        threading.Thread(target=extraction_thread, daemon=True).start()

if __name__ == "__main__":
    app = ArchiveViewer()
    app.mainloop()