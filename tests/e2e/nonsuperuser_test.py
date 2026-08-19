#!/usr/bin/env python3
"""Checks the app for non-superusers. Two scenarios, both cleaned up afterwards:

1. A user allowed to manage roles (user-management authorities + app access):
   the app must offer exactly the roles canManageRole() allows, and creating a
   role must work. The other suites run as a superuser, where every role is
   manageable and that filter is never really exercised.
2. A user who can open the app but not manage roles (app access only): the app
   must show the "Missing permissions" warning and disable the Create button.

Usage:
  DHIS2_BASE_URL=http://dhis2-<instance>:8080 DHIS2_ADMIN_PASSWORD=<password> \
      python3 nonsuperuser_test.py

DHIS2_ADMIN_USER defaults to "local_admin" and must be a superuser (hold ALL):
DHIS2 refuses to grant a user a role carrying authorities the acting user lacks,
which the demo `admin` account does not satisfy on every seed.
"""
import base64
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE = os.environ.get("DHIS2_BASE_URL")
if not BASE:
    sys.exit("DHIS2_BASE_URL is required (see usage in the module docstring)")
HOST = BASE.split("://", 1)[1].split(":")[0]
ADMIN_USER = os.environ.get("DHIS2_ADMIN_USER", "local_admin")
ADMIN_PASSWORD = os.environ.get("DHIS2_ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    sys.exit("DHIS2_ADMIN_PASSWORD is required (see usage in the module docstring)")

PROJECT_DIR = Path(__file__).parents[2]
APP_KEY = json.loads((PROJECT_DIR / "package.json").read_text())["name"]
# DHIS2 derives an app's access authority from its key, minus non-alphanumerics
APP_AUTHORITY = "M_" + re.sub(r"[^A-Za-z0-9]", "", APP_KEY)
# What the tester holds: enough to open the app and add roles, nothing more
TESTER_AUTHORITIES = [
    "F_USER_ADD",
    "F_USER_VIEW",
    "F_USER_DELETE",
    "F_USERROLE_PUBLIC_ADD",
    "M_dhis-web-user",
    APP_AUTHORITY,
]
# Enough to open the app, but not to add roles
READ_ONLY_AUTHORITIES = ["F_USER_VIEW", "M_dhis-web-user", APP_AUTHORITY]
# Preselected on the create page, and all held by the tester
DEFAULT_AUTHORITIES = {"F_USER_ADD", "F_USER_DELETE", "F_USER_VIEW", "M_dhis-web-user"}
AUTHORITY_ALL = "ALL"

CREATE_HEADING = "Create new user admin role"
PERMISSION_WARNING = "You do not have permission to create or update user roles"
TRANSFER = '[data-test="dhis2-uicore-transfer"]'
TRANSFER_OPTION = '[data-test="dhis2-uicore-transferoption"]'
ALERTBAR = '[data-test="dhis2-uicore-alertbar"]'

OUT = Path(__file__).parent / "output" / "nonsuperuser"
OUT.mkdir(parents=True, exist_ok=True)
results = []


def rec(step, status, detail=""):
    results.append((step, status, detail))
    print(f"{status}: {step} {('- ' + detail) if detail else ''}", flush=True)


def api(method, path, data=None, user=ADMIN_USER, password=ADMIN_PASSWORD):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=None if data is None else json.dumps(data).encode(),
        headers={
            "Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode(),
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, {"raw": body[:300]}


def created_uid(status, payload):
    """UID from an import report — but only when the import actually succeeded:
    DHIS2 returns a uid alongside the errors on a 409 as well."""
    if status not in (200, 201):
        return None
    return (payload.get("response") or {}).get("uid")


def cookie(user, password):
    req = urllib.request.Request(
        f"{BASE}/api/me",
        headers={"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()},
    )
    with urllib.request.urlopen(req) as r:
        for c in r.headers.get_all("Set-Cookie") or []:
            name, _, value = c.split(";", 1)[0].partition("=")
            if "JSESSIONID" in name:
                return name.strip(), value.strip()
    raise RuntimeError("no session cookie returned")


def app_frame(page):
    for f in page.frames:
        if APP_KEY in (f.url or "") and f != page.main_frame:
            return f
    return page.main_frame


def expected_manageable_roles(held):
    """The roles the app should offer, per canManageRole() in src/types/userRole.ts."""
    _, res = api("GET", "/api/userRoles?fields=id,displayName,authorities&paging=false")
    manageable = []
    for role in res.get("userRoles", []):
        authorities = role.get("authorities") or []
        if AUTHORITY_ALL in authorities:
            continue
        if all(a in held for a in authorities):
            manageable.append(role["displayName"])
    return sorted(manageable)


def create_role(name, authorities):
    st, resp = api("POST", "/api/userRoles", {
        "name": name,
        "description": "temporary role for the non-superuser e2e check",
        "authorities": authorities,
    })
    uid = created_uid(st, resp)
    rec(f"Create role {name}", "PASS" if uid else "FAIL", f"http {st} {str(resp)[:160]}")
    return uid


def create_user(username, password, role_uid):
    _, ous = api("GET", "/api/organisationUnits?level=1&fields=id&pageSize=1")
    st, resp = api("POST", "/api/users", {
        "username": username,
        "password": password,
        "firstName": "Agent",
        "surname": "Tester",
        "userRoles": [{"id": role_uid}],
        "organisationUnits": [{"id": ous["organisationUnits"][0]["id"]}],
    })
    uid = created_uid(st, resp)
    rec(f"Create user {username}", "PASS" if uid else "FAIL", f"http {st} {str(resp)[:160]}")
    return uid


def open_app_as(page, username, password):
    cookie_name, cookie_value = cookie(username, password)
    page.context.add_cookies([
        {"name": cookie_name, "value": cookie_value, "domain": HOST, "path": "/"}
    ])
    page.goto(f"{BASE}/api/apps/{APP_KEY}/index.html", wait_until="domcontentloaded")
    # On 2.42+ the app renders inside the global-shell iframe, which appears
    # some time after domcontentloaded — poll for the frame and its heading
    # rather than guessing a fixed delay.
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        frame = app_frame(page)
        try:
            frame.locator("h1", has_text=CREATE_HEADING).wait_for(timeout=2000)
            rec("App loads for non-superuser with app access", "PASS")
            return frame
        except PlaywrightTimeoutError:
            page.wait_for_timeout(500)
    frame = app_frame(page)
    notices = frame.locator('[data-test="dhis2-uicore-noticebox"]').all_inner_texts()
    page.screenshot(path=str(OUT / "app-did-not-render.png"), full_page=True)
    rec("App loads for non-superuser with app access", "FAIL",
        f"heading never rendered; frames={len(page.frames)} url={page.url} notices={notices}")
    return None


def check_manageable_roles(frame, held):
    warned = frame.get_by_text(PERMISSION_WARNING).count() > 0
    rec("No missing-permission warning", "PASS" if not warned else "FAIL")
    shown = sorted(
        text.strip()
        for text in frame.locator(TRANSFER).nth(0).locator(TRANSFER_OPTION).all_inner_texts()
    )
    expected = expected_manageable_roles(held)
    rec("Manageable roles match canManageRole()", "PASS" if shown == expected else "FAIL",
        f"shown={shown} expected={expected}")


def create_role_as_tester(page, frame, role_name):
    frame.locator('input[type="text"]').first.fill(role_name)
    frame.locator("button", has_text="Create role").click()
    try:
        frame.locator(ALERTBAR, has_text="created successfully").wait_for(timeout=15000)
        rec("Non-superuser can create a role (preselected defaults only)", "PASS")
    except Exception:
        rec("Non-superuser can create a role (preselected defaults only)", "FAIL",
            f"alerts={frame.locator(ALERTBAR).all_inner_texts()}")
    page.screenshot(path=str(OUT / "nonsuperuser-after-create.png"), full_page=True)

    st, res = api("GET", f"/api/userRoles?filter=name:eq:{urllib.request.quote(role_name)}"
                         "&fields=id,authorities")
    found = res.get("userRoles", []) if st == 200 else []
    if not found:
        rec("API verify: created role holds exactly the default authorities", "FAIL", "role not found")
        return None
    authorities = set(found[0].get("authorities") or [])
    rec("API verify: created role holds exactly the default authorities",
        "PASS" if authorities == DEFAULT_AUTHORITIES else "FAIL", f"got={sorted(authorities)}")
    return found[0]["id"]


def check_read_only_user(frame):
    warned = frame.get_by_text(PERMISSION_WARNING).count() > 0
    rec("Read-only user sees the missing-permission warning", "PASS" if warned else "FAIL")
    button = frame.locator("button", has_text="Create role")
    disabled = button.count() > 0 and button.first.get_attribute("disabled") is not None
    rec("Read-only user cannot submit (Create button disabled)", "PASS" if disabled else "FAIL",
        f"buttons={button.count()}")


def browser_page(p):
    context = p.chromium.launch().new_context(viewport={"width": 1400, "height": 1000})
    return context.new_page()


def drive_app(username, password, role_name):
    """Returns the uid of the role created through the UI, if any."""
    with sync_playwright() as p:
        page = browser_page(p)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            frame = open_app_as(page, username, password)
            if not frame:
                page.screenshot(path=str(OUT / "nonsuperuser-blocked.png"), full_page=True)
                return None
            check_manageable_roles(frame, set(TESTER_AUTHORITIES))
            page.screenshot(path=str(OUT / "nonsuperuser-create-page.png"), full_page=True)
            return create_role_as_tester(page, frame, role_name)
        finally:
            rec("No page errors", "PASS" if not errors else "FAIL", "; ".join(errors)[:150])
            page.context.browser.close()


def cleanup(uids):
    for resource, uid in uids:
        if uid:
            st, _ = api("DELETE", f"/api/{resource}/{uid}")
            rec(f"Cleanup: delete {resource}/{uid}", "PASS" if st in (200, 204) else "FAIL", f"http {st}")


def run_manager_scenario(stamp):
    """Scenario 1: a non-superuser who may manage roles."""
    username = f"agent_ura_tester_{stamp}"
    password = "Xy7!" + secrets.token_hex(8)
    role_uid = user_uid = new_role_uid = None
    try:
        role_uid = create_role(f"Agent URA Tester {stamp}", TESTER_AUTHORITIES)
        if role_uid:
            user_uid = create_user(username, password, role_uid)
        if user_uid:
            new_role_uid = drive_app(username, password, f"Agent NonSuper Role {stamp}")
    finally:
        cleanup([("userRoles", new_role_uid), ("users", user_uid), ("userRoles", role_uid)])


def run_read_only_scenario(stamp):
    """Scenario 2: a user who can open the app but not manage roles."""
    username = f"agent_ura_readonly_{stamp}"
    password = "Xy7!" + secrets.token_hex(8)
    role_uid = user_uid = None
    try:
        role_uid = create_role(f"Agent URA ReadOnly {stamp}", READ_ONLY_AUTHORITIES)
        if role_uid:
            user_uid = create_user(username, password, role_uid)
        if not user_uid:
            return
        with sync_playwright() as p:
            page = browser_page(p)
            frame = open_app_as(page, username, password)
            if frame:
                check_read_only_user(frame)
                page.screenshot(path=str(OUT / "readonly-user.png"), full_page=True)
            page.context.browser.close()
    finally:
        cleanup([("users", user_uid), ("userRoles", role_uid)])


def main():
    stamp = int(time.time())
    run_manager_scenario(stamp)
    run_read_only_scenario(stamp)
    fails = [r for r in results if r[1] == "FAIL"]
    print(f"\n{len(results)} steps, {len(fails)} FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
