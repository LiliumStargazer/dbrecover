import os
import zipfile
from utils.errors import bad_request


# -------- UNZIP SICURO (con protezione path traversal) --------
def unzip_backup(zip_path: str, dest_dir: str):
    if not zip_path:
        raise bad_request("zip_path mancante")

    if not os.path.isfile(zip_path):
        raise bad_request(f"Zip non trovato: {zip_path}")

    os.makedirs(dest_dir, exist_ok=True)

    dest_root = os.path.abspath(dest_dir)

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            target_path = os.path.abspath(os.path.join(dest_dir, member))

            # protezione path traversal
            if not target_path.startswith(dest_root):
                raise bad_request(f"Zip entry non valida: {member}")

        z.extractall(dest_dir)


# -------- CREATE ZIP --------
def create_zip_file(files_to_zip: list[str], zipped_file_path: str):
    if not files_to_zip:
        raise bad_request("files_to_zip vuoto")

    os.makedirs(os.path.dirname(zipped_file_path), exist_ok=True)

    with zipfile.ZipFile(zipped_file_path, "w", zipfile.ZIP_DEFLATED) as z:
        for file_path in files_to_zip:
            if not os.path.isfile(file_path):
                raise bad_request(f"File non trovato: {file_path}")

            z.write(file_path, arcname=os.path.basename(file_path))