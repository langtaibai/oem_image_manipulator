import os
import subprocess
from pycdlib import PyCdlib
import tarfile
import zipfile
import shutil
class ISOManipulator:
    def __init__(self, iso_path):
        self.iso_path = iso_path
        self.mount_point = "/mnt/iso"
        self.temp_dir = "/tmp/iso_content"

    def mount_iso(self):
        os.makedirs(self.mount_point, exist_ok=True)
        subprocess.run(["sudo", "mount", "-o", "loop", self.iso_path, self.mount_point])

    def unmount_iso(self):
        subprocess.run(["sudo", "umount", self.mount_point])

    def extract_iso_content(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        subprocess.run(["sudo", "cp", "-r", f"{self.mount_point}/.", self.temp_dir])

    def add_directory(self, source_dir, target_path=""):
        """copy the whole directory to temp directory"""
        dest_path = os.path.join(self.temp_dir, target_path)

        try:
            # create target directory
            os.makedirs(dest_path, exist_ok=True)

            # recurisively copy directory content
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(dest_path, item)

                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

        except Exception as e:
            raise RuntimeError(f"Directory copy failed: {str(e)}")
    def modify_content(self, operation, file_path, content=None):
        full_path = os.path.join(self.temp_dir, file_path)
        if operation == "add":
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            # cover existed file
            with open(full_path, "w") as f:
                f.write(content)
        elif operation == "modify":
            with open(full_path, "r+") as f:
                existing_content = f.read()
                f.seek(0)
                f.write(content)
                f.truncate()
        elif operation == "delete":
            os.remove(full_path)

    def add_extracted_content(self, archive_path, target_path=""):
        """decompress package to temp directory"""
        temp_root = os.path.join(self.temp_dir, target_path)
        os.makedirs(temp_root, exist_ok=True)
        try:
            if archive_path.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=temp_root)
            elif archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_root)
            else:
                raise ValueError("Unsupported archive format")
        except Exception as e:
            raise RuntimeError(f"Failed to extract archive: {str(e)}")

    def regenerate_iso(self, output_path):
        # iso = PyCdlib()
        # iso.new()
        #
        # for root, dirs, files in os.walk(self.temp_dir):
        #     for file in files:
        #         full_path = os.path.join(root, file)
        #         iso_path = full_path.replace(self.temp_dir, "")
        #         iso.add_file(full_path, iso_path=iso_path)
        #
        # iso.write(output_path)
        # iso.close()
        subprocess.run(["sudo", "genisoimage", "-o", output_path, "-R", "-J", self.temp_dir])

    def cleanup(self):
        subprocess.run(["sudo", "rm", "-rf", self.temp_dir])

def main():
    manipulator = ISOManipulator("/path/to/ubuntu.iso")
    
    manipulator.mount_iso()
    manipulator.extract_iso_content()
    manipulator.unmount_iso()
    
    # example
    manipulator.modify_content("add", "new_file.txt", "This is a new file")
    manipulator.modify_content("modify", "existing_file.txt", "Modified content")
    manipulator.modify_content("delete", "unwanted_file.txt")
    
    manipulator.regenerate_iso("/path/to/modified_ubuntu.iso")
    manipulator.cleanup()

if __name__ == "__main__":
    main()
