# CareerPilot AI - Session Handoff

## Last Updated

2026-08-19

## Current branch

`v2-development`. Working tree and push status as of this update: see
"Exact next task" below - this batch was verified and documented before
being committed/pushed; check `git status`/`git log` for the actual
current state rather than trusting this line in isolation (see
"Important design rule 13" in `PROJECT_STATE.md`).

## Current state

CareerPilot is a working, tested, single-user career-advisor tool: V2
search/matching/ranking, a Flask dashboard, save-job/application
tracking with a full interview funnel, AI resume/cover-letter
generation, CV upload/review, Layer 1 CV-strength analysis, Layer 2
job-specific skill-gap analysis with an honest "ready to apply"/"next
action" flow, and gated interview preparation are all implemented,
tested, and live-verified. Full status, including explicit
IMPLEMENTED/PARTIAL/PLANNED/BLOCKED/REQUIRES-HUMAN-DECISION labels for
every step, is in `docs/PRODUCT_VISION.md` - read that first.

## Most recent: career-advisor pivot (final V2 release work order)

Asked to verify and complete the product's full career-advisor vision:
CV strength scoring, skill proficiency levels, honest match-score
projection, a "ready to apply" / "one next action" UX (not a checklist),
an expanded application funnel with adaptive insight, gated interview
preparation, and a scoped decision on multi-visitor demo safety - all
against the actual repository, not assumed.

**Verified before building anything**: re-confirmed the skill-gap engine
built the prior session was still the only real recommendation
mechanism in the live app (`app/ai/analyzer.py`/`decision.py`/
`suitability.py`/`skill_map.py`/`scoring.py`/`target_scorer.py` remain
disconnected V1-CLI-only legacy code, untouched); re-confirmed
`robots.txt` compliance (Duunitori still unregistered, Jobly's
crawl-delay still present) and the zero `verify=False`/`debug=True`/
`subprocess`/`eval` security posture, both unchanged and not rebuilt.

**Layer 1 - CV strength** (`app/ai/cv_strength.py`, `/cv-strength`, new
sidebar entry): automatic skill proficiency (Basic/Intermediate/
Advanced) computed from real evidence - 2+ experience mentions or a
certification match for Advanced, one mention for Intermediate, bare
list membership only for Basic - strengths surfaced first, then a
capped (max 5), prioritized weakness list. Zero LLM calls, same
reasoning as skill-gap. **Bug found and fixed**: level and its evidence
-text explanation were originally computed by two separate code paths
and could contradict each other (a skill "Advanced" purely via a
certification match, described as "not demonstrated" - technically true
but confusingly worded against an Advanced label). Fixed by computing
both together in one function
(`tests/test_cv_strength.py::test_skill_backed_only_by_certification_says_so_honestly`).

**Layer 2 additions** to `app/ai/skill_gap.py`/`/analyze/<job_id>`:
`ready_to_apply` (conservative - only true when every detected
requirement is covered), `one_next_action` (exactly one primary
recommendation - apply now / close the quickest missing required skill /
strengthen weak CV evidence / an explicitly-optional nice-to-have), and
an honest match-score-improvement estimate that **re-runs V2's real
`JobMatcher.score_job()` twice** (current vs. with the missing required
skills hypothetically added) rather than inventing a separate number -
explicitly marked non-meaningful when the real delta rounds to zero,
proven with a test using a title/location that can't match anything
(`tests/test_skill_gap.py::test_match_score_projection_is_honest_about_negligible_impact`).

**Application funnel** (`app/services/application_service.py`,
`app/database/application_tracker.py`, `templates/applications.html`,
`templates/dashboard.html`): added Second Round/Final Round/No Response
statuses (all reachable via URL-encoded links, e.g. `Second%20Round`,
since Flask's `<status>` path segment can't contain a literal space);
`interview_stage_or_later` counts real progress across
Interview/Second Round/Final Round/Offer, not just the exact
"Interview" status; `_funnel_insight()` produces one calm observation on
the dashboard (many applications/few interviews -> CV/targeting focus;
several interviews/no offers -> interview-prep focus; healthy funnel ->
keep going), requiring a minimum sample (5+ applications) before
suggesting any direction change.

