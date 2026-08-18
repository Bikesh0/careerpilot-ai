# Product Vision

The intended end-to-end flow, and the honest status of each step. Nothing
below is described as complete unless it was verified working in this
repository as of this session (2026-08-18).

```
User Profile           IMPLEMENTED
     |                  profiles/profile.json - skills, target titles/
     |                  locations, experience, education, certifications.
     v
Job Search              IMPLEMENTED
     |                  V2 pipeline: multi-source collection, normalization,
     |                  deduplication (app/search/v2/).
     v
Relevant Jobs            IMPLEMENTED
     |                  Weighted matching + ranking; verified live against
     |                  the real profile to produce a sensible, correctly-
     |                  ordered top-20 (see docs/MATCHING_AND_RANKING.md).
     v
Match Explanation        IMPLEMENTED
     |                  Dashboard shows matched skills per job. The richer
     |                  reason strings (title/location/seniority match
     |                  reasons, missing skills) exist on both matchers'
     |                  output but the dashboard template currently only
     |                  renders matched_skills - see "In progress" below.
     v
Skill Gap                 PLANNED
     |                  Not implemented, and not as simple as exposing
     |                  existing data: both matchers' missing_skills
     |                  means "profile skills this job's text doesn't
     |                  mention" - the inverse of "skills the job wants
     |                  that you don't have." A posting asking for a
     |                  skill entirely absent from the profile (e.g.
     |                  Terraform) is invisible to both matchers today.
     |                  Real skill-gap detection needs requirement
     |                  extraction from the job text itself - see
     |                  NEXT_TASKS.md Priority 4 for the scoped options
     |                  (a curated taxonomy vs. a per-job LLM call) and
     |                  why the taxonomy approach is the safer default.
     v
CV Improvement            IN PROGRESS
     |                  /settings/upload-cv accepts a PDF/DOCX upload,
     |                  saves it safely (never trusting the client
     |                  filename/path - see docs/SECURITY.md), parses it
     |                  with CVParser, and extracts structured data with
     |                  ProfileExtractor via the local LLM - verified live
     |                  end to end with real .docx and .pdf files.
     |                  Deliberately review-only: the extracted data is
     |                  displayed on /settings, not auto-merged into
     |                  profiles/profile.json, so a bad or
     |                  AI-hallucinated extraction can't silently corrupt
     |                  the profile everything else depends on. "IN
     |                  PROGRESS" rather than "IMPLEMENTED" because the
     |                  merge-into-profile step - the part that actually
     |                  changes what CareerPilot does with your data -
     |                  still doesn't exist; today you'd copy the
     |                  reviewed data into profile.json by hand.
     v
Cover Letter               IMPLEMENTED
     |                  Grounded in the real profile + selected job,
     |                  generated via local Ollama, verified end-to-end
     |                  (including the graceful-failure path when Ollama
     |                  is slow/unavailable).
     v
Application               IMPLEMENTED
     |                  Save job, track status (Saved/Applied/Interview/
     |                  Offer/Rejected), delete - backed by SQLite,
     |                  verified end-to-end with V2-sourced jobs.
     v
Interview Preparation      PLANNED
                          No implementation exists for this step.
```

## In progress: unifying V1 and V2 ranking on the dashboard

As documented in `docs/ARCHITECTURE.md`, the dashboard currently displays
scores from the legacy `app.ai.matcher.JobMatcher`, not from V2's own
`JobMatcher`/`JobRanker` (which is fully built, tested, and reachable via
`V2SearchService.search()`, just not what's rendered). This is the single
most impactful "next" item for closing the gap between what V2 can do and
what the user actually sees, and it's a real design decision, not a
trivial swap - it means either:

1. Rendering V2's `RankedJob.to_dict()` output directly (loses the V1
   matcher's Finnish-language title terms, exclusion list, and
   experience-requirement penalties unless those are ported into V2's
   matcher first), or
2. Porting V1's more specific logic into V2's matcher and retiring the V1
   matcher (larger, riskier change - V1's matcher has years of informal
   tuning behind its weights and term lists).

No unilateral choice was made between these two during this session -
it's flagged here as a scoped decision for whoever picks this up next,
with both matchers' actual behavior documented in
`docs/MATCHING_AND_RANKING.md` so that decision can be made with full
information.

## Planned: real Tyomarkkinatori / Work in Finland data

Both currently return zero results because their job listings are loaded
by client-side JavaScript, not present in the static HTML this project's
scraper fetches (root-caused in `docs/DATA_SOURCES.md`, not assumed).

Tyomarkkinatori's internal JSON API was found via real browser network
inspection and a working scraper against it was built and verified live
- then deliberately not shipped, because the site's `robots.txt`
explicitly disallows `/api/`. Fixing this for real now needs explicit
permission from Tyomarkkinatori (an official API/data-sharing agreement),
not more engineering - see `docs/DATA_SOURCES.md` and `NEXT_TASKS.md`
Priority 2.

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
extraction silently overwrite curated profile data.
