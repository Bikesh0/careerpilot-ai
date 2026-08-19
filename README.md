# CareerPilot AI

CareerPilot AI is a local, Flask-based job search assistant built around one
specific job seeker's profile (a cybersecurity/IT professional job-hunting in
Finland). It collects real job postings from several Finnish job boards,
normalizes and deduplicates them, scores them against a structured profile,
and presents a ranked dashboard with AI-assisted resume and cover letter
generation for whichever job is selected.

It is not a generic multi-tenant SaaS product. It is a focused, working tool
built for one person's job search, and doubles as a portfolio project
demonstrating end-to-end software engineering: data ingestion, matching
algorithms, testing discipline, and secure development practices.

## Problem

Job boards in Finland are fragmented across several sites, none of which let
you search across all of them at once or explain *why* a given posting is a
good (or bad) fit for a specific candidate. Manually checking multiple sites
every day, filtering out irrelevant senior/lead roles, and figuring out which
skills are missing for a given posting is repetitive and easy to fall behind
on.

## Solution

CareerPilot AI runs a search across multiple job sources, merges the results
into one deduplicated list, scores each posting against the candidate's
actual skills/target titles/target locations, and explains the score
(matched skills, missing skills, title match, location match, seniority fit)
directly on the dashboard. From there it can generate a tailored resume and
cover letter for a specific posting, grounded only in the candidate's real
profile data.

## Features

Implemented and verified in this repository:

- Multi-source job collection (currently Jobly; two additional registered
  sources return no results, and a fourth, Duunitori, is implemented but
  deliberately disabled pending `robots.txt` compliance — see
  [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md))
- Canonical job normalization and cross-source deduplication (V2 search
  pipeline)
- Profile-aware matching: skills, target titles, target locations, and
  seniority, each contributing to a transparent, weighted score
- **Layer 1 - CV strength analysis** (`/cv-strength`): a general,
  job-independent look at the profile itself - automatic skill
  proficiency (Basic/Intermediate/Advanced, computed from real evidence
  in experience/certifications, not just presence/absence), strengths,
  and a short, prioritized list of the highest-value improvements - see
  [docs/MATCHING_AND_RANKING.md](docs/MATCHING_AND_RANKING.md)
- **Layer 2 - job-specific skill-gap analysis** (a "Skill Gap" button on
  every dashboard job card): required-vs-nice-to-have skill detection, a
  genuine gap check against the candidate's real profile (not the
  inverse "missing_skills" the matchers compute), real hand-curated
  certification/course/project recommendations, a "ready to apply"
  signal and one calm "next best action" instead of a checklist, and an
  honest match-score-improvement estimate computed with the real scoring
  model - never a guarantee
- A Flask dashboard showing ranked jobs, matched skills, job metadata,
  and an adaptive one-line insight about the user's own application
  funnel (e.g. "reaching interviews - focus on interview prep next")
- Save-job / application tracking with an expanded status set (Saved,
  Applied, Interview, Second Round, Final Round, Offer, Rejected, No
  Response), backed by SQLite, with duplicate-record prevention (by job
  URL, or company+title as a fallback) - interview-stage progress is
  counted as real progress even without an offer yet
- **Gated interview preparation** (`/interview/<job_id>`): AI-generated,
  job-specific technical/scenario/CV/project questions, only unlocked
  once that job's saved application has actually reached "Interview"
  status or later - never pushed proactively
- AI-assisted resume and cover letter generation via a local Ollama model,
  grounded in the candidate's actual profile (no invented experience)
- CV upload (PDF/DOCX) with AI-assisted data extraction for review - safe
  file handling (no client-controlled paths), rate-limited, automatically
  cleaned up after 24 hours, and never auto-merged into the profile
- Graceful degradation: a slow/unavailable local LLM returns a clear error
  instead of hanging the request; a failing job source doesn't take down the
  rest of the search

Not yet wired up (see [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md) for
full status):

- Merging reviewed CV-extracted data into `profiles/profile.json` (the
  upload/extract/review flow above stops short of this deliberately)
- Browser-automation-based scraping for JavaScript-rendered job boards
- A true multi-visitor demo mode where each visitor's uploaded CV drives
  its own personalized dashboard/search/skill-gap results - the current
  release keeps the CV upload flow session-safe (never touches the
  master profile, isolated per upload, rate-limited, auto-cleaned) but
  every visitor's dashboard still reflects the one master
  `profiles/profile.json` - see [docs/SECURITY.md](docs/SECURITY.md)
