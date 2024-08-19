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

    @abstractmethod
    def rename_file(self, filename, old_name, new_name):
        pass

    @property
    @abstractmethod
    def supports_deletion(self):
        pass

    @property
    @abstractmethod
    def supports_renaming(self):
        pass

    @abstractmethod
    def encrypt_archive(self, filename, password):
        pass

    @abstractmethod
    def encrypt_files(self, filename, files_to_encrypt, passwords):
        pass

    @property
    @abstractmethod
    def supports_encryption(self):
        pass