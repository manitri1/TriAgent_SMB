"""테스트 전용 환경변수를 앱 import 전에 설정한다.

webapp_bff.config는 import 시점에 환경변수를 읽으므로(모듈 최상위의
`settings = _load()`), pytest가 webapp_bff.main을 처음 import하기 전에
반드시 이 conftest가 먼저 실행되어 필요한 환경변수를 채워야 한다.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.hash_password import hash_password  # noqa: E402

TEST_USERNAME = "test-admin"
TEST_PASSWORD = "test-password-123"

os.environ.setdefault("WEBAPP_BASIC_AUTH_USERNAME", TEST_USERNAME)
os.environ.setdefault("WEBAPP_BASIC_AUTH_PASSWORD_HASH", hash_password(TEST_PASSWORD))
os.environ.setdefault("MOCK_POS_BASE_URL", "http://mock-pos-test.invalid")
os.environ.setdefault("MOCK_POS_API_KEY", "test-key")
os.environ.setdefault("STORE_ID", "store_test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from webapp_bff.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def auth_headers() -> dict:
    import base64

    token = base64.b64encode(f"{TEST_USERNAME}:{TEST_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}
