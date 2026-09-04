from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Catalog ---

class CatalogItemCreate(BaseModel):
    item_id: str
    name: str
    unit_price: int
    category: Optional[str] = None
    initial_stock: int = 0
    low_stock_threshold: int = 5
    cost: int = 0


class CatalogItem(BaseModel):
    item_id: str
    name: str
    unit_price: int
    category: Optional[str] = None
    cost: int = 0


# --- Orders ---

class OrderLineItemIn(BaseModel):
    item_id: str
    quantity: int
    note: Optional[str] = None


class OrderLineItem(OrderLineItemIn):
    unit_price: int
    subtotal: int


class OrderCreate(BaseModel):
    line_items: List[OrderLineItemIn]
    customer_id: Optional[str] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None  # COMPLETED | CANCELED


class Order(BaseModel):
    order_id: str
    store_id: str
    status: str = "OPEN"  # OPEN | COMPLETED | CANCELED | PARTIALLY_REFUNDED | REFUNDED
    line_items: List[OrderLineItem]
    total_amount: int
    currency: str = "KRW"
    customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


# --- Payments ---

class PaymentCreate(BaseModel):
    order_id: str
    method: str = "CARD"


class RefundRequest(BaseModel):
    amount: Optional[int] = None
    reason: Optional[str] = None


class Payment(BaseModel):
    payment_id: str
    store_id: str
    order_id: str
    amount: int
    currency: str = "KRW"
    status: str = "COMPLETED"  # COMPLETED | PARTIALLY_REFUNDED | REFUNDED
    method: str = "CARD"
    refunded_amount: int = 0
    created_at: datetime = Field(default_factory=utcnow)
    refunded_at: Optional[datetime] = None


# --- Inventory ---

class InventoryItem(BaseModel):
    item_id: str
    stock_quantity: int
    low_stock_threshold: int = 5
    updated_at: datetime = Field(default_factory=utcnow)


class InventoryAdjust(BaseModel):
    delta: int
    reason: Optional[str] = None


# --- Reservations ---

class ReservationCreate(BaseModel):
    customer_id: str
    datetime: datetime
    service: Optional[str] = None
    note: Optional[str] = None


class ReservationUpdate(BaseModel):
    status: Optional[str] = None  # CANCELED
    datetime: Optional[datetime] = None


class Reservation(BaseModel):
    reservation_id: str
    store_id: str
    customer_id: str
    datetime: datetime
    service: Optional[str] = None
    status: str = "BOOKED"  # BOOKED | CANCELED
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


# --- Reports ---

class SalesSummary(BaseModel):
    store_id: str
    period: str
    order_count: int
    total_sales: int
    currency: str = "KRW"


class SettlementReport(BaseModel):
    store_id: str
    period: str
    gross_sales: int
    payment_count: int
    refunded_amount: int = 0
    refunded_count: int = 0
    partial_refund_amount: int = 0
    partial_refund_count: int = 0
    currency: str = "KRW"


class TopItem(BaseModel):
    item_id: str
    name: str
    quantity: int
    revenue: int
    cost: int = 0
    margin: int = 0


class DailySales(BaseModel):
    date: str
    order_count: int
    total_sales: int


class MarginSummary(BaseModel):
    store_id: str
    period: str
    total_revenue: int
    total_cost: int
    gross_margin: int
    margin_rate: float
    currency: str = "KRW"


# --- Customers (CRM MVP) ---

class CustomerCreate(BaseModel):
    customer_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class Customer(BaseModel):
    customer_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    order_count: int = 0
    total_spent: int = 0
    last_order_at: Optional[datetime] = None


class RepeatCustomer(BaseModel):
    customer_id: str
    name: Optional[str] = None
    order_count: int
    total_spent: int
    last_order_at: Optional[datetime] = None
