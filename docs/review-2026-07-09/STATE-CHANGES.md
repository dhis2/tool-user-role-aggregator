# State changes: User Admin Role Aggregator review, 2026-07-09

Every persistent change made during this review, and its disposition.

## Project files

| File                                                                     | Change                                                             | Disposition                                       |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------- |
| `src/hooks/fetchRoleAuthorities.ts`                                      | Added (fix for finding M1)                                         | Kept                                              |
| `src/hooks/useCreateUserRole.ts`, `src/hooks/useAddAuthoritiesToRole.ts` | Mutations now fetch source-role authorities at submit time (M1)    | Kept                                              |
| `src/pages/CreateRolePage.tsx`                                           | Schema built in-component (L1); `nsSeparator` on intro string (L2) | Kept                                              |
| `src/pages/UpdateRolePage.tsx`                                           | Passes role ids instead of pre-computed authorities (M1)           | Kept                                              |
| `src/types/userRole.test.ts`                                             | Added unit tests for `canManageRole`                               | Kept                                              |
| `i18n/en.pot`                                                            | Regenerated via `d2-app-scripts i18n extract` (L2)                 | Kept                                              |
| `CHANGELOG.md`                                                           | Added fixed/upgrade notes (L3, L4)                                 | Kept                                              |
| `docs/review-2026-07-09/review-artifacts/`                               | Test screenshots                                                   | Disposable — delete when done reading the reports |
| `docs/review-2026-07-09/` reports, `tests/e2e/` suite                    | Review reports and reusable e2e test suite                         | Kept                                              |

No project config was repointed at test instances (the production bundle was installed on the instances instead; no `d2auth.json` exists in the platform setup).

## DHIS2 instances (broker)

| Instance               | Version  | Seed             | Disposition                  |
| ---------------------- | -------- | ---------------- | ---------------------------- |
| `agent-review-ura-240` | 2.40.12  | sierra-leone V40 | **Deleted** (job j-d0fb2d91) |
| `agent-review-ura-243` | 2.43.0.1 | sierra-leone v43 | **Deleted** (job j-6e4049b1) |

## Test data created

All on the (since-deleted) broker instances; also cleaned explicitly during the runs:

| Object type                                                  | Instance | Deleted?                                 |
| ------------------------------------------------------------ | -------- | ---------------------------------------- |
| userRole `Agent Test Admin Role <ts>` (several, one per run) | both     | Yes (DELETE 200 each run)                |
| user `agent_review_limited`                                  | 2.43     | Yes (DELETE 200)                         |
| app `user-role-aggregator` installed via `/api/apps`         | both     | Left installed — instance deleted anyway |

## System settings changed

None.

## Not reverted — action needed

Nothing. Both broker instances were deleted; no settings or external state remain changed.
