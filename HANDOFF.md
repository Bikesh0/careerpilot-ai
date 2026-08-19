# CareerPilot AI - Session Handoff

## Last Updated

2026-08-19

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

Every item from the user's explicit release-work list (prior session) is
complete: V1/V2 matching/ranking architecture, Jobly crawl-delay
compliance, Work in Finland investigation, Ollama cleanup, integration
testing, security review, documentation, and a final release audit.
Duunitori stays disabled, with an explicit no-circumvention policy
documented.

This session verified and completed the career-development
recommendation functionality from the original product plan - see
"Most recent" below.

## Most recent: career-recommendation engine (skill-gap analysis, certifications, courses, projects, CV evidence)

Asked to verify what's actually implemented for skill-gap analysis,
skill-improvement/certification/course/project recommendations, and CV
improvement suggestions - and not to claim anything complete without
checking the real code and tests first.

**What tracing found**: `app/ai/analyzer.py`, `decision.py`,
`suitability.py`, `skill_map.py`, `scoring.py`, and `target_scorer.py`
already existed in `app/ai/` and looked, from their names, like they
might already cover this. They don't, and none of it is reachable from
the Flask dashboard users actually see:

- All of it is wired only into `main.py`, a standalone V1 CLI script
  never imported by `webapp.py`/`app/web/routes.py`.
- `SuitabilityEngine.evaluate()` is a stub - it always returns zeros and
  empty lists, and its one test (`tests/test_suitability.py`) only
  checks that the stub's shape doesn't change.
- `JobAnalyzer.analyze()`'s "missing skills" has the exact same inverse
  flaw the matchers do (see `docs/MATCHING_AND_RANKING.md`): it means
  "profile skills this job's text doesn't mention", not "skills the job
  wants that you don't have".
- None of it recommends a certification, course, or practical project at
  all. The dashboard template renders `matched_skills` and match reasons
  only - `missing_skills` is computed by `_present_v2_ranked_jobs()` but
  was never rendered anywhere.
- `skill_map.py`/`scoring.py`/`target_scorer.py` are dead code, imported
  nowhere; `target_scorer.py` would crash on instantiation
  (`config/job_targets.json` doesn't exist).

Left all of that legacy code untouched - out of this session's scope,
and repurposing a disconnected stub isn't the same as building the
feature that was actually asked for. Built the real feature as a new
module instead.

**`app/ai/skill_gap.py`** + **`/analyze/<job_id>`** route (a new "Skill
Gap" button on every dashboard job card, `templates/skill_gap.html`):

- Detects job requirements against a curated ~30-skill taxonomy
  (`SKILL_CATALOG`) covering this profile's domain (Linux, networking,
  cloud platforms, containers, SIEM/security tooling, incident response,
  pentesting, IAM, compliance, etc.).
- Classifies each detected skill as required or nice-to-have via a
  per-sentence hedging-language heuristic, not a structural parse.
- Checks the skill against the *candidate's* full profile text (skills
  list, experience descriptions, certifications, summary) - not just the
  bare skills list - so a genuinely absent skill (e.g. Terraform, never
  in the profile at all) surfaces as a real, actionable gap. This is the
  actual fix for the flaw both matchers' `missing_skills` field has.
- For each real gap: real certifications with an honest "why", real free
  courses from well-known providers, and a realistic hands-on project
  idea - all hand-curated, zero LLM calls (see docs/AI.md for why:
  a hallucinated certification recommendation is a worse failure mode
  than a hallucinated cover-letter sentence).
- Prioritizes missing required skills before nice-to-have, each ordered
  by a rough effort estimate (quickest first).
- For skills the candidate *does* have: flags weak evidence (in the
  skills list but never demonstrated in an experience entry, or vice
  versa) without ever inventing an experience entry to "fix" it.

**A real bug found and fixed while building this**: the word-boundary
tokenizer initially mirrored `app/search/v2/matching/signals.py`'s
`normalize_skill()`, which keeps periods in its allowed character set.
That's harmless for V2's whole-text-blob matching, but this module
tokenizes real sentences from job postings, which almost always end a
requirement with the skill name immediately followed by a period
("...experience with Terraform."). The glued-on period meant the token
never equaled the bare alias, silently hiding the match. Fixed by
excluding periods from this module's (deliberately independent)
normalizer - regression test:
`tests/test_skill_gap.py::test_trailing_sentence_punctuation_does_not_hide_a_skill_mention`.

