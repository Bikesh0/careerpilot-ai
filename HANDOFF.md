# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

The full project-completion pass is done (V2 search, matching/ranking,
dashboard, documentation), plus a follow-up bug investigation and fix for
a user-reported issue: **saved jobs were not saving correctly from the
dashboard.**

## Saved-jobs bug: what was found and fixed

Traced the complete flow before changing anything: dashboard -> `Save
Job` link -> `/save/<id>` (`app/web/routes.py`) -> `ApplicationService.save_job()`
-> `ApplicationTracker.save()` -> SQLite (`data/careerpilot.db`) ->
`/applications` page.

Reproduced first with a Flask test client against an isolated on-disk
database before touching any code. Found two real, confirmed bugs:

1. **No duplicate detection on the actual save path.**
   `ApplicationTracker` has two save methods: `save()` (takes an
   `Application` dataclass, called by the dashboard route via
   `ApplicationService`) and `save_job()` (takes a raw dict, called only
   by the V1 CLI agent in `main.py`). Only `save_job()` had duplicate
   detection - `save()`, the one the dashboard actually uses, had none at
   all. Reproduced directly: clicking "Save Job" twice on the same
   posting inserted two full duplicate rows.
2. **`job_url` was silently dropped.** `Application.job_url` and
   `ApplicationService.save_job()` both carry the job's URL, but the
   `applications` SQLite table never had a `job_url` column and
   `ApplicationTracker.save()`'s `INSERT` never referenced it - the field
   was accepted and then discarded on every save.

**Fix**: added a `job_url` column (via `create_table()` +
`migrate_table()`, additive/safe for the existing production database),
and added a shared `ApplicationTracker.find_existing(job_url, company,
title)` helper - checked by `job_url` first (the reliable per-posting
identity signal), falling back to company+title for older rows saved
before `job_url` was tracked. Both `save()` and `save_job()` now use it
and now persist `job_url`. Re-saving an already-saved job returns the
existing row's id and does not touch its current status (so re-clicking
Save doesn't reset an "Applied" job back to "Saved").

**Verified after the fix**, via the reproduction script and the new test
suite: a single save persists all fields including `job_url`; saving the
same job twice leaves exactly one row; the applications page renders it
correctly; V2 `CanonicalJob` results save correctly.

New tests: `tests/test_dashboard_save_job.py` (4 tests - full-flow
persistence+display, duplicate-prevention, V2-specific, and a fast
unit-level dedup test on `ApplicationTracker` directly).

## Verification

Test result: **43 passed** (39 prior + 4 new), run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

## Documentation updated

`docs/ARCHITECTURE.md` (Persistence section - explains the two save
methods, the shared dedup helper, and the cwd-relative database path),
`docs/TESTING.md` (new test file entry + testing-approach note),
`CHANGELOG.md`, this file. `NEXT_TASKS.md` is unchanged - this fix was a
user-reported bug, not a listed task, and that file is a pure
forward-looking list by its own stated convention.

## Known, honestly-documented limitations (carried forward, unchanged)

- The dashboard displays scores from the legacy `app.ai.matcher.JobMatcher`,
  not V2's own matcher - see `docs/ARCHITECTURE.md`'s "The V1/V2 split."
- Tyomarkkinatori and Work in Finland return 0 results (client-side
  JavaScript rendering, not a TLS issue - see `docs/DATA_SOURCES.md`).
- `CVParser`/`ProfileExtractor`/`WebActions` are implemented but not wired
  to any Flask route.
- `ApplicationTracker`'s database path is resolved relative to the
  current working directory, not the project root - fine for how the app
  is normally launched (from the repo root), but worth knowing if this
  is ever run from elsewhere.

## Exact next task

Continuing autonomously per `NEXT_TASKS.md`, in priority order: (1)
decide how to unify the V1/V2 dashboard-ranking split, (2) get real data
out of the two JS-rendered sources or formally scope a Playwright
dependency, (3) wire up the already-built CV-upload path, (4) consolidate
the two Ollama wrapper classes, (5) final source-level diagnostics if
still worth it.

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update, including this session's saved-jobs fix. The repository
and its git history remain the source of truth over any prior AI
conversation, this file included where they disagree.
