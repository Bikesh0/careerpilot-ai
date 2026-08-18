# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

The full project-completion pass is done, plus four follow-up fixes made
while continuing autonomously down `NEXT_TASKS.md`: a user-reported
saved-jobs bug, a self-discovered navigation bug, the CV upload feature,
and - most recently - unifying V1/V2 ranking on the dashboard.

## Most recent: V1/V2 ranking unification

**Traced first, before changing code**: V2 search (collection ->
normalization -> dedupe -> matching -> ranking) already computed its own
score/matched_skills/reasons per job, but `app/web/routes.py._search_jobs()`
discarded that `MatchResult` one line after computing it
(`[item.job for item in ranked]`), and `_rank_jobs()` unconditionally
re-scored every job through the legacy `app.ai.matcher.JobMatcher`
regardless of whether V2 had succeeded. That's why the dashboard always
showed V1 scores.

**Fix**: `_search_jobs()` now stashes each job's `MatchResult` onto the
`CanonicalJob` itself (`job._v2_match`), the same technique already used
for `.id`. `_rank_jobs()` checks whether every job in the list carries
one; if so, a new adapter (`_present_v2_ranked_jobs()`) reshapes V2's own
data into the dashboard's presentation format, preserving V2's ranking
order (no re-sort, no re-scoring). If not - V2 disabled, or V2 itself
failed - the exact same legacy `matcher.rank_jobs()` call that existed
before runs, unchanged. Neither matcher's own logic was touched; the only
new code is the adapter and the ownership check. Added a small "match
reasons" list to `dashboard.html` (data that already existed but was
never rendered).

**Tests**: `tests/test_ranking_unification.py` (6) - V2 score/reasons
shown correctly (using reason text only V2 ever produces as proof),
ranking order preserved, legacy mode untouched when disabled, adapter
failure falls back gracefully, save/generate/cover-letter still resolve
V2 jobs.

**Live-verified against the real profile through the real Flask
dashboard** (not just tests): top result "Staff Security Engineer" now
renders with V2's exact score (74%) and V2's exact reason strings on the
page.

**Known, now-visible tradeoff, logged not hidden**: V2's matcher still
lacks V1's Finnish-language title terms, exclusion list, and
experience-requirement penalties, so results differ slightly depending on
whether V2 succeeded for a given request. This is `NEXT_TASKS.md`
Priority 1 now (porting that logic into V2's matcher).

## Everything completed this session, most recent first

1. **V1/V2 ranking unification** (above).
2. **CV upload** - `/settings` + `/settings/upload-cv`, safe file
   handling (UUID filenames, path-traversal-proof, verified), 10MB cap,
   review-only (never auto-writes to `profiles/profile.json`). Hardened
   `ProfileExtractor` against the same JSON-in-fence fragility fixed
   twice before. Fixed a PyMuPDF deprecation warning.
3. **Broken sidebar navigation** - 4 of 8 links 404'd
   (`/resume`, `/coverletter`, `/interview`, `/settings`); fixed, two
   dead/duplicate templates removed (one had the profile.json-style
   fence-corruption bug).
4. **Saved jobs not saving correctly** (user-reported) - `save()` had no
   duplicate detection at all (a differently-named sibling method did,
   but the dashboard never called it), and `job_url` was silently
   dropped from every save. Fixed both.

## Verification

Test result: **54 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

## Documentation updated this round

`docs/ARCHITECTURE.md` ("The V1/V2 split" rewritten, "Why two matchers
exist" updated with the known tradeoff, "Presentation layer" section
split by producer), `docs/MATCHING_AND_RANKING.md` (intro + "Known edge
cases" updated, live-verification note added), `docs/TESTING.md` (new
test file entry), `README.md` (architecture diagram, project structure,
roadmap - including two stale claims found and fixed: V1 matcher
described as unconditionally used by the dashboard, and CV parsing
described as "not yet wired to a route" after it already was),
`docs/PORTFOLIO.md` (updated interview answers, test count, "what's
next"), `NEXT_TASKS.md`, `CHANGELOG.md`, this file.

## Known, honestly-documented limitations (carried forward + new)

- V2's matcher lacks V1's Finnish-language title terms, exclusion list,
  and experience-requirement penalties - now a live, visible difference
  in dashboard results depending on whether V2 succeeded (`NEXT_TASKS.md`
  Priority 1).
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

Per `NEXT_TASKS.md`, in order: Priority 1 (port V1's Finnish
terms/exclusion list/experience penalty into V2's matcher - the natural
continuation of this session's unification work), Priority 2 (real data
from the two JS-rendered sources), Priority 3/3b (CV-to-profile merge
step; output-directory mismatch), Priority 4 (skill-gap feature, already
correctly scoped - it needs job-requirement extraction, not just
exposing existing data), Priority 5/6 (source diagnostics, Ollama wrapper
consolidation - both low urgency), Priority 7 (final verification pass).

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update. The repository and its git history remain the source of
truth over any prior AI conversation, this file included where they
disagree.
