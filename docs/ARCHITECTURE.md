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
   |-- Jobly (crawl-delay compliant, see DATA_SOURCES.md)        |
   |-- Tyomarkkinatori (currently 0 results, see DATA_SOURCES.md)|
   |-- Work in Finland (currently 0 results, see DATA_SOURCES.md)|
   (Duunitori is implemented but deliberately unregistered -      |
    its robots.txt disallows this scraper, see DATA_SOURCES.md)  |
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
  (`SOURCE_REGISTRY`), currently `JoblySource`, `TyomarkkinatoriSource`,
  `WorkInFinlandSource` from `app/search/sources/web_sources.py`.
  `DuunitoriSource` also exists there and is fully implemented/tested,
  but is deliberately not in `SOURCE_REGISTRY` - its `robots.txt`
  disallows this scraper's user-agent, see `docs/DATA_SOURCES.md`.
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
(`AshbySource`, `GreenhouseSource`, `RemoteJobSource`, `JoblySource` -
note: not Tyomarkkinatori or Work in Finland, and no longer
`DuunitoriSource` either - see `docs/DATA_SOURCES.md`), does its own
three-tier deduplication (source id, canonical URL, content fingerprint),
and assigns each job a local integer `.id` based on its position in
`self.latest_jobs`. `SearchManager.get_job(job_id)` is a plain list index
into `self.latest_jobs`.

Every "act on a specific job" route in the Flask app -
`/generate/<id>`, `/coverletter/<id>`, `/save/<id>`, `/analyze/<id>`
(skill-gap analysis, `app/ai/skill_gap.py`), `/interview/<id>` (gated
interview prep, `app/ai/interview_prep.py`) - resolves the job through
`manager.get_job(job_id)`, regardless of whether V2 or V1 produced the
job list. This also means all of them share the same limitation:
`job_id` is a position in the *current* `manager.latest_jobs` list, not
a durable identifier, so a job that's fallen out of the latest search
results (e.g. after a new search) is no longer reachable by that id -
saved applications persist independently in SQLite (by `job_url`), but
don't carry enough job data (no description text) to regenerate
analysis/prep for a job that's no longer in `manager.latest_jobs`. See
"The V1/V2 split" for why this matters for scoring specifically.

### The V1/V2 split (read this if nothing else)

**Ownership is decided by where the job data actually came from, not by
re-checking the feature flag.** When V2 search succeeds, the dashboard
shows V2's own score, matched skills, and reasons - not a legacy-matcher
re-score of the same job. When V2 is disabled, or V2 search/ranking
itself fails, the legacy `app.ai.matcher.JobMatcher` is still what
renders the dashboard, completely unchanged from before.

Concretely, `app/web/routes.py._search_jobs()`:

1. If V2 is enabled, calls `V2SearchService.search()`, which does the full
   V2 pipeline (collect -> normalize -> dedupe -> V2-score -> rank).
2. Assigns each `CanonicalJob` a local `.id` (0, 1, 2, ...) - it has no
   `id` field of its own, and `/generate`, `/coverletter`, and `/save`
   all resolve jobs through it (see `tests/test_routes_v2_job_ids.py`).
3. **Stashes the already-computed `MatchResult` onto the job itself**
   (`job._v2_match = item.match`) instead of discarding it, and stores
   the list on `manager.latest_jobs`.

`app/web/routes.py._rank_jobs()` then checks whether every job in the
list carries a stashed `_v2_match`:

- **If so** (V2 really is the source), `_present_v2_ranked_jobs()` adapts
  V2's own score/matched_skills/reasons directly into the dashboard's
  presentation shape, **preserving V2's ranking order** - no re-sort, no
  second scoring pass through the legacy matcher.
- **If not** (V2 disabled, or `_search_jobs()` fell back to
  `manager.search_jobs()` because V2 itself failed), the jobs are plain
  V1 `Job` objects with no stashed match, and the **exact same**
  `matcher.rank_jobs(jobs, profile)` call that existed before this change
  runs - legacy behavior is untouched on that path.
