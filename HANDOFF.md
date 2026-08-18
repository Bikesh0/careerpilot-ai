# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

The full project-completion pass is done: V2 search is implemented,
tested, and integrated; six real bugs found via live investigation are
fixed and regression-tested; the complete documentation set (`README.md`
+ 10 files under `docs/`) is written from direct code inspection and live
verification; `PROJECT_STATE.md`, `NEXT_TASKS.md`, and `CHANGELOG.md` are
refreshed to match current reality.

## Verification

Test result: **39 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean, no syntax errors.

Live V2 search: 45 unique jobs collected (35 Duunitori, 17 Jobly; the
other two sources return 0 by root-caused design, not silent failure -
see `docs/DATA_SOURCES.md`).

Live Flask verification (via test client, not just read from code):
dashboard loads with V2 enabled, job-action links resolve to real ids,
`/save/<id>` persists and shows up under `/applications` with status
"Saved", and `/generate/<id>` degrades gracefully (503 in ~5s under a
forced short `OLLAMA_TIMEOUT`) instead of hanging when the local model is
slow/unavailable.

## Completed this session (see `CHANGELOG.md` for full detail)

- Committed the previously-uncommitted V2 search foundation.
- Fixed: invalid `profile.json` (was silently causing empty-profile
  matching), a shadowed/buggy V2 ranking module, Duunitori returning the
  wrong job title from a misused JSON-LD field, broken dashboard
  job-action links, an unbounded AI call that could hang requests
  indefinitely, a hardcoded Flask debug-mode default, and a missing
  same-domain check on scraped links (SSRF-adjacent).
- Re-investigated and disproved a prior claim that Tyomarkkinatori failed
  on TLS - the real cause (for it and Work in Finland) is client-side
  JavaScript rendering, documented in `docs/DATA_SOURCES.md`.
- Removed a stale untracked database file, a tracked generated resume
  file, obsolete backup directories, and an obsolete patch script;
  expanded `.gitignore`.
- Wrote the full documentation set: `README.md`, `docs/ARCHITECTURE.md`,
  `docs/MATCHING_AND_RANKING.md`, `docs/DATA_SOURCES.md`,
  `docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT.md`,
  `docs/AI.md`, `docs/PRODUCT_VISION.md`, `docs/PORTFOLIO.md`,
  `docs/TECHNOLOGY_STACK.md`.
- Refreshed `PROJECT_STATE.md`, `NEXT_TASKS.md`, `CHANGELOG.md` to match
  verified current state.

## Known, honestly-documented limitations (not bugs to "fix" blindly)

- The dashboard displays scores from the legacy `app.ai.matcher.JobMatcher`,
  not V2's own matcher - a real, current architectural state, not an
  oversight. See `docs/ARCHITECTURE.md`'s "The V1/V2 split" and
  `NEXT_TASKS.md` Priority 1 before changing this.
- Tyomarkkinatori and Work in Finland return 0 results because their job
  listings are client-side-JavaScript-rendered. Do not "fix" this with
  `verify=False` or similar - it was never a TLS issue.
- `CVParser`/`ProfileExtractor`/`WebActions` are fully implemented but not
  wired to any Flask route.

## Exact next task

See `NEXT_TASKS.md` for the full, current, prioritized list. Top
priorities: (1) decide how to unify the V1/V2 dashboard-ranking split,
(2) get real data out of the two JS-rendered sources or formally scope a
Playwright dependency to do so, (3) wire up the already-built CV-upload
path.

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update. `PROJECT_STATE.md`, `NEXT_TASKS.md`, and `CHANGELOG.md`
are also current as of this session. The repository and its git history
remain the source of truth over any prior AI conversation, this file
included where they disagree.
