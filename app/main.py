"""FastAPI entrypoint: serves the support console and the API."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from . import config as cfg
from .service import SupportService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Institutional Memory for Support", version="0.1.0")

_service: SupportService | None = None
_service_error: str | None = None


def get_service() -> SupportService:
    global _service, _service_error
    if _service is None:
        try:
            _service = SupportService()
            _service_error = None
        except Exception as exc:  # e.g. missing GROQ_API_KEY
            _service_error = str(exc)
            raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}") from exc
    return _service


@app.get("/api/config")
def config() -> dict[str, Any]:
    return {
        "hindsight_base_url": cfg.HINDSIGHT_BASE_URL,
        "model": cfg.GROQ_MODEL,
        "org_bank_id": cfg.ORG_BANK_ID,
        "seeded": bool(_service and _service.seeded),
        "service_error": _service_error,
        "memory_kind": type(_service.memory).__name__ if _service else None,
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    service = get_service()
    try:
        return {"memory": service.memory.health(), "seeded": service.seeded}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/api/bootstrap")
def bootstrap() -> dict[str, Any]:
    service = get_service()
    with service._lock:
        result = service.seed_history()
    return {"ok": True, **result}


@app.get("/api/customers")
def customers() -> list[dict[str, Any]]:
    return [c.model_dump() for c in get_service().customers.values()]


@app.get("/api/demo-stream")
def demo_stream() -> list[dict[str, Any]]:
    service = get_service()
    return [
        {
            "ticket": t.model_dump(mode="json"),
            "customer": service.customer_for(t.customer_id).model_dump(),
        }
        for t in service.demo_stream()
    ]


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> dict[str, Any]:
    service = get_service()
    ticket = service.ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return {
        "ticket": ticket.model_dump(mode="json"),
        "customer": service.customer_for(ticket.customer_id).model_dump(),
    }


@app.post("/api/tickets/{ticket_id}/process")
def process_ticket(
    ticket_id: str,
    mode: str = Query("memory", pattern="^(memory|amnesia)$"),
) -> dict[str, Any]:
    service = get_service()
    ticket = service.ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    result = service.process(ticket, mode=mode)
    return result.model_dump(mode="json")


@app.get("/api/emerging-issues")
def emerging_issues() -> dict[str, Any]:
    model = get_service().emerging_issues()
    return model.model_dump(mode="json") if model else {}


@app.get("/api/known-issues")
def known_issues() -> dict[str, Any]:
    model = get_service().known_issues()
    return model.model_dump(mode="json") if model else {}


@app.get("/api/regressions")
def regressions() -> dict[str, Any]:
    """Proactive audit: issues believed fixed that are being reported again."""
    return {"regressions": get_service().detect_regressions()}


@app.get("/api/stream")
async def stream(delay: float = 2.0, limit: int = 0) -> StreamingResponse:
    """Replay the demo stream as server-sent events.

    ``limit`` caps how many tickets are emitted (0 = all), so demos stay short.
    """
    service = get_service()
    items = service.demo_stream()
    if limit and limit > 0:
        items = items[:limit]

    async def gen():
        for item in items:
            payload = {
                "ticket": item.model_dump(mode="json"),
                "customer": service.customer_for(item.customer_id).model_dump(),
            }
            yield f"event: ticket\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(delay)
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(cfg.FRONTEND_DIR / "index.html")


def _mount_static() -> None:
    from fastapi.staticfiles import StaticFiles

    if cfg.FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=cfg.FRONTEND_DIR), name="static")


_mount_static()
