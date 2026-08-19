"""order-payment-agent용 Mock POS 호출 레퍼런스 스크립트.

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


def list_catalog() -> list[dict]:
    resp = requests.get(f"{BASE_URL}/v1/stores/{STORE_ID}/catalog/items", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def create_order(line_items: list[dict], customer_id: str | None = None) -> dict:
    resp = requests.post(
        f"{BASE_URL}/v1/stores/{STORE_ID}/orders",
        headers=HEADERS,
        json={"line_items": line_items, "customer_id": customer_id},
    )
    resp.raise_for_status()
    return resp.json()


def pay_order(order_id: str, method: str = "CARD") -> dict:
    """결제 성공 시 주문이 COMPLETED로 전환되고 재고가 자동 차감된다.
    재고 부족이면 requests.HTTPError(409)가 발생한다 — 임의로 수량을 줄여 재시도하지 않는다.
    """
    resp = requests.post(
        f"{BASE_URL}/v1/stores/{STORE_ID}/payments",
        headers=HEADERS,
        json={"order_id": order_id, "method": method},
    )
    resp.raise_for_status()
    return resp.json()


def get_order(order_id: str) -> dict:
    resp = requests.get(f"{BASE_URL}/v1/stores/{STORE_ID}/orders/{order_id}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def refund_payment(payment_id: str) -> dict:
    """coordinator의 게이트 3(환불/취소) 승인 이후에만 호출한다.
    성공 시 결제가 REFUNDED로 전환되고 재고가 원상 복구된다. 이미 환불된 결제를 다시
    환불하려 하면 requests.HTTPError(409)가 발생한다.
    """
    resp = requests.post(
        f"{BASE_URL}/v1/stores/{STORE_ID}/payments/{payment_id}/refund", headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    catalog = list_catalog()
    print(f"카탈로그 {len(catalog)}개 품목 조회됨")
    if catalog:
        item = catalog[0]
        order = create_order([{"item_id": item["item_id"], "quantity": 1}])
        print("주문 생성:", order["order_id"], order["status"], order["total_amount"])
        payment = pay_order(order["order_id"])
        print("결제 완료:", payment["payment_id"], payment["status"])
        refunded = refund_payment(payment["payment_id"])
        print("환불 완료:", refunded["payment_id"], refunded["status"])
