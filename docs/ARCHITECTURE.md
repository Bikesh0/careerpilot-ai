# Architecture

## Purpose of this document

This explains how CareerPilot AI is actually put together, based on reading
the code - not the plan that predated it. Where the current implementation
is a deliberate interim state (see "The V1/V2 split" below), that's called
out explicitly rather than glossed over.

## High-level data flow

```
profiles/profile.json
        |
        v
app/web/routes.py  (Flask blueprint)
        |
        |-- v2_enabled() ? -------------------------------------+
        |                                                       |
        v (V2 path)                                             v (V1 fallback)
create_v2_service(profile)                              SearchManager.search_jobs()
        |                                                       |
        v                                                       |
V2SearchService.search()                                        |
        |                                                       |
        v                                                       |
SourceRunner.run()                                               |
   |-- Duunitori                                                 |
   |-- Jobly                                                     |
   |-- Tyomarkkinatori (currently 0 results, see DATA_SOURCES.md)|
   |-- Work in Finland (currently 0 results, see DATA_SOURCES.md)|
        |                                                       |
        v                                                       |
normalize_job() -> CanonicalJob                                  |
        |                                                       |
        v                                                       |
deduplicate_jobs()                                                |
        |                                                       |
        v                                                       |
JobRanker (V2 title/skill/location/seniority scoring)             |
        |                                                       |
        v                                                       |
[item.job for item in ranked]  <-------------------------------- +
        |
        v
app.ai.matcher.JobMatcher.rank_jobs(jobs, profile)
  (legacy presentation-layer scoring - see "The V1/V2 split")
        |
        v
templates/dashboard.html
```

## Component breakdown

### `profiles/profile.json`

The single source of truth for the candidate: skills, target titles, target
locations, experience, education, certifications. Every matching, resume,
and cover-letter component reads from this file via
`app.ai.profile_loader.ProfileLoader`. Nothing else in the codebase
hardcodes personal profile data.

`ProfileLoader.load()` calls `json.load()` directly with no error recovery
beyond a bare `FileNotFoundError`. `app/web/routes.py._load_profile()`
wraps this in a `try/except` and falls back to `{}` on any exception,
printing a warning. This is worth knowing: if `profile.json` is ever
invalid JSON again, the dashboard will run silently with an *empty*
profile rather than crashing loudly. (This exact failure mode happened and
was fixed during this session - see `docs/TESTING.md` and the git history
around `tests/test_profile_integrity.py`.)

### V2 search pipeline (`app/search/v2/`)

- **`job.py`** - `CanonicalJob`, a dataclass that every job source's raw
  output gets converted into. Provides `normalized_title()`,
  `normalized_company()` (strips Finnish `Oy`/`Oyj` suffixes),
  `normalized_location()`, and `dedupe_key()`.
- **`normalizer.py`** - converts a V1 `Job` object or a plain dict into a
  `CanonicalJob`: cleans whitespace, deduplicates skills/tags
  case-insensitively while preserving first-seen spelling, parses
  `posted_at` into a real `datetime`, and maps `workplace_type` strings
  into a `remote: bool | None`.
- **`dedupe.py`** - removes duplicate `CanonicalJob`s by `dedupe_key()`:
  `source:external_id` when an external id is present, otherwise
  `normalized_title|normalized_company|normalized_location`. This is
  deliberately conservative - see "Known dedupe limitation" below.
- **`registry.py`** - the list of source classes V2 knows about
  (`SOURCE_REGISTRY`), currently `DuunitoriSource`, `JoblySource`,
  `TyomarkkinatoriSource`, `WorkInFinlandSource` from
  `app/search/sources/web_sources.py`.
- **`runner.py`** - `SourceRunner` calls `.search()` on every registered
  source. A source raising an exception is caught, logged, and skipped -
  it does not stop the other sources. Results are normalized and
  deduplicated, and the unique job count is logged.
- **`matching/`** - `JobMatcher` scores a `CanonicalJob` against
  `profile_skills`/`target_titles`/`target_locations`, producing a
  `MatchResult` (see `docs/MATCHING_AND_RANKING.md` for the formula).
