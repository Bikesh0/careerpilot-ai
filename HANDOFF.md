# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

The full project-completion pass is done, plus six follow-up fixes made
while continuing autonomously down `NEXT_TASKS.md`: a user-reported
saved-jobs bug, a self-discovered navigation bug, the CV upload feature,
unifying V1/V2 ranking on the dashboard, consolidating the two Ollama
wrapper classes, and - most recently, and most significant - a
`robots.txt` compliance investigation that led to **disabling
Duunitori**, the project's largest job source.

## Most recent, and most important: robots.txt compliance

Investigating `NEXT_TASKS.md` Priority 2 (the two zero-result sources)
using real browser network inspection (`claude-in-chrome`):

- Found Tyomarkkinatori's internal JSON API, built and verified a
  working scraper against it live - then **reverted, did not ship it**,
  because `tyomarkkinatori.fi/robots.txt` disallows `/api/`.
- Found Work in Finland's "Open jobs" widget loads assets from
  `jobly.fi` - likely redundant with the existing `JoblySource`.
- Checking `robots.txt` for these two prompted checking it for the
  already-shipped sources too. **`duunitori.fi/robots.txt` disallows the
  generic `*` user-agent group entirely.** `DuunitoriSource`'s spoofed
  browser User-Agent doesn't match any of the site's named, allowlisted
  crawlers, so it falls under that blanket disallow - and had been
  running in violation of it for this entire session (including through
  a title-extraction bug fix and re-verification earlier today),
  because `robots.txt` was never checked until this point.

**This was reported directly to the user, not silently fixed or
silently left running.** Given the significant, real tradeoff (Duunitori
had been the largest source - roughly half of collected jobs), I asked
explicitly how to proceed rather than deciding unilaterally. The user
chose to disable Duunitori and to add Jobly's missing `Crawl-delay: 10`
compliance.

**Action taken**: `DuunitoriSource` unregistered from both
`app/search/v2/registry.py` and `app/search/manager.py` (class and tests
untouched - a one-line change to re-enable once resolved).
`JoblySource.get_page()` now sleeps 10s after every request. Both
verified live: a real dashboard load now returns 14 jobs (all Jobly,
correctly matched/ranked), down from 45 with Duunitori active - an
explicit, reported change, not a silent regression. New tests:
`tests/test_robots_txt_compliance.py` (3).

## Everything completed this session, most recent first

1. **robots.txt compliance** (above) - Duunitori disabled, Jobly
   crawl-delay added, Tyomarkkinatori API investigated and deliberately
   not shipped.
2. **Ollama wrapper consolidation** - `AIEngine` removed, everything
   migrated onto `LocalLLM`; fixed a real behavior gap (model
   auto-detection) as a side effect.
3. **V1/V2 ranking unification** - dashboard shows V2's own scoring when
   V2 succeeds, instead of always re-scoring through the legacy matcher.
   Known, now-visible tradeoff logged: V2 still lacks V1's
   Finnish-language title terms/exclusion list/experience penalties
   (`NEXT_TASKS.md` Priority 1).
4. **CV upload** - `/settings` + `/settings/upload-cv`, safe file
   handling, review-only (never auto-writes to `profiles/profile.json`).
5. **Broken sidebar navigation** - 4 of 8 links 404'd; fixed.
6. **Saved jobs not saving correctly** (user-reported) - duplicate
   detection and `job_url` persistence both fixed.

## Verification

Test result: **57 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

Live-verified through the real Flask dashboard after the robots.txt
changes: status 200, 14 real jobs from Jobly, correctly matched/ranked.

## Documentation updated this round

`docs/DATA_SOURCES.md` (Duunitori section substantially rewritten;
Jobly's crawl-delay documented; Tyomarkkinatori's API finding documented
in full), `docs/SECURITY.md` (new "Respecting robots.txt" coverage of
both findings), `docs/ARCHITECTURE.md`, `docs/PRODUCT_VISION.md`,
`README.md` (Features, Architecture diagram, Known Limitations, Roadmap -
all had stale Duunitori-is-active claims), `docs/PORTFOLIO.md` (test
count fixed in two places - one was already stale before this round; new
interview answer about the Duunitori finding itself), `docs/TESTING.md`
(test count fixed - was stale since an earlier session; new test file
entry), `NEXT_TASKS.md`, `CHANGELOG.md`, `PROJECT_STATE.md`, this file.

## Known, honestly-documented limitations (carried forward + new)

- **Duunitori is disabled** pending explicit permission from Duunitori
  or a resolved `robots.txt` situation - the single biggest open item
  now (`NEXT_TASKS.md` Priority 2).
- V2's matcher lacks V1's Finnish-language title terms, exclusion list,
  and experience-requirement penalties (`NEXT_TASKS.md` Priority 1).
- Tyomarkkinatori returns 0 results; a working API integration exists
  but wasn't shipped for the same `robots.txt`-permission reason as
  Duunitori.
- CV upload stops at review; nothing merges extracted data into
  `profiles/profile.json` yet (`NEXT_TASKS.md` Priority 3).
- `WebActions.latest_resume()`/`latest_cover_letter()` point at the wrong
  directory (`NEXT_TASKS.md` Priority 3b).

## Exact next task

Per `NEXT_TASKS.md`, continuing the user's explicit instruction to
proceed through the remaining release priorities: final security review,
final integration testing, documentation review, and release audit.
Priority 2 (Duunitori/Tyomarkkinatori permission) needs the user's own
outreach to those sites, not more engineering - flagged clearly, not
blocking other work. Priority 1 (port V1 matching logic into V2) remains
queued after that.

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update, including the robots.txt findings. The repository and
its git history remain the source of truth over any prior AI
conversation, this file included where they disagree.
