"""환경변수 설정. 하드코딩된 비밀값은 두지 않는다 — MOCK_POS_API_KEY와
WEBAPP_BASIC_AUTH_PASSWORD_HASH는 반드시 환경변수로 주입한다."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mock_pos_base_url: str
    mock_pos_api_key: str
    store_id: str
    hermes_container_name: str
    hermes_bin_path: str
    hermes_exec_timeout_seconds: int
    basic_auth_username: str
    basic_auth_password_hash: str


def _load() -> Settings:
    password_hash = os.environ.get("WEBAPP_BASIC_AUTH_PASSWORD_HASH")
    if not password_hash:
        raise RuntimeError(
            "WEBAPP_BASIC_AUTH_PASSWORD_HASH가 설정되지 않았습니다. "
            "webapp/scripts/hash_password.py '<비밀번호>'로 생성해 환경변수로 넣어주세요."
        )
    return Settings(
        mock_pos_base_url=os.environ.get("MOCK_POS_BASE_URL", "http://mock-pos:8080"),
        mock_pos_api_key=os.environ.get("MOCK_POS_API_KEY", "dev-key"),
        store_id=os.environ.get("STORE_ID", "store_demo"),
        hermes_container_name=os.environ.get("HERMES_CONTAINER_NAME", "hermes-triagent-smb"),
        hermes_bin_path=os.environ.get("HERMES_BIN_PATH", "/opt/hermes/bin/hermes"),
        # Phase 0 실측(2026-09-04): coordinator 중첩 위임이 200초를 넘게 걸린 사례가
        # 있어(curried-percolating-ocean.md 참고) 기본값을 넉넉히 잡는다.
        hermes_exec_timeout_seconds=int(os.environ.get("HERMES_EXEC_TIMEOUT_SECONDS", "500")),
        basic_auth_username=os.environ.get("WEBAPP_BASIC_AUTH_USERNAME", "admin"),
        basic_auth_password_hash=password_hash,
    )


settings = _load()
