"""C0.2: kiểm routing bản 2 và ROUTE_POLICY."""

from __future__ import annotations

import re
import string

from server.config import routing

PATHS = {name: value for name, value in vars(routing).items()
         if name.endswith("_PATH") and isinstance(value, str)}
AGENT_PATHS = {name: value for name, value in PATHS.items() if name.startswith("AGENT_")}
PLACEHOLDERS = {"machine_id", "menu_id", "command_id", "sha256"}


def test_co_hang_path():
    assert len(PATHS) > 50
    assert len(AGENT_PATHS) == 11


def test_moi_path_khac_nhau():
    values = list(PATHS.values())
    dup = {v for v in values if values.count(v) > 1}
    assert not dup, f"trùng đường dẫn: {dup}"


def test_moi_path_bat_dau_bang_api():
    bad = {n: v for n, v in PATHS.items() if not v.startswith("/api/")}
    assert not bad


def test_path_khong_co_query_khong_co_khoang_trang():
    for name, value in PATHS.items():
        assert "?" not in value and " " not in value, name
        assert re.fullmatch(r"/api(/[a-z0-9{}_.-]+)+", value), name


def test_cho_trong_chi_dung_ten_cho_phep():
    for name, value in PATHS.items():
        fields = {f for _, f, _, _ in string.Formatter().parse(value) if f}
        assert fields <= PLACEHOLDERS, (name, fields)


def test_moi_hang_agent_co_trong_route_policy():
    assert set(AGENT_PATHS) == set(routing.ROUTE_POLICY)


def test_route_policy_khop_hang_va_che_do_hop_le():
    for route_id, pol in routing.ROUTE_POLICY.items():
        assert getattr(routing, route_id) == pol.path
        assert pol.path.startswith("/api/agent/")
        assert pol.mode in routing.MODES
        assert pol.method in ("GET", "POST")
        assert pol.max_response > 0
        if pol.mode == routing.MODE_TLS_ONLY:
            assert pol.method == "GET" and pol.max_request == 0
        else:
            assert pol.method == "POST" and pol.max_request > 0


def test_che_do_tung_route_theo_thiet_ke_m4():
    mode = {k: v.mode for k, v in routing.ROUTE_POLICY.items()}
    assert mode.pop("AGENT_TRUST_PATH") == "trust"
    assert mode.pop("AGENT_ENROLL_PATH") == "enroll"
    assert mode.pop("AGENT_MEDIA_PATH") == "tls_only"
    assert set(mode.values()) == {"fm1"}


def test_route_bi_bo_khong_con():
    for gone in ("AGENT_HEARTBEAT_PATH", "MACHINE_TOKEN_ROTATE_PATH",
                 "AGENT_COMMAND_RESULT_PATH", "DISPLAY_PATH"):
        assert not hasattr(routing, gone), gone


def test_route_moi_ban_2_co_mat():
    for name in ("AGENT_TRUST_PATH", "AGENT_ENROLL_PATH", "AGENT_RESULTS_PATH",
                 "MACHINE_ENROLL_CODE_PATH", "MACHINE_REVOKE_PATH", "MACHINE_COMMAND_PATH",
                 "MACHINE_COMMAND_CHECK_PATH", "DISPLAY_APPLY_PATH", "DISPLAY_KEEP_PATH",
                 "STEPUP_PATH", "CLOCK_CONFIRM_PATH", "CA_CERT_PATH",
                 "INGREDIENT_REGISTRY_PATH", "MENU_BULK_PATH"):
        assert name in PATHS, name
    assert routing.AGENT_RESULTS_PATH == "/api/agent/results"
    assert routing.AGENT_MEDIA_PATH == "/api/agent/media/{sha256}"


def test_ham_dung_duong_dan():
    assert routing.machine_path(routing.INGREDIENTS_PATH, 3) == "/api/machines/3/ingredients"
    assert (routing.machine_path(routing.MACHINE_COMMAND_PATH, 3, command_id="ab")
            == "/api/machines/3/commands/ab")
    assert routing.menu_path(routing.LAYOUT_PATH, 2) == "/api/menus/2/store/layout"
    try:
        routing.machine_path(routing.MENU_PATH, 3)
    except KeyError:
        pass
    else:
        raise AssertionError("template menu dựng bằng machine_path phải ném KeyError")
