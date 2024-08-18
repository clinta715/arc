import os
import py7zr
import zipfile
import rarfile
import tarfile
import gzip
import bz2
from tkinter import messagebox
import threading
from archive_base import ArchiveHandler

class SevenZipHandler(ArchiveHandler):
    def get_file_list(self, filename):
        with py7zr.SevenZipFile(filename, mode='r') as archive:
            return archive.getnames()

    def extract_files(self, filename, files_to_extract, extract_dir, callback):
        with py7zr.SevenZipFile(filename, mode='r') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(path=extract_dir, targets=[file])
                callback(i, len(files_to_extract), file)

    def delete_files(self, filename, files_to_delete):
        temp_filename = filename + '.temp'
        with py7zr.SevenZipFile(filename, mode='r') as archive_read:
            with py7zr.SevenZipFile(temp_filename, mode='w') as archive_write:
                for file_info in archive_read.list():
                    if file_info.filename not in files_to_delete:
                        archive_write.write({file_info.filename: archive_read.read([file_info.filename])[file_info.filename]})
        os.remove(filename)
        os.rename(temp_filename, filename)

    @property
    def supports_deletion(self):
        return True

class ZipHandler(ArchiveHandler):
    def get_file_list(self, filename):
        with zipfile.ZipFile(filename, 'r') as archive:
            return archive.namelist()

    def extract_files(self, filename, files_to_extract, extract_dir, callback):
        with zipfile.ZipFile(filename, 'r') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(file, path=extract_dir)
                callback(i, len(files_to_extract), file)

    def delete_files(self, filename, files_to_delete):
        temp_filename = filename + '.temp'
        with zipfile.ZipFile(filename, 'r') as archive_read:
            with zipfile.ZipFile(temp_filename, 'w') as archive_write:
                for item in archive_read.infolist():
                    if item.filename not in files_to_delete:
                        archive_write.writestr(item, archive_read.read(item.filename))
        os.remove(filename)
        os.rename(temp_filename, filename)

    @property
    def supports_deletion(self):
        return True

class RarHandler(ArchiveHandler):
    def get_file_list(self, filename):
        with rarfile.RarFile(filename, 'r') as archive:
            return archive.namelist()

    def extract_files(self, filename, files_to_extract, extract_dir, callback):
        with rarfile.RarFile(filename, 'r') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(file, path=extract_dir)
                callback(i, len(files_to_extract), file)

    def delete_files(self, filename, files_to_delete):
        raise NotImplementedError("Deletion is not supported for RAR archives")

    @property
    def supports_deletion(self):
        return False

class TarHandler(ArchiveHandler):
    def get_file_list(self, filename):
        with tarfile.open(filename, 'r:*') as archive:
            return archive.getnames()

    def extract_files(self, filename, files_to_extract, extract_dir, callback):
        with tarfile.open(filename, 'r:*') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(file, path=extract_dir)
                callback(i, len(files_to_extract), file)

    def delete_files(self, filename, files_to_delete):
        return
    
    @property
    def supports_deletion(self):
        return False

class GzipHandler(ArchiveHandler):
    def get_file_list(self, filename):
        return [os.path.basename(filename[:-3])]  # Remove .gz extension

    def extract_files(self, filename, files_to_extract, extract_dir, callback):
        with gzip.open(filename, 'rb') as f_in:
            with open(os.path.join(extract_dir, files_to_extract[0]), 'wb') as f_out:
                f_out.write(f_in.read())
        callback(1, 1, files_to_extract[0])

    def delete_files(self, filename, files_to_delete):
        return
    
    @property
    def supports_deletion(self):
        return False

class Bzip2Handler(ArchiveHandler):
    def get_file_list(self, filename):
        return [os.path.basename(filename[:-4])]  # Remove .bz2 extension

    def extract_files(self, filename, files_to_extract, extract_dir, callback):
        with bz2.open(filename, 'rb') as f_in:
            with open(os.path.join(extract_dir, files_to_extract[0]), 'wb') as f_out:
                f_out.write(f_in.read())
        callback(1, 1, files_to_extract[0])

    def delete_files(self, filename, files_to_delete):
        return
    
    @property
    def supports_deletion(self):
        return False

# Dictionary to map file extensions to their respective handlers
ARCHIVE_HANDLERS = {
    '7z': SevenZipHandler(),
    'zip': ZipHandler(),
    'rar': RarHandler(),
    'tar': TarHandler(),
    'gz': GzipHandler(),
    'bz2': Bzip2Handler(),
}

def get_archive_handler(filename):
    extension = os.path.splitext(filename)[1][1:].lower()
    return ARCHIVE_HANDLERS.get(extension)

def populate_tree(self, filename):
    self.tree.delete(*self.tree.get_children())
    try:
        handler = get_archive_handler(filename)
        if not handler:
            raise ValueError(f"Unsupported file format: {os.path.splitext(filename)[1]}")
        
        file_list = handler.get_file_list(filename)
        
        for file_path in file_list:
            self.tree.insert("", "end", values=(
                "☐",  # Unchecked box
                file_path,
                ""  # Size information not available
            ))
        
        self.status_var.set(f"Loaded {len(file_list)} files from archive")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read archive: {str(e)}")

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

    extract_dir = self.select_extract_directory()
    if not extract_dir:
        return

    def extraction_thread():
        try:
            handler = get_archive_handler(self.archive_filename)
            if not handler:
                raise ValueError(f"Unsupported file format: {os.path.splitext(self.archive_filename)[1]}")
            
            def update_progress(current, total, file):
                self.status_var.set(f"Extracting: {file}")
                self.progress_bar['value'] = (current / total) * 100
                self.update_idletasks()

            handler.extract_files(self.archive_filename, files_to_extract, extract_dir, update_progress)

            self.status_var.set(f"Extraction completed. Files extracted to {extract_dir}")
            messagebox.showinfo("Success", f"Extraction completed. Files extracted to {extract_dir}")
        except Exception as e:
            self.status_var.set(f"Error during extraction: {str(e)}")
            messagebox.showerror("Error", f"Error during extraction: {str(e)}")
        finally:
            self.progress_bar['value'] = 0

    threading.Thread(target=extraction_thread, daemon=True).start()