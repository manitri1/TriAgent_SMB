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
    return templates.TemplateResponse(request, "home.html", {"active": None})


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
