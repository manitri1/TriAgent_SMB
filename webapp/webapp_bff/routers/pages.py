"""화면 라우트."""
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from webapp_bff.auth import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])
templates = Jinja2Templates(directory="webapp_bff/templates")

# 컨테이너 기동 시점마다 바뀌는 값 — /static/* 링크에 ?v=<ASSET_VERSION>으로 붙여
# 배포할 때마다 브라우저의 정적 파일(특히 app.css, chat.js 등 JS) 캐시가 확실히
# 무효화되게 한다. 실전에서 겪은 문제: 캐시된 구버전 chat.js가 남아있으면
# 데모 큐 기능이 반영되지 않고도 페이지가 "정상"으로 보여 원인 파악이 어려웠다.
ASSET_VERSION = str(int(time.time()))
templates.env.globals["v"] = ASSET_VERSION


@router.get("/")
def index():
    return RedirectResponse(url="/dashboard")


@router.get("/home")
def home_page(request: Request):
    return templates.TemplateResponse(request, "home.html", {"active": "home"})


@router.get("/inventory")
def inventory_page(request: Request):
    return templates.TemplateResponse(request, "inventory.html", {"active": "inventory"})


@router.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active": "dashboard"})


@router.get("/support")
def support_page(request: Request):
    return templates.TemplateResponse(request, "support.html", {"active": "support"})


@router.get("/orders")
def orders_page(request: Request):
    return templates.TemplateResponse(request, "orders.html", {"active": "orders"})


@router.get("/reservations")
def reservations_page(request: Request):
    return templates.TemplateResponse(request, "reservations.html", {"active": "reservations"})


@router.get("/live-demo")
def live_demo_page(request: Request):
    return templates.TemplateResponse(request, "live_demo.html", {"active": "live-demo"})


@router.get("/live-demo/customer")
def customer_live_demo_page(request: Request):
    return templates.TemplateResponse(request, "customer_live_demo.html", {"active": "customer-live-demo"})


# ── 고객 화면 미리보기(데모) — 실제 손님용 공개 서비스가 아니라, 같은 직원
# 인증 뒤에서 "손님이라면 이렇게 보일 것"을 보여주는 시연용 화면이다. 그래서
# 별도 인증 모델 없이 기존 require_auth를 그대로 쓰고, mode="customer"만
# 넘겨 base.html이 톤/네비게이션을 다르게 렌더링하게 한다.

@router.get("/customer")
def customer_home_page(request: Request):
    return templates.TemplateResponse(request, "customer_home.html", {"active": "customer-home", "mode": "customer"})


@router.get("/customer/faq")
def customer_faq_page(request: Request):
    return templates.TemplateResponse(request, "customer_faq.html", {"active": "customer-faq", "mode": "customer"})


@router.get("/customer/order")
def customer_order_page(request: Request):
    return templates.TemplateResponse(request, "customer_order.html", {"active": "customer-order", "mode": "customer"})


@router.get("/customer/reservation")
def customer_reservation_page(request: Request):
    return templates.TemplateResponse(
        request, "customer_reservation.html", {"active": "customer-reservation", "mode": "customer"}
    )
