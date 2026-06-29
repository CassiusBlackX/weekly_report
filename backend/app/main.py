"""FastAPI application entrypoint.

Everything is served under settings.base_path (default /weekly_report) so a
single nginx `location` can reverse-proxy the whole app without touching the
lab homepage's other paths. The API lives at {base_path}/api/* and the built
React SPA is served from {base_path}/* with history-fallback to index.html.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .bootstrap import ensure_admin
from .config import settings
from .database import Base, engine
from .scheduler import shutdown_scheduler, start_scheduler
from .routers import auth, cycles, reports, schedules, uploads, users

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_admin()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Weekly Report", lifespan=lifespan, docs_url=None, redoc_url=None)

# ---- API ----
api = APIRouter(prefix=f"{settings.base_path}/api")
api.include_router(auth.router)
api.include_router(users.router)
api.include_router(cycles.router)
api.include_router(reports.router)
api.include_router(uploads.router)
api.include_router(schedules.router)
app.include_router(api)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def root_redirect():
    return RedirectResponse(url=f"{settings.base_path}/")


# ---- Static SPA ----
_dist = settings.frontend_dist
_index = _dist / "index.html"

if (_dist / "assets").is_dir():
    app.mount(
        f"{settings.base_path}/assets",
        StaticFiles(directory=_dist / "assets"),
        name="assets",
    )


@app.get(settings.base_path)
@app.get(f"{settings.base_path}/")
@app.get(f"{settings.base_path}/{{full_path:path}}")
def spa(full_path: str = ""):
    """Serve a real static file if it exists, else the SPA index (history mode)."""
    # Unknown API paths must not fall back to the HTML shell.
    if full_path.startswith("api/"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")
    candidate = (_dist / full_path).resolve()
    if full_path and _dist.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    if _index.is_file():
        return FileResponse(_index)
    return {"detail": "frontend not built"}
