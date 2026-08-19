# Product Vision

## Core mission

CareerPilot's purpose is to make the user more employable and help them
get hired - not to maximize the number of applications sent, generate
endless AI content, or gamify the process. It is a calm AI career
advisor: it should encourage and strengthen the user, tell them plainly
when they're already a good match ("You're ready. Apply."), and never
invent an improvement merely to have something to show.

The intended end-to-end flow, and the honest status of each step. Nothing
below is described as complete unless it was verified working in this
repository as of this session (2026-08-19). Status labels used
throughout this document and the rest of `docs/`:
**IMPLEMENTED**, **PARTIAL**, **PLANNED**, **BLOCKED**, **REQUIRES HUMAN
DECISION**.

```
User Profile                     IMPLEMENTED
     |     profiles/profile.json - the master profile; skills, target
     |     titles/locations, experience, education, certifications.
     v
Layer 1: CV Strength              IMPLEMENTED
     |     /cv-strength (app/ai/cv_strength.py) - a general, job-
     |     independent look at the profile: automatic skill proficiency
     |     (Basic/Intermediate/Advanced, computed from real evidence -
     |     not just presence/absence), strengths surfaced first, then a
     |     short, prioritized list of the highest-value improvements
     |     (never more than 5, so the user isn't overwhelmed).
     v
Job Search                        IMPLEMENTED
     |     V2 pipeline: multi-source collection, normalization,
     |     deduplication (app/search/v2/).
     v
Relevant Jobs                     IMPLEMENTED
     |     Weighted matching + ranking; verified live against the real
     |     profile (see docs/MATCHING_AND_RANKING.md).
     v
Match Explanation                 IMPLEMENTED
     |     Dashboard shows matched skills and human-readable match
     |     reasons (title/location/seniority, missing-skill count) per
     |     job, plus an adaptive one-line insight about the user's own
     |     application funnel.
     v
Layer 2: Skill Gap                IMPLEMENTED
     |     A "Skill Gap" button on every dashboard job card
     |     (/analyze/<job_id>, app/ai/skill_gap.py). Genuinely closes
     |     the gap both matchers' "missing_skills" has (see
     |     "Job requirement -> current skill -> gap" below): required-
     |     vs-nice-to-have detection, real hand-curated certification/
     |     course/project recommendations (zero LLM calls - see
     |     docs/AI.md), and CV-evidence checks that flag weak evidence
     |     without inventing experience.
     v
Project Development (AI-coached)  IMPLEMENTED
     |     "Start this project" on a Skill Gap recommendation creates a
     |     tracked project (/projects, /projects/<id>,
     |     app/database/project_tracker.py) with status Planned -> In
     |     Progress -> Completed -> Verified - never changed except by
     |     an explicit click. An AI project coach
     |     (app/ai/project_coach.py, local Ollama) answers open-ended
     |     technical questions grounded in the project itself. Once
     |     Verified, a CV bullet can be drafted - grounded only in the
     |     project's own recorded title/description/notes, never the
     |     wider profile, always review-only. A Verified project also
     |     strengthens that skill's proficiency on the Layer 1 CV-
     |     Strength page (app/ai/cv_strength.py) - real, produced
     |     evidence outranks a bare claim.
     v
Ready to Apply / One Next Action  IMPLEMENTED
     |     Part of the Layer 2 page. Deliberately conservative: "ready
     |     to apply" is only claimed when every detected required skill
     |     is covered, and the page always surfaces exactly one primary
     |     next action (apply now / close this specific gap / add this
     |     specific evidence / optional nice-to-have) instead of a
     |     checklist. An honest match-score-improvement estimate, using
     |     the real V2 scoring model, accompanies a genuine gap - never
     |     exaggerated, never a guarantee.
     v
CV Improvement (upload/review)    PARTIAL
     |     /settings/upload-cv accepts a PDF/DOCX upload, saves it
     |     safely, parses it, and extracts structured data via the
     |     local LLM for review - verified live end to end. Review-only
     |     by design: never auto-merged into profiles/profile.json, so
     |     a bad extraction can't silently corrupt the profile
     |     everything else depends on. The merge-into-profile step
     |     itself is PLANNED, not built - see NEXT_TASKS.md Priority 2.
     v
Resume / Cover Letter             IMPLEMENTED (tailoring is PARTIAL)
     |     Both grounded in the real profile + selected job, generated
     |     via local Ollama, verified end-to-end including graceful
     |     failure when Ollama is slow/unavailable. Tailoring today is
     |     a full LLM rewrite constrained to profile data by prompt,
     |     not the lighter "reorder/re-emphasize a ~90%-stable master
     |     CV" approach the product spec describes - see "CV tailoring"
     |     below for why this wasn't rearchitected this session.
     v
Application Tracking              IMPLEMENTED
     |     Save job, track status across the full interview funnel
     |     (Saved/Applied/Interview/Second Round/Final Round/Offer/
     |     Rejected/No Response/Withdrawn), delete - backed by SQLite.
     |     Interview-stage progress counts as real progress in every
     |     stat shown, not just an eventual offer. Status only ever
     |     changes via an explicit user click - nothing in the codebase
     |     changes it automatically (verified directly, not assumed).
     v
Interview Preparation (gated)     IMPLEMENTED
     |     /interview/<job_id> - AI-generated technical/scenario/CV/
     |     project/"explain this" questions, grounded in the real
     |     profile and job description. Gated: only reachable once that
     |     job's saved application has reached "Interview" status or
     |     later - never pushed proactively, consistent with "calm
     |     advisor, not pressure."
     v
Progressive Employability         PARTIAL
                     A funnel-aware insight (many applications/few
                     interviews -> CV/targeting focus; several
                     interviews/few offers -> interview-prep focus) is
                     implemented and shown on the dashboard, and a
                     Verified project now durably strengthens a skill's
                     proficiency (see "Project Development" above) -
                     rejecting an application doesn't erase that. What's
                     still missing: a single combined view showing all
                     of "applications submitted, interviews reached,
                     projects verified, skills strengthened" together
                     over time - each exists individually
                     (/applications, /projects, /cv-strength) but isn't
                     unified into one progress picture yet.
```