- **`ranking/`** - `JobRanker` wraps `JobMatcher`, sorts by
  `(score, title_score, skill_score, location_score, posted_at)`, and
  assigns a sequential `rank`.
- **`service.py`** / **`factory.py`** - `V2SearchService` composes
  `SourceRunner` + `JobRanker`. `create_v2_service(profile)` builds one
  from a loaded profile dict, and `v2_enabled()` reads the
  `CAREERPILOT_SEARCH_V2` environment variable.

### V1 search (`app/search/manager.py`, `app/search/sources/`)

`SearchManager` predates V2. It runs its own fixed list of sources
(`AshbySource`, `GreenhouseSource`, `RemoteJobSource`, `DuunitoriSource`,
`JoblySource` - note: not Tyomarkkinatori or Work in Finland), does its own
three-tier deduplication (source id, canonical URL, content fingerprint),
and assigns each job a local integer `.id` based on its position in
`self.latest_jobs`. `SearchManager.get_job(job_id)` is a plain list index
into `self.latest_jobs`.

Every "act on a specific job" route in the Flask app -
`/generate/<id>`, `/coverletter/<id>`, `/save/<id>` - resolves the job
through `manager.get_job(job_id)`, regardless of whether V2 or V1 produced
the job list. See "The V1/V2 split" for why this matters.

### The V1/V2 split (read this if nothing else)

**V2 owns collection, normalization, deduplication, and its own scoring.**
**The dashboard's displayed score/matched-skills/reasons currently come
from the older `app.ai.matcher.JobMatcher`, not V2's `JobMatcher`.**

Concretely, `app/web/routes.py._search_jobs()`:

1. If V2 is enabled, calls `V2SearchService.search()`, which does the full
   V2 pipeline (collect -> normalize -> dedupe -> V2-score -> rank).
2. Then discards the V2 score/match data and keeps only the
   `CanonicalJob` objects: `[item.job for item in ranked]`.
3. Assigns each job a local `.id` (0, 1, 2, ...) and stores the list on
   `manager.latest_jobs`, so `/generate`, `/coverletter`, and `/save` can
   resolve it - `CanonicalJob` has no `id` field of its own, and without
   this step those three routes were broken (see `docs/TESTING.md`,
   `tests/test_routes_v2_job_ids.py`).
4. `app/web/routes.py._rank_jobs()` then runs those same `CanonicalJob`
   objects through the **legacy** `app.ai.matcher.JobMatcher.rank_jobs()`
   - a considerably larger, hand-tuned matcher with weighted skills,
   Finnish-language title terms, seniority penalties tailored for a
   junior/entry-level candidate, and an explicit exclusion list for
   obviously unrelated roles (marketing, sales, etc.).

This is not accidental - it's stated directly in a comment in
`routes.py`: *"V2 provides improved ingestion and matching data, while
the existing matcher continues to provide dashboard-compatible ranked
job objects."* In practice this means:

- V2's collection/normalization/dedupe improvements (and the Duunitori
  title-extraction fix made during this session) benefit the dashboard
  immediately, because they affect the `CanonicalJob` objects everyone
  downstream consumes.
- V2's own `JobMatcher`/`JobRanker` scoring is fully implemented, tested,
  and reachable via `V2SearchService.search()` / `.search_jobs()`, but is
  **not** what a user sees on the dashboard today.
- Unifying the two (either by having the dashboard render V2's
  `RankedJob.to_dict()` output directly, or by porting the V1 matcher's
  Finnish-language/seniority-penalty logic into V2's matcher) is real,
  scoped future work - see `docs/PRODUCT_VISION.md`.

### Presentation layer (`app/ai/matcher.py`)

`JobMatcher.rank_jobs(jobs, profile)` (the one actually driving the
dashboard) accepts either dicts or objects, normalizes each job into a
dict, and produces a list of
`{"job": {...}, "match_score": 0-100, "matched_skills": [...],
"title_category": "Primary"|"Secondary"|"Related"|"Security-related"|"Other",
"seniority": ..., "match_details": {...}}`. See
`docs/MATCHING_AND_RANKING.md` for the full scoring breakdown.

### Flask layer (`app/web/routes.py`, `webapp.py`)

`webapp.py` builds the Flask app and registers the single `web` blueprint
from `app/web/routes.py`. Routes: `/` (dashboard), `/search` (force a
re-search), `/generate/<id>` (resume), `/coverletter/<id>`, `/save/<id>`,
`/applications`, `/status/<id>/<status>`, `/delete/<id>`, plus four
sidebar-navigation routes that previously 404'd (`/resume` and
`/coverletter` redirect to the dashboard since generation is
job-specific; `/interview` renders an existing "Coming soon" placeholder;
`/settings` now hosts the CV upload form) and `/settings/upload-cv`
(`POST`, see "CV upload" below). Debug mode is opt-in via
`FLASK_DEBUG=1`, and request bodies are capped at 10MB
(`app.config["MAX_CONTENT_LENGTH"]`) - see `docs/SECURITY.md`.

