# services/dbrecover/job_store.py
import os
import threading
from threading import Lock
from uuid import uuid4

_jobs = {}
_jobs_lock = Lock()


def _ctx():
    return f"pid={os.getpid()} tid={threading.get_ident()} jobs={len(_jobs)}"


def create_job(serial: str, backup: str):
    job_id = uuid4().hex
    job = {
        "jobId": job_id,
        "serial": serial,
        "backup": backup,
        "status": "queued",
        "step": "queued",
        "progress": 0,
        "error": None,
    }
    with _jobs_lock:
        _jobs[job_id] = job
        print(f"[job-store:create] {_ctx()} job_id={job_id}")
    return job


def get_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        print(f"[job-store:get] {_ctx()} job_id={job_id} found={job is not None}")
        return job


def update_job(job_id: str, **patch):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            print(
                f"[job-store:update] {_ctx()} job_id={job_id} NOT_FOUND patch={patch}"
            )
            return None
        job.update(patch)
        print(f"[job-store:update] {_ctx()} job_id={job_id} patch={patch}")
        return job
