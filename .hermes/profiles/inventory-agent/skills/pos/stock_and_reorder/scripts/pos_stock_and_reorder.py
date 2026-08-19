"""inventory-agent용 Mock POS 호출 레퍼런스 스크립트.

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

LOW_STOCK_THRESHOLD = 5  # USER.md에서 매장별로 조정된 값을 사용할 것


def list_inventory() -> list[dict]:
    resp = requests.get(f"{BASE_URL}/v1/stores/{STORE_ID}/inventory", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def get_inventory_item(item_id: str) -> dict:
    resp = requests.get(f"{BASE_URL}/v1/stores/{STORE_ID}/inventory/{item_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def adjust_inventory(item_id: str, delta: int, reason: str | None = None) -> dict:
    """delta는 양수(입고)/음수(출고·폐기). 음수로 재고가 0 미만이 되면 400 오류가 발생한다."""
    resp = requests.post(
        f"{BASE_URL}/v1/stores/{STORE_ID}/inventory/{item_id}/adjust",
        headers=HEADERS,
        json={"delta": delta, "reason": reason},
    )
    resp.raise_for_status()
    return resp.json()


def find_low_stock_items(threshold: int = LOW_STOCK_THRESHOLD) -> list[dict]:
    return [item for item in list_inventory() if item["stock_quantity"] <= threshold]


if __name__ == "__main__":
    low = find_low_stock_items()
    if low:
        print(f"재고 경고 대상 {len(low)}개:")
        for item in low:
            print(f"  - {item['item_id']}: {item['stock_quantity']}개")
    else:
        print("임계치 이하 품목 없음")
