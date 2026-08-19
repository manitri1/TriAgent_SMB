"""reservation-agent용 Mock POS 호출 레퍼런스 스크립트.

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


def create_reservation(
    customer_id: str,
    datetime_iso: str,
    service: str | None = None,
    note: str | None = None,
) -> dict:
    """datetime_iso 예시: '2026-08-20T14:00:00+09:00' (ISO 8601, 타임존 포함 권장)."""
    resp = requests.post(
        f"{BASE_URL}/v1/stores/{STORE_ID}/reservations",
        headers=HEADERS,
        json={"customer_id": customer_id, "datetime": datetime_iso, "service": service, "note": note},
    )
    resp.raise_for_status()
    return resp.json()


def list_reservations(date: str | None = None, status: str | None = None) -> list[dict]:
    """date: 'YYYY-MM-DD' (해당 날짜 예약만), status: 'BOOKED'|'CANCELED'. 둘 다 생략하면 전체."""
    params = {k: v for k, v in {"date": date, "status": status}.items() if v is not None}
    resp = requests.get(
        f"{BASE_URL}/v1/stores/{STORE_ID}/reservations", headers=HEADERS, params=params
    )
    resp.raise_for_status()
    return resp.json()


def get_reservation(reservation_id: str) -> dict:
    resp = requests.get(
        f"{BASE_URL}/v1/stores/{STORE_ID}/reservations/{reservation_id}", headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()


def cancel_reservation(reservation_id: str) -> dict:
    resp = requests.patch(
        f"{BASE_URL}/v1/stores/{STORE_ID}/reservations/{reservation_id}",
        headers=HEADERS,
        json={"status": "CANCELED"},
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    reservation = create_reservation("cust_demo", "2026-08-20T14:00:00+09:00", service="컷트")
    print("예약 생성:", reservation["reservation_id"], reservation["status"])
    fetched = get_reservation(reservation["reservation_id"])
    print("예약 조회:", fetched["datetime"], fetched["status"])
    today_list = list_reservations(status="BOOKED")
    print(f"현재 BOOKED 예약 {len(today_list)}건")
