# services/paths.py
from __future__ import annotations

import os
from dataclasses import dataclass
import tempfile
from typing import Literal, TypedDict
from utils.errors import bad_request, not_found


def default_backups_root() -> str:
    # Directory temporanea cross-platform:
    # macOS: /var/folders/...
    # Linux: /tmp
    # Windows: %TEMP%
    base = tempfile.gettempdir()
    # Cartella dedicata all'app per evitare casino nel temp
    return os.path.join(base, "dbrecover")


BACKUPS_ROOT = os.environ.get("BACKUPS_ROOT", default_backups_root())

SoftwareType = Literal["android", "windows", "farmax"]


# -------------------------
# Typed return structures
# -------------------------
class FtpPaths(TypedDict):
    zip: str
    out_dir: str
    update_dir: str
    recovered_with_finger_zip: str


class LocalPaths(TypedDict):
    zip: str
    unzip_dir: str
    recovered_zip: str
    recovered_with_finger_zip: str


class BackupPaths(TypedDict):
    ftp: FtpPaths
    local: LocalPaths


class DbPaths(TypedDict):
    logs_db: str
    products_db: str
    finger_db: str
    recovery_db: str


# -------------------------
# Base paths
# -------------------------
@dataclass(frozen=True, slots=True)
class BasePaths:
    """
    Costruisce i path "base" (FTP e locali) per un serial.
    Nota: i path FTP sono stringhe POSIX-style (con /), quindi li componiamo manualmente.
    I path locali usano os.path.join.
    """

    backups_root: str
    serial: str

    # ------- LOCAL -------
    @property
    def local_serial_root(self) -> str:
        return os.path.join(self.backups_root, self.serial)

    @property
    def local_zips_dir(self) -> str:
        return os.path.join(self.local_serial_root, "zips")

    @property
    def local_unzipped_dir(self) -> str:
        return os.path.join(self.local_serial_root, "unzipped")

    def local_backup_zip(self, backup_zip_name: str) -> str:
        return os.path.join(self.local_zips_dir, backup_zip_name)

    def local_backup_unzip_dir(self, backup_zip_name: str) -> str:
        # cartella dove estrarre (usa il nome zip senza .zip)
        folder = strip_zip_ext(backup_zip_name)
        return os.path.join(self.local_unzipped_dir, folder)

    # ------- FTP (POSIX) -------
    @property
    def ftp_serial_root(self) -> str:
        return f"/{self.serial}"

    @property
    def ftp_config_dir(self) -> str:
        return f"{self.ftp_serial_root}/config"

    @property
    def ftp_out_dir(self) -> str:
        return f"{self.ftp_config_dir}/Out"

    @property
    def ftp_update_dir(self) -> str:
        return f"{self.ftp_serial_root}/update/DB.zip"

    def ftp_backup_zip(self, backup_zip_name: str) -> str:
        return f"{self.ftp_config_dir}/{backup_zip_name}"

    def ftp_out_zip(self, filename: str) -> str:
        return f"{self.ftp_out_dir}/{filename}"


def build_base_paths(serial: str, backups_root: str = BACKUPS_ROOT) -> BasePaths:
    serial = (serial or "").strip()
    if not serial:
        raise bad_request("Serial mancante")

    backups_root = (backups_root or "").strip()
    if not backups_root:
        raise bad_request("backups_root mancante")

    # Assicura che la directory esista (e quindi sia scrivibile)
    os.makedirs(backups_root, exist_ok=True)

    return BasePaths(backups_root=backups_root, serial=serial)


# -------------------------
# Backup paths
# -------------------------
def build_backup_paths(base: BasePaths, backup_zip_name: str) -> BackupPaths:
    backup_zip_name = (backup_zip_name or "").strip()
    if not backup_zip_name:
        raise bad_request("Backup mancante")

    local_zip = base.local_backup_zip(backup_zip_name)
    unzip_dir = base.local_backup_unzip_dir(backup_zip_name)

    return {
        "ftp": {
            "zip": base.ftp_backup_zip(backup_zip_name),
            "out_dir": base.ftp_out_dir,
            "update_dir": base.ftp_update_dir,
            "recovered_with_finger_zip": base.ftp_out_zip("DBAndFinger.zip"),
        },
        "local": {
            # zip scaricato (pre-unzip)
            "zip": local_zip,
            # cartella estrazione
            "unzip_dir": unzip_dir,
            # zip finali creati (post-process)
            "recovered_zip": os.path.join(unzip_dir, "DB.zip"),
            "recovered_with_finger_zip": os.path.join(unzip_dir, "DBAndFinger.zip"),
        },
    }


# -------------------------
# DB paths inside unzip dir
# -------------------------
def resolve_db_paths(unzip_dir: str, software_type: str) -> DbPaths:
    unzip_dir = (unzip_dir or "").strip()
    if not unzip_dir:
        raise bad_request("unzip_dir mancante")

    if software_type == "android":
        return {
            "logs_db": os.path.join(unzip_dir, "AndBk.s3db"),
            "products_db": os.path.join(unzip_dir, "ProdDbTouch.s3db"),
            "finger_db": os.path.join(unzip_dir, "fingerRead.s3db"),
            "recovery_db": os.path.join(unzip_dir, "AndDbTouch.s3db"),
        }

    if software_type == "windows":
        return {
            "logs_db": os.path.join(unzip_dir, "DbBackup.s3db"),
            "products_db": os.path.join(unzip_dir, "DbProduct.s3db"),
            "finger_db": os.path.join(unzip_dir, "DbRFinger.s3db"),
            "recovery_db": os.path.join(unzip_dir, "TouchBull.s3db"),
        }

    if software_type == "farmax":
        return {
            "logs_db": os.path.join(unzip_dir, "AndBkFarma.s3db"),
            "products_db": os.path.join(unzip_dir, "ProdDbTouch.s3db"),
            "finger_db": os.path.join(unzip_dir, "fingerRead.s3db"),
            "recovery_db": os.path.join(unzip_dir, "AndDbTouch.s3db"),
        }

    raise bad_request(f"software_type non supportato: {software_type}")


# -------------------------
# Small helpers
# -------------------------
def strip_zip_ext(name: str) -> str:
    # rimuove solo l'ultima occorrenza finale ".zip" (case-insensitive)
    if name.lower().endswith(".zip"):
        return name[:-4]
    return name


def ensure_file_exists(path_: str, msg: str) -> None:
    if not os.path.isfile(path_):
        raise not_found(msg)
