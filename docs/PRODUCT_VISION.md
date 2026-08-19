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
     |     Rejected/No Response), delete - backed by SQLite. Interview-
     |     stage progress counts as real progress in every stat shown,
     |     not just an eventual offer.
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
                     implemented and shown on the dashboard. A fuller
                     "skills strengthened / projects completed over
                     time" progression view, and a persistent skill-
                     proficiency store that advances via completed
                     projects/labs (rather than being recomputed fresh
                     from the profile each time), are not built - see
                     NEXT_TASKS.md.
```

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
