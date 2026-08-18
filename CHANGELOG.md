# CareerPilot AI - Changelog

## 2026-08-18 - Unify V1/V2 ranking on the dashboard

Continuing down `NEXT_TASKS.md` Priority 1: the dashboard always
re-scored every job through the legacy `app.ai.matcher.JobMatcher`,
even when V2 search succeeded and had already computed its own score,
matched skills, and human-readable reasons for the same jobs -
`app/web/routes.py._search_jobs()` discarded that `MatchResult` data
one line after computing it. Traced the complete flow (V2 collection ->
normalization -> dedupe -> matching -> ranking -> `_search_jobs()` ->
`_rank_jobs()` -> legacy `JobMatcher` -> `dashboard.html`) before
changing anything.

Fixed with a small, targeted integration rather than deleting either
matcher or duplicating scoring logic: `_search_jobs()` now stashes each
job's already-computed `MatchResult` onto the `CanonicalJob` itself
(`job._v2_match`, the same dynamic-attribute technique already used for
`.id`). `_rank_jobs()` checks whether every job in the list carries one;
if so, a new adapter (`_present_v2_ranked_jobs()`) reshapes V2's own
score/matched_skills/reasons into the dashboard's existing presentation
format, preserving V2's ranking order exactly (no re-sort). If not - V2
disabled, or V2 search/ranking itself failed and `_search_jobs()` fell
back to `manager.search_jobs()` - the **exact same**
`matcher.rank_jobs()` call that existed before this change runs,
completely unchanged. Ownership is decided by where the data actually
came from, not by re-checking the feature flag.

Added a small "match reasons" list to `dashboard.html` (data that
already existed on both matchers but was never rendered anywhere) so
"why was this job recommended" is now genuinely visible, not just
theoretically available.

Added `tests/test_ranking_unification.py` (6 tests): the dashboard
shows V2's exact score and reason text (using reason phrasing only V2's
matcher ever produces, and a job description V1 would score very
differently, as unambiguous proof); V2's ranking order is preserved;
legacy mode is provably untouched when V2 is disabled; a presentation
adapter failure falls back to the legacy matcher instead of crashing;
save/generate/cover-letter routes still resolve V2 jobs correctly.

**Live-verified against the real profile and the real Flask dashboard**
(not just the test suite): the same top result from earlier live
testing ("Staff Security Engineer") now renders with V2's exact score
(74%) and V2's exact reason strings ("Target job title matched",
"Matched 6 profile skills", "Target location matched", "11 profile
skills not found") directly on the page.

**Known, now-visible tradeoff**: V2's matcher still lacks V1's
Finnish-language title terms, exclusion list, and experience-requirement
penalties, so a Finnish-titled posting scores differently depending on
whether V2 succeeded for that request. Logged as `NEXT_TASKS.md`
Priority 1 (the natural next step, not treated as newly discovered
scope) rather than silently accepted.

Full suite: 54 passed (was 48).

## 2026-08-18 - Feature: CV upload with AI-assisted extraction (review-only)

Continuing down `NEXT_TASKS.md` Priority 3: wired up `CVParser`
(PDF/DOCX text extraction) and `ProfileExtractor` (LLM-based CV-to-JSON),
both previously implemented and unit-tested in isolation but unreachable
from any route.

New: `GET /settings` (upload form) and `POST /settings/upload-cv`. File
handling never trusts the client-supplied filename beyond its extension
(checked against a `.pdf`/`.docx` allow-list) - the file is always saved
under a fresh `uuid4().hex` name in `data/cv_uploads/`, verified directly
with a test that uploads a file named `"../../evil.docx"` and asserts it
cannot escape that directory. Request bodies are capped at 10MB
(`app.config["MAX_CONTENT_LENGTH"]`).

Deliberately stops at review: extracted data is displayed on `/settings`,
never automatically written to `profiles/profile.json` - a bad or
AI-hallucinated extraction should not be able to silently corrupt the
profile that matching, resumes, and cover letters all depend on. Logged
as a separate, explicit next step in `NEXT_TASKS.md`.

While wiring this up, hardened `ProfileExtractor.extract()`
(`app/ai/profile_extractor.py`), which previously called `json.loads()`
directly on the raw model response with no fence-stripping or
`None`-check - the exact bug class found twice already this session
(`profiles/profile.json`, `templates/resume_template.html`). It now
extracts the first `{...}` block from the response (matching the
existing, more robust pattern in `resume_builder.py`) and raises a clear
error instead of an unhandled `TypeError` if the model doesn't respond.

Also fixed a `DeprecationWarning` in `app/parsers/cv_parser.py`
(`import fitz` -> `import pymupdf as fitz`), noticed while live-testing
this now-live code path.

Verified live end to end with real `.docx` and `.pdf` files through the
actual `CVParser` (not mocked). Added `tests/test_cv_upload.py` (4
tests). Full suite: 48 passed.

## 2026-08-18 - Fix: broken sidebar navigation links

While continuing down `NEXT_TASKS.md` after the saved-jobs fix below,
found that four of the eight links in the dashboard's sidebar
(`templates/base.html`) - `/resume`, `/coverletter` (bare, no job id),
`/interview`, `/settings` - had no matching Flask route at all and
404'd. Also found their two backing templates for a "generate a
document" landing page, `templates/resume_template.html` and
`templates/cover_template.html`, were dead/unused (confirmed via a
repo-wide search for any `render_template()` or Jinja include
referencing them) and superseded duplicates of the actually-used
`resume.html`/`coverletter.html` - one of them, `resume_template.html`,
also had the same Markdown-code-fence corruption bug found in
`profiles/profile.json` earlier this session, wrapping its entire body
in a stray ` ``` ` block.

Removed both dead templates. Added `/resume` and `/coverletter` (bare)
as redirects to the dashboard - generation is inherently job-specific
(`/generate/<id>`, `/coverletter/<id>`), so there's no meaningful
standalone page for the un-parameterized link - and `/interview`/
`/settings` now render their existing, honest "Coming soon" placeholder
templates instead of 404ing.

Also found, documented but did not build on: `app/web/actions.py`'s
`WebActions.latest_resume()`/`latest_cover_letter()` look for generated
files in `resumes/`/`cover_letters/`, but `ResumeGenerator`/
`CoverLetterGenerator` actually save to `output/` - those helpers would
never find anything even if wired up. Left as a known gap in
`NEXT_TASKS.md` rather than fixed opportunistically alongside an
unrelated navigation fix.

Added `tests/test_sidebar_navigation.py`. Full suite: 44 passed.

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
