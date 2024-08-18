# archive_base.py
from abc import ABC, abstractmethod

class ArchiveHandler(ABC):
    @abstractmethod
    def get_file_list(self, filename):
        pass

    @abstractmethod
    def extract_files(self, filename, files_to_extract, extract_dir, callback):
        pass

    @abstractmethod
    def delete_files(self, filename, files_to_delete):
        pass

    @property
    @abstractmethod
    def supports_deletion(self):
        pass