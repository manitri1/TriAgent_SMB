"""mock-pos에 대한 서버 측 전용 클라이언트.

X-API-Key는 여기서만 쓰이고 브라우저로는 절대 전달되지 않는다 — 브라우저는
same-origin `/api/pos/...`만 호출한다(webapp_bff/routers/pos_proxy.py).
"""
import httpx

from webapp_bff.config import settings


class PosClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=f"{settings.mock_pos_base_url}/v1/stores/{settings.store_id}",
            headers={"X-API-Key": settings.mock_pos_api_key},
            timeout=10.0,
        )

    def get(self, path: str, params: dict | None = None) -> httpx.Response:
        return self._client.get(path, params=params)

    def post(self, path: str, json: dict | None = None) -> httpx.Response:
        return self._client.post(path, json=json)

    def close(self) -> None:
        self._client.close()


pos_client = PosClient()