## Geographic priority: Finland first, Europe second

**Status: documented honestly, not fully built.** The mission's stated
priority is Finland first (Helsinki, Espoo, Vantaa, Tampere, Turku,
Oulu, and remote/hybrid Finnish roles), then Europe more broadly,
treating the candidate's dual Finnish/Nepalese citizenship as full EU
work authorization - never as a sponsorship concern.

What's actually true today, checked directly rather than assumed:

- **All four registered/implemented job sources are Finland-only**
  (Jobly, Tyomarkkinatori, Work in Finland, and the disabled Duunitori -
  see `docs/DATA_SOURCES.md`). There is **no European job source at
  all** - not scraped, not planned in code, nothing to disable or
  re-enable. Building real European sources (each with its own
  `robots.txt` check, HTML/API structure, and possibly a different
  language) is a genuinely separate, sizable scoping effort per
  country - not attempted this session. **PLANNED, REQUIRES SCOPING.**
- **Finland-first ranking already exists** in both matchers: V1's
  `LOCATION_PRIORITY` ranks Helsinki/Espoo/Vantaa above a generic
  Finland match, and V2's `location_matches()` scores any
  `target_locations` match (currently all Finnish cities in
  `profiles/profile.json`) - see `docs/MATCHING_AND_RANKING.md`.
- **No sponsorship-based penalty exists anywhere** - checked directly
  (zero occurrences of "sponsor" anywhere in `app/`). There was nothing
  to remove; this is confirmed-correct by inspection, not a fix.
- **Nothing currently expresses location-specific copy** like "Germany -
  relocation required" or "Netherlands - EU work authorization" - since
  there's no non-Finnish source, there's no non-Finnish job to label
  this way yet. This kind of per-country framing only becomes
  meaningful once a real European source exists.

## Match score clarity

**Status: fixed this session**, in direct response to a concrete
problem: earlier live verification produced dashboard scores as low as
11-13% for jobs where the title/location simply didn't match anything
in the profile - technically correct given the scoring formula, but
easy to misread as "you're a weak candidate" rather than "this
particular posting's title didn't match."

Fixes, both presentation-level (the underlying formula in
`app/search/v2/matching/matcher.py` was not rewritten - it's tested,
documented, and the low score was a labeling problem, not a
calculation error):

