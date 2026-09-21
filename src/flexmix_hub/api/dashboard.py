"""Prototype operator pages. The machine and operator APIs remain separate."""

import hmac
import hashlib
import secrets
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from flexmix_hub.api.overview import overview
from flexmix_hub.infrastructure.database.session import get_session
from flexmix_hub.modules.catalogue.models import (
    CatalogueDrink,
    CatalogueIngredient,
    CatalogueRecipeAction,
    DesiredStateMeta,
)
from flexmix_hub.modules.commands.models import MachineCommand
from flexmix_hub.modules.events.models import MachineOrderEvent
from flexmix_hub.modules.backups.models import BackupMetadata

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")
COOKIE = "flexmix_dashboard_session"
_PASSWORDS = PasswordHasher()

# Routes describe the operator workflow; pages without a backing model state
# plainly that their workflow is not available in this prototype.
NAV_GROUPS = (
    ("🏪 Cửa hàng", (("Danh sách cửa hàng", "store-list"), ("Cài đặt cửa hàng", "store-settings"))),
    ("🤖 Máy", (("Danh sách máy", "machine-fleet"), ("Đăng ký / Cấp phát máy", "provision-enroll"))),
    ("🥤 Sản phẩm", (("Nguyên liệu", "ingredients"), ("Đồ uống", "drinks"), ("Công thức", "recipes"))),
    ("📋 Thực đơn", (("Thực đơn hiện tại", "current-menu"), ("Xuất bản", "publish-menu"), ("Lịch sử phiên bản", "version-history"))),
    ("📦 Đơn hàng", (("Đơn hàng", "orders"),)),
    ("⚠️ Vận hành", (("Lỗi", "errors"), ("Lệnh", "commands"), ("Giám sát", "monitoring"))),
    ("💾 Sao lưu", (("Trạng thái", "backup-status"), ("Lịch sử", "backup-history"), ("Khôi phục", "restore"))),
    ("🚀 Phiên bản & Cập nhật", (("Phiên bản & Cập nhật máy", "releases"),)),
    ("⚙️ Quản trị", (("Người dùng", "users"), ("Vai trò & Quyền hạn", "roles-permissions"), ("Cài đặt hệ thống", "system-settings"), ("Nhật ký kiểm toán", "audit-log"))),
)
PAGES = {slug: (group, label) for group, items in NAV_GROUPS for label, slug in items}
# Retain old UI URLs for bookmarks, while deliberately keeping them out of the sidebar.
PAGES.update({
    "machine-detail": ("🤖 Máy", "Chi tiết máy"),
    "machine-health": ("🤖 Máy", "Sức khỏe máy"),
    "order-events": ("📦 Đơn hàng", "Sự kiện đơn hàng"),
    "machine-updates": ("🚀 Phiên bản & Cập nhật", "Phiên bản & Cập nhật máy"),
})


def _key(request: Request) -> bytes:
    configured = request.app.state.settings.admin_password_hash
    material = configured.get_secret_value() if configured is not None else ""
    return hmac.new(b"flexmix-dashboard-session", material.encode(), "sha256").digest()


def _valid(request: Request) -> bool:
    value = request.cookies.get(COOKIE, "")
    parts = value.split(".", 1)
    return len(parts) == 2 and hmac.compare_digest(
        parts[1], hmac.new(_key(request), parts[0].encode(), hashlib.sha256).hexdigest()
    )


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(request: Request):
    form = parse_qs((await request.body()).decode("utf-8", "ignore"))
    supplied_username = form.get("username", [""])[0]
    supplied_password = form.get("password", [""])[0]
    settings = request.app.state.settings
    expected_username = settings.admin_username
    expected_hash = settings.admin_password_hash
    valid = expected_username is not None and expected_hash is not None
    if valid:
        valid = secrets.compare_digest(supplied_username, expected_username)
        try:
            valid = valid and _PASSWORDS.verify(expected_hash.get_secret_value(), supplied_password)
        except (VerificationError, VerifyMismatchError, InvalidHashError, TypeError):
            valid = False
    if not valid:
        raise HTTPException(401, "Tên đăng nhập hoặc mật khẩu không đúng")
    nonce = secrets.token_urlsafe(24)
    proof = hmac.new(_key(request), nonce.encode(), hashlib.sha256).hexdigest()
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        COOKIE, f"{nonce}.{proof}", httponly=True, secure=request.url.scheme == "https",
        samesite="lax", max_age=3600,
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE)
    return response


