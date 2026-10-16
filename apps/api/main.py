"""
LeaseGuard FastAPI Application Entrypoint
Full-Stack PropTech & Applied AI Backend for Athens, GA Renters
"""

import importlib.util
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.config import ALLOWED_ORIGINS, SAMPLE_LEASE_PATH
from apps.api.routes import leases, disputes


def split_origins(origins: List[str]) -> Tuple[List[str], str]:
    """Split ALLOWED_ORIGINS into exact origins and a regex covering wildcard entries like https://*.vercel.app."""
    exact = [o for o in origins if "*" not in o]
    wild = [re.escape(o).replace(r"\*", r"[A-Za-z0-9\-]+") for o in origins if "*" in o]
    return exact, "|".join(wild) if wild else ""


def ensure_sample_lease() -> None:
    """Generate the sample PDF if the image/checkout does not already contain it."""
    if os.path.exists(SAMPLE_LEASE_PATH):
        return
    script = Path(__file__).resolve().parents[2] / "packages" / "sample-data" / "generate_sample_lease.py"
    spec = importlib.util.spec_from_file_location("generate_sample_lease", str(script))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.generate_athens_sample_lease(str(SAMPLE_LEASE_PATH))


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_sample_lease()
    leases.get_auditor()  # builds the statute store (pgvector or SQLite fallback) and BM25/vector index at startup
    yield


app = FastAPI(
    title="LeaseGuard API",
    description="Applied AI and PropTech Statutory Lease Auditor & Deposit Shield for Athens, Georgia",
    version="1.0.0",
    lifespan=lifespan,
)

_exact, _regex = split_origins(ALLOWED_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_exact,
    allow_origin_regex=_regex or None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(leases.router)
app.include_router(disputes.router)


@app.get("/api/v1/health")
@app.get("/health", include_in_schema=False)
def health_check():
    retriever = leases.get_auditor().retriever
    return {
        "status": "ok",
        "statutes_loaded": len(retriever.statutes),
        "sample_pdf_ready": os.path.exists(SAMPLE_LEASE_PATH),
        "storage_mode": retriever.storage_mode,
    }


if __name__ == "__main__":
    import uvicorn
    from apps.api.config import API_HOST, API_PORT
    uvicorn.run("apps.api.main:app", host=API_HOST, port=API_PORT)