- The dashboard's gauge is now labeled **"Profile Match"**, not the
  bare word "Match", with a legend directly above the job list
  explaining what it measures (title/skill/location/seniority fit) and
  stating explicitly that it is **not a probability of getting hired or
  an interview**.
- The Layer 2 page's "Readiness" stat is now labeled **"Requirement
  coverage"**, with a line distinguishing it from the dashboard's
  Profile Match score - they measure genuinely different things
  (weighted job-title/location fit vs. how much of a specific posting's
  detected requirements the candidate actually covers), and neither is
  a hiring probability.

Tests: `tests/test_status_transitions_route.py::test_dashboard_explains_what_profile_match_means`,
`tests/test_skill_gap_route.py::test_analyze_route_clarifies_the_score_is_not_a_probability`.

## Investigated: a job appearing as "Interview" that was never applied to

**Root cause found, not the application's logic.** Traced directly
rather than assumed: `app/database/application_tracker.py`'s
`update_status()` is the *only* code path that changes a status, and
it's only ever called from `app/web/routes.py`'s
`/status/<id>/<status>` route, itself only ever reached by an explicit
link click - there is no code anywhere that changes a status
automatically, no seed/demo data baked into the app, and no shared
state across users (verified directly, and covered by
`tests/test_project_tracking.py::test_status_only_changes_via_explicit_update_call`'s
equivalent for projects).

What actually happened: this session's own live-verification testing
called routes like `/status/1/Interview` directly against the real
`data/careerpilot.db` instead of an isolated copy, the way the
automated test suite always does (`tmp_path`/`monkeypatch.chdir`). That
left rows in the real database that didn't reflect anything the actual
user did. This was a mistake in the verification *process*, not a
defect in the shipped code - and it's specifically why the database was
cleared once identified, with the user's explicit confirmation first
(clearing a user's real data is not a decision to make unilaterally,
even when self-caused). **Going forward, any manual/live verification
that touches persistence must run in an isolated working directory,
matching what the automated suite already enforces** - this is now a
documented rule, not just a one-off fix.

## Job requirement -> current skill -> gap -> recommended action

This is the exact flow `/analyze/<job_id>` renders, and it's worth
stating explicitly because it's the core UX contract for Layer 2:

1. **Job requirement**: a skill from CareerPilot's curated taxonomy,
   detected in the job's text, classified required or nice-to-have.
2. **Current skill**: whether the candidate's profile (skills list,
   experience text, certifications, summary) demonstrates it at all.
3. **Gap**: if not demonstrated anywhere, it's a real gap - shown with a
   real, hand-curated certification/course/project recommendation and a
   rough effort estimate. If demonstrated only weakly (e.g. in the
   skills list but never in an experience entry), it's flagged as a CV-
   evidence gap instead - a much smaller ask.
4. **Recommended action**: the page always leads with exactly one
   primary next step - "Apply now", a specific quick action for the
   single most impactful gap, or strengthening existing weak evidence -
   with everything else still visible below for a user who wants to
   look further, never as a mandatory checklist.

## UI copy: no implementation details in the product itself

