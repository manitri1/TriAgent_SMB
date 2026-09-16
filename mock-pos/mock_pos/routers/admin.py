"""데모/리허설용 목업 데이터 초기화 엔드포인트.

다른 라우터와 달리 "지금 있는 데이터를 전부 지우고 다시 채운다"는 파괴적
동작을 수행한다 — 실제 매장 운영 데이터를 다루는 경로가 아니라 시연/개발
준비 전용이다. 매장별(store_id) 격리는 다른 라우터와 동일하게 유지된다.
"""
from fastapi import APIRouter, Depends, HTTPException

from mock_pos import seed
from mock_pos.auth import verify_api_key
from mock_pos.models import SeedRequest, SeedResult

router = APIRouter(
    prefix="/v1/stores/{store_id}/admin",
    tags=["admin"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/seed", response_model=SeedResult)
def seed_store(store_id: str, payload: SeedRequest):
    if payload.mode == "quick":
        result = seed.run_quick_seed(store_id)
    elif payload.mode == "month":
        result = seed.run_month_seed(store_id)
    else:
        raise HTTPException(status_code=400, detail="mode must be 'quick' or 'month'")
    return SeedResult(**result)
