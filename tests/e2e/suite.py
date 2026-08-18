#!/usr/bin/env python3
"""Functional test suite for the User Role Aggregator app (App Platform build).

Installs the built zip into a DHIS2 instance, drives the UI with Playwright,
verifies effects via the API, and cleans up created metadata.

Usage:
  DHIS2_ADMIN_PASSWORD=<password> python3 suite.py \
      --base http://dhis2-<instance>:8080 --label 2.42 [--user admin] [--zip <bundle.zip>]

The password can also be passed with --password. The zip defaults to the
bundle for the current package.json name and version.
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

OUTDIR = Path(__file__).parent / "output"
PROJECT_DIR = Path(__file__).parents[2]
PKG = json.loads((PROJECT_DIR / "package.json").read_text())
# The DHIS2 app key equals the app name in package.json / d2.config.js
APP_KEY = PKG["name"]
DEFAULT_ZIP = PROJECT_DIR / "build" / "bundle" / f"{APP_KEY}-{PKG['version']}.zip"
TRANSFER = '[data-test="dhis2-uicore-transfer"]'
TRANSFER_OPTION = '[data-test="dhis2-uicore-transferoption"]'
CLERK_ROLE = "Data entry clerk"


def api(base, user, password, method, path, data=None, content_type="application/json", raw=False):
    req = urllib.request.Request(
        f"{base}{path}",
        data=data if isinstance(data, (bytes, type(None))) else json.dumps(data).encode(),
        headers={
            "Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode(),
            **({"Content-Type": content_type} if data is not None else {}),
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            if raw:
                return r.status, body
            return r.status, (json.loads(body) if body else None)
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body[:500]


def install_app(base, user, password, zip_path):
    zip_file = Path(zip_path).resolve()
    if zip_file.suffix != ".zip" or not zip_file.is_file():
        raise ValueError(f"--zip must point to an existing .zip file, got: {zip_path}")
    boundary = "----agentboundary42"
    payload = zip_file.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="app.zip"\r\n'
        f"Content-Type: application/zip\r\n\r\n"
    ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
    return api(base, user, password, "POST", "/api/apps", data=body,
               content_type=f"multipart/form-data; boundary={boundary}")


def login_cookie(base, user, password):
    req = urllib.request.Request(
        f"{base}/api/me",
        headers={"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()},
    )
    with urllib.request.urlopen(req) as r:
        for c in r.headers.get_all("Set-Cookie") or []:
            head = c.split(";", 1)[0]
            n, _, v = head.partition("=")
            if "JSESSIONID" in n:
                return n.strip(), v.strip()
    raise RuntimeError("No JSESSIONID returned")


class Suite:
    def __init__(self, base, label, user, password):
        self.base, self.label, self.user, self.password = base, label, user, password
        self.results = []
        self.console = []
        self.pageerrors = []
        self.reqfailed = []
        self.http_errors = []
        self.created_role_uids = []
        self.shot_n = 0
        self.dir = OUTDIR / label
        self.dir.mkdir(parents=True, exist_ok=True)

    def record(self, step, status, detail=""):
        self.results.append({"step": step, "status": status, "detail": detail})
        print(f"[{self.label}] {status}: {step} {('- ' + detail) if detail else ''}", flush=True)

    def shot(self, page, name):
        self.shot_n += 1
        path = self.dir / f"{self.shot_n:02d}-{name}.png"
        page.screenshot(path=str(path), full_page=True)
        return path

    # ---- helpers on the app frame ----
    def app_frame(self, page):
        # App may render inside global shell iframe (2.42+) or top-level (2.40)
        for f in page.frames:
            if APP_KEY in (f.url or "") and f != page.main_frame:
                return f
        return page.main_frame

    def transfer_pick(self, frame, transfer_index, option_label):
        transfers = frame.locator(TRANSFER)
        t = transfers.nth(transfer_index)
        # filter to the option to avoid scrolling long lists
        t.locator('[data-test="dhis2-uicore-transfer-filter"] input').first.fill(option_label)
        opt = t.locator(TRANSFER_OPTION, has_text=option_label).first
        opt.dblclick()

    def run(self, zip_path):
        self.api_preflight()
        launch = self.install(zip_path)
        role_name = f"Agent Test Admin Role {int(time.time())}"
        self.run_browser_flows(launch, role_name)
        self.cleanup_roles()
        self.summarize()

    def api_preflight(self):
        st, info = api(self.base, self.user, self.password, "GET", "/api/system/info")
        self.record("API: system/info", "PASS" if st == 200 else "FAIL", f"version={info.get('version') if st==200 else st}")
        st, roles = api(self.base, self.user, self.password, "GET",
                        "/api/userRoles?fields=id,displayName,authorities&paging=false")
        n_roles = len(roles.get("userRoles", [])) if st == 200 else 0
        self.record("API: userRoles list", "PASS" if st == 200 and n_roles > 0 else "FAIL", f"{n_roles} roles")
        st, auths = api(self.base, self.user, self.password, "GET", "/api/authorities")
        n_auths = len(auths.get("systemAuthorities", [])) if st == 200 else 0
        self.record("API: authorities list", "PASS" if st == 200 and n_auths > 0 else "FAIL", f"{n_auths} authorities")
        self.demo_roles = {r["displayName"]: r for r in roles.get("userRoles", [])}

    def install(self, zip_path):
        st, _ = install_app(self.base, self.user, self.password, zip_path)
        self.record("Install app zip via /api/apps", "PASS" if st in (200, 201, 204) else "FAIL", f"http {st}")
        st, apps = api(self.base, self.user, self.password, "GET", "/api/apps")
        entry = next((a for a in apps if APP_KEY in (a.get("key") or "")), None) if st == 200 else None
        launch = entry.get("launchUrl") if entry else f"{self.base}/api/apps/{APP_KEY}/index.html"
        self.record("App registered", "PASS" if entry else "WARN", f"launchUrl={launch}")
        return launch

    def run_browser_flows(self, launch, role_name):
        cn, cv = login_cookie(self.base, self.user, self.password)
        host = self.base.split("://", 1)[1].split(":")[0]
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1400, "height": 900})
            ctx.add_cookies([{"name": cn, "value": cv, "domain": host, "path": "/"}])
            page = ctx.new_page()
            page.on("console", lambda m: self.console.append((m.type, m.text)) if m.type in ("error", "warning") else None)
            page.on("pageerror", lambda e: self.pageerrors.append(str(e)))
            page.on("requestfailed", lambda r: self.reqfailed.append((r.url, str(r.failure))))
            page.on("response", lambda r: self.http_errors.append((r.status, r.url)) if r.status >= 400 else None)
            try:
                self.flow_create(page, launch, role_name)
                self.flow_update(page, role_name)
            finally:
                self.shot(page, "final")
                browser.close()

    def cleanup_roles(self):
        for uid in self.created_role_uids:
            st, _ = api(self.base, self.user, self.password, "DELETE", f"/api/userRoles/{uid}")
            self.record(f"Cleanup: delete role {uid}", "PASS" if st in (200, 204) else "FAIL", f"http {st}")

    def summarize(self):
        self.record("Console errors", "PASS" if not [c for c in self.console if c[0] == "error"] else "WARN",
                    f"{len([c for c in self.console if c[0]=='error'])} errors")
        self.record("Page errors", "PASS" if not self.pageerrors else "FAIL", f"{len(self.pageerrors)}")
        app_http_errors = [e for e in self.http_errors if "/api/" in e[1]]
        self.record("HTTP >=400 responses", "PASS" if not app_http_errors else "WARN",
                    "; ".join(f"{s} {u.split('/api/')[-1][:60]}" for s, u in app_http_errors[:5]))

        (self.dir / "results.json").write_text(json.dumps({
            "results": self.results,
            "console": self.console[:50],
            "pageerrors": self.pageerrors[:20],
            "requestfailed": self.reqfailed[:20],
            "http_errors": self.http_errors[:50],
        }, indent=2))

    def flow_create(self, page, launch, role_name):
        page.goto(launch, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        f = self.app_frame(page)
        # wait for the create page heading
        try:
            f.locator("h1", has_text="Create new user admin role").wait_for(timeout=20000)
            self.record("App loads: create page renders", "PASS")
        except Exception as e:
            self.shot(page, "load-fail")
            self.record("App loads: create page renders", "FAIL", str(e)[:120])
            raise
        self.shot(page, "create-page")

        transfers = f.locator(TRANSFER)
        n_role_opts = transfers.nth(0).locator(TRANSFER_OPTION).count()
        self.record("Roles transfer populated", "PASS" if n_role_opts > 0 else "FAIL", f"{n_role_opts} options")

        picked = f.locator(TRANSFER).nth(1) \
            .locator(f'[data-test="dhis2-uicore-transfer-pickedoptions"] {TRANSFER_OPTION}')
        picked_labels = picked.all_inner_texts()
        # authority *names* are shown, not ids; just assert some defaults picked
        self.record("Default authorities preselected", "PASS" if len(picked_labels) >= 3 else "FAIL",
                    f"{len(picked_labels)} picked: {picked_labels[:6]}")

        # --- validation: submit empty form ---
        f.locator("button", has_text="Create role").click()
        page.wait_for_timeout(500)
        err_visible = f.get_by_text("Role name is required").count() > 0
        self.record("Validation: empty name rejected", "PASS" if err_visible else "FAIL")
        self.shot(page, "validation")

        # --- fill and submit ---
        f.locator('input[type="text"]').first.fill(role_name)
        self.transfer_pick(f, 0, CLERK_ROLE)
        self.shot(page, "create-filled")
        f.locator("button", has_text="Create role").click()
        try:
            f.locator('[data-test="dhis2-uicore-alertbar"]', has_text="created successfully").wait_for(timeout=15000)
            self.record("Create role: success alert", "PASS")
        except Exception:
            self.shot(page, "create-fail")
            self.record("Create role: success alert", "FAIL")
        self.shot(page, "create-done")

        # --- API verify ---
        st, res = api(self.base, self.user, self.password, "GET",
                      f"/api/userRoles?filter=name:eq:{urllib.request.quote(role_name)}&fields=id,name,description,authorities")
        found = res.get("userRoles", []) if st == 200 else []
        if found:
            self.created_role_uids.append(found[0]["id"])
            clerk = self.demo_roles.get(CLERK_ROLE, {})
            clerk_auths = set(clerk.get("authorities", []))
            new_auths = set(found[0].get("authorities", []))
            missing = clerk_auths - new_auths
            has_defaults = {"F_USER_ADD", "F_USER_VIEW"} <= new_auths
            ok = not missing and has_defaults
            self.record("API verify: created role aggregates authorities", "PASS" if ok else "FAIL",
                        f"{len(new_auths)} auths, missing from clerk: {sorted(missing)[:5]}, defaults={has_defaults}")
        else:
            self.record("API verify: created role exists", "FAIL", f"http {st}")

    def flow_update(self, page, role_name):
        f = self.app_frame(page)
        f.locator("a", has_text="Update existing role").click()
        page.wait_for_timeout(1000)
        f = self.app_frame(page)
        try:
            f.locator("h1", has_text="Update existing user role").wait_for(timeout=10000)
            self.record("Update page renders", "PASS")
        except Exception as e:
            self.shot(page, "update-load-fail")
            self.record("Update page renders", "FAIL", str(e)[:120])
            return
        self.shot(page, "update-page")

        # select the role created in flow_create
        f.locator('[data-test="dhis2-uicore-select"]').click()
        menu = f.locator('[data-test="dhis2-uicore-select-menu-menuwrapper"]')
        if menu.count() == 0:  # menu rendered in a portal/layer on the page
            menu = f.locator('[data-test="dhis2-uicore-layer"]')
        filt = f.locator('[data-test="dhis2-uicore-select-filter"] input')
        if filt.count() > 0:
            filt.fill(role_name)
        f.locator('[data-test="dhis2-uicore-singleselectoption"]', has_text=role_name).first.click()
        page.wait_for_timeout(500)
        self.shot(page, "update-selected")

        managed = f.locator("ul li").all_inner_texts()
        has_clerk = any(CLERK_ROLE in m for m in managed)
        self.record("Managed roles list shows Data entry clerk", "PASS" if has_clerk else "FAIL",
                    f"{len(managed)} managed listed")

        # add another role's authorities
        target = "M and E Officer"
        if target not in self.demo_roles:
            target = next((n for n in self.demo_roles
                           if n != CLERK_ROLE and "Super" not in n and self.demo_roles[n].get("authorities")), None)
        self.transfer_pick(f, 0, target)  # only one transfer on this page
        self.shot(page, "update-picked")
        f.locator("button", has_text="Add authorities to role").click()
        try:
            f.locator('[data-test="dhis2-uicore-alertbar"]', has_text="updated successfully").wait_for(timeout=15000)
            self.record("Update role: success alert", "PASS")
        except Exception:
            self.shot(page, "update-fail")
            self.record("Update role: success alert", "FAIL")
        page.wait_for_timeout(1500)
        self.shot(page, "update-done")

        # UI should refresh: managed list now includes the target role (cache invalidation)
        managed_after = f.locator("ul li").all_inner_texts()
        self.record("Managed list refreshes after update (cache invalidation)",
                    "PASS" if any(target in m for m in managed_after) else "FAIL",
                    f"target={target}")

        # API verify merge
        if self.created_role_uids:
            uid = self.created_role_uids[0]
            st, role = api(self.base, self.user, self.password, "GET",
                           f"/api/userRoles/{uid}?fields=name,description,authorities")
            tgt_auths = set(self.demo_roles.get(target, {}).get("authorities", []))
            new_auths = set(role.get("authorities", [])) if st == 200 else set()
            missing = tgt_auths - new_auths
            self.record("API verify: authorities merged, nothing lost",
                        "PASS" if st == 200 and not missing and role.get("description") else "FAIL",
                        f"missing={sorted(missing)[:5]} description_kept={bool(role.get('description'))}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--user", default=os.environ.get("DHIS2_ADMIN_USER", "admin"))
    ap.add_argument("--password", default=os.environ.get("DHIS2_ADMIN_PASSWORD"))
    ap.add_argument("--zip", default=str(DEFAULT_ZIP))
    args = ap.parse_args()
    if not args.password:
        ap.error("--password or DHIS2_ADMIN_PASSWORD is required")
    s = Suite(args.base, args.label, args.user, args.password)
    s.run(args.zip)
    fails = [r for r in s.results if r["status"] == "FAIL"]
    print(f"\n[{args.label}] {len(s.results)} steps, {len(fails)} FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
