# dbrecover/routes.py
from threading import Thread
from flask import Blueprint, request, jsonify

from utils.errors import bad_request, to_http_response
from .job_store import create_job, get_job
from .recover_worker import run_recover_job

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
        daemon=True,
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
