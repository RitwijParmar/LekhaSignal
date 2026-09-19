from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .contracts import OperatorRequest
from .engine import investigate, platform_metrics, sample_timeline

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
app = FastAPI(title="LekhaSignal", docs_url=None, redoc_url=None)
app.mount("/assets", StaticFiles(directory=WEB), name="assets")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lekhasignal", "mode": "deterministic-demo"}


@app.get("/api/overview")
def overview() -> dict:
    return {"metrics": [metric.model_dump() for metric in platform_metrics()], "timeline": sample_timeline()}


@app.post("/api/investigate")
def run_investigation(request: OperatorRequest) -> dict:
    return investigate(request.message).model_dump(mode="json")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB / "index.html")


def run() -> None:
    import uvicorn
    uvicorn.run("lekh_signal.api:app", host="0.0.0.0", port=8080, reload=True)
