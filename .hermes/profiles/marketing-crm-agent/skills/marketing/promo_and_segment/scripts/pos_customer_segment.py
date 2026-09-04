"""marketing-crm-agent용 Mock POS 고객 세그먼트 조회 레퍼런스 스크립트.

code_execution 샌드박스에서 이 파일을 그대로 실행하거나, 함수를 복사해 필요한 값만
바꿔 호출한다. 이 프로필은 Mock POS를 읽기 전용(GET)으로만 호출한다 — messaging
툴셋이 없으므로 이 스크립트로는 아무것도 발송할 수 없다(게이트 1 유지).

주의: code_execution 샌드박스는 프로필의 .env(MOCK_POS_BASE_URL 등)를 자동으로
물려받지 않는다. 그래서 아래 기본값은 docker-compose.yml의 실제 배포 값과 동일하게
하드코딩했다 — Mock POS API Key는 실서비스 비밀값이 아니라 개발용 고정 키(dev-key)
이므로 하드코딩해도 안전하다.
"""
import os

import requests

BASE_URL = os.environ.get("MOCK_POS_BASE_URL", "http://mock-pos:8080")
API_KEY = os.environ.get("MOCK_POS_API_KEY", "dev-key")
STORE_ID = os.environ.get("STORE_ID", "store_demo")
HEADERS = {"X-API-Key": API_KEY}


def get_repeat_customers(period: str = "all", min_orders: int = 2) -> list[dict]:
    """period: today|week|month|all. min_orders 이상 주문한 고객만 반환한다."""
    resp = requests.get(
        f"{BASE_URL}/v1/stores/{STORE_ID}/reports/repeat-customers",
        headers=HEADERS,
        params={"period": period, "min_orders": min_orders},
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    customers = get_repeat_customers("all", 2)
    if not customers:
        print("현재 2회 이상 재구매한 고객이 없습니다.")
    else:
        for c in customers:
            label = c["name"] or c["customer_id"]
            print(f"{label}: 주문 {c['order_count']}건, 누적 결제액 {c['total_spent']}원")
