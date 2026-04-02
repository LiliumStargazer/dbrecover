# .services/dbrecover/routes.py
from threading import Thread
from flask import Blueprint, request, jsonify


from utils.errors import bad_request, to_http_response
from .job_store import create_job, get_job
from .recover_worker import run_recover_job
from services.dbrecover.integrity_worker import run_integrity_check_job

bp = Blueprint("dbrecover_api", __name__)


@bp.route("/recover", methods=["POST"])
def recover_route():
    data = request.get_json(silent=True)
    if not data:
        return to_http_response(bad_request("Dati JSON non forniti"))

    serial = data.get("serial")
    backup = data.get("backup")

    if not serial:
        return to_http_response(bad_request("Serial non valida"))
    if not backup:
        return to_http_response(bad_request("Backup non valido"))

    job = create_job(serial, backup)

    thread = Thread(
        target=run_recover_job,
        args=(job["jobId"], serial, backup),
        daemon=False,
    )
    thread.start()

    return (
        jsonify(
            {
                "success": True,
                "jobId": job["jobId"],
                "status": job["status"],
            }
        ),
        202,
    )


@bp.route("/recover/<job_id>", methods=["GET"])
def recover_status_route(job_id):
    print(f"[recover-status] requested job_id={job_id}")

    job = get_job(job_id)

    if not job:
        print(f"[recover-status] job not found: {job_id}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Job non trovato",
                }
            ),
            404,
        )

    print(f"[recover-status] found job: {job}")
    return jsonify(job), 200


@bp.route("/integrity_check", methods=["POST"])
def integrity_check_route():
    data = request.get_json(silent=True)
    if not data:
        return to_http_response(bad_request("Dati JSON non forniti"))

    serial = data.get("serial")
    backup = data.get("backup")

    if not serial:
        return to_http_response(bad_request("Serial non valida"))
    if not backup:
        return to_http_response(bad_request("Backup non valido"))

    job = create_job(serial, backup)

    thread = Thread(
        target=run_integrity_check_job,
        args=(job["jobId"], serial, backup),
        daemon=False,
    )
    thread.start()

    return (
        jsonify(
            {
                "success": True,
                "jobId": job["jobId"],
                "status": job["status"],
            }
        ),
        202,
    )


@bp.route("/integrity_check/<job_id>", methods=["GET"])
def integrity_check_status_route(job_id):
    job = get_job(job_id)

    if not job:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Job non trovato",
                }
            ),
            404,
        )

    return jsonify(job), 200
