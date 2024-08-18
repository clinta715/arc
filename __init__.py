# archive_viewer.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading

from .ui_components import create_widgets, set_dark_theme
from .archive_handlers import populate_tree, extract_files, get_archive_handler
from .utils import SUPPORTED_FORMATS