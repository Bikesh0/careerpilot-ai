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
     |                  Not surfaced anywhere as an actionable suggestion
     |                  (short course / lab / project). V2's MatchResult
     |                  already computes a missing_skills list per job
     |                  (app/search/v2/matching/result.py); V1's
     |                  match_details currently exposes only a count/ratio,
     |                  not the list itself, so wiring this up would need
     |                  either V1 to also return the list, or the dashboard
     |                  to read it from V2's matcher directly.
     v
CV Improvement            IN PROGRESS
     |                  CVParser (app/parsers/cv_parser.py) parses PDF/docx
     |                  CVs to text and is unit-testable in isolation, but
     |                  no Flask route uses it - there is no upload form.
     |                  ProfileExtractor (app/ai/profile_extractor.py)
     |                  exists to turn parsed CV text into structured
     |                  profile data via the local LLM, also not wired to
     |                  a route.
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
Fixing this needs either their internal JSON API (undocumented, would
need to be reverse-engineered from real browser traffic) or a headless
browser dependency (Playwright/Selenium - neither currently installed).

## Planned: CV upload route

`CVParser` and `ProfileExtractor` are implemented and would only need a
Flask route (accept a file upload, save it to a path this project
controls - not a client-supplied path, see `docs/SECURITY.md` - parse it,
and either merge the result into `profiles/profile.json` or present it for
review) to close this loop.
