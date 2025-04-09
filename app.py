import os
import sqlite3
import subprocess

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/recover', methods=['POST'])
def handle_dump():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Dati JSON non forniti"}), 400

    db_path = data['db_path']

    original_dir, original_filename = os.path.split(db_path)

    db_recovered_path = ''

    if "And" in original_filename:
        db_recovered_path = os.path.join(original_dir, 'AndDbTouch.s3db')
    elif "DbBackup" in original_filename:
        db_recovered_path = os.path.join(original_dir, 'TouchBull.s3db')
    elif "Prod" in original_filename or "DbProduct" in original_filename:
        db_recovered_path = db_path

    try:
        subprocess.run(
            f"sqlite3 {db_path} '.recover' | sqlite3 {db_recovered_path}",
            shell=True,
            check=True
        )

        os.replace(db_recovered_path, db_path)
        conn = sqlite3.connect(db_path)
        if "And" in db_path:
            with conn:
                conn.execute("DELETE FROM Eventi WHERE ID < (SELECT MAX(ID) FROM Eventi) - 300000")
                conn.execute("DELETE FROM EventiSup WHERE ID < (SELECT MAX(ID) FROM EventiSup) - 150000")
                conn.execute("DELETE FROM Param WHERE ID < (SELECT MAX(ID) FROM Param) - 10")
                conn.execute("DELETE FROM Frigo WHERE ID < (SELECT MAX(ID) FROM Frigo) - 50000")
                conn.execute("DELETE FROM LogVendita WHERE ID < (SELECT MAX(ID) FROM LogVendita) - 75000")

        conn.execute("PRAGMA auto_vacuum = FULL")
        conn.execute("VACUUM")
        conn.close()

        if "And" in original_filename:
            os.rename(db_path, os.path.join(original_dir, 'AndDbTouch.s3db'))
        elif "DbBackup" in original_filename:
            os.rename(db_path, os.path.join(original_dir, 'TouchBull.s3db'))

        return jsonify({"result": 0}), 200

    except (sqlite3.Error, OSError) as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()