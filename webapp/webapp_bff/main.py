"""웹앱 BFF 진입점.

5개 화면(고객 문의/주문 접수/재고 관리/예약 관리/대시보드) + mock-pos 읽기 전용
프록시 + 에이전트 릴레이를 하나의 FastAPI 앱으로 묶는다. `/health`만 인증 없이
열어둔다(mock_pos/main.py와 동일한 관례 — 컨테이너 헬스체크용).
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from webapp_bff.routers import agent, pages, pos_proxy

app = FastAPI(title="TriAgent_SMB Webapp")

app.mount("/static", StaticFiles(directory="webapp_bff/static"), name="static")

app.include_router(pages.router)
app.include_router(pos_proxy.router)
app.include_router(agent.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
