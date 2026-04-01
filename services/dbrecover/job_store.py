# dbrecover/job_store.py
from threading import Lock
from uuid import uuid4

_jobs = {}
_jobs_lock = Lock()


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
    return job


def get_job(job_id: str):
    with _jobs_lock:
        return _jobs.get(job_id)


def update_job(job_id: str, **patch):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        job.update(patch)
        return job
