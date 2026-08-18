# CareerPilot AI - Project State

## Project

CareerPilot AI is a Flask-based job-search and career-assistance
application built around one specific candidate's profile. It collects
job postings from multiple Finnish job sources, normalizes them into a
canonical model, deduplicates them, matches them against the profile,
ranks them, and exposes the results through a Flask dashboard with
AI-assisted resume/cover-letter generation.

Full architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Current branch

`v2-development`, pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`).

## Current V2 status

V2 search is implemented, tested, and integrated with the Flask
application.

Feature flag: `CAREERPILOT_SEARCH_V2=1`

Key modules: `app/search/v2/factory.py`, `service.py`, `runner.py`,
`normalizer.py`, `dedupe.py`, `job.py`, `matching/`, `ranking/`.

**Important**: the Flask dashboard now displays V2's own
score/matched-skills/reasons whenever V2 search succeeds - verified live
against the real profile. The legacy `app.ai.matcher.JobMatcher` remains
the presentation layer only when V2 is disabled or V2 search/ranking
itself fails, unchanged from before. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)'s "The V1/V2 split" for the
exact mechanism (a stashed `MatchResult` per job, checked by
`_rank_jobs()`) and "Why two matchers exist instead of one" for the known,
now-visible remaining gap: V2's matcher still lacks V1's Finnish-language
title terms, exclusion list, and experience-requirement penalties.

## Sources

Registered sources: Duunitori, Jobly, Tyomarkkinatori, Work in Finland.

- **Duunitori**: working. A live search collected 35 jobs. A bug where
  the scraper trusted a JSON-LD field that actually holds an internal
  occupation-taxonomy slug (not the real title) was found and fixed this
  session - see [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).
- **Jobly**: working. A live search collected 17 jobs.
- **Tyomarkkinatori**: returns 0 jobs. Root cause is **not** TLS (a prior
  claim to that effect was re-investigated and disproved this session) -
  it's that job listings are loaded by client-side JavaScript not present
  in the static HTML this project's scraper fetches. See
  [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for the full
  investigation.
- **Work in Finland**: returns 0 jobs, same underlying cause
  (client-side-rendered listings) as Tyomarkkinatori, independently
  confirmed.

A live V2 search currently collects 45 unique jobs total (35 + 17 from
the two working sources).

## Profile

Profile file: `profiles/profile.json`

Contains: 17 skills, 13 target titles, 4 target locations, plus
experience, education, certifications, languages, interests.

**Fixed this session**: the file was previously wrapped in a Markdown
code fence (` ```json ... ``` `), making it invalid JSON. Since profile
loading failures were caught silently and fell back to an empty profile,
this meant the live dashboard was matching every job against 0 skills/
titles/locations with no visible error. Fixed; regression test added
(`tests/test_profile_integrity.py`).

## Tests

Current test result: **54 passed**

Run with:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Full breakdown by file: [docs/TESTING.md](docs/TESTING.md). 30 of the 54
tests were added this session, each a direct regression test for a
specific bug found and fixed: profile corruption, the ranking module
collision, the Duunitori title bug, the SSRF-adjacent domain guard, the
broken dashboard job-action links, a saved-jobs duplicate-record bug
(user-reported), four broken sidebar navigation links, the CV upload
path, and the V1/V2 ranking-unification (V2's own score silently
discarded before reaching the dashboard).

## Flask

The dashboard works with V2 enabled - verified live (not just read from
code): dashboard loads and shows V2's own score/matched-skills/reasons
directly (not a legacy re-score), job-action links resolve to real ids,
save-job persists (without creating duplicates) and shows up under
`/applications`, every sidebar link resolves without a 404, CV upload
extracts and displays real `.docx`/`.pdf` data for review, and the
resume/cover-letter generation routes fail fast and gracefully (503)
instead of hanging when the local Ollama model is slow/unavailable,
verified with a live timed test.

Main web integration: `app/web/routes.py`.

## Important design rules

1. Do not disable TLS verification merely to make a source work.
2. Do not remove existing tests to make a change pass.
3. Preserve backwards compatibility where practical.
4. Keep V2 logic inside `app/search/v2`.
5. Keep profile data in `profiles/profile.json`.
6. Run `pytest` after meaningful changes.
7. Run `py_compile` after structural Python changes.
8. Do bulk changes when several related files need modification.
9. Do not redo completed work.
10. Update `HANDOFF.md` whenever a development session ends.
11. Update `CHANGELOG.md` when a meaningful feature or architectural
    change is completed.
12. Update `NEXT_TASKS.md` when priorities change.
13. Verify claims against the actual code/live behavior before writing
    them into documentation or a handoff - two claims in this file's
    prior version (the TLS failure theory, the profile's assumed
    validity) were wrong and caused real, silent bugs. Trust the code
    over prior notes.

## Documentation

Full set complete: `README.md` plus `docs/ARCHITECTURE.md`,
`docs/MATCHING_AND_RANKING.md`, `docs/DATA_SOURCES.md`,
`docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT.md`,
`docs/AI.md`, `docs/PRODUCT_VISION.md`, `docs/PORTFOLIO.md`,
`docs/TECHNOLOGY_STACK.md`. All written from direct code inspection and
live verification, not from the (partially inaccurate) prior handoff
notes.

## Current milestone

The V2 search pipeline, profile-aware matching (V2 owns dashboard
presentation when it succeeds; V1 is the tested fallback), dashboard,
saved jobs (duplicate-safe), sidebar navigation, CV upload with
AI-assisted extraction, and AI document generation are all implemented,
tested, and verified working end-to-end. Ten real bugs found through
live investigation across this session (six in the initial audit, plus a
user-reported saved-jobs bug, a self-discovered navigation bug, a
JSON-extraction fragility found while wiring up CV upload, and V2's own
score being silently discarded before reaching the dashboard) are fixed.
Documentation is complete and accurate as of this update.

Remaining honestly-scoped work (see
[NEXT_TASKS.md](NEXT_TASKS.md) and
[docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md)): porting V1's
Finnish-language title terms, exclusion list, and experience-requirement
penalties into V2's matcher so its scoring doesn't regress relative to
V1's; getting real data out of the two JS-rendered sources; building the
review-to-profile merge step for CV data; fixing the resume/cover-letter
output-directory mismatch; and a skill-gap feature (already correctly
scoped - needs job-requirement extraction, not just exposing existing
data).
