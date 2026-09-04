"""HTTP Basic Auth — 자체 scrypt 해시 검증.

.hermes/config.yaml의 dashboard.basic_auth 패턴(scrypt)을 참고하되, 이 웹앱은
Hermes의 plugins.dashboard_auth.basic 모듈에 접근할 수 없으므로 표준 라이브러리
hashlib.scrypt로 독립 구현한다 — Hermes 대시보드 계정과 공유하지 않는다.
"""
import base64
import binascii
import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from webapp_bff.config import settings

security = HTTPBasic()


def _verify_scrypt(password: str, encoded_hash: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, hash_b64 = encoded_hash.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, binascii.Error):
        return False

    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
    )
    return hmac.compare_digest(derived, expected)


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    username_ok = secrets.compare_digest(credentials.username, settings.basic_auth_username)
    password_ok = _verify_scrypt(credentials.password, settings.basic_auth_password_hash)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
