# services/software_detector.py
import os
from utils.errors import bad_request


def software_detector_by_name(name: str) -> str:
    n = name.lower()

    name.startswith

    if "andbkfarma" in n:
        return "farmax"
    if "andbk" in n:
        return "android"
    if "dbbackup" in n:
        return "windows"

    return "unknown"


def detect_software_type(unzip_dir: str) -> str:
    if not unzip_dir:
        raise bad_request("unzip_dir mancante")

    if not os.path.isdir(unzip_dir):
        raise bad_request(f"Cartella non valida: {unzip_dir}")

    files = os.listdir(unzip_dir)

    for filename in files:
        detected = software_detector_by_name(filename)
        if detected != "unknown":
            return detected

    raise bad_request("Unable to detect software type")