- Deterministic (reorder-not-regenerate) CV tailoring - resume generation
  currently uses a grounded LLM rewrite of the whole profile per job,
  not a lighter deterministic reorder of a stable master CV

## Architecture

```
Profile (profiles/profile.json)
        |
        v
V2 Search Service  --------------------------------------------+
        |                                                       |
        v                                                       |
Source Runner  -->  Jobly / Tyomarkkinatori / Work in Finland     |
                     (each isolated; one source failing doesn't  |
                     stop the others; Duunitori is implemented   |
                     but disabled, see docs/DATA_SOURCES.md)     |
        |                                                       |
        v                                                       |
Normalizer  -->  CanonicalJob                                    |
        |                                                       |
        v                                                       |
Deduplicator                                                     |
        |                                                       |
        v                                                       |
V2 Matcher/Ranker (title, skill, location, seniority scoring) <--+
        |
        v
Flask dashboard  -->  shows V2's own score/reasons when V2 search
        |              succeeds; falls back to the legacy JobMatcher
        |              only when V2 is disabled or itself fails (see
        |              docs/ARCHITECTURE.md's "The V1/V2 split")
        v
Save job / Generate resume / Generate cover letter
        |                                   |
        v                                   v
  SQLite (data/careerpilot.db)      Local Ollama LLM, grounded
                                     in profiles/profile.json
```

Full breakdown, including the current V1/V2 relationship, is in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Technology Stack

| Technology | Role |
| --- | --- |
| Python 3.10–3.12 | Application language |
| Flask | Web dashboard |
| requests + BeautifulSoup4 | Job board scraping |
| Ollama (local LLM) | Resume/cover-letter generation, optional |
| SQLite | Saved jobs / application tracking |
| python-docx, PyMuPDF | Document generation and CV parsing |
| pytest | Automated test suite |

Full details, including what's a runtime dependency vs. a development tool,
are in [docs/TECHNOLOGY_STACK.md](docs/TECHNOLOGY_STACK.md).

## V2 Search Architecture

