import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mock_pos import self_heal
from mock_pos.routers import admin, catalog, customers, dashboard, inventory, orders, payments, reports, reservations


# "오늘 데이터 없음"(대시보드 매출/리포트 0) 자가치유 — MOCK_POS_SELF_HEAL_ENABLED=true
# 로만 켠다(docker-compose 전용). 명시적 opt-in이라 pytest는 이 환경변수를 설정하지
# 않으므로 테스트 스위트는 영향받지 않는다.
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("MOCK_POS_SELF_HEAL_ENABLED", "false").lower() == "true":
        store_id = os.environ.get("STORE_ID", "store_demo")
        self_heal.run_self_heal_once(store_id)  # 기동 즉시 한 번 채워, 다음 점검(1시간 뒤)까지 기다리지 않게 한다
        task = asyncio.create_task(self_heal.self_heal_loop(store_id))
        yield
        task.cancel()
    else:
        yield


app = FastAPI(
    title="Mock POS API",
    description="docs/05-skills-and-tools.md 기반 소상공인 AX 에이전트 시스템용 Mock POS 시뮬레이터",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(catalog.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(inventory.router)
app.include_router(reservations.router)
app.include_router(reports.router)
app.include_router(customers.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
