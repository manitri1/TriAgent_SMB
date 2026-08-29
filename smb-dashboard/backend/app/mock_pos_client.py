"""Mock POS REST API 프록시 클라이언트. CORS가 mock-pos에 설정되어 있지 않아
(docs/13-mvp-dashboard-design.md §1) 브라우저가 직접 호출할 수 없으므로, 이 백엔드가
서버 사이드에서 대신 호출한다.
"""
import os
from typing import Optional

import httpx
from fastapi import HTTPException

BASE_URL = os.environ.get("MOCK_POS_BASE_URL", "http://mock-pos:8080")
API_KEY = os.environ.get("MOCK_POS_API_KEY", "dev-key")
STORE_ID = os.environ.get("STORE_ID", "store_demo")
HEADERS = {"X-API-Key": API_KEY}
TIMEOUT = 10.0


async def _get(path: str, params: Optional[dict] = None) -> dict | list:
    url = f"{BASE_URL}/v1/stores/{STORE_ID}{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="재고/주문 서비스에 일시적으로 연결할 수 없습니다") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"재고/주문 서비스 오류: {exc.response.status_code}") from exc


async def list_orders(status: Optional[str] = None) -> list[dict]:
    params = {"status": status} if status else {}
    return await _get("/orders", params=params)  # type: ignore[return-value]


async def list_inventory() -> list[dict]:
    return await _get("/inventory")  # type: ignore[return-value]


async def list_reservations(date: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    params = {k: v for k, v in {"date": date, "status": status}.items() if v}
    return await _get("/reservations", params=params)  # type: ignore[return-value]


async def sales_summary(period: str = "today") -> dict:
    return await _get("/reports/sales", params={"period": period})  # type: ignore[return-value]
