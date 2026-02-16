# dbrecover/services/sqlite_ops.py
import os
import sqlite3
import subprocess
import tempfile

from utils.errors import bad_request, internal_error


def remove_recovered_files(db_prod_recovered_path: str, db_recovered_path: str) -> None:
    if os.path.isfile(db_recovered_path):
        os.remove(db_recovered_path)
    if os.path.isfile(db_prod_recovered_path):
        os.remove(db_prod_recovered_path)


def clean_and_optimize_database(db_path: str) -> None:
    # mantiene lo stesso comportamento del tuo codice: pulisce solo se "And" è nel path
    if "And" not in db_path:
        return

    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.execute(
                "DELETE FROM Eventi WHERE ID < (SELECT MAX(ID) FROM Eventi) - 300000"
            )
            conn.execute(
                "DELETE FROM EventiSup WHERE ID < (SELECT MAX(ID) FROM EventiSup) - 150000"
            )
            conn.execute(
                "DELETE FROM Param WHERE ID < (SELECT MAX(ID) FROM Param) - 10"
            )
            conn.execute(
                "DELETE FROM Frigo WHERE ID < (SELECT MAX(ID) FROM Frigo) - 50000"
            )
            conn.execute(
                "DELETE FROM LogVendita WHERE ID < (SELECT MAX(ID) FROM LogVendita) - 75000"
            )

        conn.execute("PRAGMA auto_vacuum = FULL")
        conn.execute("VACUUM")
    finally:
        conn.close()


def recover(db_original_path: str, db_recovered_path: str) -> None:
    same_target = os.path.abspath(db_original_path) == os.path.abspath(
        db_recovered_path
    )

    tmp_db: str | None = None
    target_db = db_recovered_path

    if same_target:
        fd, tmp_db = tempfile.mkstemp(suffix=".s3db")
        os.close(fd)
        target_db = tmp_db

    temp_sql_name: str | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_sql:
            temp_sql_name = temp_sql.name

        result = subprocess.run(
            ["sqlite3", db_original_path, ".recover --ignore-freelist"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        filtered = "\n".join(
            line for line in result.stdout.splitlines() if "sqlite_sequence" not in line
        )
        with open(temp_sql_name, "w") as out_file:
            out_file.write(filtered)

        with open(temp_sql_name, "r") as in_file:
            subprocess.run(
                ["sqlite3", target_db],
                stdin=in_file,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

        if same_target:
            os.replace(target_db, db_recovered_path)
            # dopo replace, il tmp_db “non esiste più” come file separato
            tmp_db = None

    except subprocess.CalledProcessError as e:
        raise internal_error(f"Errore sqlite recover: {e.stderr or str(e)}")

    except FileNotFoundError:
        raise internal_error("sqlite3 non trovato nel sistema")

    finally:
        if temp_sql_name and os.path.exists(temp_sql_name):
            os.remove(temp_sql_name)

        if tmp_db and os.path.exists(tmp_db):
            try:
                os.remove(tmp_db)
            except Exception:
                pass


def dump(db_original_path: str, db_recovered_path: str) -> None:
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_dump:
        temp_dump_name = temp_dump.name

    try:
        # genera dump
        result = subprocess.run(
            ["sqlite3", db_original_path, ".dump"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        with open(temp_dump_name, "w") as f:
            f.write(result.stdout)

        # importa dump nel db recovered
        with open(temp_dump_name, "r") as f:
            subprocess.run(
                ["sqlite3", db_recovered_path],
                stdin=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

    except subprocess.CalledProcessError as e:
        raise internal_error(f"Errore sqlite dump/import: {e.stderr or str(e)}")

    except FileNotFoundError:
        raise internal_error("sqlite3 non trovato nel sistema")

    finally:
        if os.path.exists(temp_dump_name):
            os.remove(temp_dump_name)


def integrity_check(db_path: str) -> None:
    try:
        result = subprocess.run(
            ["sqlite3", db_path, "PRAGMA integrity_check;"],
            check=True,
            capture_output=True,
            text=True,
        )

    except FileNotFoundError:
        raise internal_error("sqlite3 non trovato nel sistema")

    except subprocess.CalledProcessError as e:
        raise internal_error(f"Errore eseguendo integrity_check: {e.stderr or str(e)}")

    output = (result.stdout or "").strip().lower()

    if output != "ok":
        raise bad_request(f"Integrity check failed for {db_path}: {output}")
