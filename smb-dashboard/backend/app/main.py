from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth import BasicAuthMiddleware
from app.routers import approvals, inventory, orders, reports, reservations

app = FastAPI(
    title="SMB Dashboard API",
    description="docs/13-mvp-dashboard-design.md 기반 SMB 사장님용 커스텀 대시보드 백엔드",
    version="0.1.0",
)
app.add_middleware(BasicAuthMiddleware)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


# API 라우터를 먼저 등록해야 한다 — Starlette는 등록 순서대로 경로를 매칭하므로,
# 아래 StaticFiles(SPA fallback)가 "/api/*"를 가로채지 않으려면 반드시 이보다 먼저 와야 한다.
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(reservations.router)
app.include_router(reports.router)
app.include_router(approvals.router)

_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
