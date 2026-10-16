"""
Lease Analysis Routes for LeaseGuard
Instant sample analysis, uploaded-PDF analysis, and SSE streaming of the live audit pipeline.
"""

import json
import os
import tempfile
from typing import Iterator, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from apps.api.config import SAMPLE_LEASE_PATH, MAX_UPLOAD_BYTES
from apps.api.models.lease import LeaseAuditResponse
from apps.api.services.lease_auditor import LeaseAuditorService

router = APIRouter(prefix="/api/v1/leases", tags=["leases"])

_auditor: Optional[LeaseAuditorService] = None

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def get_auditor() -> LeaseAuditorService:
    global _auditor
    if _auditor is None:
        _auditor = LeaseAuditorService()
    return _auditor


async def _read_upload(upload: UploadFile) -> Tuple[str, str]:
    """Validate and persist an uploaded PDF to a temp file. Returns (path, filename)."""
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"PDF exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="Uploaded file is not a PDF")
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix="lease_upload_")
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    return path, os.path.basename(upload.filename or "uploaded_lease.pdf")


def _sample_path() -> str:
    if not os.path.exists(SAMPLE_LEASE_PATH):
        raise HTTPException(status_code=404, detail="Sample lease PDF not found")
    return str(SAMPLE_LEASE_PATH)


@router.get("/sample", response_model=LeaseAuditResponse)
def get_sample_lease_audit():
    """Runs the full audit pipeline on the bundled Athens student lease (zero login)."""
    return get_auditor().audit_lease(_sample_path(), "athens_student_lease_sample.pdf")


@router.post("/analyze", response_model=LeaseAuditResponse)
async def analyze_lease(file: Optional[UploadFile] = File(None)):
    """Synchronously audits an uploaded PDF (multipart field `file`), or the sample lease when none is sent."""
    path, name, temp = (None, None, False)
    if file is not None:
        path, name = await _read_upload(file)
        temp = True
    else:
        path, name = _sample_path(), "athens_student_lease_sample.pdf"
    try:
        return get_auditor().audit_lease(path, name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        if temp:
            os.unlink(path)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _stream(path: str, name: str, cleanup: bool):
    def run() -> Iterator[str]:
        yield _sse("progress", {"stage": "START", "message": f"Auditing {name}"})
        try:
            for kind, payload in get_auditor().pipeline(path, name):
                if kind == "progress":
                    yield _sse("progress", payload)
                elif kind == "clause":
                    yield _sse("clause_analyzed", payload.model_dump())
                else:
                    yield _sse("complete", payload.model_dump())
        except ValueError as exc:
            yield _sse("error", {"detail": str(exc)})
        except Exception as exc:  # never leave the client hanging on an open stream
            yield _sse("error", {"detail": f"Audit failed: {type(exc).__name__}"})
        finally:
            if cleanup and os.path.exists(path):
                os.unlink(path)

    async for chunk in iterate_in_threadpool(run()):
        yield chunk


@router.get("/analyze-stream")
async def analyze_lease_stream_get():
    """SSE audit of the bundled sample lease (EventSource-friendly)."""
    return StreamingResponse(_stream(_sample_path(), "athens_student_lease_sample.pdf", False),
                             media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/analyze-stream")
async def analyze_lease_stream_post(file: Optional[UploadFile] = File(None)):
    """SSE audit of an uploaded PDF (multipart field `file`); falls back to the sample lease when none is sent."""
    if file is None:
        return StreamingResponse(_stream(_sample_path(), "athens_student_lease_sample.pdf", False),
                                 media_type="text/event-stream", headers=SSE_HEADERS)
    path, name = await _read_upload(file)
    return StreamingResponse(_stream(path, name, True), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/sample-pdf")
async def download_sample_pdf():
    """Serves the sample Athens student lease PDF for download or inline viewing."""
    return FileResponse(_sample_path(), media_type="application/pdf", filename="athens_student_lease_sample.pdf")
