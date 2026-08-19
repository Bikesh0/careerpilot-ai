# CareerPilot AI - Changelog

## 2026-08-19 - Employment mission: AI-coached projects, real recommendation paths, UI-copy cleanup

Personal employment mission work order: made the product genuinely
usable end-to-end for its actual first user, not just feature-complete.
Read the real code/tests before changing anything (per the work order's
own "first rule"); did not rebuild anything that already worked.

**Investigated a real bug report** ("a job I never applied to appeared
as Interview-stage"): traced `update_status()`'s only caller
(`/status/<id>/<status>`, always an explicit click) and confirmed no
code path changes a status automatically. Root cause was this session's
own live-verification scripts writing to the real `data/careerpilot.db`
instead of an isolated copy. Cleared the polluted rows with the user's
explicit confirmation first (never unilaterally), and established a
firm rule going forward: any manual verification touching persistence
must use an isolated working directory, matching what the automated
test suite already enforces.

**AI-coached practical projects** (`app/database/project_tracker.py`,
`app/services/project_service.py`, `app/ai/project_coach.py`,
`/projects`, `/projects/<id>`): the mechanism that turns a
recommendation into real evidence. Start a project from any Layer 2
skill-gap recommendation or Layer 1 CV-strength weakness (a new
job-independent `/projects/start-general/<skill_key>` route). Status
only ever changes via an explicit click
(`Planned -> In Progress -> Completed -> Verified` - verified directly
that nothing changes it as a side effect). The AI coach gives a
step-by-step starting plan (`plan()`), answers open technical questions
(`ask()`), and reviews real pasted work (`review()`) - all grounded,
never claiming completed work that wasn't submitted. A `Verified`
project drafts a CV bullet (gated at the route level, grounded only in
the project's own recorded text) and strengthens that skill's evidence
on the CV-strength page, even for a skill not yet in the profile's
declared list.

**Layer 1 (CV strength) now gives a complete practical path**: a
weakly-evidenced skill matching the curated catalog
(`app/ai/skill_gap.py`'s `SKILL_CATALOG`) shows what to build, how, a
realistic time estimate, and a "Start this project" button - the same
real, hand-curated data Layer 2 already used for job-specific gaps,
instead of a bare "add an example" line.

**Layer 2 (skill gap) leads with strengths**: a "You already
demonstrate" section now appears before any gap detail, and the page
gained a direct Apply/View-posting link - found missing during live
verification (the dashboard card had one, this deeper analysis page
didn't).

**Match-score labels double-checked**: "Profile Match" and "Requirement
coverage" (relabeled/explained in the prior session) confirmed still
correct and re-tested.

**UI copy cleanup**: removed internal implementation language from user
-facing pages - "How this works: deterministic, zero AI-generated
content...", `profiles/profile.json` file-path references, "review-only
preview" phrasing - from `skill_gap.html`, `cv_strength.html`, and
`settings.html`. That reasoning now lives only in `docs/`. Added
`Withdrawn` as an application status (was missing from the funnel).

Added 24 new regression tests (project tracking/routes, the plan/review
AI-coach actions, the job-independent start-project route, the CV
-strength recommendation-path enrichment, UI-jargon-absence checks, and
the Apply-link checks on both the dashboard and the skill-gap page).
Full suite: 148 passed (was 134 at the end of the prior session's
batch). Live-verified end-to-end in an isolated working directory (CV
strength -> start project -> save job -> mark Interview -> Interview
Prep button appears -> gated route -> applications page), correctly
never touching the real database this time.

Updated `docs/PRODUCT_VISION.md`, `docs/AI.md`, `docs/TESTING.md`,
`docs/PORTFOLIO.md`, `README.md`, `PROJECT_STATE.md`, `NEXT_TASKS.md`,
and `HANDOFF.md`.

## 2026-08-19 - Career-advisor pivot: CV strength, ready-to-apply, gated interview prep, application funnel

Final V2 release/production-readiness work order: verified the existing
implementation against the actual repository first (traced every claim
against real code/tests, not prior notes), then extended it. Full
release status and honest scope boundaries are in
`docs/PRODUCT_VISION.md`; this entry summarizes what changed.

**Layer 1 - CV strength** (`app/ai/cv_strength.py`, `/cv-strength`, new
sidebar link): job-independent skill proficiency
(Basic/Intermediate/Advanced, computed from real evidence in experience
text and certifications, not just list membership), strengths surfaced
first, then a capped, prioritized list of the highest-value
improvements. Zero LLM calls - same reasoning as the existing skill-gap
engine. Found and fixed a real bug while building it: proficiency level
and its evidence-text explanation were computed independently and could
contradict each other (a skill reaching "Advanced" purely via a
certification match, with zero experience evidence, was paired with
evidence text implying it *was* demonstrated on the job) - fixed by
computing both together in one function.

**Layer 2 additions** to `app/ai/skill_gap.py` / `/analyze/<job_id>`:

- **Ready to apply**: conservative by design - only `True` when at least
  one requirement was detected and every one is covered, never invented
  to look encouraging.
- **One next best action**: apply now / close the single quickest
  missing required skill / strengthen the most useful weak CV evidence /
  an explicitly-optional nice-to-have - instead of a checklist, with the
  full breakdown still available below it.
- **Honest match-score-improvement estimate**: re-runs V2's real
  `JobMatcher.score_job()` twice (current profile vs. profile with the
  missing required skills added) - the same deterministic function the
  dashboard uses, not a separate guess - and is explicitly marked
  non-meaningful (not exaggerated) when the real delta is negligible.

**Application funnel** (`app/services/application_service.py`,
`app/database/application_tracker.py`): added Second Round, Final Round,
and No Response statuses; `interview_stage_or_later` now counts real
progress (Interview/Second Round/Final Round/Offer) instead of just the
exact "Interview" status; a new `_funnel_insight()` produces one calm,
honest observation on the dashboard (e.g. "reaching interviews - focus
on interview prep next"), requiring a minimum sample size before
suggesting any direction change so a handful of applications can't
produce a false signal.

**Gated interview preparation** (`app/ai/interview_prep.py`,
`/interview/<job_id>`): the fourth LLM call site in this codebase (after
resume, cover letter, and CV extraction) - grounded the same way (no
invented experience), but access-controlled: only reachable once a
job's saved application has actually reached "Interview" status or
later, via `ApplicationService.status_for_job_url()` and
`INTERVIEW_STAGE_STATUSES`. A "Interview Prep" button appears on a
dashboard job card only once that job qualifies.

**CV-upload hardening** (`app/web/routes.py`): 24-hour retention
cleanup (`_cleanup_old_uploads()`), a lightweight in-memory rate limiter
(20/min/IP), and a direct regression test hashing the real
`profiles/profile.json` before and after an upload to prove it's never
modified - the master-profile-protection guarantee was already true by
construction (no write path exists), now it's also verified, not just
asserted.

**Deliberately not built**, with reasons documented in
`docs/PRODUCT_VISION.md` and `docs/SECURITY.md`: true per-visitor
session-isolated personalization (would need session-scoped profile
threading through nearly every route, plus CSRF protection - flagged as
`NEXT_TASKS.md` Priority 5), a deterministic "reorder don't regenerate"
CV-tailoring rearchitecture (Priority 6), and a persistent/progressive
skill-proficiency store with a completion-tracking workflow (Priority
7). Verified that `app/ai/analyzer.py`/`decision.py`/`suitability.py`/
`skill_map.py`/`scoring.py`/`target_scorer.py` (pre-existing, V1-CLI-only
legacy code) don't already cover any of this before building anything
new.

Added 19 regression tests across `tests/test_cv_strength.py`,
`tests/test_cv_strength_route.py`, `tests/test_application_funnel.py`,
`tests/test_status_transitions_route.py`, `tests/test_interview_prep.py`,
`tests/test_cv_upload_hardening.py`, plus 7 more in the existing
`tests/test_skill_gap.py`/`tests/test_skill_gap_route.py`. Full suite:
110 passed (was 91 before this batch, 75 at the start of this session).
Live-verified through the real Flask dashboard against real, live
sources.

Updated `README.md`, `docs/PRODUCT_VISION.md`, `docs/MATCHING_AND_RANKING.md`,
`docs/AI.md`, `docs/PORTFOLIO.md`, `docs/TESTING.md`, `docs/DATA_SOURCES.md`,
`docs/SECURITY.md`, `PROJECT_STATE.md`, `NEXT_TASKS.md`, and `HANDOFF.md`.

## 2026-08-19 - Add career-recommendation engine: skill-gap analysis, certifications, courses, projects, CV evidence checks

Verified the original product plan's career-development recommendation
functionality against the actual codebase before building anything.
Traced every candidate module (`app/ai/analyzer.py`, `decision.py`,
`suitability.py`, `skill_map.py`, `scoring.py`, `target_scorer.py`) and
confirmed none of it is reachable from the Flask dashboard - it's V1-CLI
-only code (`main.py`, a standalone script), `SuitabilityEngine` is a
stub that always returns zeros, and none of it does certification/
course/project recommendation at all. Left that legacy code untouched
(out of scope) and built the real feature as a new module.

**`app/ai/skill_gap.py`** + **`/analyze/<job_id>`** (a new "Skill Gap"
button on every dashboard job card):

- **Genuine skill-gap detection**, not the matchers' inverse
  `missing_skills`. Both matchers' `missing_skills` means "profile
  skills this job's text doesn't happen to repeat" - a posting asking
  for a skill entirely absent from the profile (e.g. Terraform) was
  invisible to both matchers. This feature scans job text against a
  curated ~30-skill taxonomy and checks the *candidate's* skills,
  experience, certifications, and summary text for real evidence of
  each one - a genuine gap now surfaces with a real recommendation.
- **Required vs. nice-to-have**, classified per sentence via a
  hedging-language heuristic ("nice to have", "preferred", "a plus",
  "bonus", ...) rather than assuming clean section headers exist in
  scraped job text.
- **Certification/course/project recommendations** from a small,
  hand-curated catalog of real, well-known, currently-existing
  resources - no LLM call, by deliberate design (see docs/AI.md): a
  hallucinated certification recommendation is a worse failure than a
  hallucinated cover-letter sentence, so every recommendation is
  verifiable by construction instead. Certifications are never invented
  for skills that don't have a real standalone one (Git, VPN correctly
  have an empty certifications list).
- **Prioritization by relevance and effort**: missing required skills
  first, then nice-to-have, each ordered by a rough (min, max) effort
  estimate, quickest first.
- **CV/profile evidence check**: a skill claimed in the profile's bare
  skills list but never demonstrated in an experience entry (or vice
  versa) is flagged with a suggestion to add a concrete example - never
  an invented one.

Found and fixed one real bug while building this: `app/ai/skill_gap.py`'s
word-boundary tokenizer initially kept periods in the normalized
character set (mirroring `app/search/v2/matching/signals.py`'s
`normalize_skill`), which is harmless there but silently broke matching
here - a requirement sentence almost always ends with the skill name
immediately followed by a period ("...experience with Terraform."), and
the glued-on period meant the token never equaled the bare alias. Fixed
by excluding periods from this module's normalizer (a different,
deliberately independent implementation from V2's, not a shared one -
see docs/MATCHING_AND_RANKING.md).

Added 12 regression tests (`tests/test_skill_gap.py`,
`tests/test_skill_gap_route.py`) covering required-vs-nice-to-have
classification, genuine-gap detection, CV-evidence notes (both raised and
correctly absent), the no-fabricated-certifications guarantee,
effort-based prioritization ordering, the "no requirements detected"
flag, the punctuation regression, and the full dashboard-to-analysis
route end to end. Live-verified through the real Flask dashboard with
`CAREERPILOT_SEARCH_V2=1` against a real, live Jobly search (14 jobs) -
`/analyze/<id>` rendered correctly for a real posting ("OT Cybersecurity
Engineer"), showing the full requirement -> skill -> gap -> recommended-
action flow.

Updated `docs/PRODUCT_VISION.md`, `docs/MATCHING_AND_RANKING.md`,
`docs/AI.md`, `docs/PORTFOLIO.md`, `docs/TESTING.md`, `NEXT_TASKS.md`,
`PROJECT_STATE.md`, and `HANDOFF.md`.

Full suite: 75 passed (was 63).

## 2026-08-18 - Port V1's Finnish titles, exclusion list, and experience penalty into V2

Continuing down `NEXT_TASKS.md` (formerly Priority 1, now closed):
closed the three specific V1-only capabilities identified when the V1/V2
ranking-unification first shipped - V2's matcher lacked Finnish-language
title recognition, an exclusion list for obviously unrelated roles, and
an experience-requirement penalty.

- **Finnish-language titles**: ported as *data*, not code. V1 hardcodes
  Finnish terms into a `PRIMARY_TITLES` Python constant; V2's title
  matching has no hardcoded vocabulary at all - it matches against
  whatever `target_titles` the profile supplies. Added the same four
  Finnish terms V1 already used to `profiles/profile.json["target_titles"]`
  (`Tietoturva-asiantuntija`, `Tietoturva-analyytikko`,
  `Kyberturvallisuusasiantuntija`, `Kyberturvallisuus`) rather than
  hardcoding them into matcher code - keeps the profile as the single
  source of truth for candidate-specific data, consistent with this
  project's existing "don't hardcode personal profile data in Python"
  principle (which V1's own hardcoded list predates).
- **`EXCLUDED_TITLE_TERMS`**: ported verbatim as code into
  `app/search/v2/matching/matcher.py` (generic, not profile-specific). A
  title match now short-circuits `JobMatcher.score_job()` - the job gets
  `score=0.0`, a new `MatchResult.excluded=True` field, and a specific
  reason - and `JobRanker.rank()` drops any excluded job from the ranked
  output entirely, matching V1's skip-before-scoring behavior exactly
  (not just a low score).
- **Required-experience penalty**: ported verbatim thresholds from V1's
  `_experience_requirement_penalty` (7+ years: -20 ... 2+: -3), backed
  by a new `extract_required_experience_years()` signal using V1's exact
  regex patterns, subtracted from V2's weighted score before the final
  clamp.

Added 8 regression tests across `tests/test_v2_matching_regressions.py`
(Finnish title matching, exclusion scoring, ranker-level exclusion,
experience-year extraction, experience penalty) and
`tests/test_profile_integrity.py` (confirms the real profile file
contains the Finnish terms). Live-verified against the real profile and
live sources.

Deliberately **not** ported (a design-philosophy difference, not a gap):
V1's tiered title-category scoring, weighted skill importance, the skill
alias table, and V1's much steeper flat seniority-mismatch penalties -
see `docs/ARCHITECTURE.md`'s "Why two matchers exist instead of one" for
the reasoning.

Full suite: 63 passed (was 57).

## 2026-08-18 - Release audit: final security/documentation review

Final pass through the remaining release priorities (security review,
integration testing, documentation review, release audit) after the
robots.txt compliance work below.

**Security re-scan**: confirmed, repo-wide, zero occurrences of
`verify=False`, hardcoded secrets, `subprocess`/`eval`/`exec`/
`pickle.load`, or hardcoded `debug=True`. No secret-shaped files tracked
in git. Found and fixed one real gap: `data/cv_uploads/` (holds real
personal documents once the CV upload feature is used) was not covered
by `.gitignore` - only `data/*.db` was. Added it.

**Found and fixed a second live robots.txt gap**, missed in the earlier
compliance pass: `test_sources.py`, the manual live smoke-check script
this project's own README tells developers to run, still imported and
called `DuunitoriSource().search()` directly - completely bypassing the
registry-level disable. Removed it from that script too, with a comment
explaining why, so running the documented dev workflow can't
accidentally violate `duunitori.fi/robots.txt` again.

**Documentation review** found and removed `app/search/docs/V2_SEARCH_ARCHITECTURE.md`
- a tracked, ~67KB planning/interview-prep document from a very early
V2 development stage, discovered to contain its own content pasted
twice inside itself (a real generation bug), severely outdated (predates
almost this entire multi-session engagement - describes V2 as not yet
integrated into the application, references only 7 early commits, lists
all four sources as equally active), and sitting in a non-standard
location a reader wouldn't expect documentation to live in. The current
`docs/` directory already covers everything it attempted, more
accurately. Also swept every doc for other stale claims and fixed what
was found: `docs/TESTING.md` and `README.md` both still said "39 tests"
(stale since an earlier session's test additions), `docs/DEVELOPMENT.md`
didn't mention that a dashboard load now takes several minutes because
of Jobly's crawl-delay, and `docs/MATCHING_AND_RANKING.md`'s live-
verification examples referenced a Duunitori posting that no longer
appears now that Duunitori is disabled - clarified rather than removed,
since the scoring mechanism itself was still correctly verified.

**Also removed** `bootstrap.py` and `run.py` - two 0-byte files with no
references anywhere in the codebase, confirmed unused before deleting
(not blindly).

**Final integration test**: one continuous live pass (dashboard, /search,
save-job idempotency, applications page, all four sidebar links, CV
upload, generate/cover-letter graceful degradation) run end to end
against the real, now-compliant source set - all 7 checks passed. Full
suite: 57 passed (unchanged - this was cleanup and documentation, not
new functionality).

## 2026-08-18 - robots.txt compliance: Duunitori disabled, Jobly crawl-delay added

Continuing down `NEXT_TASKS.md` Priority 2, used real browser network
inspection (the `claude-in-chrome` tool) to investigate Tyomarkkinatori
and Work in Finland's zero-result sources. Found Tyomarkkinatori's
internal JSON search API (`POST /api/jobpostingfulltext/search/v2/search`),
confirmed it unauthenticated and working, and built and verified a full
`TyomarkkinatoriSource` implementation against it live (4 real,
correctly-matched jobs). **Did not ship it**: `tyomarkkinatori.fi/robots.txt`
explicitly disallows `/api/`. Reverted the implementation rather than
commit it, since a public/unauthenticated endpoint doesn't override the
site's stated crawling policy. Also found, via the same network
inspection, that Work in Finland's "Open jobs" widget loads company-logo
assets directly from `jobly.fi` - strong evidence its listings are
already covered by the existing `JoblySource`, making a separate scraper
low-value.

While checking `robots.txt` for these two, checked it for the two
already-shipped sources too - and found a real, live compliance problem
in the project's **largest** source:

- **`duunitori.fi/robots.txt`** disallows the generic `*` user-agent
  group entirely (`Disallow: /`), with exceptions only for a named
  allowlist of crawlers (Googlebot, Bingbot, etc.). `DuunitoriSource`
  sends a spoofed generic browser User-Agent, matching none of those
  exceptions - it had been running (and was fixed and re-verified
  multiple times) in violation of that policy for this entire session,
  because `robots.txt` was never checked until now. Reported directly
  rather than silently patched or silently left running. **At the
  user's explicit direction, `DuunitoriSource` is now disabled** -
  unregistered from `app/search/v2/registry.py`'s `SOURCE_REGISTRY` and
  `app/search/manager.py`'s `SearchManager.searchers`. The class, its
  title-extraction fix, and its tests are untouched, so re-enabling it
  is a one-line change once compliance is actually resolved (permission
  from Duunitori, and/or an honestly-identifying User-Agent). A live V2
  search now collects 14 jobs (all Jobly), down from 45 - an explicit,
  reported tradeoff, not a silent regression.
- **`jobly.fi/robots.txt`** specifies `Crawl-delay: 10` for the generic
  group, which the scraper wasn't honoring at all. Fixed:
  `JoblySource.get_page()` now sleeps 10 seconds after every request. A
  full Jobly search (14 terms + one detail fetch per matching job) now
  takes several minutes instead of seconds - the accepted cost of
  compliance, per the user's explicit choice to add it.

Added `tests/test_robots_txt_compliance.py` (3 tests): Duunitori is
excluded from both the V1 and V2 source lists; Jobly's `get_page()`
sleeps for the crawl delay on every call. Live-verified end to end
through the actual Flask dashboard after both changes: status 200, 14
real jobs, correctly matched and ranked. Full suite: 57 passed (was 54).

## 2026-08-18 - Consolidate the two Ollama wrapper classes

Continuing down `NEXT_TASKS.md` Priority 6: `app/ai/llm.py`'s `LocalLLM`
and `app/ai/ai_engine.py`'s `AIEngine` were two independent
implementations of the same "call a local model without hanging, return
`None` on failure" pattern - `LocalLLM` used by `app/ai/analyzer.py` and
`app/documents/cover_letter_generator.py`; `AIEngine` (hardened earlier
this session to match `LocalLLM`'s reliability behavior) used by
`ResumeBuilder`, `CoverLetterBuilder`, and `ProfileExtractor`.

Gave `LocalLLM.ask()` an optional `system` parameter (sent as a leading
system-role message, same shape `AIEngine` built by hand), fully
backward compatible with existing single-prompt callers. Migrated all
three `AIEngine` call sites onto `LocalLLM` and removed `ai_engine.py`
entirely - confirmed unused by any other code or test first.

This also fixed a small, real behavior gap in the process: `AIEngine`
defaulted to a hardcoded `model="llama3.1"` with no auto-detection, while
`LocalLLM` auto-detects whichever model is actually installed when
`OLLAMA_MODEL` isn't set. Verified live: after the switch, resume/cover-
letter/CV-extraction all correctly report the actually-installed model
(`"Local LLM: llama3.1:latest"`) and still degrade gracefully within the
configured timeout when Ollama doesn't respond in time.

No test suite changes needed - `tests/test_cv_upload.py` and
`tests/test_ranking_unification.py` mock at the builder-method level, not
the underlying Ollama client, so they were unaffected. Full suite: 54
passed (unchanged).

## 2026-08-18 - Unify V1/V2 ranking on the dashboard

Continuing down `NEXT_TASKS.md` Priority 1: the dashboard always
re-scored every job through the legacy `app.ai.matcher.JobMatcher`,
even when V2 search succeeded and had already computed its own score,
matched skills, and human-readable reasons for the same jobs -
`app/web/routes.py._search_jobs()` discarded that `MatchResult` data
one line after computing it. Traced the complete flow (V2 collection ->
normalization -> dedupe -> matching -> ranking -> `_search_jobs()` ->
`_rank_jobs()` -> legacy `JobMatcher` -> `dashboard.html`) before
changing anything.

Fixed with a small, targeted integration rather than deleting either
matcher or duplicating scoring logic: `_search_jobs()` now stashes each
job's already-computed `MatchResult` onto the `CanonicalJob` itself
(`job._v2_match`, the same dynamic-attribute technique already used for
`.id`). `_rank_jobs()` checks whether every job in the list carries one;
if so, a new adapter (`_present_v2_ranked_jobs()`) reshapes V2's own
score/matched_skills/reasons into the dashboard's existing presentation
format, preserving V2's ranking order exactly (no re-sort). If not - V2
disabled, or V2 search/ranking itself failed and `_search_jobs()` fell
back to `manager.search_jobs()` - the **exact same**
`matcher.rank_jobs()` call that existed before this change runs,
completely unchanged. Ownership is decided by where the data actually
came from, not by re-checking the feature flag.

Added a small "match reasons" list to `dashboard.html` (data that
already existed on both matchers but was never rendered anywhere) so
"why was this job recommended" is now genuinely visible, not just
theoretically available.

Added `tests/test_ranking_unification.py` (6 tests): the dashboard
shows V2's exact score and reason text (using reason phrasing only V2's
matcher ever produces, and a job description V1 would score very
differently, as unambiguous proof); V2's ranking order is preserved;
legacy mode is provably untouched when V2 is disabled; a presentation
adapter failure falls back to the legacy matcher instead of crashing;
save/generate/cover-letter routes still resolve V2 jobs correctly.

**Live-verified against the real profile and the real Flask dashboard**
(not just the test suite): the same top result from earlier live
testing ("Staff Security Engineer") now renders with V2's exact score
(74%) and V2's exact reason strings ("Target job title matched",
"Matched 6 profile skills", "Target location matched", "11 profile
skills not found") directly on the page.

**Known, now-visible tradeoff**: V2's matcher still lacks V1's
Finnish-language title terms, exclusion list, and experience-requirement
penalties, so a Finnish-titled posting scores differently depending on
whether V2 succeeded for that request. Logged as `NEXT_TASKS.md`
Priority 1 (the natural next step, not treated as newly discovered
scope) rather than silently accepted.

Full suite: 54 passed (was 48).

## 2026-08-18 - Feature: CV upload with AI-assisted extraction (review-only)

Continuing down `NEXT_TASKS.md` Priority 3: wired up `CVParser`
(PDF/DOCX text extraction) and `ProfileExtractor` (LLM-based CV-to-JSON),
both previously implemented and unit-tested in isolation but unreachable
from any route.

New: `GET /settings` (upload form) and `POST /settings/upload-cv`. File
handling never trusts the client-supplied filename beyond its extension
(checked against a `.pdf`/`.docx` allow-list) - the file is always saved
under a fresh `uuid4().hex` name in `data/cv_uploads/`, verified directly
with a test that uploads a file named `"../../evil.docx"` and asserts it
cannot escape that directory. Request bodies are capped at 10MB
(`app.config["MAX_CONTENT_LENGTH"]`).

Deliberately stops at review: extracted data is displayed on `/settings`,
never automatically written to `profiles/profile.json` - a bad or
AI-hallucinated extraction should not be able to silently corrupt the
profile that matching, resumes, and cover letters all depend on. Logged
as a separate, explicit next step in `NEXT_TASKS.md`.

While wiring this up, hardened `ProfileExtractor.extract()`
(`app/ai/profile_extractor.py`), which previously called `json.loads()`
directly on the raw model response with no fence-stripping or
`None`-check - the exact bug class found twice already this session
(`profiles/profile.json`, `templates/resume_template.html`). It now
extracts the first `{...}` block from the response (matching the
existing, more robust pattern in `resume_builder.py`) and raises a clear
error instead of an unhandled `TypeError` if the model doesn't respond.

Also fixed a `DeprecationWarning` in `app/parsers/cv_parser.py`
(`import fitz` -> `import pymupdf as fitz`), noticed while live-testing
this now-live code path.

Verified live end to end with real `.docx` and `.pdf` files through the
actual `CVParser` (not mocked). Added `tests/test_cv_upload.py` (4
tests). Full suite: 48 passed.

## 2026-08-18 - Fix: broken sidebar navigation links

While continuing down `NEXT_TASKS.md` after the saved-jobs fix below,
found that four of the eight links in the dashboard's sidebar
(`templates/base.html`) - `/resume`, `/coverletter` (bare, no job id),
`/interview`, `/settings` - had no matching Flask route at all and
404'd. Also found their two backing templates for a "generate a
document" landing page, `templates/resume_template.html` and
`templates/cover_template.html`, were dead/unused (confirmed via a
repo-wide search for any `render_template()` or Jinja include
referencing them) and superseded duplicates of the actually-used
`resume.html`/`coverletter.html` - one of them, `resume_template.html`,
also had the same Markdown-code-fence corruption bug found in
`profiles/profile.json` earlier this session, wrapping its entire body
in a stray ` ``` ` block.

Removed both dead templates. Added `/resume` and `/coverletter` (bare)
as redirects to the dashboard - generation is inherently job-specific
(`/generate/<id>`, `/coverletter/<id>`), so there's no meaningful
standalone page for the un-parameterized link - and `/interview`/
`/settings` now render their existing, honest "Coming soon" placeholder
templates instead of 404ing.

Also found, documented but did not build on: `app/web/actions.py`'s
`WebActions.latest_resume()`/`latest_cover_letter()` look for generated
files in `resumes/`/`cover_letters/`, but `ResumeGenerator`/
`CoverLetterGenerator` actually save to `output/` - those helpers would
never find anything even if wired up. Left as a known gap in
`NEXT_TASKS.md` rather than fixed opportunistically alongside an
unrelated navigation fix.

Added `tests/test_sidebar_navigation.py`. Full suite: 44 passed.

## 2026-08-18 - Fix: saved jobs not saving correctly

Investigated a user-reported issue ("saved jobs are not saving correctly
from the dashboard") by tracing the complete flow - dashboard -> `Save
Job` link -> `/save/<id>` -> `ApplicationService` -> `ApplicationTracker`
-> SQLite -> `/applications` page - and reproducing with a Flask test
client against an isolated database before changing any code.

Found and fixed two real bugs:

- **Saving the same job twice created a duplicate database row.**
  `ApplicationTracker.save()` (what the dashboard's `/save/<id>` route
  actually calls) had no duplicate detection at all. A separate,
  differently-named sibling method (`save_job()`, used only by the V1 CLI
  agent) did have dedup logic, but the dashboard never went through it.
- **The job's URL was silently dropped on every save.** `job_url` was
  accepted by `Application`/`ApplicationService.save_job()` but was never
  in the `applications` table's schema or `ApplicationTracker.save()`'s
  `INSERT` statement.

Added a `job_url` column (safe/additive migration) and a shared
`ApplicationTracker.find_existing()` duplicate check (by `job_url`, or
company+title as a fallback for older rows), used by both save methods.
Re-saving an already-saved job now returns the existing record instead of
inserting a duplicate, and no longer resets its status.

Added `tests/test_dashboard_save_job.py`: full-flow persistence and
display, duplicate-prevention, V2 `CanonicalJob` compatibility, and a
fast unit-level dedup test on `ApplicationTracker` directly. Full suite:
**43 passed** (was 39).

## 2026-08-18 - V2 completion, live bug fixes, and full documentation

### V2 search foundation completed

Committed the previously-uncommitted V2 job search architecture: canonical
job model, normalization, deduplication, source registry/runner, matching,
ranking, Flask integration, and profile-aware configuration
(`app/search/v2/`).

### Bugs found and fixed (each verified live, not just read from code)

- **`profiles/profile.json` was invalid JSON** (wrapped in a Markdown code
  fence), and the app silently fell back to an empty profile on any
  loading failure. This meant every job was matched against 0 skills/
  titles/locations with no visible error - the root cause of most
  ranking-quality complaints in the prior handoff. Fixed; regression test
  added.
- **A stray `app/search/v2/ranking.py` file shadowed the real
  `app/search/v2/ranking/` package** (Python resolves the package first),
  so a newer, bug-fixed ranker was dead code while an older ranker with a
  real crash bug (comparing `datetime` and `str` on a score tie) was
  silently active. Consolidated and fixed.
- **Duunitori's scraper trusted the wrong JSON-LD field for job titles** -
  `JobPosting.title` on that site holds an internal occupation-taxonomy
  slug, not the posted title, which zeroed out title-match scoring for
  most Duunitori postings. Fixed to prefer the page's `<h1>`.
- **The dashboard's Generate Resume / Cover Letter / Save Job links were
  broken whenever V2 search succeeded** - `CanonicalJob` has no `id`
  field and the job-lookup list (`manager.latest_jobs`) was never
  populated on the V2 path. Fixed; verified live via a Flask test client.
- **`AIEngine.ask()` (the resume/cover-letter generation path) had no
  request timeout** and could hang a Flask request indefinitely when the
  local Ollama model was slow. Reproduced live, then fixed with the same
  bounded-timeout pattern already used elsewhere in the codebase;
  verified the fixed route now fails gracefully within the configured
  timeout instead of hanging.
- **Flask ran with `debug=True` hardcoded** (interactive-debugger RCE
  risk if ever exposed beyond localhost). Now off by default, opt-in via
  `FLASK_DEBUG=1`.
- **A same-domain safety check was missing** before following any link
  scraped out of third-party job-listing HTML, meaning an absolute
  off-domain link could have been fetched as if it were a job posting.
  Added `is_same_site()` guard across all four sources.
- **Several packages used `_init_.py` instead of `__init__.py`**
  (`app/database`, `app/search/sources`, `tests/utils`) - one of them,
  `tests/utils/_init_.py`, contained a stray, syntactically-broken code
  fragment that would have crashed on import once correctly named. Fixed
  and cleaned up.

### Root-cause investigation (previous claims re-verified, not trusted)

The prior handoff claimed Tyomarkkinatori failed on a TLS certificate
error. Re-investigated from scratch: not reproducible through this
project's actual `requests`+`certifi` code path. The real cause of both
Tyomarkkinatori and Work in Finland returning zero results is
client-side-JavaScript-rendered job listings not present in the static
HTML this project's scraper fetches - confirmed by inspecting the actual
fetched content for each site. Documented in `docs/DATA_SOURCES.md`.

### Cleanup

Untracked a stale, unused root-level `careerpilot.db` (superseded by the
actively-used, already-gitignored `data/careerpilot.db`) and a tracked
generated resume file; removed one-off local backup directories and an
obsolete bulk-patch script (`apply.ps1`); expanded `.gitignore`
accordingly.

### Documentation

Full documentation set written from direct code inspection and live
verification: `README.md` (rewritten), `docs/ARCHITECTURE.md`,
`docs/MATCHING_AND_RANKING.md`, `docs/DATA_SOURCES.md`,
`docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT.md`,
`docs/AI.md`, `docs/PRODUCT_VISION.md`, `docs/PORTFOLIO.md`,
`docs/TECHNOLOGY_STACK.md`. Explicitly documents the current V1/V2
dual-matcher state on the dashboard as a real architectural tradeoff
rather than silently resolving or hiding it.

### Verification

Test suite: **39 passed** (24 baseline + 15 new regression tests, one per
bug fixed above).

Live V2 search: **45 unique jobs** collected (35 Duunitori, 17 Jobly, 0
from the two JS-rendered sources - by root-caused design, not silent
failure).

Live-verified end-to-end: dashboard load, job-action links, save-job
persistence through to `/applications`, and the resume-generation route's
graceful-timeout behavior under a forced short `OLLAMA_TIMEOUT`.

## Previous entries

Prior to this session's audit, the changelog described V2's initial
implementation with a since-corrected claim of "24 passed" tests and an
inaccurate TLS-failure theory for Tyomarkkinatori. See git history for
the original text; it is superseded by the entry above.
