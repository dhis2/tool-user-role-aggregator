#!/usr/bin/env python3
"""Extra tests (2.42+ instances): global-shell URL sync + non-privileged user warning.

Usage:
  DHIS2_BASE_URL=http://dhis2-<instance>:8080 DHIS2_ADMIN_PASSWORD=<password> python3 extra_tests.py

DHIS2_ADMIN_USER defaults to "admin"; broker/demo instances use the standard demo password.
"""
import base64
import json
import os
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("DHIS2_BASE_URL")
if not BASE:
    sys.exit("DHIS2_BASE_URL is required (see usage in the module docstring)")
HOST = BASE.split("://", 1)[1].split(":")[0]
ADMIN_USER = os.environ.get("DHIS2_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("DHIS2_ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    sys.exit("DHIS2_ADMIN_PASSWORD is required (see usage in the module docstring)")
# temporary non-privileged user, created and deleted by this script
LIMITED_USERNAME = "agent_review_limited"
LIMITED_PASSWORD = "Xy7!" + secrets.token_hex(8)
# The DHIS2 app key equals the app name in package.json / d2.config.js
APP_KEY = json.loads((Path(__file__).parents[2] / "package.json").read_text())["name"]
OUT = Path(__file__).parent / "output" / "extra-tests"
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
            **({"Content-Type": "application/json"} if data is not None else {}),
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None


def cookie(user, password):
    req = urllib.request.Request(
        f"{BASE}/api/me",
        headers={"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()},
    )
    with urllib.request.urlopen(req) as r:
        for c in r.headers.get_all("Set-Cookie") or []:
            head = c.split(";", 1)[0]
            n, _, v = head.partition("=")
            if "JSESSIONID" in n:
                return n.strip(), v.strip()
    raise RuntimeError("no cookie")


def app_frame(page):
    for f in page.frames:
        if "user-role-aggregator" in (f.url or "") and f != page.main_frame:
            return f
    return page.main_frame


def test_url_sync(p):
    cn, cv = cookie(ADMIN_USER, ADMIN_PASSWORD)
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1400, "height": 900})
    ctx.add_cookies([{"name": cn, "value": cv, "domain": HOST, "path": "/"}])
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    # global shell path on 2.42+
    page.goto(f"{BASE}/apps/{APP_KEY}", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    f = app_frame(page)
    in_shell = f != page.main_frame
    rec("Global shell wraps app in iframe", "PASS" if in_shell else "WARN", f"frames={len(page.frames)}")
    f.locator("a", has_text="Update existing role").click()
    page.wait_for_timeout(1500)
    url = page.url
    rec("URL syncs with global shell on navigation", "PASS" if "update" in url else "FAIL", f"url={url}")
    page.screenshot(path=str(OUT / "urlsync.png"), full_page=True)
    # navigate back
    f = app_frame(page)
    f.locator("a", has_text="Create new role").click()
    page.wait_for_timeout(1000)
    rec("URL syncs back", "PASS" if "update" not in page.url else "FAIL", f"url={page.url}")
    rec("No page errors during shell navigation", "PASS" if not errors else "FAIL", "; ".join(errors)[:150])
    b.close()


def test_nonprivileged(p):
    # find Data entry clerk role id
    st, roles = api("GET", "/api/userRoles?filter=name:eq:Data entry clerk&fields=id".replace(" ", "%20"))
    clerk_id = roles["userRoles"][0]["id"]
    # find an org unit
    st, ous = api("GET", "/api/organisationUnits?level=1&fields=id&pageSize=1")
    ou = ous["organisationUnits"][0]["id"]
    payload = {
        "username": LIMITED_USERNAME,
        "password": LIMITED_PASSWORD,
        "firstName": "Agent",
        "surname": "Limited",
        "userRoles": [{"id": clerk_id}],
        "organisationUnits": [{"id": ou}],
    }
    st, resp = api("POST", "/api/users", payload)
    uid = None
    if st in (200, 201) and resp and resp.get("response"):
        uid = resp["response"].get("uid")
    rec("Create limited test user", "PASS" if uid else "FAIL", f"http {st} uid={uid}")
    if not uid:
        return None

    try:
        cn, cv = cookie(LIMITED_USERNAME, LIMITED_PASSWORD)
    except Exception as e:
        rec("Limited user login", "FAIL", str(e)[:100])
        return uid
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1400, "height": 900})
    ctx.add_cookies([{"name": cn, "value": cv, "domain": HOST, "path": "/"}])
    page = ctx.new_page()
    page.goto(f"{BASE}/api/apps/{APP_KEY}/index.html", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    f = app_frame(page)
    page.screenshot(path=str(OUT / "limited-user.png"), full_page=True)
    loaded = f.locator("h1", has_text="Create new user admin role").count() > 0
    rec("App loads for limited user", "PASS" if loaded else "WARN",
        "app did not render (may lack app access authority)" if not loaded else "")
    if loaded:
        warned = f.get_by_text("You do not have permission to create or update user roles").count() > 0
        rec("Missing-permission warning shown", "PASS" if warned else "FAIL")
        btn = f.locator("button", has_text="Create role")
        disabled = btn.get_attribute("disabled") is not None
        rec("Create button disabled for limited user", "PASS" if disabled else "FAIL")
    b.close()
    return uid


with sync_playwright() as p:
    test_url_sync(p)
    uid = test_nonprivileged(p)

# cleanup user
if uid:
    st, _ = api("DELETE", f"/api/users/{uid}")
    rec("Cleanup: delete limited user", "PASS" if st in (200, 204) else "FAIL", f"http {st}")

fails = [r for r in results if r[1] == "FAIL"]
(Path(OUT) / "results.json").write_text(json.dumps(results, indent=2))
sys.exit(1 if fails else 0)
