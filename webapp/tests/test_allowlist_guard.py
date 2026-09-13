"""회귀 가드: 이 webapp의 모든 화면(정적 JS + 템플릿)이 /api/agent/message에
보내는 profile은 agent.py의 _ALLOWED_PROFILES(coordinator, customer-service-agent)
안에서만 골라야 한다. order-payment-agent/inventory-agent 등 다른 프로필은
자체 승인(HITL) 채널이 없어, 직접 호출하면 승인 절차가 조용히 무력화된다
(routers/agent.py 상단 주석 참고). 새 화면(고객용 포함)을 추가할 때 실수로
다른 profile을 쓰는 것을 여기서 잡는다.
"""
import re
from pathlib import Path

ALLOWED_PROFILES = {"coordinator", "customer-service-agent"}


def _all_profile_refs() -> set[str]:
    base = Path(__file__).resolve().parent.parent / "webapp_bff"
    profiles: set[str] = set()
    for f in list((base / "static").glob("*.js")) + list((base / "templates").glob("*.html")):
        profiles |= set(re.findall(r'profile:\s*"([^"]+)"', f.read_text(encoding="utf-8")))
    return profiles


def test_all_profile_references_are_allowlisted():
    profiles = _all_profile_refs()
    assert profiles, "profile: \"...\" 참조가 하나도 발견되지 않음 — 검사 패턴이 깨졌을 수 있음"
    assert profiles <= ALLOWED_PROFILES, f"허용되지 않은 profile 발견: {profiles - ALLOWED_PROFILES}"
