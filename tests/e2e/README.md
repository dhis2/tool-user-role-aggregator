# End-to-end tests

Playwright-driven functional tests that exercise the app against a live DHIS2 instance. They were written for the 2026-07-09 App Platform migration review (see `docs/review-2026-07-09/`) and are reusable for regression testing.

Unit tests live next to the code in `src/` (`pnpm test`); this folder holds only the e2e suite.

## What the suite does

`suite.py` installs the production bundle (`build/bundle/*.zip`) into the target instance via `POST /api/apps`, then drives both app flows in Chromium and verifies every mutation through the API:

- create page renders, transfers populated, default authorities preselected
- form validation blocks an empty submit
- create role → API-verified aggregated authorities
- update page: managed-roles list, add authorities from another role → API-verified merge, owner fields preserved
- cache invalidation (managed list refreshes without reload)
- console / page-error / failed-request / HTTP ≥ 400 capture throughout
- created roles are deleted afterwards

`extra_tests.py` checks URL sync inside the global shell (skipped below DHIS2 2.42, where no global shell exists) and the missing-permissions behavior for a non-privileged user (creates and deletes a test user).

`nonsuperuser_test.py` drives the app as a user who may manage roles but is not a superuser: it creates a role holding only user-management authorities plus the app authority, a user holding that role, and verifies that "user roles to manage" lists exactly the roles `canManageRole()` allows and that the create flow works for that user. Its admin user must be a superuser — DHIS2 refuses to grant a role carrying authorities the acting user lacks, which the demo `admin` does not satisfy on every seed, so it defaults to `local_admin`.

## Requirements

- `pip install playwright && playwright install chromium`
- A **disposable** DHIS2 instance with demo data (e.g. Sierra Leone seed) — the suite creates and deletes user roles.
- `pnpm run build` first, so the bundle zip exists.

## Running

```bash
export DHIS2_ADMIN_PASSWORD=<password>   # or pass --password to suite.py

python3 tests/e2e/suite.py --base http://dhis2-<instance>:8080 --label 2.42 \
    [--user admin] [--zip build/bundle/<app>-<version>.zip]

DHIS2_BASE_URL=http://dhis2-<instance>:8080 python3 tests/e2e/extra_tests.py

DHIS2_BASE_URL=http://dhis2-<instance>:8080 python3 tests/e2e/nonsuperuser_test.py
```

The zip defaults to the bundle matching the name and version in `package.json`;
the app key the tests open is read from the same file.

Screenshots and a `results.json` are written next to the scripts, in a folder named after the `--label`. Exit code is non-zero if any step fails.
