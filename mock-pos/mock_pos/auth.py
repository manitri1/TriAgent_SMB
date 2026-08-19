"""docs/05-skills-and-tools.md 공통 규칙: X-API-Key 헤더 인증 (초안 단계).

MOCK_POS_API_KEY 환경변수가 설정된 경우에만 값 일치를 검증한다.
설정되지 않으면 헤더 존재 여부만 확인한다 (로컬 개발/테스트 편의).
"""
import os

from fastapi import Header, HTTPException, status


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
        )

    expected = os.environ.get("MOCK_POS_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