**Status: fixed this session.** Earlier UI copy leaked implementation
details a candidate has no reason to see - "How this works: deterministic,
zero AI-generated content...", `profiles/profile.json` file paths,
"review-only preview" phrasing, references to `NEXT_TASKS.md`. All of
that belongs in `docs/`, not the product a user is actually looking at.
Removed from `templates/skill_gap.html`, `templates/cv_strength.html`,
and `templates/settings.html`; replaced with plain language ("Upload
your latest CV and CareerPilot will analyze it", "Nothing is saved
automatically - you'll always see what was found first"). Tests:
`tests/test_skill_gap_route.py::test_analyze_route_hides_internal_implementation_jargon`,
`tests/test_cv_strength_route.py` (asserts `"profile.json"` and
`"deterministic"` are absent), `tests/test_cv_upload.py::test_settings_page_hides_internal_implementation_details`.

## Layer 1 gives a complete path, not just a label

**Status: fixed this session.** `/cv-strength` previously flagged a weak
skill ("Python is listed but isn't demonstrated...") with no concrete
next step. Each weakly-evidenced skill that matches the same curated
catalog Layer 2 uses (`app/ai/skill_gap.py`'s `SKILL_CATALOG`) now shows
the full path: what to build, how, a realistic time estimate, what
evidence results, and a "Start this project" button
(`/projects/start-general/<skill_key>` - the job-independent variant of
Layer 2's start-project route, since Layer 1 has no job context) - the
exact what/where/how/time/why/evidence structure the product spec asks
for. A skill outside the curated taxonomy still gets a plain-language
note rather than nothing.

## Layer 2 leads with strengths, not a missing-skills wall

**Status: fixed this session.** `/analyze/<job_id>` now shows a "You
already demonstrate" section - every matched required/nice-to-have
skill, as a clean positive list - directly under the one-next-action
banner and before any gap detail. The full required/nice-to-have
breakdown (with status per skill and recommendations for real gaps)
stays below for anyone who wants it, but it's no longer the first thing
on the page. The page also now has a direct **Apply / View posting**
link at the top - found missing during live verification: the dashboard
card had one, the deep-dive analysis page a candidate might spend the
most time on didn't.

## Project tracking and the AI project coach

The mechanism that turns "you're missing Kubernetes security evidence"
into an actual GitHub repository, not just advice.

**Starting a project**: on `/analyze/<job_id>` (Layer 2), a "Start this
project" link appears next to any missing skill's recommended project.
Clicking it creates a project record
(`app/database/project_tracker.py`) using the *curated* catalog's
title/description (`app/ai/skill_gap.py`'s `SKILL_CATALOG` - the same
zero-LLM, hand-checked data the recommendation itself came from), with
status `Planned`.

**Status only ever changes by an explicit click** - `Planned -> In
Progress -> Completed -> Verified`, via `/projects/<id>/status/<status>`.
Nothing in the codebase changes a project's status as a side effect of
anything else (verified directly:
`tests/test_project_tracking.py::test_status_only_changes_via_explicit_update_call`).
`Completed` and `Verified` are deliberately separate steps - `Verified`
is the gate for both CV-bullet drafting and counting as skill evidence,
so it should mean "the real evidence (repo, README, findings) actually
exists," not just "I think I'm done."

**The AI project coach** (`app/ai/project_coach.py`) is the one place
in this session's work where Ollama is used for open-ended technical
help, not a grounded-but-templated document. Four capabilities, all
grounded in the project's own title/description (and notes, where
relevant):

- `plan()` - a concrete day-by-day starting plan with checkpoints,
  triggered by a "Get a step-by-step plan" button - the "how do I even
  begin" answer for a project the user just started.
- `ask()` - open-ended Q&A (explain a concept, help with a command,
  debug an error).
- `review()` - honest feedback on work the candidate actually pastes in
  (code, config, notes, logs) - reviews only what's submitted, never
  claims to have seen more.
- `draft_cv_bullet()` - see below.

This is a deliberate exception to the "zero-LLM for recommendations"
rule elsewhere (`app/ai/skill_gap.py`, `app/ai/cv_strength.py`) - see
`docs/AI.md` for why open-ended coaching/review and factual
recommendation are different risk categories.

**CV-bullet drafting** (`draft_cv_bullet()`) is gated to `Verified`
projects only (enforced in `app/web/routes.py`, not just the prompt),
and grounded *only* in the project's own recorded text - never the
wider candidate profile, never inventing tools/outcomes not mentioned.
The result is always review-only, displayed on the project's page for
the user to copy themselves; nothing writes to `profiles/profile.json`
automatically, consistent with the CV-upload flow's existing review-
only precedent.

**Strengthening CV-Strength evidence**: a `Verified` project's skill is
passed into `analyze_cv_strength()` as `verified_skill_keys`
(`app/ai/cv_strength.py`), upgrading that skill to `Advanced` with
evidence text that specifically credits the verified project - even for
a skill not yet in the profile's declared skills list at all (real,
produced evidence surfaces regardless of whether the skills list has
caught up). See `docs/MATCHING_AND_RANKING.md`'s "CV strength analysis"
section.

**Not built**: an in-between proficiency contribution for "In Progress"
work, or a project fading a skill's evidence back down if later
invalidated - level is always recomputed fresh from current profiles/
project data, not an independently-accumulating score. See
`NEXT_TASKS.md`.

## CV tailoring: current state, and why it wasn't rearchitected

The product spec (section 13 of the release work order) describes CV
tailoring as: maintain one master profile, and for a given job, reorder/
re-emphasize/reword *existing* content rather than regenerating
everything. What's actually implemented (`app/ai/resume_builder.py`) is
different: the *entire* profile is sent to the local LLM with an
instruction to rewrite `summary`/`skills`/`experience` for the target
job, returned as JSON. It is grounded (the prompt forbids inventing
anything, and only profile data is supplied), but it's a full rewrite
per job, not a deterministic reorder of stable content.

This was deliberately **not** rearchitected this session - it's a
working, tested feature (`tests/test_...` resume-generation coverage,
live-verified in an earlier session), and rewriting its core mechanism
under this session's scope would risk destabilizing something that
already works, for a difference that's about *how* grounding is
achieved rather than *whether* it's grounded. Marked **PARTIAL** here
rather than silently claimed as matching the spec exactly - see
NEXT_TASKS.md for the scoped follow-up if this is prioritized later.

## Multi-visitor demo mode: what's safe today, what's not built

Section 14 of the release work order asks for master-profile protection
and per-visitor session isolation for a small beta/demo deployment. What
was verified and hardened this session:

- **Master profile is already safe by construction**: no code path
  anywhere writes to `profiles/profile.json` from the CV-upload flow (or
  anywhere else at runtime) - verified directly with a regression test
  that hashes the file before and after an upload
  (`tests/test_cv_upload_hardening.py::test_master_profile_is_never_modified_by_a_cv_upload`).
  A visitor's uploaded CV cannot overwrite or corrupt it, today, with no
  new code required.
- **CV uploads are isolated per file** (a fresh UUID filename, never the
  client-supplied name), **rate-limited** (20 uploads/minute/IP, in-
  memory), and **auto-cleaned** after 24 hours - all added this session,
  see `app/web/routes.py` and `docs/SECURITY.md`.

What's explicitly **not** built, and why: a true multi-visitor
experience where each visitor's uploaded CV drives its *own*
personalized dashboard/search/skill-gap results would require threading
a session-scoped profile through every route in `app/web/routes.py`
(`_load_profile()`, the matcher, skill-gap analysis, resume/cover-letter
generation - essentially every route in the file) instead of the one
global master profile, plus CSRF protection before the state-mutating
routes (`/save/<id>`, `/status/<id>/<status>`, `/delete/<id>`) could
safely be exposed beyond a single trusted user (see `docs/SECURITY.md`'s
"Known limitations"). That's a genuinely large, cross-cutting change,
and building it under this session's time budget risked destabilizing
the working single-profile architecture for a feature that wasn't the
primary ask. **Today's safe deployment model is: share the app (and its
one master profile) with a small group of trusted testers via a tunnel,
not an open multi-tenant demo where strangers get personalized
results.** See `docs/SECURITY.md` for the exact checklist to go through
before exposing it even to trusted testers.