**Gated interview preparation** (`app/ai/interview_prep.py`,
`/interview/<job_id>`): the fourth LLM call site (after resume, cover
letter, CV extraction), grounded the same way, but access-controlled -
`ApplicationService.status_for_job_url()` gates it on
`INTERVIEW_STAGE_STATUSES`, so it's unreachable (no LLM call made at
all) until a job's saved application actually reaches "Interview" or
later. A "Interview Prep" button only appears on a dashboard job card
once that job qualifies (`_attach_interview_readiness()`).

**CV-upload hardening**: 24-hour retention cleanup
(`_cleanup_old_uploads()`, best-effort, runs on every upload attempt), a
dependency-free in-memory rate limiter (20/min/IP, 429 past that), and a
direct regression test that hashes the real `profiles/profile.json`
before and after an upload+extraction to prove the master profile is
never touched - it already was safe by construction (no write path
exists), now that's verified, not just asserted.

**Deliberately not built, with reasons written down** (not silently
skipped): true per-visitor session-isolated personalization (would need
session-scoped profile threading through nearly every route in
`app/web/routes.py` plus CSRF protection - `NEXT_TASKS.md` Priority 5);
a deterministic "reorder don't regenerate" CV-tailoring rearchitecture
(Priority 6); a persistent, completion-tracking skill-proficiency store
(Priority 7). Each has a full writeup in `docs/PRODUCT_VISION.md`
explaining exactly what's missing and why it wasn't attempted under this
session's scope.

Added 19 new regression tests (`tests/test_cv_strength.py`,
`tests/test_cv_strength_route.py`, `tests/test_application_funnel.py`,
`tests/test_status_transitions_route.py`, `tests/test_interview_prep.py`,
`tests/test_cv_upload_hardening.py`) plus 7 more added to the existing
`tests/test_skill_gap.py`/`tests/test_skill_gap_route.py`. Full suite:
**110 passed** (was 91 at the start of this batch, 75 at the start of
this session). Live-verified through the real Flask dashboard with
`CAREERPILOT_SEARCH_V2=1` against real, live sources - see "Verification"
below for the exact results.

Updated `README.md`, `docs/PRODUCT_VISION.md` (substantially rewritten -
new final-product-flow diagram with explicit status labels, "job
requirement -> current skill -> gap -> recommended action" section, CV-
tailoring and multi-visitor-demo scoping writeups), `docs/MATCHING_AND_RANKING.md`,
`docs/AI.md`, `docs/PORTFOLIO.md`, `docs/TESTING.md`,
`docs/DATA_SOURCES.md`, `docs/SECURITY.md` (new "Exposing this app to
testers via a tunnel" section), `PROJECT_STATE.md`, `NEXT_TASKS.md`
(three new priorities), and this file.

## Prior sessions (compressed - see git history/CHANGELOG.md for full detail)

- **Career-recommendation engine** (skill-gap analysis,
  certification/course/project recommendations, CV-evidence checks) -
  `app/ai/skill_gap.py`, `/analyze/<job_id>`. Verified the same legacy
  V1-CLI code wasn't already doing this before building it. Fixed a
  sentence-final-punctuation matching bug found while building it.
- **V1-to-V2 matching port** - Finnish titles (as profile data), the
  exclusion list, and the experience-requirement penalty ported from
  V1's matcher into V2's, closing the gap identified when V2 took over
  dashboard presentation.
- **Duunitori no-circumvention policy** made explicit across
  `docs/DATA_SOURCES.md`/`NEXT_TASKS.md`/`docs/SECURITY.md`.
- **Final release audit** (security re-scan, gitignore gap fix, a live
  `robots.txt`-compliance gap in `test_sources.py`, stale-doc removal,
  a full manual integration pass).
- **robots.txt compliance**: Duunitori disabled (user's explicit
  decision), Jobly crawl-delay added, Tyomarkkinatori's working API
  integration built then deliberately not shipped for the same reason.
- **Ollama wrapper consolidation** (`AIEngine` removed, everything onto
  `LocalLLM`), **V1/V2 ranking unification** (dashboard shows V2's own
  scoring when V2 succeeds), **CV upload** (review-only), **sidebar
  navigation fixes**, and the original **user-reported saved-jobs bug**
  (duplicate detection + `job_url` persistence).

## Verification

Test result: **110 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

Live-verified through the real Flask dashboard with
`CAREERPILOT_SEARCH_V2=1` against real, live Jobly results across this
and prior sessions - most recently, a single continuous pass covering:
`/cv-strength` with the real profile; a real live dashboard search;
`/analyze/<id>` against a real posting; save -> `/status/.../Interview`
-> the dashboard's "Interview Prep" button appearing -> `/interview/<id>`
unlocking. (If this exact pass hasn't been re-run since this file was
last touched, the automated test suite's route-level tests
(`tests/test_interview_prep.py` etc.) cover the identical logic with a
mocked LLM call, so the gating/flow behavior itself is verified either
way - only the "does a real live job render sensibly" check needs a live
run to re-confirm.)

## Documentation

Complete and reviewed for staleness across this session:
`README.md` + `docs/ARCHITECTURE.md`, `docs/MATCHING_AND_RANKING.md`,
`docs/DATA_SOURCES.md`, `docs/SECURITY.md`, `docs/TESTING.md`,
`docs/DEVELOPMENT.md`, `docs/AI.md`, `docs/PRODUCT_VISION.md`,
`docs/PORTFOLIO.md`, `docs/TECHNOLOGY_STACK.md`, `NEXT_TASKS.md`,
`CHANGELOG.md`, `PROJECT_STATE.md`, this file.

## Known, honestly-documented limitations

- **Duunitori is disabled**, pending Duunitori's explicit permission or
  an official/approved API - no circumvention path is in scope
  (`NEXT_TASKS.md` Priority 1).
- Tyomarkkinatori returns 0 results for the same reason.
- V2's matcher still has design-philosophy differences from V1 (tiered
  title scoring, weighted skills, steeper seniority penalties) -
  deliberately not ported, see `docs/ARCHITECTURE.md`.
