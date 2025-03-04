import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QListWidget, QLabel, QFileDialog, QMessageBox, QMenu)
from isoframework import ISOManipulator
from PyQt6.QtWidgets import QInputDialog
import shutil
class ISOManipulatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ISO Manipulator")
        self.setGeometry(100, 100, 600, 400)

        self.manipulator = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # ISO selection
        iso_layout = QHBoxLayout()
        self.iso_path_input = QLineEdit()
        iso_browse_button = QPushButton("Browse")
        iso_browse_button.clicked.connect(self.browse_iso)
        iso_layout.addWidget(QLabel("Select ISO image:"))
        iso_layout.addWidget(self.iso_path_input)
        iso_layout.addWidget(iso_browse_button)
        layout.addLayout(iso_layout)

        # file list
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        # button
        button_layout = QHBoxLayout()
        self.setup_buttons(button_layout)
        layout.addLayout(button_layout)
        #add_button = QPushButton("Add")
        modify_button = QPushButton("Modify")
        delete_button = QPushButton("Delete")
        #add_button.clicked.connect(self.add_file)
        modify_button.clicked.connect(self.modify_file)
        delete_button.clicked.connect(self.delete_file)
        #button_layout.addWidget(add_button)
        button_layout.addWidget(modify_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

        # Output ISO
        output_layout = QHBoxLayout()
        self.output_path_input = QLineEdit()
        output_browse_button = QPushButton("Browse")
        output_browse_button.clicked.connect(self.browse_output)
        output_layout.addWidget(QLabel("Output ISO:"))
        output_layout.addWidget(self.output_path_input)
        output_layout.addWidget(output_browse_button)
        layout.addLayout(output_layout)

        # Generate button
        generate_button = QPushButton("Generate new ISO")
        generate_button.clicked.connect(self.generate_iso)
        layout.addWidget(generate_button)

    def setup_buttons(self, layout):
        """创建功能按钮组"""
        add_menu = QMenu()
        add_menu.addAction("📄 Add File", self.add_file)
        add_menu.addAction("📁 Add Directory", self.add_directory)
        add_menu.addAction("📦 Add Archive", self.add_archive)

        add_button = QPushButton("Add")
        add_button.setMenu(add_menu)

        # modify_button = QPushButton("Modify")
        # delete_button = QPushButton("Delete")

        layout.addWidget(add_button)
        # layout.addWidget(modify_button)
        # layout.addWidget(delete_button)
    def browse_iso(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select ISO", "", "ISO files (*.iso)")
        if filename:
            self.iso_path_input.setText(filename)
            try:
                self.manipulator = ISOManipulator(filename)
                self.manipulator.mount_iso()
                self.manipulator.extract_iso_content()
                self.manipulator.unmount_iso()
                self.update_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    def browse_output(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save ISO", "", "ISO files (*.iso)")
        if filename:
            self.output_path_input.setText(filename)

    def update_file_list(self):
        self.file_list.clear()
        for root, dirs, files in os.walk(self.manipulator.temp_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.manipulator.temp_dir)
                self.file_list.addItem(rel_path)

    def add_file(self):
        """Add single file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select file to add", "", "All Files (*)"
        )
        if filename:
            try:
                # Get absolute path
                dest_path, ok = QInputDialog.getText(
                    self,
                    "Destination Path",
                    "Enter target path (relative to ISO root):",
                    text=os.path.basename(filename)
                )

                if ok:
                    self._add_single_file(filename, dest_path)
                    self.update_file_list()

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _add_single_file(self, src_path, dest_path):
        """add file logic"""
        full_dest = os.path.join(self.manipulator.temp_dir, dest_path)

        # create target directory
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)
        #copy file
        shutil.copy2(src_path, full_dest)

    def add_directory(self):
        """Add directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select directory to add")
        if dir_path:
            try:
                # Get destination directory
                dest_path, ok = QInputDialog.getText(
                    self,
                    "Destination Path",
                    "Enter target path (relative to ISO root):",
                    text=os.path.basename(dir_path)
                )

                if ok:
                    self.manipulator.add_directory(dir_path, dest_path)
                    self.update_file_list()
                    QMessageBox.information(self, "Success", "Directory added successfully")

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def add_archive(self):
        """Add package"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select archive to add",
            "",
            "Archives (*.tgz *.tar.gz *.zip);;All Files (*)"
        )
        if filename:
            try:
                dest_path, ok = QInputDialog.getText(
                    self,
                    "Extraction Path",
                    "Enter extraction path (relative to ISO root):",
                    text=""
                )
                if ok:
                    self.manipulator.add_extracted_content(filename, dest_path)
                    #self.manipulator.add_extracted_content(filename)
                    self.update_file_list()
                    QMessageBox.information(self, "Success", "Archive extracted successfully")

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def modify_file(self):
        selected_items = self.file_list.selectedItems()
        if selected_items:
            filename = selected_items[0].text()
            with open(os.path.join(self.manipulator.temp_dir, filename), 'r') as f:
                content = f.read()
            new_content, ok = QInputDialog.getMultiLineText(self, "Modify", "Input new content:", content)
            if ok:
                self.manipulator.modify_content("modify", filename, new_content)

    def delete_file(self):
        selected_items = self.file_list.selectedItems()
        if selected_items:
            filename = selected_items[0].text()
            reply = QMessageBox.question(self, 'Confirm delete', f"Are you want to delete {filename}",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.manipulator.modify_content("delete", filename)
                self.update_file_list()

    def generate_iso(self):
        if not self.manipulator or not self.output_path_input.text():
            QMessageBox.critical(self, "Fail", "please select output path")
            return
        self.manipulator.regenerate_iso(self.output_path_input.text())
        self.manipulator.cleanup()
        QMessageBox.information(self, "Success", "The new ISO has been generated")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ISOManipulatorGUI()
    window.show()
    sys.exit(app.exec())