### CV upload (`/settings`, `/settings/upload-cv`)

`_save_uploaded_cv()` in `app/web/routes.py` never trusts the
client-supplied filename for anything beyond its extension (checked
against an allow-list) - the file is always written to a fresh
`uuid4().hex`-named path under `data/cv_uploads/`. The route then runs
`CVParser.parse()` (PDF via PyMuPDF, DOCX via python-docx) and
`ProfileExtractor.extract()` (local LLM, JSON-in-Markdown-fence-tolerant
- see `docs/AI.md`) and renders the result on `/settings` for review.
It deliberately does not write to `profiles/profile.json` - see
`docs/PRODUCT_VISION.md` for why that's a real, separate step rather
than an oversight.

### AI document generation (`app/ai/*_builder.py`, `app/documents/`)

`AIDocumentService` composes `ResumeBuilder`/`ResumeGenerator` and
`CoverLetterBuilder`/`CoverLetterGenerator`. The `*_builder.py` classes
build a prompt from the profile + selected job and call a local Ollama
model through `AIEngine` (`app/ai/ai_engine.py`); the `*_generator.py`
classes turn the AI's output into an actual `.docx` file via
`app/documents/`. See `docs/AI.md` for the full AI architecture and why
two separate Ollama wrapper classes (`AIEngine` and `app.ai.llm.LocalLLM`)
currently coexist.

### Persistence (`app/database/`)

`app/database/database.py` opens `data/careerpilot.db` (SQLite, gitignored
- it's local runtime state, not source). `ApplicationTracker` /
`ApplicationService` implement save-job and application-status tracking,
used by `/save/<id>`, `/applications`, `/status/<id>/<status>`, and
`/delete/<id>`.

`ApplicationTracker` has two save methods with different callers: `save()`
(an `Application` dataclass in, used by the dashboard's `/save/<id>` route
via `ApplicationService.save_job()`) and `save_job()` (a raw dict in, used
only by the V1 CLI agent in `main.py`). Both now share one
`find_existing()` duplicate check - job_url when present, else
company+title - so saving the same job twice returns the existing row's
id instead of inserting a second record. `ApplicationTracker.__init__`
resolves its database path relative to the current working directory
(`Path("data") / "careerpilot.db"`) unless a `database_path` override is
passed - worth knowing when writing a test or running the app from an
unexpected working directory.

## Known dedupe limitation

`CanonicalJob.dedupe_key()` requires an exact match of normalized
title+company+location when there's no external id. During live testing,
one real posting appeared as two near-identical `CanonicalJob` entries
because the scraped title text differed slightly between two listing
pages on the same source (word order swapped). This is a deliberate
conservative tradeoff - the alternative (fuzzy/token-set title matching)
risks merging genuinely different postings that happen to share the same
words - documented here rather than "fixed" with a riskier heuristic. See
`docs/DATA_SOURCES.md`.

## Why two matchers exist instead of one

Deleting either matcher outright would have been the wrong call for a
handover document to write into the plan without evidence: the V1
`JobMatcher` handles cases (Finnish title terms, an explicit exclusion
list, experience-requirement penalties, seniority-specific mismatch
penalties) that V2's matcher does not yet implement, and it is what
currently ships to the user. Removing it in favor of an unfinished V2
matcher would be a regression, not a cleanup. The two are kept explicitly
distinct here rather than silently merged.
