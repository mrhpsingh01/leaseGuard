"""
One-command local launcher:  python scripts/dev.py [--install]

Starts FastAPI on :8000 and the Next.js dev server on :3000, and stops both on Ctrl+C.
--install first runs `pip install -r apps/api/requirements.txt` and `npm ci` in apps/web.
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
NPM = shutil.which("npm") or "npm"


def main() -> int:
    if "--install" in sys.argv:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ROOT / "apps/api/requirements.txt")])
        subprocess.check_call([NPM, "ci"], cwd=WEB)

    procs = [
        subprocess.Popen([sys.executable, "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=ROOT),
        subprocess.Popen([NPM, "run", "dev"], cwd=WEB),
    ]
    print("\nLeaseGuard -> http://localhost:3000   (API docs: http://127.0.0.1:8000/docs)\n")
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
