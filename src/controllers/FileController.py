import os
FILES_UPLOAD_DIR = "uploads"

class FileController:

    def __init__(self):
        os.makedirs(FILES_UPLOAD_DIR, exist_ok=True)

    def get_file_path(self, dir_name: str, file_name: str) -> str:

        target_dir = os.path.join(FILES_UPLOAD_DIR, dir_name)
        os.makedirs(target_dir, exist_ok=True)
        return os.path.join(target_dir, file_name)