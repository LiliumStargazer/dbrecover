# /services/dbrecover/recover_worker.py


import os
import shutil
import sqlite3
import tempfile

from services.fs_ops import purge_dir_contents
from services.ftp import connect_sftp
from services.path import build_backup_paths, build_base_paths, resolve_db_paths
from services.software_detector import detect_software_type
from services.sqlite_ops import (
    recover,
    clean_and_optimize_database,
    integrity_check,
)
from services.zip_utils import create_zip_file, unzip_backup
from utils.errors import AppError

from .job_store import update_job


def run_recover_job(job_id: str, serial: str, backup: str):
    work_dir = tempfile.mkdtemp(prefix=f"dbrecover_{job_id}_")

    try:
        update_job(job_id, status="running", step="preparing", progress=5)

        source_basepath = build_base_paths(serial)
        source_paths = build_backup_paths(source_basepath, backup)

        local_zip = os.path.join(work_dir, "backup.zip")
        unzip_dir = os.path.join(work_dir, "unzipped")
        recovered_db = os.path.join(work_dir, "recovered.db")
        recovered_products_db = os.path.join(work_dir, "products.db")
        recovered_zip = os.path.join(work_dir, "recovered.zip")

        os.makedirs(unzip_dir, exist_ok=True)

        update_job(job_id, step="downloading_backup", progress=15)
        sftp = connect_sftp()
        sftp.download(source_paths["ftp"]["zip"], local_zip)
        sftp.close()

        update_job(job_id, step="unzipping_backup", progress=30)
        unzip_backup(local_zip, unzip_dir)

        update_job(job_id, step="detecting_software", progress=40)
        softwaretype = detect_software_type(unzip_dir)
        db_paths = resolve_db_paths(unzip_dir, softwaretype)

        update_job(job_id, step="recovering_logs_db", progress=55)
        recover(db_paths["logs_db"], recovered_db)

        update_job(job_id, step="checking_recovered_logs_db", progress=65)
        integrity_check(recovered_db)

        update_job(job_id, step="optimizing_recovered_logs_db", progress=72)
        clean_and_optimize_database(recovered_db)

        update_job(job_id, step="recovering_products_db", progress=80)
        recover(db_paths["products_db"], recovered_products_db)

        update_job(job_id, step="checking_products_db", progress=88)
        integrity_check(recovered_products_db)

        update_job(job_id, step="creating_zip", progress=93)
        create_zip_file([recovered_db, recovered_products_db], recovered_zip)

        update_job(job_id, step="uploading_zip", progress=97)
        sftp = connect_sftp()
        sftp.upload(recovered_zip, source_basepath.ftp_update_dir)
        sftp.close()

        update_job(job_id, status="done", step="completed", progress=100)

    except AppError as e:
        update_job(job_id, status="error", error=str(e))
    except (sqlite3.Error, OSError) as e:
        update_job(job_id, status="error", error=str(e))
    except Exception as e:
        update_job(job_id, status="error", error=f"Errore generico: {str(e)}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


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

        update_job(job_id, step="detecting_software", progress=55)
        softwaretype = detect_software_type(unzip_dir)
        db_paths = resolve_db_paths(unzip_dir, softwaretype)

        update_job(job_id, step="checking_logs_db", progress=75)
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
