"""
Configuration settings for LeaseGuard API (all values overridable via environment variables).
"""

import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Sample data lives in <repo>/packages/sample-data locally; the Docker image sets SAMPLE_DATA_DIR.
SAMPLE_DATA_DIR = Path(os.getenv("SAMPLE_DATA_DIR", str(BASE_DIR / "packages" / "sample-data")))
SAMPLE_LEASE_PATH = SAMPLE_DATA_DIR / "athens_student_lease_sample.pdf"
STATUTES_PATH = SAMPLE_DATA_DIR / "georgia_statutes.json"

# Optional PostgreSQL + pgvector. When unset (or unreachable) the API falls back to SQLite + in-memory index.
DATABASE_URL = os.getenv("DATABASE_URL") or None
SQLITE_PATH = Path(os.getenv("SQLITE_PATH", str(Path(tempfile.gettempdir()) / "leaseguard_local.sqlite3")))

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

DEFAULT_ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",") if o.strip()]

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
