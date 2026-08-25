# CareerPilot AI - Session Handoff

## Last Updated

2026-08-25

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

## Most recent: career-family/career-intelligence session - all six commits landed locally

A multi-part session (2026-08-24/25) evolved CareerPilot toward the
"career advisor, not just a job matcher" product spec: job-deduplication
improvements, Finland/Europe/Outside-Europe geographic scope filtering,
a UI-copy rename ("Skill Gap" -> "Career Fit & Growth") plus an
Applications empty-state fix, a substantially expanded skill-gap engine
(catalog growth incl. Finnish aliases, section-aware nice-to-have
detection, an additive per-skill evidence field, project-continuity
awareness), and a new career-intelligence layer: an evidence-tier
Living Career Profile, career-track ranking + job-family classification,
application readiness, and an ATS/HR/technical-manager "hiring
perspective" view on `/analyze/<job_id>`. See `docs/CAREER_INTELLIGENCE.md`
for what each new module does and its explicit non-goals (no new
external research/scraping - see that doc's "Explicitly out of scope"
section).

**All six commits are now landed locally on `v2-development`**, each
individually staged, diff-reviewed, and tested before being committed
(the same reconstruct/verify/stage/diff-review/test-run process used
throughout the session), in order:

- `3072417` - Milestone 1: one-sentence career-family connector on a
  skill-gap recommendation, `/analyze/<job_id>`.
- `fcf1681` - Commit 1: application tracker column-order bug, Ashby API
  field name fix (`description` -> `descriptionPlain`), V2's
  canonical-URL dedup signal.
- `acc946d` - Commit 2: Finland/Europe/Outside-Europe geographic scope
  filtering, wired into both V1 and V2.
- `314e879` - Commit 3: "Skill Gap" -> "Career Fit & Growth" rename,
  and the Applications page empty-state fix.
- `464f402` - Commit 4: skill-gap engine expansion (catalog growth incl.
  Finnish aliases, section-aware nice-to-have detection, additive
  per-skill `evidence` field, project-continuity awareness, plus the
  new `app/ai/capability_graph.py`).
- `ad47892` - Commit 5: the career-intelligence layer
  (`app/ai/career_profile.py`, `app/ai/career_tracks.py`,
  `app/ai/application_readiness.py`, `app/ai/hiring_perspective.py`),
  wired into `/cv-strength`, the dashboard, and `/analyze/<job_id>`.

**Do not reopen Milestone 1 or Commits 1-5** unless a future regression
actually requires it. See `NEXT_TASKS.md`'s "Priority 0" for the full
per-commit breakdown.

**Application readiness on `/cv-strength`: closed, not applicable by
design.** `/cv-strength` is the job-independent Layer 1 page; readiness
is inherently job-specific. A synthetic average across postings would
not be grounded in any real job and would conflict with the
no-fabrication principle - see `NEXT_TASKS.md`'s "Explicitly not planned
right now". Resolved, not an open question.

**Testing**: real result is **219 passed, 0 failed**, via
`python -m pytest -q --basetemp=<writable dir>` - see `NEXT_TASKS.md`'s
"Known environment quirk" for why the bare command shows ~51 spurious
errors (a pre-existing Windows temp-directory permission issue, not a
code regression).

**Only remaining working-tree changes are this file and
`NEXT_TASKS.md` themselves**, both updated to record this final state -
no source, template, test, or other documentation file is outstanding.

## Prior session: employment mission - AI-coached projects, real recommendation paths, UI cleanup

Asked to make the product genuinely usable end-to-end for its actual
first user (not just feature-complete), and to investigate a
specifically reported bug: a job that appeared as "Interview"-stage
without ever having been applied to.

**Bug investigated, root cause found**: traced `update_status()`'s only
caller (`/status/<id>/<status>`, always an explicit user click) and
confirmed directly that no code path anywhere changes a status
automatically - not a defect in the shipped application. The actual
cause was this session's own live-verification testing writing to the
real `data/careerpilot.db` instead of an isolated copy (unlike the
automated test suite, which always isolates via `tmp_path`). Found the
exact polluted rows, asked the user how to handle their real data rather
than deciding unilaterally, and cleared them once confirmed. **New rule
going forward, now documented**: any manual verification that touches
persistence must use an isolated working directory - see
`docs/PRODUCT_VISION.md`'s "Investigated" section. (This rule was
violated once more by accident immediately after being established,
during a `/cv-strength` smoke check - caught and corrected the same way,
second time with no repeat since.)

**AI-coached practical projects** (`app/database/project_tracker.py`,
`app/services/project_service.py`, `app/ai/project_coach.py`,
`/projects`, `/projects/<id>`) - the mechanism that turns a
recommendation into real evidence rather than just advice:

- Start a project from any Layer 2 skill-gap recommendation
  (`/projects/start/<job_id>/<skill_key>`) or Layer 1 CV-strength
  weakness (`/projects/start-general/<skill_key>`, job-independent).
- Status only changes by an explicit click - `Planned -> In Progress ->
  Completed -> Verified` - verified directly with a test that re-reads
  a project repeatedly to confirm nothing flips it automatically.
