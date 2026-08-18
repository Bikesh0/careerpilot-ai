# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

Every item from the user's explicit release-work list is complete:
V1/V2 matching/ranking architecture (both the dashboard-ownership
unification and, most recently, porting V1's Finnish titles/exclusion
list/experience penalty into V2's matcher), Jobly crawl-delay compliance,
Work in Finland investigation, Ollama cleanup, integration testing,
security review, documentation, and a final release audit. Duunitori
stays disabled, with an explicit no-circumvention policy documented.

## Most recent: ported V1's matching logic into V2

Closed the three specific gaps identified when V2 first took over
dashboard presentation:

- **Finnish-language titles** - ported as **data**, not code. Added the
  same Finnish terms V1 hardcodes (`Tietoturva-asiantuntija`,
  `Tietoturva-analyytikko`, `Kyberturvallisuusasiantuntija`,
  `Kyberturvallisuus`) to `profiles/profile.json["target_titles"]`,
  since V2's title matching has no hardcoded vocabulary of its own to
  add a Python constant to - the profile is the single source of truth
  for this kind of candidate-specific data, consistent with the
  project's existing "don't hardcode personal data in Python" rule
  (which V1's own hardcoded list predates).
- **`EXCLUDED_TITLE_TERMS`** - ported verbatim as code (generic, not
  profile-specific). A match now short-circuits `JobMatcher.score_job()`
  (`score=0.0`, new `MatchResult.excluded=True` field, a specific
  reason), and `JobRanker.rank()` drops any excluded job from the
  ranked output entirely - a real exclusion, not just a low score,
  matching V1's skip-before-scoring behavior.
- **Required-experience penalty** - ported verbatim thresholds (7+
  years: -20 ... 2+: -3) via a new `extract_required_experience_years()`
  signal using V1's exact regex patterns.

Deliberately **not** ported: V1's tiered title-category scoring,
weighted skill importance, the skill alias table, and V1's much steeper
flat seniority-mismatch penalties - a genuine design-philosophy
difference between the two matchers, not a gap to mechanically copy.

Added 8 new regression tests (`tests/test_v2_matching_regressions.py`,
`tests/test_profile_integrity.py`). Live-verified against the real
profile and real Jobly results: 14 jobs, correctly matched and ranked,
scores unchanged for jobs unaffected by the new penalties/exclusion,
zero false exclusions.

## Everything completed this session, most recent first

1. **V1-to-V2 matching port** (above).
2. **Duunitori no-circumvention policy made explicit** - tightened
   `docs/DATA_SOURCES.md`, `NEXT_TASKS.md`, `docs/SECURITY.md` so the
   re-enable guidance can't be misread as suggesting a User-Agent change
   alone is valid. Only two legitimate paths documented: Duunitori's
   explicit permission, or an official/approved API.
3. **Final release audit** - security re-scan (clean), found and fixed
   a gitignore gap (`data/cv_uploads/`) and a live compliance gap
   (`test_sources.py` still ran `DuunitoriSource` directly, bypassing
   the registry-level disable); removed a severely outdated,
   self-duplicated planning document
   (`app/search/docs/V2_SEARCH_ARCHITECTURE.md`) and two 0-byte unused
   files; swept all docs for stale claims; ran one continuous live
   integration pass through every major user flow (all 7 checks passed).
4. **robots.txt compliance** - Duunitori disabled (user's explicit
   decision, largest source, reported directly not silently handled),
   Jobly crawl-delay added, Tyomarkkinatori API investigated and
   deliberately not shipped for the same reason.
5. **Ollama wrapper consolidation** - `AIEngine` removed, everything
   migrated onto `LocalLLM`.
6. **V1/V2 ranking unification** - dashboard shows V2's own scoring when
   V2 succeeds, instead of always re-scoring through the legacy matcher.
7. **CV upload** - `/settings` + `/settings/upload-cv`, safe file
   handling, review-only.
8. **Broken sidebar navigation** - 4 of 8 links 404'd; fixed.
9. **Saved jobs not saving correctly** (user-reported) - duplicate
   detection and `job_url` persistence both fixed.

## Verification

Test result: **63 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

Live-verified through direct `V2SearchService.search()` calls and the
real Flask dashboard at multiple points this session, most recently: 14
real Jobly jobs, correctly matched/ranked, zero false exclusions, scores
consistent with pre-port values for unaffected jobs.

## Documentation

Complete and reviewed for staleness across this session:
`README.md` + `docs/ARCHITECTURE.md`, `docs/MATCHING_AND_RANKING.md`,
`docs/DATA_SOURCES.md`, `docs/SECURITY.md`, `docs/TESTING.md`,
`docs/DEVELOPMENT.md`, `docs/AI.md`, `docs/PRODUCT_VISION.md`,
`docs/PORTFOLIO.md`, `docs/TECHNOLOGY_STACK.md`, `NEXT_TASKS.md`,
`CHANGELOG.md`, `PROJECT_STATE.md`, this file.

## Known, honestly-documented limitations

- **Duunitori is disabled**, and stays disabled, pending Duunitori's
  explicit permission or an official/approved API - no circumvention
  path is in scope (`NEXT_TASKS.md` Priority 1).
- Tyomarkkinatori returns 0 results for the same reason - a working API
  integration exists but wasn't shipped.
- V2's matcher still has design-philosophy differences from V1 (tiered
  title scoring, weighted skills, steeper seniority penalties) -
  deliberately not ported, see `docs/ARCHITECTURE.md`.
- CV upload stops at review; nothing merges extracted data into
  `profiles/profile.json` yet (`NEXT_TASKS.md` Priority 2).
- `WebActions.latest_resume()`/`latest_cover_letter()` point at the wrong
  directory (`NEXT_TASKS.md` Priority 2b).

## Exact next task

All items explicitly requested this session are done. Remaining work is
entirely in `NEXT_TASKS.md`, in priority order, and every remaining
priority needs either a human decision/outreach (Duunitori/
Tyomarkkinatori permission, the CV-merge UX) or is explicitly low-urgency
(skill-gap feature, source diagnostics).

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update. The repository and its git history remain the source of
truth over any prior AI conversation, this file included where they
disagree.