- CV upload stops at review; nothing merges extracted data into
  `profiles/profile.json` yet (`NEXT_TASKS.md` Priority 2).
- `WebActions.latest_resume()`/`latest_cover_letter()` point at the wrong
  directory (`NEXT_TASKS.md` Priority 2b).
- The skill-gap engine only recognizes skills in its curated ~30-entry
  taxonomy; required-vs-nice-to-have is a per-sentence heuristic, not a
  real parse (`NEXT_TASKS.md` Priority 4).
- **No true multi-visitor personalization** - every visitor to a shared
  deployment sees the one master profile's results; CV upload itself is
  isolated/rate-limited/auto-cleaned, but the dashboard/search/skill-gap
  pages are not session-scoped (`NEXT_TASKS.md` Priority 5). **No CSRF
  protection** - do not expose this app beyond a small group of trusted
  testers (`docs/SECURITY.md`).
- CV tailoring is a full grounded LLM rewrite per job, not the lighter
  deterministic "reorder a stable master CV" approach the product spec
  describes (`NEXT_TASKS.md` Priority 6).
- Skill proficiency (Layer 1) is computed fresh from the profile each
  time - no persistent store, no "mark this project complete to advance
  a skill" workflow (`NEXT_TASKS.md` Priority 7).

## Exact next task

Verify `git status`/`git log` directly rather than trusting a written
claim about push state - this file describes what was built and tested,
not a live git query. If this batch isn't committed/pushed yet: stage,
commit with a message describing the career-advisor batch, `git push
origin v2-development`, then confirm `git status` is clean and local
HEAD matches `origin/v2-development`, following the same ritual used for
every prior batch this session.

After that, remaining work is entirely in `NEXT_TASKS.md`, in priority
order. Priorities 1-4 need a human decision/outreach or are low-urgency
maintenance; Priorities 5-7 (multi-visitor isolation, deterministic CV
tailoring, persistent skill-proficiency tracking) are larger, explicitly
-scoped features that need a real planning pass before implementation,
not a quick follow-up.

## Handoff protocol

Read `README.md` and everything in `docs/` first, starting with
`docs/PRODUCT_VISION.md` for the full flow and honest status of every
step. The repository and its git history remain the source of truth
over any prior AI conversation, this file included where they disagree.