- The AI coach: `plan()` (a day-by-day starting plan with checkpoints),
  `ask()` (open technical Q&A), `review()` (honest feedback on real
  pasted code/config/notes - reviews only what's submitted). All
  grounded in the project's own recorded text.
- `draft_cv_bullet()` is gated to `Verified` status at the *route*
  level (not just the prompt), grounded only in the project's own text,
  always review-only.
- A `Verified` project strengthens that skill's evidence on the
  CV-strength page (`verified_skill_keys` parameter,
  `app/ai/cv_strength.py`) - even for a skill not yet in the profile's
  declared skills list at all.

**Layer 1 now gives a complete practical path**: a weakly-evidenced
skill matching the curated catalog shows what to build, how, a time
estimate, and a "Start this project" button - reusing the exact same
hand-curated data Layer 2 already had, instead of a bare "add an
example" line with nowhere to go.

**Layer 2 leads with strengths**: a "You already demonstrate" section
now appears before any gap detail, and the page gained a direct
Apply/View-posting link - found missing during live verification (the
dashboard card had one, this deeper analysis page didn't).

**UI copy cleanup**: removed internal implementation language from user
-facing pages - "How this works: deterministic...", `profiles/profile.json`
file-path references, "review-only preview" phrasing - from
`skill_gap.html`, `cv_strength.html`, `settings.html`. Verified absent
with dedicated tests, not just removed and assumed gone. Added
`Withdrawn` as an application status (was missing from the funnel).

Added 24 new regression tests. Full suite: **148 passed** (was 134).
Live-verified end-to-end in an isolated scratch directory (confirmed
the real database stayed untouched this time): CV strength -> start
project -> save job -> mark Interview -> Interview Prep button appears
on the dashboard -> route unlocks -> applications page shows the funnel
stat. Interview-prep generation itself hit a real Ollama timeout during
this live check (503, graceful) - expected, documented behavior, not a
bug (the same path is verified with a mocked LLM in the automated
suite).

Updated `docs/PRODUCT_VISION.md`, `docs/AI.md`, `docs/TESTING.md`,
`docs/PORTFOLIO.md`, `README.md`, `PROJECT_STATE.md`, `NEXT_TASKS.md`
(Priority 7 closed for the main case), and this file.

## Prior session: career-advisor pivot (final V2 release work order)

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

- **Career-advisor pivot** (prior session) - Layer 1 CV strength, ready-
  to-apply/one-next-action on Layer 2, honest match-score projection,
  the expanded application funnel with adaptive insight, gated interview
  preparation, CV-upload hardening.
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

**Current (2026-08-25)**: **219 passed, 0 failed**, via
`python -m pytest -q --basetemp=<writable dir>` - see `NEXT_TASKS.md`'s
"Known environment quirk" for why the bare command alone shows ~51
spurious `PermissionError` errors on this machine (pre-existing, not a
regression).

Prior session's verification (2026-08-19), kept for history:

Test result: **148 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

Live-verified in an isolated scratch working directory (not the real
`data/careerpilot.db` - see "Most recent" above for why that matters):
`/cv-strength` with the real profile; a mocked-but-realistic dashboard
search; `/analyze/<id>` with an Apply link and "You already demonstrate"
section; starting a project from a skill-gap recommendation; save ->
`/status/.../Interview` -> the dashboard's "Interview Prep" button
appearing -> the route unlocking; `/applications` showing the funnel
stat; marking a project `Verified`. Real Ollama was reached for the
project's CV-bullet draft (succeeded) and for interview-prep generation
(timed out, correctly returned `503`) - both are pre-existing,
documented behaviors (graceful degradation), not new findings.

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
- **Mostly closed**: skill proficiency now advances via `Verified`
  projects (`NEXT_TASKS.md` Priority 7) - what's still open is narrower:
  no partial credit for `In Progress` work, all-or-nothing at
  `Verified`.
- The AI project coach's `plan()`/`ask()`/`review()` are single-shot,
  not a multi-turn conversation - each call is independently grounded in
  the project's title/description/notes, with no memory of the
  conversation itself beyond what's already saved to notes.
- **Application readiness is not shown on `/cv-strength`** - a closed,
  deliberate decision (job-independent page, job-specific concept), not
  a gap. See `NEXT_TASKS.md`'s "Explicitly not planned right now".
- **The 2026-08-24/25 career-intelligence session's six commits are
  landed locally but not yet pushed** - verify with `git log`/`git
  status` rather than trusting this line; pushing `v2-development` is
  the only remaining step. See `NEXT_TASKS.md`'s "Priority 0".

## Exact next task

Verify `git status`/`git log` directly rather than trusting a written
claim about commit/push state - this file describes what was built and
tested, not a live git query. As of this update, the career-family/
career-intelligence feature split is complete: all six commits
(`3072417`, `fcf1681`, `acc946d`, `314e879`, `464f402`, `ad47892`) are
landed locally on `v2-development`. The only remaining step is
`git push origin v2-development`, then confirm local `HEAD` matches
`origin/v2-development`.

After that, remaining work is entirely in `NEXT_TASKS.md`, in priority
order. Priorities 1-4 need a human decision/outreach or are low-urgency
maintenance; Priority 5 (multi-visitor isolation) and Priority 6
(deterministic CV tailoring) are larger, explicitly-scoped features that
need a real planning pass before implementation, not a quick follow-up;
Priority 7 (skill-proficiency progression) is now mostly closed, with
only minor open edges left.

## Handoff protocol

Read `README.md` and everything in `docs/` first, starting with
`docs/PRODUCT_VISION.md` for the full flow and honest status of every
step. The repository and its git history remain the source of truth
over any prior AI conversation, this file included where they disagree.
