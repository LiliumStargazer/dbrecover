# dbrecover/routes.py  (SOLUZIONE A: Blueprint)
import sqlite3
from flask import Blueprint, request, jsonify


from services.fs_ops import purge_dir_contents
from services.ftp import connect_sftp
from services.path import build_backup_paths, build_base_paths, resolve_db_paths
from services.software_detector import detect_software_type
from services.sqlite_ops import (
    remove_recovered_files,
    recover,
    clean_and_optimize_database,
    integrity_check,
)
from services.zip_utils import create_zip_file, unzip_backup
from utils.errors import (
    AppError,
    bad_request,
    internal_error,
    to_http_response,
)

bp = Blueprint("dbrecover_api", __name__)


@bp.route("/integrity_check", methods=["POST"])
def integrity_check_route():
    data = request.get_json(silent=True)
    if not data:
        return to_http_response(bad_request("Dati JSON non forniti"))

    serial = data.get("serial")
    backup = data.get("backup")

    try:
        basepath = build_base_paths(serial)
        paths = build_backup_paths(basepath, backup)
        sftp = connect_sftp()
        sftp.download(paths["ftp"]["zip"], paths["local"]["zip"])
        sftp.close()
        unzip_backup(paths["local"]["zip"], paths["local"]["unzip_dir"])
        softwaretype = detect_software_type(paths["local"]["unzip_dir"])
        db_paths = resolve_db_paths(paths["local"]["unzip_dir"], softwaretype)
        integrity_check(db_paths["logs_db"])
        integrity_check(db_paths["products_db"])
        return jsonify({"result": 0}), 200

    except AppError as e:
        return to_http_response(e)
    except (sqlite3.Error, OSError) as e:
        return to_http_response(internal_error(str(e)))
    except Exception as e:
        return to_http_response(internal_error(f"Errore generico: {str(e)}"))


@bp.route("/recover", methods=["POST"])
def recover_route():
    data = request.get_json(silent=True)

    if not data:
        return to_http_response(bad_request("Dati JSON non forniti"))

    source_serial = data.get("serial")
    source_backup = data.get("backup")

    try:
        source_basepath = build_base_paths(source_serial)
        source_databases_paths = build_backup_paths(source_basepath, source_backup)
        # Rimuove eventuali file recuperati da processi precedenti per evitare che sqlite3 .recover fallisca
        # quindi puliamo tutto prima di cominciare.
        purge_dir_contents(source_databases_paths["local"]["unzip_dir"])

        sftp = connect_sftp()
        sftp.download(
            source_databases_paths["ftp"]["zip"], source_databases_paths["local"]["zip"]
        )
        sftp.close()
        unzip_backup(
            source_databases_paths["local"]["zip"],
            source_databases_paths["local"]["unzip_dir"],
        )
        softwaretype = detect_software_type(
            source_databases_paths["local"]["unzip_dir"]
        )
        source_db_paths = resolve_db_paths(
            source_databases_paths["local"]["unzip_dir"], softwaretype
        )

        recover(source_db_paths["logs_db"], source_db_paths["recovery_db"])
        integrity_check(source_db_paths["recovery_db"])
        clean_and_optimize_database(source_db_paths["recovery_db"])
        recover(source_db_paths["products_db"], source_db_paths["products_db"])
        integrity_check(source_db_paths["products_db"])

        files_to_zip = [source_db_paths["recovery_db"], source_db_paths["products_db"]]
        create_zip_file(files_to_zip, source_databases_paths["local"]["recovered_zip"])

        print(
            f"Backup recuperato e zip creato: {source_databases_paths['local']['recovered_zip']}"
        )
        print(f"source_basepath.ftp_update_dir: {source_basepath.ftp_update_dir}")

        sftp = connect_sftp()
        sftp.upload(
            source_databases_paths["local"]["recovered_zip"],
            source_basepath.ftp_update_dir,
        )
        sftp.close()

        return jsonify({"result": 0}), 200

    except AppError as e:
        return to_http_response(e)
    except (sqlite3.Error, OSError) as e:
        return to_http_response(internal_error(str(e)))
    except Exception as e:
        return to_http_response(internal_error(f"Errore generico: {str(e)}"))
