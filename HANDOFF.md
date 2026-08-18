# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

The full project-completion pass is done, plus three follow-up fixes
made while continuing autonomously down `NEXT_TASKS.md`: a user-reported
saved-jobs bug, a self-discovered broken-navigation bug, and Priority 3
(CV upload).

## What's been fixed/built, most recent first

### 3. CV upload with AI-assisted extraction (review-only)

Wired up `CVParser`/`ProfileExtractor` (previously implemented but
unreachable) as `GET /settings` + `POST /settings/upload-cv`. Never
trusts the client-supplied filename beyond its extension - saves to a
fresh `uuid4().hex` name under `data/cv_uploads/`, verified with a test
uploading a `"../../evil.docx"` filename. 10MB request-body cap added.
Deliberately stops at a review display - never auto-writes to
`profiles/profile.json` (a bad/hallucinated extraction shouldn't be able
to silently corrupt the profile everything else depends on; the merge
step is left as an explicit next task). Hardened
`ProfileExtractor.extract()` (same JSON-in-a-fence fragility already
fixed twice elsewhere this session) and fixed a PyMuPDF deprecation
warning in `cv_parser.py`. Verified live with real `.docx` and `.pdf`
files. Tests: `tests/test_cv_upload.py` (4).

### 2. Broken sidebar navigation links

Found while investigating for the CV-upload work: `/resume`,
`/coverletter` (bare), `/interview`, `/settings` - four of eight sidebar
links - had no matching route and 404'd. Their two backing templates
(`resume_template.html`, `cover_template.html`) were confirmed dead and
one had the same Markdown-fence corruption bug as `profiles/profile.json`
- both removed. `/resume`/`/coverletter` now redirect to the dashboard;
`/interview` keeps its honest "Coming soon" stub. Also found (documented,
not fixed - logged as `NEXT_TASKS.md` Priority 3b):
`WebActions.latest_resume()`/`latest_cover_letter()` look in the wrong
directory (`resumes/`/`cover_letters/` vs. the generators' actual
`output/`). Tests: `tests/test_sidebar_navigation.py`.

### 1. Saved jobs not saving correctly (user-reported)

Traced the full flow (dashboard -> `/save/<id>` -> `ApplicationService`
-> `ApplicationTracker` -> SQLite -> `/applications`) and reproduced with
a Flask test client before changing code. Two real bugs: `save()` (what
the dashboard actually calls) had no duplicate detection at all, while a
differently-named sibling method (`save_job()`, used only by the V1 CLI)
did - clicking "Save Job" twice created two full duplicate rows. Also,
`job_url` was accepted by `Application`/`ApplicationService` but silently
dropped - never in the table schema or the `INSERT`. Added a `job_url`
column and a shared `find_existing()` dedup check (by `job_url`, or
company+title as a fallback) used by both save methods. Tests:
`tests/test_dashboard_save_job.py` (4).

## Verification

Test result: **48 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

## Documentation updated

This session's three fixes are reflected in `docs/ARCHITECTURE.md`
(Persistence, Flask layer, and new CV-upload sections), `docs/SECURITY.md`
(Path handling - now a live, verified-safe attack surface),
`docs/PRODUCT_VISION.md` (CV Improvement moved from "not wired up" to
"IN PROGRESS", with the exact remaining gap named), `docs/AI.md`
(`ProfileExtractor` hardening), `docs/TESTING.md` (3 new test file
entries), `README.md`, `CHANGELOG.md`, `NEXT_TASKS.md`, this file.

## Known, honestly-documented limitations (carried forward + new)

- The dashboard displays scores from the legacy `app.ai.matcher.JobMatcher`,
  not V2's own matcher - see `docs/ARCHITECTURE.md`'s "The V1/V2 split."
  Deliberately not attempted this session: it's a real design decision
  with regression risk to a currently-good feature, not a quick fix.
- Tyomarkkinatori and Work in Finland return 0 results (client-side
  JavaScript rendering, not TLS - see `docs/DATA_SOURCES.md`).
- CV upload stops at review; nothing merges extracted data into
  `profiles/profile.json` yet (`NEXT_TASKS.md` Priority 3).
- `WebActions.latest_resume()`/`latest_cover_letter()` point at the wrong
  directory relative to where documents are actually generated
  (`NEXT_TASKS.md` Priority 3b).
- `ApplicationTracker`'s database path is resolved relative to the
  current working directory, not the project root.

## Exact next task

Per `NEXT_TASKS.md`, in order: finish Priority 3 (build the
accept-fields merge step for CV data), Priority 3b (fix the output-
directory mismatch), Priority 4 (skill-gap feature - the underlying
`missing_skills` data already exists in V2's `MatchResult`), Priority 5
(source diagnostics, low urgency), Priority 6 (consolidate the two Ollama
wrapper classes, low urgency), Priority 7 (final verification pass).
Priority 1 (V1/V2 ranking unification) remains a flagged, deliberate
design decision rather than something to resolve unilaterally - read
`docs/ARCHITECTURE.md`'s "The V1/V2 split" before touching it.

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update. The repository and its git history remain the source of
truth over any prior AI conversation, this file included where they
disagree.
