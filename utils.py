# utils.py
from tkinter import filedialog

SUPPORTED_FORMATS = ["7z", "zip", "rar", "tar", "gz", "bz2"]

def select_extract_directory(self):
    return filedialog.askdirectory(
        title="Select Extraction Directory",
        initialdir=self.last_extraction_path
    )