"""sales-analytics-agent용 Mock POS 호출 레퍼런스 스크립트.

code_execution 샌드박스에서 이 파일을 그대로 실행하거나, 함수를 복사해 필요한 값만
바꿔 호출한다.

주의(2026-08-19 실측): code_execution 샌드박스는 프로필의 .env(MOCK_POS_BASE_URL 등)를
자동으로 물려받지 않는다. 그래서 아래 기본값은 docker-compose.yml의 실제 배포 값과
동일하게 하드코딩했다 — Mock POS API Key는 실서비스 비밀값이 아니라 개발용 고정 키(dev-key)
이므로 하드코딩해도 안전하다. 다른 값을 쓰려면 환경변수로 덮어쓸 수 있다.
"""
import os

import requests

BASE_URL = os.environ.get("MOCK_POS_BASE_URL", "http://mock-pos:8080")
API_KEY = os.environ.get("MOCK_POS_API_KEY", "dev-key")
STORE_ID = os.environ.get("STORE_ID", "store_demo")
HEADERS = {"X-API-Key": API_KEY}


def get_sales_summary(period: str = "today") -> dict:
    """period: today|week|month|all"""
    resp = requests.get(
        f"{BASE_URL}/v1/stores/{STORE_ID}/reports/sales", headers=HEADERS, params={"period": period}
    )
    resp.raise_for_status()
    return resp.json()


def get_settlement_report(period: str = "today") -> dict:
    resp = requests.get(
        f"{BASE_URL}/v1/stores/{STORE_ID}/reports/settlement",
        headers=HEADERS,
        params={"period": period},
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    sales = get_sales_summary("today")
    settlement = get_settlement_report("today")
    print(f"오늘 매출: {sales['total_sales']}원 (주문 {sales['order_count']}건)")
    print(f"오늘 정산: 총매출 {settlement['gross_sales']}원, 결제 {settlement['payment_count']}건")