- If `_present_v2_ranked_jobs()` itself raises for any reason, `_rank_jobs()`
  catches it and falls back to the legacy matcher rather than crashing
  the request - the same fail-soft convention used everywhere else in
  this module.

This was a deliberate, scoped integration rather than a rewrite of
either matcher: V2's collection/normalization/dedupe/matching/ranking
code is completely unchanged, the legacy `JobMatcher` class is completely
unchanged (and remains the sole presentation layer for V1), and the only
new code is the adapter (`_present_v2_ranked_jobs()`) plus the ownership
check in `_rank_jobs()`. `templates/dashboard.html` also gained a small
"match reasons" list (rendered when `item.match_reasons` is present -
only true for V2-presented jobs; a no-op, unchanged rendering for legacy
dict-based jobs, which never have that key).

### Presentation layer (`app/ai/matcher.py`, `app/web/routes.py`)

Two producers feed the same dashboard shape
(`{"job": {...}, "match_score": 0-100, "matched_skills": [...], ...}`),
and `_rank_jobs()` (see "The V1/V2 split" above) picks exactly one per
request, never both:

- **`_present_v2_ranked_jobs()`** (`app/web/routes.py`) - used when V2
  is the source. A thin adapter: `job.to_dict()` plus the injected `id`
  for the `"job"` key, and `match_score`/`matched_skills`/
  `missing_skills`/`match_reasons` read directly off the stashed
  `MatchResult`. No scoring logic lives here - it only reshapes data V2
  already computed.
- **`JobMatcher.rank_jobs(jobs, profile)`** (`app/ai/matcher.py`) - used
  for the V1 fallback path, completely unchanged. Accepts either dicts or
  objects, normalizes each job into a dict, and produces a list of
  `{"job": {...}, "match_score": 0-100, "matched_skills": [...],
  "title_category": "Primary"|"Secondary"|"Related"|"Security-related"|"Other",
  "seniority": ..., "match_details": {...}}`.

See `docs/MATCHING_AND_RANKING.md` for each matcher's actual scoring
formula.

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
model through `app.ai.llm.LocalLLM` (the single Ollama wrapper class in
this codebase - a previously-separate duplicate, `AIEngine`, was
consolidated into it, see `docs/AI.md`); the `*_generator.py` classes
turn the AI's output into an actual `.docx` file via `app/documents/`.

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

Deleting either matcher outright would have been the wrong call: V1
`JobMatcher` handled cases V2's matcher didn't implement yet. Rather than
choosing one and discarding real, working functionality, the dashboard
uses **whichever matcher actually produced the job list** (see "The
V1/V2 split"): V2's own scoring when V2 search succeeds, V1's more
elaborate scoring as a genuine fallback when it doesn't. Both classes
remain independently usable - ownership is decided by a thin adapter and
a presence check in `app/web/routes.py`, not by picking a winner and
deleting the other.

**Three specific gaps identified when this integration first shipped
have since been ported into V2's matcher**: Finnish-language title
recognition (as data - added to `profiles/profile.json`, since V2's
title matching has no hardcoded vocabulary of its own to add Python
constants to), an exclusion list for obviously unrelated roles
(marketing, sales, HR, etc. - ported as code, since it's generic rather
than profile-specific), and a required-experience penalty (ported as
code, same thresholds as V1). See `docs/MATCHING_AND_RANKING.md`'s
"Ported from V1" for the exact mechanism and tests, live-verified against
the real profile and real sources afterward.

**Remaining differences, a deliberate scope boundary, not an oversight**:
V1's tiered title-category scoring (`PRIMARY`/`SECONDARY`/`RELATED`
rather than V2's binary match/no-match), weighted skill importance
(`SKILL_WEIGHTS` plus a skill-alias table), and V1's much steeper flat
seniority-mismatch penalties were **not** ported - these are genuine
design-philosophy differences between a simpler, cleanly-weighted matcher
(V2) and a heavily hand-tuned one (V1), not gaps to mechanically copy
over. Porting them would mean re-deriving V1's weights inside V2 without
the evidence trail that produced them in the first place. If full parity
is ever wanted, that's a real design decision - see `docs/MATCHING_AND_RANKING.md`'s
"Known edge cases and limitations".
