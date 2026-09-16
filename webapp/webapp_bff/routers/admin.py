"""목업 데이터 초기화 릴레이 — 데모/리허설 준비용 관리자 기능.

`pos_proxy.py`는 구조적으로 GET만 등록해야 한다(그 파일 docstring 참고 — 대시
보드는 조회 전용이라는 원칙, `test_pos_proxy_never_registers_a_write_route`로
고정됨). 이 엔드포인트는 그 원칙의 예외다: 목업 데이터 재시드는 "업무 결정"이
아니라 "시연/개발 환경 초기화"라 애초에 coordinator가 승인·위임할 대상이
아니다(승인할 "결정"이 없다 — 사람이 이미 버튼을 눌러 명시적으로 요청한
행위이고, 되돌릴 결과도 실제 매장 데이터가 아니라 목업 데이터다). 그래서
coordinator를 거치지 않고 mock-pos를 직접 호출하되, pos_proxy.py와는 별도
파일로 분리해 그 파일의 "쓰기 없음" 구조적 보증을 건드리지 않는다.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from webapp_bff.auth import require_auth
from webapp_bff.pos_client import pos_client

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_auth)])

_ALLOWED_MODES = {"quick", "month"}


class SeedIn(BaseModel):
    mode: str = "quick"


@router.post("/seed-mock-data")
def seed_mock_data(payload: SeedIn):
    if payload.mode not in _ALLOWED_MODES:
        raise HTTPException(status_code=400, detail="mode must be 'quick' or 'month'")

    resp = pos_client.post("/admin/seed", json={"mode": payload.mode})
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
