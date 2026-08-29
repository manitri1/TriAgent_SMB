"""docs/13-mvp-dashboard-design.md §3.3: /health를 제외한 모든 경로(API + 정적 프론트엔드
번들)가 basic-auth 뒤에 있어야 한다. 라우터별 Depends가 아니라 미들웨어로 구현해야
StaticFiles(SPA 정적 파일)도 함께 보호된다 — 브라우저는 최상위 문서 요청에서 401을 받으면
네이티브 로그인 다이얼로그를 띄우고, 이후 같은 오리진의 fetch 요청에도 자격증명을
자동으로 재사용한다(기존 Hermes 대시보드의 dashboard.basic_auth와 동일한 방식).

자격증명은 환경변수(DASHBOARD_BASIC_AUTH_USER/_PASSWORD)로 주입되며, 호출 시점에 읽어
테스트에서 monkeypatch하기 쉽게 한다 (mock-pos/auth.py의 os.environ.get 패턴과 동일).
"""
import base64
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

UNAUTHORIZED_HEADERS = {"WWW-Authenticate": 'Basic realm="SMB Dashboard"'}


def _credentials_valid(username: str, password: str) -> bool:
    expected_user = os.environ.get("DASHBOARD_BASIC_AUTH_USER", "owner")
    expected_password = os.environ.get("DASHBOARD_BASIC_AUTH_PASSWORD", "smb-dashboard-dev-2026")
    return secrets.compare_digest(username, expected_user) and secrets.compare_digest(
        password, expected_password
    )


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        header = request.headers.get("authorization")
        if header and header.lower().startswith("basic "):
            try:
                decoded = base64.b64decode(header[6:]).decode("utf-8")
                username, _, password = decoded.partition(":")
            except (ValueError, UnicodeDecodeError):
                username, password = "", ""
            if _credentials_valid(username, password):
                return await call_next(request)

        return Response(status_code=401, headers=UNAUTHORIZED_HEADERS)
