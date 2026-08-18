# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

The full project-completion pass is done, plus seven follow-up
fixes/investigations made while continuing autonomously down
`NEXT_TASKS.md`: a user-reported saved-jobs bug, a self-discovered
navigation bug, the CV upload feature, unifying V1/V2 ranking on the
dashboard, consolidating the two Ollama wrapper classes, a `robots.txt`
compliance investigation that led to **disabling Duunitori** (the
project's largest job source), and a final security/documentation/
integration release audit.

## Most significant this session: robots.txt compliance

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
  running in violation of it for this entire session, because
  `robots.txt` was never checked until this point.

**Reported directly to the user, not silently fixed or silently left
running.** The user chose to disable Duunitori and to add Jobly's
missing `Crawl-delay: 10` compliance. `DuunitoriSource` is now
unregistered from both `app/search/v2/registry.py` and
`app/search/manager.py` (class and tests untouched). `JoblySource.get_page()`
now sleeps 10s after every request. **Also found and fixed during the
follow-up release audit**: `test_sources.py` (the manual live smoke
script the README tells developers to run) still imported and called
`DuunitoriSource().search()` directly, completely bypassing the
registry-level disable - fixed. A real dashboard load now returns 14
jobs (all Jobly, correctly matched/ranked), down from 45 with Duunitori
active - an explicit, reported tradeoff.

## Everything completed this session, most recent first

1. **Final release audit** - security re-scan (clean: no `verify=False`,
   no secrets, no unsafe subprocess/eval), found and fixed a gitignore
   gap (`data/cv_uploads/` held uncovered personal data) and the
   `test_sources.py` Duunitori gap above; removed a severely outdated,
   internally self-duplicated planning document
   (`app/search/docs/V2_SEARCH_ARCHITECTURE.md`) and two 0-byte unused
   files (`bootstrap.py`, `run.py`); swept all docs for stale claims
   (two remaining "39 tests" mentions, missing crawl-delay timing note,
   a live-verification example referencing a now-disabled source) and
   fixed them; ran one continuous live integration pass through every
   major user flow.
2. **robots.txt compliance** - Duunitori disabled, Jobly crawl-delay
   added, Tyomarkkinatori API investigated and deliberately not shipped.
3. **Ollama wrapper consolidation** - `AIEngine` removed, everything
   migrated onto `LocalLLM`; fixed a real behavior gap (model
   auto-detection) as a side effect.
4. **V1/V2 ranking unification** - dashboard shows V2's own scoring when
   V2 succeeds. Known, now-visible tradeoff logged: V2 still lacks V1's
   Finnish-language title terms/exclusion list/experience penalties
   (`NEXT_TASKS.md` Priority 1).
5. **CV upload** - `/settings` + `/settings/upload-cv`, safe file
   handling, review-only.
6. **Broken sidebar navigation** - 4 of 8 links 404'd; fixed.
7. **Saved jobs not saving correctly** (user-reported) - duplicate
   detection and `job_url` persistence both fixed.

## Verification

Test result: **57 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

Final live integration pass run end to end against the real, compliant
source set - all 7 checks passed: dashboard (real live V2 search, 15
jobs that run - live counts fluctuate slightly between runs, expected),
`/search` route, save-job + applications page, save idempotency (no
duplicate row), all four sidebar links, CV upload (mocked AI), and
generate/cover-letter graceful degradation.

## Documentation

Complete and reviewed for staleness this round: `README.md` +
`docs/ARCHITECTURE.md`, `docs/MATCHING_AND_RANKING.md`,
`docs/DATA_SOURCES.md`, `docs/SECURITY.md`, `docs/TESTING.md`,
`docs/DEVELOPMENT.md`, `docs/AI.md`, `docs/PRODUCT_VISION.md`,
`docs/PORTFOLIO.md`, `docs/TECHNOLOGY_STACK.md`, `NEXT_TASKS.md`,
`CHANGELOG.md`, `PROJECT_STATE.md`, this file.

## Known, honestly-documented limitations

- **Duunitori is disabled** pending explicit permission from Duunitori
  or a resolved `robots.txt` situation - the single biggest open item
  (`NEXT_TASKS.md` Priority 2).
- V2's matcher lacks V1's Finnish-language title terms, exclusion list,
  and experience-requirement penalties (`NEXT_TASKS.md` Priority 1).
- Tyomarkkinatori returns 0 results; a working API integration exists
  but wasn't shipped for the same `robots.txt`-permission reason.
- CV upload stops at review; nothing merges extracted data into
  `profiles/profile.json` yet (`NEXT_TASKS.md` Priority 3).
- `WebActions.latest_resume()`/`latest_cover_letter()` point at the wrong
  directory (`NEXT_TASKS.md` Priority 3b).

## Exact next task

All items explicitly requested this session (ranking unification, the
two JS-rendered sources, Ollama consolidation, final security review,
final integration testing, documentation review, release audit) are
done. Remaining work is entirely in `NEXT_TASKS.md`, in priority order,
and Priorities 1-3b all need either a human decision (Duunitori/
Tyomarkkinatori permission, the CV-merge UX) or are explicitly low-
urgency (Priority 4/5, source diagnostics).

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update. The repository and its git history remain the source of
truth over any prior AI conversation, this file included where they
disagree.
