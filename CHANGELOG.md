# CareerPilot AI - Changelog

## 2026-08-18 - Fix: saved jobs not saving correctly

Investigated a user-reported issue ("saved jobs are not saving correctly
from the dashboard") by tracing the complete flow - dashboard -> `Save
Job` link -> `/save/<id>` -> `ApplicationService` -> `ApplicationTracker`
-> SQLite -> `/applications` page - and reproducing with a Flask test
client against an isolated database before changing any code.

Found and fixed two real bugs:

- **Saving the same job twice created a duplicate database row.**
  `ApplicationTracker.save()` (what the dashboard's `/save/<id>` route
  actually calls) had no duplicate detection at all. A separate,
  differently-named sibling method (`save_job()`, used only by the V1 CLI
  agent) did have dedup logic, but the dashboard never went through it.
- **The job's URL was silently dropped on every save.** `job_url` was
  accepted by `Application`/`ApplicationService.save_job()` but was never
  in the `applications` table's schema or `ApplicationTracker.save()`'s
  `INSERT` statement.

Added a `job_url` column (safe/additive migration) and a shared
`ApplicationTracker.find_existing()` duplicate check (by `job_url`, or
company+title as a fallback for older rows), used by both save methods.
Re-saving an already-saved job now returns the existing record instead of
inserting a duplicate, and no longer resets its status.

Added `tests/test_dashboard_save_job.py`: full-flow persistence and
display, duplicate-prevention, V2 `CanonicalJob` compatibility, and a
fast unit-level dedup test on `ApplicationTracker` directly. Full suite:
**43 passed** (was 39).

## 2026-08-18 - V2 completion, live bug fixes, and full documentation

### V2 search foundation completed

Committed the previously-uncommitted V2 job search architecture: canonical
job model, normalization, deduplication, source registry/runner, matching,
ranking, Flask integration, and profile-aware configuration
(`app/search/v2/`).

### Bugs found and fixed (each verified live, not just read from code)

- **`profiles/profile.json` was invalid JSON** (wrapped in a Markdown code
  fence), and the app silently fell back to an empty profile on any
  loading failure. This meant every job was matched against 0 skills/
  titles/locations with no visible error - the root cause of most
  ranking-quality complaints in the prior handoff. Fixed; regression test
  added.
- **A stray `app/search/v2/ranking.py` file shadowed the real
  `app/search/v2/ranking/` package** (Python resolves the package first),
  so a newer, bug-fixed ranker was dead code while an older ranker with a
  real crash bug (comparing `datetime` and `str` on a score tie) was
  silently active. Consolidated and fixed.
- **Duunitori's scraper trusted the wrong JSON-LD field for job titles** -
  `JobPosting.title` on that site holds an internal occupation-taxonomy
  slug, not the posted title, which zeroed out title-match scoring for
  most Duunitori postings. Fixed to prefer the page's `<h1>`.
- **The dashboard's Generate Resume / Cover Letter / Save Job links were
  broken whenever V2 search succeeded** - `CanonicalJob` has no `id`
  field and the job-lookup list (`manager.latest_jobs`) was never
  populated on the V2 path. Fixed; verified live via a Flask test client.
- **`AIEngine.ask()` (the resume/cover-letter generation path) had no
  request timeout** and could hang a Flask request indefinitely when the
  local Ollama model was slow. Reproduced live, then fixed with the same
  bounded-timeout pattern already used elsewhere in the codebase;
  verified the fixed route now fails gracefully within the configured
  timeout instead of hanging.
- **Flask ran with `debug=True` hardcoded** (interactive-debugger RCE
  risk if ever exposed beyond localhost). Now off by default, opt-in via
  `FLASK_DEBUG=1`.
- **A same-domain safety check was missing** before following any link
  scraped out of third-party job-listing HTML, meaning an absolute
  off-domain link could have been fetched as if it were a job posting.
  Added `is_same_site()` guard across all four sources.
- **Several packages used `_init_.py` instead of `__init__.py`**
  (`app/database`, `app/search/sources`, `tests/utils`) - one of them,
  `tests/utils/_init_.py`, contained a stray, syntactically-broken code
  fragment that would have crashed on import once correctly named. Fixed
  and cleaned up.

### Root-cause investigation (previous claims re-verified, not trusted)

The prior handoff claimed Tyomarkkinatori failed on a TLS certificate
error. Re-investigated from scratch: not reproducible through this
project's actual `requests`+`certifi` code path. The real cause of both
Tyomarkkinatori and Work in Finland returning zero results is
client-side-JavaScript-rendered job listings not present in the static
HTML this project's scraper fetches - confirmed by inspecting the actual
fetched content for each site. Documented in `docs/DATA_SOURCES.md`.

### Cleanup

Untracked a stale, unused root-level `careerpilot.db` (superseded by the
actively-used, already-gitignored `data/careerpilot.db`) and a tracked
generated resume file; removed one-off local backup directories and an
obsolete bulk-patch script (`apply.ps1`); expanded `.gitignore`
accordingly.

### Documentation

Full documentation set written from direct code inspection and live
verification: `README.md` (rewritten), `docs/ARCHITECTURE.md`,
`docs/MATCHING_AND_RANKING.md`, `docs/DATA_SOURCES.md`,
`docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT.md`,
`docs/AI.md`, `docs/PRODUCT_VISION.md`, `docs/PORTFOLIO.md`,
`docs/TECHNOLOGY_STACK.md`. Explicitly documents the current V1/V2
dual-matcher state on the dashboard as a real architectural tradeoff
rather than silently resolving or hiding it.

### Verification

Test suite: **39 passed** (24 baseline + 15 new regression tests, one per
bug fixed above).

Live V2 search: **45 unique jobs** collected (35 Duunitori, 17 Jobly, 0
from the two JS-rendered sources - by root-caused design, not silent
failure).

Live-verified end-to-end: dashboard load, job-action links, save-job
persistence through to `/applications`, and the resume-generation route's
graceful-timeout behavior under a forced short `OLLAMA_TIMEOUT`.

## Previous entries

Prior to this session's audit, the changelog described V2's initial
implementation with a since-corrected claim of "24 passed" tests and an
inaccurate TLS-failure theory for Tyomarkkinatori. See git history for
the original text; it is superseded by the entry above.