Added 12 regression tests (`tests/test_skill_gap.py`,
`tests/test_skill_gap_route.py`). Full suite: **75 passed** (was 63).
Live-verified through the real Flask dashboard with
`CAREERPILOT_SEARCH_V2=1` against a real, live Jobly search (14 jobs) -
the dashboard correctly links every job card to `/analyze/<id>`, and a
real posting ("OT Cybersecurity Engineer") rendered the full requirement
-> skill -> gap -> recommended-action flow end to end.

Updated `docs/PRODUCT_VISION.md` (Skill Gap: PLANNED -> IMPLEMENTED),
`docs/MATCHING_AND_RANKING.md` (new "Skill-gap analysis" section),
`docs/AI.md` (new "zero LLM calls, by design" subsection),
`docs/PORTFOLIO.md` (feature description + two interview Q&As),
`docs/TESTING.md`, `NEXT_TASKS.md` (Priority 3 skill-gap item removed as
complete, per this file's own convention; a low-urgency "catalog
maintenance" follow-up added), `PROJECT_STATE.md`, and this file.

## Prior session: ported V1's matching logic into V2

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

## Everything completed across this and the prior session, most recent first

1. **Career-recommendation engine** (above) - skill-gap analysis,
   certification/course/project recommendations, CV evidence checks.
2. **V1-to-V2 matching port** - Finnish titles, exclusion list,
   experience penalty (see "Prior session" above).
3. **Duunitori no-circumvention policy made explicit** - tightened
   `docs/DATA_SOURCES.md`, `NEXT_TASKS.md`, `docs/SECURITY.md` so the
   re-enable guidance can't be misread as suggesting a User-Agent change
   alone is valid. Only two legitimate paths documented: Duunitori's
   explicit permission, or an official/approved API.
4. **Final release audit** - security re-scan (clean), found and fixed
   a gitignore gap (`data/cv_uploads/`) and a live compliance gap
   (`test_sources.py` still ran `DuunitoriSource` directly, bypassing
   the registry-level disable); removed a severely outdated,
   self-duplicated planning document
   (`app/search/docs/V2_SEARCH_ARCHITECTURE.md`) and two 0-byte unused
   files; swept all docs for stale claims; ran one continuous live
   integration pass through every major user flow (all 7 checks passed).
5. **robots.txt compliance** - Duunitori disabled (user's explicit
   decision, largest source, reported directly not silently handled),
   Jobly crawl-delay added, Tyomarkkinatori API investigated and
   deliberately not shipped for the same reason.
6. **Ollama wrapper consolidation** - `AIEngine` removed, everything
   migrated onto `LocalLLM`.
7. **V1/V2 ranking unification** - dashboard shows V2's own scoring when
   V2 succeeds, instead of always re-scoring through the legacy matcher.
8. **CV upload** - `/settings` + `/settings/upload-cv`, safe file
   handling, review-only.
9. **Broken sidebar navigation** - 4 of 8 links 404'd; fixed.
10. **Saved jobs not saving correctly** (user-reported) - duplicate
    detection and `job_url` persistence both fixed.

## Verification

Test result: **75 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

Live-verified through direct `V2SearchService.search()` calls and the
real Flask dashboard at multiple points across this and the prior
session, most recently: a real, live V2 search (14 Jobly jobs) followed
by a real `/analyze/<id>` request against one of those live postings,
rendering the full skill-gap flow correctly.

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
- The skill-gap engine only recognizes skills in its curated ~30-entry
  taxonomy, and splits required-vs-nice-to-have with a per-sentence
  heuristic, not a real parse - both documented in
  `docs/MATCHING_AND_RANKING.md`'s "Skill-gap analysis" section and
  `NEXT_TASKS.md` Priority 4 (low urgency).

## Exact next task

All items explicitly requested across this and the prior session are
done and pushed (commit `2b4d81c`). Remaining work is entirely in
`NEXT_TASKS.md`, in priority order, and every remaining priority needs
either a human decision/outreach (Duunitori/Tyomarkkinatori permission,
the CV-merge UX) or is explicitly low-urgency (skill-gap catalog
maintenance, source diagnostics).

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update. The repository and its git history remain the source of
truth over any prior AI conversation, this file included where they
disagree.