## Planned: real Tyomarkkinatori / Work in Finland data

Both currently return zero results because their job listings are loaded
by client-side JavaScript, not present in the static HTML this project's
scraper fetches (root-caused in `docs/DATA_SOURCES.md`, not assumed).

Tyomarkkinatori's internal JSON API was found via real browser network
inspection and a working scraper against it was built and verified live
- then deliberately not shipped, because the site's `robots.txt`
explicitly disallows `/api/`. Fixing this for real now needs explicit
permission from Tyomarkkinatori (an official API/data-sharing agreement),
not more engineering - see `docs/DATA_SOURCES.md` and `NEXT_TASKS.md`.
**REQUIRES HUMAN DECISION.**

Work in Finland's listings appear to already be sourced from Jobly
(company logo assets load directly from `jobly.fi`), so a separate
scraper likely wouldn't add meaningful new coverage beyond the existing
`JoblySource` - worth confirming rigorously before investing further
effort either way.

## Planned: merge extracted CV data into the profile

`/settings/upload-cv` extracts and displays CV data but never writes to
`profiles/profile.json` - that was a deliberate scope boundary (see
"CV Improvement" above), not an oversight. Closing this loop needs a
real UI decision: an "accept these fields" review step (checkbox per
field, or per section) rather than a single blind merge, since the
whole point of keeping this review-only was to not let an imperfect
extraction silently overwrite curated profile data. **PLANNED.**
