from fastapi import FastAPI

from mock_pos.routers import catalog, inventory, orders, payments, reports, reservations

app = FastAPI(
    title="Mock POS API",
    description="docs/05-skills-and-tools.md 기반 소상공인 AX 에이전트 시스템용 Mock POS 시뮬레이터",
    version="0.1.0",
)

app.include_router(catalog.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(inventory.router)
app.include_router(reservations.router)
app.include_router(reports.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
