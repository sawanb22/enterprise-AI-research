"""Local development launcher that also supports the workspace-installed packages."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BACKEND_DIR.parent
LOCAL_PACKAGES = BACKEND_DIR / ".packages"

if LOCAL_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_PACKAGES))
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn  # noqa: E402


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
