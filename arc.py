import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QPushButton, 
    QLabel, 
    QLineEdit, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QProgressBar,
    QHeaderView,
    QHBoxLayout,
    QVBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import os
import py7zr
import zipfile
import rarfile
import tarfile
import gzip
import bz2
import keyring
from abc import ABC, abstractmethod  # Import abstractmethod

class ArchiveHandler:
    def __init__(self, filename):
        self.filename = filename

    @abstractmethod
    def get_file_list(self):
        pass

    @abstractmethod
    def extract_files(self, files_to_extract, extract_dir, callback):
        pass

    @abstractmethod
    def delete_files(self, files_to_delete):
        pass

    @abstractmethod
    def rename_file(self, old_name, new_name):
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
    def encrypt_archive(self, password):
        pass

    @abstractmethod
    def encrypt_files(self, files_to_encrypt, passwords):
        pass

    @property
    @abstractmethod
    def supports_encryption(self):
        pass

    @abstractmethod
    def create_archive(self):
        pass

    @abstractmethod
    def add_files(self, files_to_add):
        pass

    @property
    @abstractmethod
    def supports_creation(self):
        pass

    @property
    @abstractmethod
    def supports_adding(self):
        pass


class SevenZipHandler(ArchiveHandler):
    def get_file_list(self):
        with py7zr.SevenZipFile(self.filename, mode='r') as archive:
            return archive.getnames()

    def extract_files(self, files_to_extract, extract_dir, callback):
        with py7zr.SevenZipFile(self.filename, mode='r') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(path=extract_dir, targets=[file])
                callback.emit(i, len(files_to_extract), file)

    def delete_files(self, files_to_delete):
        temp_filename = self.filename + '.temp'
        with py7zr.SevenZipFile(self.filename, mode='r') as archive_read:
            with py7zr.SevenZipFile(temp_filename, mode='w') as archive_write:
                for file_info in archive_read.list():
                    if file_info.filename not in files_to_delete:
                        archive_write.write({file_info.filename: archive_read.read([file_info.filename])[file_info.filename]})
        os.remove(self.filename)
        os.rename(temp_filename, self.filename)

    @property
    def supports_deletion(self):
        return True

    def rename_file(self, old_name, new_name):
        temp_filename = self.filename + '.temp'
        with py7zr.SevenZipFile(self.filename, mode='r') as archive_read:
            with py7zr.SevenZipFile(temp_filename, mode='w') as archive_write:
                for file_info in archive_read.list():
                    if file_info.filename == old_name:
                        archive_write.writestr({new_name: archive_read.read([old_name])[old_name]})
                    else:
                        archive_write.writestr({file_info.filename: archive_read.read([file_info.filename])[file_info.filename]})
        os.remove(self.filename)
        os.rename(temp_filename, self.filename)

    @property
    def supports_renaming(self):
        return True

    def encrypt_archive(self, password):
        return

    def encrypt_files(self, files_to_encrypt, passwords):
        return

    @property
    def supports_encryption(self):
        return False

    def create_archive(self):
        with py7zr.SevenZipFile(self.filename, 'w') as _:
            pass

    def add_files(self, files_to_add):
        with py7zr.SevenZipFile(self.filename, 'a') as archive:
            for file_path in files_to_add:
                archive.write(file_path, os.path.basename(file_path))

    @property
    def supports_creation(self):
        return True

    @property
    def supports_adding(self):
        return True