The job-collection, normalization, deduplication, and matching pipeline
lives under `app/search/v2/` and is explained in detail in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and
[docs/MATCHING_AND_RANKING.md](docs/MATCHING_AND_RANKING.md). It is enabled
with the `CAREERPILOT_SEARCH_V2=1` environment variable (see
[Configuration](#configuration)).

## Matching and Ranking

Each job is scored against the candidate's profile using four signals -
title relevance, skill overlap, location match, and seniority fit - combined
into one weighted score with human-readable reasons ("Target job title
matched", "3 profile skills not found", etc.). The full scoring formula,
including known edge cases, is documented in
[docs/MATCHING_AND_RANKING.md](docs/MATCHING_AND_RANKING.md).

## AI Features

Resume and cover-letter generation call a local Ollama model, never a
hosted API, and the prompts explicitly forbid inventing experience,
education, or skills not present in `profiles/profile.json`. If Ollama is
unreachable or slow, the request fails fast (bounded timeout) with a clear
error rather than hanging. Full details, plus the distinction between "AI
used to develop this project" (Claude Code) and "AI used at runtime by this
project" (Ollama), are in [docs/AI.md](docs/AI.md).

## Security

- TLS certificate verification is never disabled (`verify=False` is banned
  by policy in this repository).
- Scraped detail-page links are checked against the source's own domain
  before being fetched, to avoid following an absolute link to an
  attacker-controlled or unrelated host.
- Flask's debug mode (interactive debugger + stack traces) is off unless
  `FLASK_DEBUG=1` is explicitly set.
- Jinja2's default autoescaping is relied on throughout; no template uses
  `| safe` or `Markup()` on scraped or user-derived content.
- No hardcoded credentials; local LLM configuration is read from
  environment variables.

Full write-up: [docs/SECURITY.md](docs/SECURITY.md).

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`requirements.txt` contains runtime dependencies only. `requirements-dev.txt`
adds pytest for the automated test suite.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `CAREERPILOT_SEARCH_V2` | Enable the V2 search pipeline (`1`/`true`/`yes`/`on`) | disabled |
| `FLASK_DEBUG` | Enable Flask's interactive debugger (`1`/`true`/`yes`/`on`) | disabled |
| `OLLAMA_HOST` | Local Ollama server URL | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Local model name | first installed model |
| `OLLAMA_TIMEOUT` | Seconds before an AI request is abandoned | `30` |
| `OLLAMA_MAX_TOKENS` | Max generated tokens per AI request | `350` |

## Running

```powershell
# Flask web application (dashboard)
$env:CAREERPILOT_SEARCH_V2 = "1"
.\.venv\Scripts\python.exe webapp.py

# CLI daily job agent (V1 search path)
.\.venv\Scripts\python.exe main.py
```

The AI features (resume/cover letter generation) require Ollama to be
running locally with a model installed; without it, those two actions
return a clear "unavailable" response instead of failing silently.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest
```

110 tests, all fixture- or mock-backed. The suite performs no live job
searches and never calls Ollama. Details, including what each test file
covers, are in [docs/TESTING.md](docs/TESTING.md).

Manual live smoke checks (deliberately outside `tests/`, require network
access and/or a running Ollama instance):

```powershell
.\.venv\Scripts\python.exe test_sources.py
.\.venv\Scripts\python.exe app\ai\test_llm.py
```

## Project Structure

```
app/
  search/v2/        V2 search pipeline: ingestion, normalization,
                     dedupe, matching, ranking (see docs/ARCHITECTURE.md)
  search/sources/    Scrapers for each job board
  search/            V1 search manager and profile-driven matcher
  ai/                Local LLM wrapper, resume/cover-letter builders,
                     CV-data extraction, and the legacy JobMatcher used
                     as the dashboard's presentation layer only when V2
                     is disabled or itself fails (see docs/ARCHITECTURE.md)
  documents/         Resume/cover-letter document generation (docx)
  parsers/           CV parsing (PDF/docx text extraction), used by
                     the /settings/upload-cv route
  database/          SQLite connection and application tracking
  services/          Thin orchestration layer used by the Flask routes
  web/                Flask blueprint (routes.py) and dashboard actions
profiles/
  profile.json        The candidate's structured profile - the single
                       source of truth for matching, resumes, and cover
                       letters
templates/, static/   Flask templates and assets
tests/                 pytest suite (fixture/mock-backed only)
docs/                  Full documentation set (this file links to all of it)
```

## Known Limitations

See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for source-by-source
status. In short: Duunitori is fully implemented and was the largest
source of collected jobs, but is deliberately **disabled** - its
`robots.txt` disallows this scraper's user-agent, discovered after it had
already shipped, and it was turned off rather than left running against
that policy. Tyomarkkinatori and Work in Finland are JavaScript-rendered
sites whose job listings are not present in the static HTML this
project's `requests`+BeautifulSoup scraper fetches - they currently
return zero results, honestly, rather than partially-broken data. A
working integration for Tyomarkkinatori's own internal API was built and
verified live, then deliberately not shipped for the same `robots.txt`
reason. CV upload/extraction stops at a review step by design - it never
automatically writes to `profiles/profile.json`.

## Roadmap

- **Implemented**: V2 search/matching/ranking pipeline, Flask dashboard,
  save-job/application tracking with a full interview-stage funnel
  (duplicate-safe), Layer 1 CV-strength analysis, Layer 2 job-specific
  skill-gap analysis with honest match-score projection and a single
  "next best action", gated interview preparation, AI resume and
  cover-letter generation, CV upload with AI-assisted extraction for
  review (rate-limited, auto-cleaned), automated test suite (110 tests).
- **Partial by design**: CV tailoring uses a grounded LLM rewrite per
  job rather than a deterministic reorder of a stable master CV; skill
  proficiency (Basic/Intermediate/Advanced) is computed fresh from
  profile data each time, not a persistent store that advances via a
  "mark this project complete" workflow; merging reviewed CV-upload
  data into the profile is still review-only, never auto-merged.
- **Planned**: resolving Duunitori's disabled status (explicit permission
  from Duunitori, and/or an honestly-identifying User-Agent, needed
  before it can be re-registered); getting Tyomarkkinatori's explicit
  permission to use its internal API (a working integration exists but
  wasn't shipped - `robots.txt` disallows it without permission);
  confirming whether Work in Finland's listings genuinely add coverage
  beyond the existing Jobly source before investing in a separate
  scraper for it; a true multi-visitor demo mode with per-visitor
  personalized results (would need session-scoped profile threading
  through every route plus CSRF protection - see
  [docs/SECURITY.md](docs/SECURITY.md)).

## Portfolio Value

See [docs/PORTFOLIO.md](docs/PORTFOLIO.md) for the engineering skills this
project demonstrates and how to talk about it in an interview.
