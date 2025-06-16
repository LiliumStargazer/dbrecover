import os
import sqlite3
import subprocess
import tempfile

from flask import Flask, request, jsonify

app = Flask(__name__)



@app.route('/integrity_check', methods=['POST'])
def handle_integrity_check():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dati JSON non forniti"}), 400
    try:
        paths = initialize_backup_paths(data)  # Ottieni le variabili condivise
        db_original_path = paths["db_original_path"]
        db_prod_original_path= paths["db_prod_original_path"]
        integrity_check(db_original_path)
        integrity_check(db_prod_original_path)

        return jsonify({"result": 0}), 200

    except (sqlite3.Error, OSError) as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Errore generico: {str(e)}"}), 500


@app.route('/recover', methods=['POST'])
def handle_check():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dati JSON non forniti"}), 400
    try:
        paths = initialize_backup_paths(data)  # Ottieni le variabili condivise
        db_original_path = paths["db_original_path"]
        db_recovered_path = paths["db_recovered_path"]
        db_prod_original_path= paths["db_prod_original_path"]
        db_prod_recovered_path = paths["db_prod_recovered_path"]
        remove_recovered_files(db_prod_recovered_path, db_recovered_path)
        recover(db_original_path, db_recovered_path)
        clean_and_optimize_database(db_recovered_path)
        integrity_check(db_recovered_path)
        recover(db_prod_original_path, db_prod_recovered_path)
        integrity_check(db_prod_recovered_path)
        print("Database: OK ")
        return jsonify({"result": 0}), 200

    except (sqlite3.Error, OSError) as e:
        print("Error: ", e)
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        print("Error: ", e)
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        print("Error: ", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print("Error: ", e)
        return jsonify({"error": f"Errore generico: {str(e)}"}), 500

def initialize_backup_paths(data):
    """Inizializza le variabili e i percorsi dei file in base ai dati forniti."""
    serial = data.get('serial')
    backup = data.get('backup')

    if not serial or not backup:
        raise ValueError("Dati mancanti: 'serial' o 'backup' non forniti")

    db_folder_name = backup.replace(".zip", "")  # Rimuove l'estensione .zip
    db_dir_path = os.path.join('/backups', serial, db_folder_name)

    # Determinazione dei nomi dei file in base al tipo di backup
    if "AndBk" in backup:
        db_filename = "AndBk.s3db"
        db_prod_filename = "ProdDbTouch.s3db"
        db_recovered_path = os.path.join(db_dir_path, 'AndDbTouch.s3db')
    elif "DbBackup" in backup:
        db_filename = "DbBackup.s3db"
        db_prod_filename = "DbProduct.s3db"
        db_recovered_path = os.path.join(db_dir_path, 'TouchBull.s3db')
    elif "LastBkValid" in backup:
        if os.path.isfile(os.path.join(db_dir_path, 'AndBk.s3db')):
            db_filename = "AndBk.s3db"
            db_prod_filename = "ProdDbTouch.s3db"
            db_recovered_path = os.path.join(db_dir_path, 'AndDbTouch.s3db')
        else :
            db_filename = "DbBackup.s3db"
            db_prod_filename = "DbProduct.s3db"
            db_recovered_path = os.path.join(db_dir_path, 'TouchBull.s3db')
    else:
        raise ValueError("Backup non presente o tipo backup non riconosciuto")

    db_original_path = os.path.join(db_dir_path, db_filename)
    db_prod_original_path = os.path.join(db_dir_path, db_prod_filename)
    db_prod_recovered_path = os.path.join(db_dir_path, 'ProdRecovered.s3db')

    if not os.path.isfile(db_original_path):
        raise FileNotFoundError("Il file originale del database non è stato trovato")

    # Restituisci tutte le variabili calcolate come dizionario
    return {
        "serial": serial,
        "backup": backup,
        "db_folder_name": db_folder_name,
        "db_dir_path": db_dir_path,
        "db_filename": db_filename,
        "db_prod_filename": db_prod_filename,
        "db_recovered_path": db_recovered_path,
        "db_original_path": db_original_path,
        "db_prod_original_path": db_prod_original_path,
        "db_prod_recovered_path": db_prod_recovered_path,
    }

def remove_recovered_files(db_prod_recovered_path, db_recovered_path):
    if os.path.isfile(db_recovered_path):  # se il file del database di recupero è già esistente  lo rimuovo.
        os.remove(db_recovered_path)
    if os.path.isfile(db_prod_recovered_path):  # se il file di recupero dei prodotti è già esistente lo rimuovo.
        os.remove(db_prod_recovered_path)

def clean_and_optimize_database(db_path):
    if "And" in db_path:
        conn = sqlite3.connect(db_path)
        try:
            # Controlla se "And" è nel percorso e pulisce le tabelle corrispondenti

            with conn:
                conn.execute("DELETE FROM Eventi WHERE ID < (SELECT MAX(ID) FROM Eventi) - 300000")
                conn.execute("DELETE FROM EventiSup WHERE ID < (SELECT MAX(ID) FROM EventiSup) - 150000")
                conn.execute("DELETE FROM Param WHERE ID < (SELECT MAX(ID) FROM Param) - 10")
                conn.execute("DELETE FROM Frigo WHERE ID < (SELECT MAX(ID) FROM Frigo) - 50000")
                conn.execute("DELETE FROM LogVendita WHERE ID < (SELECT MAX(ID) FROM LogVendita) - 75000")

            # Ottimizzazione del database
            conn.execute("PRAGMA auto_vacuum = FULL")
            conn.execute("VACUUM")
        finally:
            # Chiude sempre la connessione
            conn.close()

def recover(db_original_path, db_recovered_path):
    with tempfile.NamedTemporaryFile(delete=False) as temp_sql:
        temp_sql_name = temp_sql.name
    try:
        subprocess.run(
            f"sqlite3 {db_original_path} '.recover --ignore-freelist' | grep -v 'sqlite_sequence' > {temp_sql_name}",
            shell=True,
            check=True
        )
        subprocess.run(
            f"sqlite3 {db_recovered_path} < {temp_sql_name}",
            shell=True,
            check=True
        )
    finally:
        if os.path.exists(temp_sql_name):
            os.remove(temp_sql_name)


def dump(db_original_path, db_recovered_path):
    with tempfile.NamedTemporaryFile(delete=False) as temp_dump:
        temp_dump_name = temp_dump.name
    try:
        subprocess.run(
            f"sqlite3 {db_original_path} '.dump' > {temp_dump_name}",
            shell=True,
            check=True
        )
        subprocess.run(
            f"sqlite3 {db_recovered_path} < {temp_dump_name}",
            shell=True,
            check=True
        )
    finally:
        if os.path.exists(temp_dump_name):
            os.remove(temp_dump_name)


def integrity_check(db_recovered_path):
    result = subprocess.run(
        f"sqlite3 {db_recovered_path} 'PRAGMA integrity_check;'",
        shell=True,
        check=True,
        capture_output=True,
        text=True
    )
    if "ok" not in result.stdout.strip().lower():
        raise Exception(f"Integrity check failed for {db_recovered_path}: {result.stdout.strip()}")


if __name__ == '__main__':
    app.run()