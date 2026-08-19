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
`_rank_jobs()`).

V2's matcher previously lacked V1's Finnish-language title terms,
exclusion list, and experience-requirement penalties - **all three are
now ported** (Finnish terms as profile data, the other two as code) - see
[docs/MATCHING_AND_RANKING.md](docs/MATCHING_AND_RANKING.md)'s "Ported
from V1". Remaining differences (tiered title scoring, weighted skills,
V1's steeper seniority penalties) are a deliberate design-philosophy
boundary, not a gap - see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)'s "Why two matchers exist
instead of one".

## Sources

Registered and active: Jobly, Tyomarkkinatori, Work in Finland.
Implemented but deliberately **not** registered: Duunitori.

- **Duunitori**: implemented, tested, was working (35 jobs in an earlier
  live search this session, including a real title-extraction bug found
  and fixed - see [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)) - but is
  now **disabled**. `duunitori.fi/robots.txt` disallows the generic `*`
  user-agent group entirely; this scraper's spoofed browser User-Agent
  matches none of the site's named, allowlisted crawlers, so it falls
  under that blanket disallow. It had already shipped, been fixed, and
  been re-verified multiple times before `robots.txt` was checked at
  all. Found, reported directly, and disabled at the user's explicit
  direction (not a unilateral decision) - unregistered from both
  `SOURCE_REGISTRY` (V2) and `SearchManager.searchers` (V1); the class
  and its tests are untouched. See
  [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for how to re-enable it.
- **Jobly**: working. A live search collected 17 jobs (before this
  session's crawl-delay fix - see below). `jobly.fi/robots.txt` also
  specifies `Crawl-delay: 10`, which the scraper wasn't honoring; fixed
  by adding a 10-second pause after every request. A full Jobly search
  now takes several minutes instead of seconds - the accepted cost of
  compliance.
- **Tyomarkkinatori**: returns 0 jobs. Root cause is **not** TLS (a prior
  claim to that effect was re-investigated and disproved this session) -
  it's that job listings are loaded by client-side JavaScript not present
  in the static HTML this project's scraper fetches. Its internal JSON
  API was found via real browser network inspection, and a working
  scraper against it was built and verified live - then deliberately
  reverted, not shipped, because `robots.txt` explicitly disallows
  `/api/`. This is now a permission question, not a technical one. See
  [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for the full
  investigation.
- **Work in Finland**: returns 0 jobs, same underlying cause
  (client-side-rendered listings) as Tyomarkkinatori. Its "Open jobs"
  widget's assets load directly from `jobly.fi`, suggesting its listings
  may already be covered by the existing `JoblySource` - not confirmed
  with full certainty, but reason enough to deprioritize a separate
  scraper until checked more rigorously.

A live V2 search now collects 14 unique jobs total, all from Jobly (the
only currently-active source with real results) - verified live through
the actual Flask dashboard after disabling Duunitori and adding Jobly's
crawl-delay. Down from 45 earlier in the session, when Duunitori was
still active; the tradeoff for compliance was made explicitly, not
silently.

## Profile

Profile file: `profiles/profile.json`

Contains: 17 skills, 17 target titles (13 English + 4 Finnish, added
this session so V2's matcher can recognize Finnish-titled postings - see
`docs/MATCHING_AND_RANKING.md`), 4 target locations, plus experience,
education, certifications, languages, interests.

**Fixed this session**: the file was previously wrapped in a Markdown
code fence (` ```json ... ``` `), making it invalid JSON. Since profile
loading failures were caught silently and fell back to an empty profile,
this meant the live dashboard was matching every job against 0 skills/
titles/locations with no visible error. Fixed; regression test added
(`tests/test_profile_integrity.py`).

## Career-advisor features (this session)

Verified against the actual code/tests before being claimed as done -
see `docs/PRODUCT_VISION.md` for the full flow and honest status labels
(IMPLEMENTED/PARTIAL/PLANNED/BLOCKED/REQUIRES HUMAN DECISION):

- **Layer 1 - CV strength** (`/cv-strength`, `app/ai/cv_strength.py`):
  job-independent skill proficiency (Basic/Intermediate/Advanced,
  computed from real evidence), strengths-first, capped/prioritized
  weaknesses. Zero LLM calls.
- **Layer 2 additions** to the existing skill-gap engine
  (`app/ai/skill_gap.py`, `/analyze/<job_id>`): a conservative "ready to
  apply" signal, a single primary "next best action" instead of a
  checklist, and an honest match-score-improvement estimate computed by
  re-running V2's real `JobMatcher.score_job()` - never a guarantee, and
  explicitly suppressed when the effect wouldn't be meaningful.
- **Application funnel**: expanded statuses (Second Round, Final Round,
  No Response added), an `interview_stage_or_later` stat that counts
  real progress beyond just "Interview", and a one-line adaptive insight
  on the dashboard (`app/services/application_service._funnel_insight()`).
- **Gated interview preparation** (`/interview/<job_id>`,
  `app/ai/interview_prep.py`): AI-generated, grounded, job-specific
  questions - only unlocked once that job's saved application reaches
  "Interview" status or later.
- **CV-upload hardening**: 24-hour retention cleanup, per-IP rate
  limiting (20/min), and a direct regression test proving the master
  profile is never modified by an upload.
- **Explicitly not built**: true per-visitor session-isolated
  personalization, and a persistent/progressive skill-proficiency store
  - both documented with reasons in `docs/PRODUCT_VISION.md`, not
  silently skipped.

## Tests

Current test result: **110 passed**

Run with:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Full breakdown by file: [docs/TESTING.md](docs/TESTING.md). 86 of the
110 tests were added across this and the prior two sessions, each a
direct regression test for a specific bug found and fixed, or a specific
behavior verified: profile corruption, the ranking module collision, the
Duunitori title bug, the SSRF-adjacent domain guard, the broken dashboard
job-action links, a saved-jobs duplicate-record bug (user-reported), four
broken sidebar navigation links, the CV upload path, the V1/V2
ranking-unification (V2's own score silently discarded before reaching
the dashboard), Duunitori/Jobly `robots.txt` compliance (Duunitori
disabled, Jobly crawl-delay added), the V1-to-V2 matching port (Finnish
titles, exclusion list, experience penalty), the skill-gap recommendation
engine (required-vs-nice-to-have classification, genuine skill-gap
detection distinct from the matchers' inverse `missing_skills`,
CV-evidence notes, a sentence-final-punctuation bug that silently hid
skill mentions), and this session's career-advisor features (ready-to-
apply/next-action logic, honest match-score projection, a CV-strength
level/evidence contradiction bug found and fixed, the application
funnel, gated interview preparation, and CV-upload hardening).

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

A final documentation-review pass swept every file for stale claims
(found and fixed: two remaining "39 tests" mentions, a missing note
about Jobly's crawl-delay slowing dashboard loads, live-verification
examples referencing a since-disabled Duunitori posting) and found
`app/search/docs/V2_SEARCH_ARCHITECTURE.md` - a tracked, severely
outdated, internally self-duplicated planning document from a very early
V2 stage, superseded entirely by the docs above. Removed.

## Current milestone

The V2 search pipeline, profile-aware matching (V2 owns dashboard
presentation when it succeeds, with Finnish-title recognition, an
exclusion list, and an experience-requirement penalty ported from V1;
V1 is the tested fallback), dashboard, saved jobs (duplicate-safe),
sidebar navigation, CV upload with AI-assisted extraction, AI document
generation, `robots.txt` compliance across all sources, and a
job-specific skill-gap/career-recommendation engine
(`app/ai/skill_gap.py`, `/analyze/<job_id>`) are all implemented, tested,
and verified working end-to-end. Fourteen real issues found through live
investigation across this and the prior session (six in the initial
audit, a user-reported saved-jobs bug, a self-discovered navigation bug,
a JSON-extraction fragility found while wiring up CV upload, V2's own
score being silently discarded before reaching the dashboard, two
`robots.txt` compliance gaps - Duunitori disallowed entirely, Jobly's
crawl-delay unhonored - a stale, self-duplicated planning document found
during the release audit, and a sentence-final-punctuation bug found
while building the skill-gap feature that silently hid skill mentions
ending a sentence) are fixed, ported, built, or, in Duunitori's case,
resolved by disabling the source at the user's explicit direction.
Documentation is complete and accurate as of this update.

The skill-gap engine was verified against the actual codebase before
being built, not assumed: `app/ai/analyzer.py`, `decision.py`,
`suitability.py`, `skill_map.py`, `scoring.py`, and `target_scorer.py`
already existed in `app/ai/`, but are legacy V1-CLI-only code
(`main.py`, a standalone script disconnected from the Flask app) - none
of them are reachable from the dashboard, `suitability.py` is a stub
that always returns zeros, and none of them do certification/course/
project recommendation at all. They were left untouched (out of this
session's scope) rather than silently repurposed or deleted; the new
feature was built as its own module rather than resurrecting dead code
that doesn't do what was asked.

Remaining honestly-scoped work (see
[NEXT_TASKS.md](NEXT_TASKS.md) and
[docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md)): resolving Duunitori's
disabled status (needs the site's explicit permission, or an
official/approved API - no circumvention path is in scope) and
Tyomarkkinatori's (same, for its own internal API, already built and
verified but not shipped); building the review-to-profile merge step for
CV data; fixing the resume/cover-letter output-directory mismatch;
low-urgency skill-gap catalog maintenance (expanding taxonomy coverage,
periodic manual review of the curated certification/course list); and a
larger, explicitly-deferred item - true multi-visitor session isolation
with personalized per-visitor results, which needs CSRF protection and
session-scoped profile threading through nearly every route before it
would be safe to build (see `docs/PRODUCT_VISION.md` and
`docs/SECURITY.md`).