class ZipHandler(ArchiveHandler):
    def get_file_list(self):
        with zipfile.ZipFile(self.filename, 'r') as archive:
            return [
                (os.path.basename(item.filename), item.file_size)
                for item in archive.infolist()
            ]

    def extract_files(self, files_to_extract, extract_dir, callback):
        with zipfile.ZipFile(self.filename, 'r') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(file, path=extract_dir)
                callback.emit(i, len(files_to_extract), file)

    def delete_files(self, files_to_delete):
        temp_filename = self.filename + '.temp'
        with zipfile.ZipFile(self.filename, 'r') as archive_read:
            with zipfile.ZipFile(temp_filename, 'w') as archive_write:
                for item in archive_read.infolist():
                    if item.filename not in files_to_delete:
                        archive_write.writestr(item, archive_read.read(item.filename))
        os.remove(self.filename)
        os.rename(temp_filename, self.filename)

    def create_archive(self):
        with zipfile.ZipFile(self.filename, 'w', zipfile.ZIP_DEFLATED) as _:
            pass

    def add_files(self, files_to_add):
        with zipfile.ZipFile(self.filename, 'a') as archive:
            for file_path in files_to_add:
                archive.write(file_path, os.path.basename(file_path))

    @property
    def supports_creation(self):
        return True

    @property
    def supports_adding(self):
        return True

    @property
    def supports_deletion(self):
        return True

    def rename_file(self, old_name, new_name):
        temp_filename = self.filename + '.temp'
        with zipfile.ZipFile(self.filename, 'r') as archive_read:
            with zipfile.ZipFile(temp_filename, 'w') as archive_write:
                for item in archive_read.infolist():
                    if item.filename == old_name:
                        data = archive_read.read(item.filename)
                        archive_write.writestr(new_name, data)
                    else:
                        archive_write.writestr(item, archive_read.read(item.filename))
        os.remove(self.filename)
        os.rename(temp_filename, self.filename)

    @property
    def supports_renaming(self):
        return True

    def encrypt_archive(self, password):
        temp_filename = self.filename + '.temp'
        with zipfile.ZipFile(self.filename, 'r') as zin:
            with zipfile.ZipFile(temp_filename, 'w') as zout:
                zout.comment = zin.comment
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    zout.writestr(item, data, zipfile.ZIP_DEFLATED)
        os.remove(self.filename)
        os.rename(temp_filename, self.filename)

        with zipfile.ZipFile(self.filename, 'w') as zf:
            zf.setpassword(password.encode())
            for item in zf.infolist():
                zf.writestr(item, zf.read(item.filename), zipfile.ZIP_DEFLATED)

    def encrypt_files(self, files_to_encrypt, passwords):
        temp_filename = self.filename + '.temp'
        with zipfile.ZipFile(self.filename, 'r') as zin:
            with zipfile.ZipFile(temp_filename, 'w') as zout:
                zout.comment = zin.comment
                for item in zin.infolist():
                    if item.filename in files_to_encrypt:
                        zout.writestr(item, zin.read(item.filename),
                                      zipfile.ZIP_DEFLATED,
                                      pwd=passwords[item.filename].encode())
                    else:
                        zout.writestr(item, zin.read(item.filename))
        os.remove(self.filename)
        os.rename(temp_filename, self.filename)

    @property
    def supports_encryption(self):
        return True


class RarHandler(ArchiveHandler):
    def get_file_list(self):
        with rarfile.RarFile(self.filename, 'r') as archive:
            return archive.namelist()

    def extract_files(self, files_to_extract, extract_dir, callback):
        with rarfile.RarFile(self.filename, 'r') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(file, path=extract_dir)
                callback.emit(i, len(files_to_extract), file)

    def delete_files(self, files_to_delete):
        raise NotImplementedError("Deletion is not supported for RAR archives")

    @property
    def supports_deletion(self):
        return False

    def rename_file(self, old_name, new_name):
        return

    @property
    def supports_renaming(self):
        return False

    def encrypt_archive(self, password):
        return

    def encrypt_files(self, files_to_encrypt, passwords):
        return

    @property
    def supports_encryption(self):
        return False

    def create_archive(self):
        return

    def add_files(self, files_to_add):
        return

    @property
    def supports_creation(self):
        return False

    @property
    def supports_adding(self):
        return False


class TarHandler(ArchiveHandler):
    def get_file_list(self):
        with tarfile.open(self.filename, 'r:*') as archive:
            return [
                (member.name, member.size)
                for member in archive
            ]

    def extract_files(self, files_to_extract, extract_dir, callback):
        with tarfile.open(self.filename, 'r:*') as archive:
            for i, file in enumerate(files_to_extract, 1):
                archive.extract(file, path=extract_dir)
                callback.emit(i, len(files_to_extract), file)

    def delete_files(self, files_to_delete):
        return

    @property
    def supports_deletion(self):
        return False

    def rename_file(self, old_name, new_name):
        return

    @property
    def supports_renaming(self):
        return False

    def encrypt_archive(self, password):
        return

    def encrypt_files(self, files_to_encrypt, passwords):
        return

    @property
    def supports_encryption(self):
        return False

    def create_archive(self):
        return

    def add_files(self, files_to_add):
        return

    @property
    def supports_creation(self):
        return False

    @property
    def supports_adding(self):
        return False


