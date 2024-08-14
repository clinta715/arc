import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import patoolib
import subprocess

class ArchiveViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Archive Viewer")
        self.geometry("600x400")

        self.supported_formats = [
            "zip", "rar", "7z", "tar", "gzip", "bzip2", "xz",
            "lzma", "cab", "cpio", "ar", "arj", "lzh", "lha"
        ]
        self.create_widgets()

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
        self.tree.pack(expand=True, fill="both")

        # Bind click event to the "Extract" column
        self.tree.bind("<ButtonRelease-1>", self.on_click)

        # Extract button
        self.extract_button = ttk.Button(self, text="Extract Selected Files", command=self.extract_files)
        self.extract_button.pack(pady=10)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def select_file(self):
        filetypes = [("All supported archives", f"*.{' *.'.join(self.supported_formats)}")]
        filetypes.extend([(f.upper() + " files", f"*.{f}") for f in self.supported_formats])
        filetypes.append(("All files", "*.*"))

        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.archive_filename = filename
            self.populate_tree(filename)

    def populate_tree(self, filename):
        self.tree.delete(*self.tree.get_children())
        try:
            result = subprocess.run(['patool', 'list', filename], capture_output=True, text=True)
            file_list = result.stdout.strip().split('\n')[1:]  # Skip the first line (archive name)
            
            for file_info in file_list:
                file_path = file_info.strip()
                # We don't have size information, so we'll leave it blank
                self.tree.insert("", "end", values=(
                    "☐",  # Unchecked box
                    file_path,
                    ""
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
            messagebox.showinfo("Info", "No files selected for extraction.")
            return

        extract_dir = filedialog.askdirectory(title="Select Extraction Directory")
        if not extract_dir:
            return

        total_files = len(selected_files)

        def extraction_thread():
            try:
                patoolib.extract_archive(self.archive_filename, outdir=extract_dir, interactive=False, verbosity=-1)
                
                for i, file in enumerate(selected_files, 1):
                    self.status_var.set(f"Extracting: {file}")
                    self.progress_bar['value'] = (i / total_files) * 100
                    self.update_idletasks()

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