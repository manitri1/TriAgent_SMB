import uuid

from fastapi import APIRouter, Depends, HTTPException

from mock_pos.auth import verify_api_key
from mock_pos.models import Reservation, ReservationCreate, ReservationUpdate
from mock_pos.store import store

router = APIRouter(
    prefix="/v1/stores/{store_id}/reservations",
    tags=["reservations"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=Reservation, status_code=201)
def create_reservation(store_id: str, payload: ReservationCreate):
    data = store.get(store_id)
    reservation = Reservation(
        reservation_id=f"resv_{uuid.uuid4().hex[:12]}",
        store_id=store_id,
        customer_id=payload.customer_id,
        datetime=payload.datetime,
        service=payload.service,
        note=payload.note,
    )
    data.reservations[reservation.reservation_id] = reservation.model_dump()
    return reservation


@router.get("", response_model=list[Reservation])
def list_reservations(store_id: str, date: str | None = None, status: str | None = None):
    """date: YYYY-MM-DD (예약 datetime의 날짜 부분과 일치하는 것만 반환). status: BOOKED|CANCELED."""
    data = store.get(store_id)
    items = list(data.reservations.values())
    if date:
        items = [r for r in items if r["datetime"].date().isoformat() == date]
    if status:
        items = [r for r in items if r["status"] == status]
    return items


@router.get("/{reservation_id}", response_model=Reservation)
def get_reservation(store_id: str, reservation_id: str):
    data = store.get(store_id)
    reservation = data.reservations.get(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@router.patch("/{reservation_id}", response_model=Reservation)
def update_reservation(store_id: str, reservation_id: str, payload: ReservationUpdate):
    data = store.get(store_id)
    reservation = data.reservations.get(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if payload.status is not None:
        if payload.status != "CANCELED":
            raise HTTPException(status_code=400, detail="status can only be set to CANCELED")
        reservation["status"] = payload.status

    if payload.datetime is not None:
        reservation["datetime"] = payload.datetime

    return reservation