class GzipHandler(ArchiveHandler):
    def get_file_list(self):
        return [os.path.basename(self.filename[:-3])]

    def extract_files(self, files_to_extract, extract_dir, callback):
        with gzip.open(self.filename, 'rb') as f_in:
            with open(os.path.join(extract_dir, files_to_extract[0]), 'wb') as f_out:
                f_out.write(f_in.read())
        callback.emit(1, 1, files_to_extract[0])

    def delete_files(self, files_to_delete):
        return

    @property
    def supports_deletion(self):
        return False

    def rename_file(self, old_name, new_name):
        return

    @property
    def supports_renaming(self):
        return False

    def encrypt_archive(self, password):
        return

    def encrypt_files(self, files_to_encrypt, passwords):
        return

    @property
    def supports_encryption(self):
        return False

    def create_archive(self):
        return

    def add_files(self, files_to_add):
        return

    @property
    def supports_creation(self):
        return False

    @property
    def supports_adding(self):
        return False


class Bzip2Handler(ArchiveHandler):
    def get_file_list(self):
        return [os.path.basename(self.filename[:-4])]

    def extract_files(self, files_to_extract, extract_dir, callback):
        with bz2.open(self.filename, 'rb') as f_in:
            with open(os.path.join(extract_dir, files_to_extract[0]), 'wb') as f_out:
                f_out.write(f_in.read())
        callback.emit(1, 1, files_to_extract[0])

    def delete_files(self, files_to_delete):
        return

    @property
    def supports_deletion(self):
        return False

    def rename_file(self, old_name, new_name):
        return

    @property
    def supports_renaming(self):
        return False

    def encrypt_archive(self, password):
        return

    def encrypt_files(self, files_to_encrypt, passwords):
        return

    @property
    def supports_encryption(self):
        return False

    def create_archive(self):
        return

    def add_files(self, files_to_add):
        return

    @property
    def supports_creation(self):
        return False

    @property
    def supports_adding(self):
        return False


