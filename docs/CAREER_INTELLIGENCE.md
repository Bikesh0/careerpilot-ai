# Career Intelligence

Status labels follow the convention set in `docs/PRODUCT_VISION.md`:
**IMPLEMENTED**, **PARTIAL**, **PLANNED**, **BLOCKED**, **REQUIRES HUMAN
DECISION**. Nothing below is marked IMPLEMENTED unless it was verified
working in this repository, against real data, in the session that
built it.

## Privacy and source-provenance principles

Every module documented here operates only on data the app already
legitimately holds:

- `profiles/profile.json` - the user's own, self-reported profile.
- `data/careerpilot.db` - applications and tracked projects the user
  created through explicit actions in the app.
- `manager.latest_jobs` - job postings from the app's own configured,
  robots.txt-respecting sources (see `docs/DATA_SOURCES.md`), from
  whatever the last real search actually returned - never re-scraped
  or fetched fresh just to feed a career-intelligence feature.

**Nothing in this codebase performs new external research** (no calls
to job boards, training providers, certification bodies, event
listings, or labour-market data beyond what's already described in
`docs/DATA_SOURCES.md`). Where a feature request called for that kind
of continuous external research (a "Career Research Engine" scraping
Saranen/Opiframe/LinkedIn/meetup platforms, a live-refreshing
"Opportunity Engine", competitive analysis of other career apps), it is
explicitly **NOT BUILT** - see "Explicitly out of scope" below for why,
and what would be required to build it responsibly.

## Job Deduplication (IMPLEMENTED, improved)

`app/search/v2/dedupe.py` / `app/search/v2/job.py`. A job is treated as
a duplicate of an earlier one if *either* signal matches:
`dedupe_key()` (source+external_id, or normalized title+company+location)
or `canonical_url()` (the same posting URL with tracking parameters
stripped). V1 (`app/search/manager.py`) has always had a third,
richer signal - a content fingerprint including description text - and
now also carries the geographic filter below in the same collection
loop. Real, different vacancies from the same company are never merged
- title+company+location alone is deliberately not sufficient (see the
content-fingerprint comment in `app/search/manager.py`).

## Geographic Normalization (IMPLEMENTED)

`app/ai/geo_normalizer.py`. Classifies a job's free-text location into
`FINLAND` / `EUROPE` / `OUTSIDE_EUROPE` / `UNKNOWN` using real,
verifiable country/city name lists - not fuzzy matching, not an LLM
guess. Wired into both search paths (`app/search/manager.py` for V1,
`app/web/routes.py::_search_jobs` for V2) as a filter applied *before*
local job ids are assigned, so dashboard action links stay correctly
indexed. Only a confidently-identified non-European location is
excluded by default; an `UNKNOWN` location (missing data, a bare
"Remote" with no country) is never excluded - excluding on missing
information would silently drop real, relevant postings.

## Application Readiness (IMPLEMENTED)

`app/ai/application_readiness.py`. Five tiers - Apply now / Apply -
stretch / Prepare, then apply / Low priority / Likely not a fit -
computed deterministically from the Profile Match score (dashboard
cards) or Requirement Coverage (the Career Fit & Growth deep-dive
page, a more specific signal once a candidate is looking at one
posting). `EXCLUDE` only fires on a near-zero composite score - never
from a single weak signal like "requires more years of experience than
the user has," matching the product spec's explicit instruction that
years-of-experience alone must never exclude a job outright.

## Career Fit & Growth / requirement extraction (IMPLEMENTED, expanded)

`app/ai/skill_gap.py`. Zero-LLM, deterministic, hand-curated catalog
(`SKILL_CATALOG`, ~55 entries) - see the module's own docstring for why
this stays zero-LLM (reproducibility, and certification/course claims
must never be hallucinated). This session's work expanded catalog
coverage (compliance frameworks, secure-development tooling, Windows/
M365, Go/JavaScript) and added Finnish-language aliases for the skills
most commonly requested in real, audited Finnish postings - closing the
dominant real cause of "no requirements detected" on Finnish-language
jobs. A section-aware classifier (`_chunk_nice_to_have_flags`) now also
recognizes a "Bonus points if you also:"-style bulleted section as
nice-to-have even when individual bullets don't repeat a hedge word
themselves - verified against a real, live-fetched Hoxhunt posting
(`tests/fixtures/hoxhunt_secops_description.txt`).

