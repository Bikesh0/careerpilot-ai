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

- Multi-source job collection (Duunitori, Jobly; two additional sources are
  registered but currently return no results — see
  [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md))
- Canonical job normalization and cross-source deduplication (V2 search
  pipeline)
- Profile-aware matching: skills, target titles, target locations, and
  seniority, each contributing to a transparent, weighted score
- A Flask dashboard showing ranked jobs, matched skills, and job metadata
- Save-job / application tracking with status updates, backed by SQLite
- AI-assisted resume and cover letter generation via a local Ollama model,
  grounded in the candidate's actual profile (no invented experience)
- Graceful degradation: a slow/unavailable local LLM returns a clear error
  instead of hanging the request; a failing job source doesn't take down the
  rest of the search

Not yet wired up (see [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md) for
full status):

- CV/resume file upload and parsing (`CVParser` exists and is tested in
  isolation, but no route uses it yet)
- Browser-automation-based scraping for JavaScript-rendered job boards

## Architecture

```
Profile (profiles/profile.json)
        |
        v
V2 Search Service  --------------------------------------------+
        |                                                       |
        v                                                       |
Source Runner  -->  Duunitori / Jobly / Tyomarkkinatori /        |
                     Work in Finland (each isolated; one         |
                     source failing doesn't stop the others)     |
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
Flask dashboard  -->  legacy JobMatcher re-scores the same jobs
        |              for presentation (see docs/ARCHITECTURE.md
        |              for why both matchers currently exist)
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

39 tests, all fixture- or mock-backed. The suite performs no live job
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
                     the presentation-layer JobMatcher used by the dashboard
  documents/         Resume/cover-letter document generation (docx)
  parsers/           CV parsing (PDF/docx text extraction; not yet
                     wired to a route)
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
status. In short: Tyomarkkinatori and Work in Finland are JavaScript-rendered
sites whose job listings are not present in the static HTML this project's
`requests`+BeautifulSoup scraper fetches - they currently return zero
results, honestly, rather than partially-broken data. CV file upload/parsing
is implemented but not yet exposed through a route.

## Roadmap

- **Implemented**: V2 search/matching/ranking pipeline, Flask dashboard,
  save-job/application tracking, AI resume and cover-letter generation,
  automated test suite.
- **In progress**: unifying the dashboard's presentation ranking (currently
  the legacy `app.ai.matcher.JobMatcher`) with the V2 matcher's scoring
  output - see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **Planned**: fetching Tyomarkkinatori/Work in Finland listings via their
  underlying JSON APIs (or a headless browser) instead of static HTML;
  wiring up CV upload/parsing to a route.

## Portfolio Value

See [docs/PORTFOLIO.md](docs/PORTFOLIO.md) for the engineering skills this
project demonstrates and how to talk about it in an interview.