@router.get("/")
def dashboard(request: Request, session: Session = Depends(get_session)):
    if not _valid(request):
        return RedirectResponse("/login", status_code=303)

    machines = overview(None, session)["machines"]
    version = session.get(DesiredStateMeta, 1).version
    drinks = session.scalars(select(CatalogueDrink).order_by(CatalogueDrink.id)).all()
    ingredients = session.scalars(select(CatalogueIngredient).order_by(CatalogueIngredient.id)).all()
    events = session.scalars(
        select(MachineOrderEvent).order_by(MachineOrderEvent.id.desc()).limit(5)
    ).all()
    commands = session.scalars(
        select(MachineCommand).order_by(MachineCommand.id.desc()).limit(5)
    ).all()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "machines": machines,
            "nav_groups": NAV_GROUPS,
            "active_page": "dashboard",
            "version": version,
            "drinks": drinks,
            "ingredients": ingredients,
            "events": events,
            "commands": commands,
            "online_count": sum(machine["online"] for machine in machines),
            "event_count": sum(machine["event_count"] for machine in machines),
            "stale_count": sum(machine["backup_stale"] for machine in machines),
            "failed_count": sum(machine["command_counts"].get("failed", 0) for machine in machines),
            "pending_count": sum(machine["command_counts"].get("pending", 0) for machine in machines),
            "missing_backup_count": sum(machine["backup_age_seconds"] is None for machine in machines),
        },
    )


@router.get("/admin/{page}")
def admin_page(page: str, request: Request, session: Session = Depends(get_session)):
    if not _valid(request):
        return RedirectResponse("/login", status_code=303)
    if page not in PAGES:
        raise HTTPException(404, "Unknown admin page")

    group, title = PAGES[page]
    context = {
        "nav_groups": NAV_GROUPS,
        "active_page": page,
        "page": page,
        "group": group,
        "title": title,
        "machines": [],
        "ingredients": [],
        "drinks": [],
        "recipes": [],
        "events": [],
        "commands": [],
        "backups": [],
        "version": None,
        "selected_machine": None,
        "has_data": False,
    }
    if page in {"machine-fleet", "machine-detail", "machine-health", "monitoring", "backup-status"}:
        context["machines"] = overview(None, session)["machines"]
        context["has_data"] = True
        if page == "machine-detail":
            raw_mid = request.query_params.get("mid")
            if raw_mid and raw_mid.isdecimal():
                context["selected_machine"] = next(
                    (machine for machine in context["machines"] if machine["mid"] == int(raw_mid)), None
                )
    if page in {"ingredients", "current-menu"}:
        context["ingredients"] = session.scalars(select(CatalogueIngredient).order_by(CatalogueIngredient.id)).all()
        context["has_data"] = True
    if page in {"drinks", "current-menu"}:
        context["drinks"] = session.scalars(select(CatalogueDrink).order_by(CatalogueDrink.id)).all()
        context["has_data"] = True
    if page == "recipes":
        context["recipes"] = session.scalars(
            select(CatalogueRecipeAction).order_by(
                CatalogueRecipeAction.drink_id, CatalogueRecipeAction.step_no
            )
        ).all()
        context["has_data"] = True
    if page in {"current-menu", "version-history", "publish-menu"}:
        context["version"] = session.get(DesiredStateMeta, 1).version
        context["has_data"] = page == "current-menu"
    if page in {"orders", "order-events"}:
        context["events"] = session.scalars(select(MachineOrderEvent).order_by(MachineOrderEvent.id.desc()).limit(50)).all()
        context["has_data"] = True
    if page in {"commands", "machine-detail"}:
        context["commands"] = session.scalars(select(MachineCommand).order_by(MachineCommand.id.desc()).limit(50)).all()
        context["has_data"] = page in {"commands", "machine-detail"}
    if page in {"backup-history", "machine-detail"}:
        context["backups"] = session.scalars(select(BackupMetadata).order_by(BackupMetadata.id.desc()).limit(50)).all()
        context["has_data"] = page in {"backup-history", "machine-detail"}
    return templates.TemplateResponse(request, "admin_page.html", context)