## Living Career Profile (IMPLEMENTED)

`app/ai/career_profile.py`, surfaced on `/cv-strength`. Distinguishes
six evidence *kinds* per profile skill - `KNOWS` (bare claim),
`STUDIED` (named in an education entry), `PRACTICED` (a tracked
project underway but not yet Verified), `CERTIFIED` (named in
certifications), `PROFESSIONAL_EXPERIENCE` (named in an experience
entry), `BUILT` (backed by a Verified project - the strongest tier,
since it's real produced work). A skill can carry more than one tier at
once. This sits alongside, not instead of, `app/ai/cv_strength.py`'s
existing Basic/Intermediate/Advanced proficiency score - one answers
"how strong," the other "what kind."

**Continuity** (`career_profile.continuity`): lists tracked projects
that are already Planned/In Progress/Completed (not yet Verified) and
ones that are Verified, so the app can point at *continuing* existing
work instead of always proposing something new. This same signal now
also feeds `app/ai/skill_gap.py::analyze_skill_gap()` via an optional
`existing_projects` argument: a skill backed by a Verified project
counts as matched even before the profile's own text mentions it
(mirroring `cv_strength.py`'s existing precedent), and a skill with a
project already underway gets a "Continue your project" link on the
Career Fit & Growth page instead of another "Start this project"
prompt - `_start_project_from_catalog()` is not idempotent per
skill_key, so without this a user could otherwise create duplicate
tracked projects for the same gap.

## Career Track Engine (IMPLEMENTED, intentionally small)

`app/ai/career_tracks.py`, surfaced on `/cv-strength`. Seven
hand-curated tracks (SOC/Security Operations, Cybersecurity Analyst,
Network Security, Penetration Testing, Cloud Security, DevSecOps, IT
Support -> Security), each mapped to a small set of `SKILL_CATALOG`
keys. Two components are shown, always separately, never blended into
one number presented as a probability:

- **Profile fit** (0-100): the Living Career Profile's own evidence
  tiers, weighted - a Verified project counts far more than a bare
  claim, and a skill with zero profile signal contributes zero.
- **Market signal** (0-100, or explicitly absent): how often the
  track's skills appear across whatever jobs the app's own last search
  actually returned. Shown as absent (not a misleading 0%) when no
  search has run yet.

Deliberately seven tracks, not dozens - each track-to-skill mapping is
a real editorial claim, not something to assert at scale without
genuine labour-market research behind it (see "Explicitly out of
scope" below).

## Explicitly out of scope, and why

The product spec (across two large session prompts) asked for a
"Career Research Engine" continuously scraping Finnish training
providers (Saranen, Opiframe), certification bodies, meetup/conference
listings, and labour-market reports; an "Opportunity Engine" surfacing
internships/traineeships/funded training; a Career Boost Engine and
Certification Strategy Engine layered on top of live external data; and
research into competing career-AI products. None of this is built.

Two honest reasons, not a shortcut:

1. **Provenance.** Every other module in this app is deterministic and
   traceable to a real, specific, already-legitimately-held data
   source. Scraping new external sites for this would mean either
   standing up new scrapers without verifying `robots.txt`/terms first
   (this project already disabled `DuunitoriSource` for exactly that
   violation - see `docs/DATA_SOURCES.md` - and won't repeat it), or
   fabricating plausible-sounding "research findings" with no real
   source behind them, which `docs/AI.md`'s anti-hallucination
   principle and the product spec's own Section 31/14 explicitly
   forbid.
2. **Freshness/caching infrastructure implies a running service.** A
   genuinely "continuously refreshing" research engine needs a
   scheduler, a persistence layer for freshness/dedup state, and a
   decision about how often it's acceptable to hit each external
   source - real infrastructure decisions, not a same-session code
   addition on top of a Flask app that otherwise only fetches data on
   an explicit user request.

**What would make this buildable next**: pick one single, real,
public, terms-compliant source (e.g. a specific university's public
course catalog API, or one certification vendor's public exam list)
and build one narrow, verified integration for it - the same way
`app/search/sources/` grew one verified source at a time - rather than
a generic "research engine" for all categories at once.
