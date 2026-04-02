import os
import shutil
import sqlite3
import tempfile

from services.ftp import connect_sftp
from services.path import build_backup_paths, build_base_paths, resolve_db_paths
from services.software_detector import detect_software_type
from services.sqlite_ops import integrity_check
from services.zip_utils import unzip_backup
from utils.errors import AppError

from .job_store import update_job


def run_integrity_check_job(job_id: str, serial: str, backup: str):
    work_dir = tempfile.mkdtemp(prefix=f"integrity_{job_id}_")

    try:
        update_job(job_id, status="running", step="preparing", progress=5)

        basepath = build_base_paths(serial)
        paths = build_backup_paths(basepath, backup)

        local_zip = os.path.join(work_dir, "backup.zip")
        unzip_dir = os.path.join(work_dir, "unzipped")

        os.makedirs(unzip_dir, exist_ok=True)

        update_job(job_id, step="downloading_backup", progress=20)
        sftp = connect_sftp()
        sftp.download(paths["ftp"]["zip"], local_zip)
        sftp.close()

        update_job(job_id, step="unzipping_backup", progress=40)
        unzip_backup(local_zip, unzip_dir)

        update_job(job_id, step="detecting_software", progress=60)
        softwaretype = detect_software_type(unzip_dir)
        db_paths = resolve_db_paths(unzip_dir, softwaretype)

        update_job(job_id, step="checking_logs_db", progress=80)
        integrity_check(db_paths["logs_db"])

        update_job(job_id, step="checking_products_db", progress=90)
        integrity_check(db_paths["products_db"])

        update_job(job_id, status="done", step="completed", progress=100)

    except AppError as e:
        update_job(job_id, status="error", error=str(e))
    except (sqlite3.Error, OSError) as e:
        update_job(job_id, status="error", error=str(e))
    except Exception as e:
        update_job(job_id, status="error", error=f"Errore generico: {str(e)}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