ARCHIVE_HANDLERS = {
    '7z': SevenZipHandler,
    'zip': ZipHandler,
    'rar': RarHandler,
    'tar': TarHandler,
    'gz': GzipHandler,
    'bz2': Bzip2Handler,
}

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Archive Viewer")
        self.setGeometry(300, 300, 600, 400)
        self.password_manager = keyring.get_keyring()
        self.archive_filename = None
        self.archive_handler = None

        self.initUI()

    def initUI(self):
        # File selection
        top_button_layout = QHBoxLayout()  # Layout for top buttons
        top_button_layout.addWidget(QPushButton("Select Archive", self, clicked=self.openFile))
        top_button_layout.addWidget(QPushButton("New Archive", self, clicked=self.createNewArchive))

        # Center the top buttons
        top_button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # File list
        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Select", "Filename", "Size", "Subdirectory"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # Expand columns
        self.tree.setGeometry(10, 80, self.width() - 20, self.height() - 180)
        self.tree.itemClicked.connect(self.onTreeItemClicked)

        # Action Buttons
        bottom_button_layout = QHBoxLayout()  # Layout for bottom buttons
        bottom_button_layout.addWidget(QPushButton("Extract", self, clicked=self.extractFiles))
        bottom_button_layout.addWidget(QPushButton("Delete", self, clicked=self.deleteFiles))
        bottom_button_layout.addWidget(QPushButton("Rename", self, clicked=self.renameFile))
        bottom_button_layout.addWidget(QPushButton("Encrypt", self, clicked=self.encryptFiles))

        # Center the bottom buttons
        bottom_button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(10, self.height() - 40, 280, 15)  # Adjust position

        # Status label
        self.status_label = QLabel("Status: No archive selected", self)

        # Layout the main widget
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_button_layout)
        main_layout.addWidget(self.tree)
        main_layout.addLayout(bottom_button_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)

    def openFile(self):
        self.archive_filename = QFileDialog.getOpenFileName(
            self, "Select Archive", "",
            "All supported archives (*.7z *.zip *.rar *.tar *.gz *.bz2);;7z files (*.7z);;Zip files (*.zip);;Rar files (*.rar);;Tar files (*.tar);;Gzip files (*.gz);;Bzip2 files (*.bz2);;All files (*.*)"
        )[0]

        if self.archive_filename:
            self.populateTree()
            self.updateStatus(f"Loaded {len(self.archive_handler.get_file_list())} files from archive")

    def createNewArchive(self):
        self.archive_filename = QFileDialog.getSaveFileName(
            self, "Create New Archive", "",
            "7z files (*.7z);;Zip files (*.zip);;Rar files (*.rar);;Tar files (*.tar);;Gzip files (*.gz);;Bzip2 files (*.bz2);;All files (*.*)"
        )[0]

        if self.archive_filename:
            self.createArchive()

    def createArchive(self):
        _, extension = os.path.splitext(self.archive_filename)
        extension = extension[1:].lower()

        if extension not in ARCHIVE_HANDLERS:
            QMessageBox.warning(self, "Error", f"Unsupported file format: {extension}")
            return

        HandlerClass = ARCHIVE_HANDLERS[extension]
        self.archive_handler = HandlerClass(self.archive_filename)

        if not self.archive_handler.supports_creation:
            QMessageBox.warning(self, "Error", f"Creation of {extension} archives is not supported.")
            return

        try:
            self.archive_handler.create_archive()
            QMessageBox.information(self, "Success", f"New {extension} archive created successfully.")
            self.populateTree()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create archive: {str(e)}")

    def populateTree(self):
        self.tree.clear()
        try:
            _, extension = os.path.splitext(self.archive_filename)
            extension = extension[1:].lower()

            HandlerClass = ARCHIVE_HANDLERS[extension]
            self.archive_handler = HandlerClass(self.archive_filename)
            file_list = self.archive_handler.get_file_list()

            for file_path, file_size in file_list:
                subdirectory = os.path.dirname(file_path)
                subdirectory = subdirectory if subdirectory else ""  # Handle root files

                item = QTreeWidgetItem(self.tree)
                item.setText(0, "☐")
                item.setText(1, file_path)
                item.setText(2, f"{file_size} bytes")
                item.setText(3, subdirectory)

            self.updateStatus(f"Loaded {len(file_list)} files from archive")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read archive: {str(e)}")

    def onTreeItemClicked(self, item, column):
        if column == 0:
            if item.text(0) == "☐":
                item.setText(0, "☑")
            else:
                item.setText(0, "☐")

    def updateStatus(self, message):
        self.status_label.setText(f"Status: {message}")

    def extractFiles(self):
        if not self.archive_filename:
            QMessageBox.warning(self, "Error", "No archive file selected.")
            return

        selected_files = [self.tree.topLevelItem(i).text(1)
                         for i in range(self.tree.topLevelItemCount())
                         if self.tree.topLevelItem(i).text(0) == "☑"]

        if not selected_files:
            selected_files = [self.tree.topLevelItem(i).text(1)
                             for i in range(self.tree.topLevelItemCount())]

        if not selected_files:
            QMessageBox.information(self, "Info", "No files to extract.")
            return

        extract_dir = QFileDialog.getExistingDirectory(
            self, "Select Extraction Directory", os.path.expanduser("~")
        )

        if not extract_dir:
            return

        def extraction_thread(files, extract_dir, callback):
            try:
                for i, file in enumerate(files, 1):
                    self.archive_handler.extract_files(
                        [file], extract_dir, callback
                    )
                callback.emit(len(files), len(files), "")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error during extraction: {str(e)}")

        class ExtractionProgress(QThread):
            update_signal = pyqtSignal(int, int, str)

            def __init__(self, files, extract_dir):
                super().__init__()
                self.files = files
                self.extract_dir = extract_dir

            def run(self):
                extraction_thread(self.files, self.extract_dir, self.update_signal)

        self.extraction_progress = ExtractionProgress(selected_files, extract_dir)
        self.extraction_progress.update_signal.connect(self.updateProgressBar)
        self.extraction_progress.start()
        self.progress_bar.setValue(0)

    def updateProgressBar(self, current, total, file):
        self.progress_bar.setValue(int((current / total) * 100))
        self.updateStatus(f"Extracting: {file}")
        if current == total:
            self.updateStatus(
                f"Extraction completed. Files extracted to {self.extraction_progress.extract_dir}"
            )
            QMessageBox.information(
                self, "Success",
                f"Extraction completed. Files extracted to {self.extraction_progress.extract_dir}",
            )
            self.progress_bar.setValue(0)

    def deleteFiles(self):
        if not self.archive_filename:
            QMessageBox.warning(self, "Error", "No archive file selected.")
            return

        selected_files = [
            self.tree.topLevelItem(i).text(1)
            for i in range(self.tree.topLevelItemCount())
            if self.tree.topLevelItem(i).text(0) == "☑"
        ]

        if not selected_files:
            QMessageBox.warning(self, "Error", "No files selected for deletion.")
            return

        if not self.archive_handler.supports_deletion:
            QMessageBox.warning(
                self, "Error", "Deletion is not supported for this archive format."
            )
            return

        if QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_files)} file(s) from the archive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            try:
                self.archive_handler.delete_files(selected_files)
                QMessageBox.information(
                    self, "Success", f"Successfully deleted {len(selected_files)} file(s) from the archive."
                )
                self.populateTree()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete files: {str(e)}")

    def renameFile(self):
        if not self.archive_filename:
            QMessageBox.warning(self, "Error", "No archive file selected.")
            return

        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No file selected for renaming.")
            return

        if not self.archive_handler.supports_renaming:
            QMessageBox.warning(
                self, "Error", "Renaming is not supported for this archive format."
            )
            return

        renamed_files = 0
        skipped_files = 0

        for item in selected_items:
            old_name = item.text(1)
            new_name, ok = QInputDialog.getText(
                self, "Rename File", f"Enter new name for {old_name}:"
            )

            if ok:
                if new_name == old_name:
                    skipped_files += 1
                    continue

                try:
                    self.archive_handler.rename_file(old_name, new_name)
                    renamed_files += 1
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to rename {old_name}: {str(e)}")
                    skipped_files += 1
            else:
                skipped_files += 1

        if renamed_files > 0:
            QMessageBox.information(
                self, "Success", f"Successfully renamed {renamed_files} file(s)."
            )
            self.populateTree()

        if skipped_files > 0:
            QMessageBox.information(
                self, "Information", f"{skipped_files} file(s) were not renamed."
            )

    def encryptFiles(self):
        if not self.archive_filename:
            QMessageBox.warning(self, "Error", "No archive file selected.")
            return

        if not self.archive_handler.supports_encryption:
            QMessageBox.warning(
                self, "Error", "Encryption is not supported for this archive format."
            )
            return

        selected_items = self.tree.selectedItems()
        if not selected_items:
            # Encrypt entire archive
            password, ok = QInputDialog.getText(
                self, "Encrypt Archive", "Enter master password for the archive:", echo=QLineEdit.EchoMode.Password
            )
            if ok:
                try:
                    self.password_manager.set(self.archive_filename, "master_password", password)
                    self.archive_handler.encrypt_archive(password)
                    QMessageBox.information(self, "Success", "Archive encrypted successfully.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to encrypt archive: {str(e)}")
        else:
            # Encrypt selected files
            files_to_encrypt = {}
            for item in selected_items:
                file_name = item.text(1)
                password, ok = QInputDialog.getText(
                    self, "Encrypt File", f"Enter password for {file_name}:", echo=QLineEdit.EchoMode.Password
                )
                if ok:
                    self.password_manager.set(self.archive_filename, file_name, password)
                    files_to_encrypt[file_name] = password

            if files_to_encrypt:
                try:
                    self.archive_handler.encrypt_files(files_to_encrypt, files_to_encrypt)
                    QMessageBox.information(
                        self, "Success", f"Successfully encrypted {len(files_to_encrypt)} file(s)."
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to encrypt files: {str(e)}")

        self.populateTree()

    def addFiles(self):
        if not self.archive_filename:
            QMessageBox.warning(self, "Error", "No archive file selected. Please create or open an archive first.")
            return

        if not self.archive_handler.supports_adding:
            QMessageBox.warning(self, "Error", "Adding files is not supported for this archive format.")
            return

        files_to_add = QFileDialog.getOpenFileNames(
            self, "Select Files to Add", "", "All files (*.*)"
        )[0]

        if files_to_add:
            try:
                self.archive_handler.add_files(files_to_add)
                QMessageBox.information(
                    self, "Success", f"Successfully added {len(files_to_add)} file(s) to the archive."
                )
                self.populateTree()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add files: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())