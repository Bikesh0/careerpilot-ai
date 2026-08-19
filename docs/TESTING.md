# Testing

## Running the suite

```powershell
$env:TEMP = "$PWD\.pytest-tmp"
$env:TMP = "$PWD\.pytest-tmp"
New-Item -ItemType Directory -Force .\.pytest-tmp | Out-Null
.\.venv\Scripts\python.exe -m pytest -q
```

The `TEMP`/`TMP` redirection exists because this project's default
Windows temp directory has been unreliable in some development
environments (a prior session hit permission errors against the system
temp dir); redirecting to a project-local `.pytest-tmp/` sidesteps it.
It's optional in a normal environment - `pytest -q` on its own works fine
there.

**Current result: 148 passed**, in a couple of seconds. No test in the
suite performs a live network request or calls Ollama.

## What's covered, by file

| File | Covers |
| --- | --- |
| `test_search_v2_core.py` | `CanonicalJob` normalization/dedupe: whitespace/case collapsing, Finnish `Oy`/`Oyj` suffix stripping, dedupe key composition, skill deduplication, invalid-date handling, remote/hybrid mapping |
| `test_v2_matching_regressions.py` | Word-boundary skill/title matching (the Java/JavaScript false-positive case), full `JobMatcher.score_job()` scoring, and the V1-to-V2 matching port: a Finnish-titled job matches a Finnish target title, `EXCLUDED_TITLE_TERMS` scores a job 0 and flags it excluded, `JobRanker.rank()` drops excluded jobs entirely, `extract_required_experience_years()` finds the highest figure mentioned, and the experience-requirement penalty measurably lowers a demanding posting's score |
| `test_v2_ranking.py` | `JobRanker`: the mixed-`datetime`/`None` tie-break crash regression, sequential rank assignment, `limit` handling, `to_dict()` shape, title-match ordering |
| `test_profile_integrity.py` | `profiles/profile.json` is valid JSON with the fields matching depends on, and `ProfileLoader` loads it successfully - a direct regression test for the Markdown-fence corruption bug fixed this session |
| `test_duunitori_source.py` | `DuunitoriSource.parse_job_detail()` prefers `<h1>` over the JSON-LD taxonomy-slug `title` field - a direct regression test for that bug |
| `test_source_domain_guard.py` | `WebSourceBase.is_same_site()` accepts same-domain links and rejects absolute off-domain links, per source |
| `test_routes_v2_job_ids.py` | `_search_jobs()` assigns sequential local ids to V2 results and registers them on `manager.latest_jobs` - a direct regression test for the broken Generate/Save dashboard links |
| `test_dashboard_save_job.py` | Full dashboard -> `/save/<id>` -> `ApplicationTracker` -> SQLite -> `/applications` flow, using a real Flask test client and an isolated on-disk database: a job saves and persists correctly (including `job_url`, previously silently dropped), appears on the applications page, saving the same job twice does not create a duplicate row, and V2 `CanonicalJob` results save correctly |
| `test_sidebar_navigation.py` | Every link in `templates/base.html`'s sidebar resolves without a 404 - a direct regression test for four routes (`/resume`, `/coverletter`, `/interview`, `/settings`) that had no matching Flask route at all |
| `test_cv_upload.py` | `/settings/upload-cv`: rejects unsupported extensions, requires a file, extracts and displays real `.docx` data end to end (with `ProfileExtractor.extract` mocked to avoid an Ollama dependency in the automated suite), degrades gracefully when AI extraction fails, verifies a malicious filename (`"../../evil.docx"`) cannot escape the upload directory - the saved file is always named by a fresh UUID, never by client input - and `/settings` itself has no `profile.json`/"review-only preview" implementation jargon in its copy |
| `test_ranking_unification.py` | The dashboard renders V2's own score and reason strings (not a legacy re-score) when V2 succeeds - proven with a job description that would score very differently under the legacy matcher, and reason text ("Target job title matched") only V2's matcher ever produces; V2's ranking order is preserved (no re-sort); legacy mode is untouched when V2 is disabled (no V2-only text ever appears, `manager.search_jobs()` is confirmed as the actual source); presentation-adapter failures fall back to the legacy matcher instead of crashing; save/generate/cover-letter routes still resolve V2 jobs correctly through the new presentation path |
| `test_robots_txt_compliance.py` | `DuunitoriSource` is not registered in either V1's `SearchManager.searchers` or V2's `SOURCE_REGISTRY` (its `robots.txt` disallows this scraper's user-agent - see `docs/DATA_SOURCES.md`); `JoblySource.get_page()` sleeps for its `robots.txt`-specified `Crawl-delay` after every request (mocked, doesn't actually sleep in the suite) |
| `test_skill_gap.py` | `app/ai/skill_gap.analyze_skill_gap()`: required vs. nice-to-have classification per sentence, a genuinely-absent skill (e.g. Terraform) surfacing as a real gap - not the matchers' inverse `missing_skills` - with a real recommendation attached, CV-evidence notes for skills claimed but not demonstrated in experience (and no note when they are), certifications never fabricated for skills with none real (Git, VPN), effort-based prioritization ordering, the "no requirements detected" flag, and a regression test for a sentence-final-punctuation bug that silently hid skill mentions ("Terraform." not matching the alias "terraform") |
| `test_skill_gap_route.py` | `/analyze/<job_id>`: the dashboard links every job card to its analysis, the rendered page shows the full requirement -> skill -> gap -> recommended-action flow end to end, a "You already demonstrate" section renders before the detailed breakdown, a direct Apply link to the real posting is present, the "ready to apply" banner renders when every required skill is matched, the score is explicitly labeled as not a probability, internal implementation jargon is absent, and an unknown job id returns 404 |
| `test_cv_strength.py` | `app/ai/cv_strength.analyze_cv_strength()`: skill proficiency (Advanced via 2+ experience mentions, Advanced-but-honest via certification-only, Basic when unevidenced), the certification/evidence-text contradiction bug found and fixed, unquantified-experience detection, the 5-item weakness cap, honest (never-fabricated) certification/project suggestions, a weakly-evidenced catalog skill carries the full what/where/how/time recommendation path (plus the catalog key for the "Start this project" link), a skill outside the catalog still gets a plain-language suggestion, verified-project evidence upgrades a skill to Advanced (both when already declared and when surfacing a wholly new one), and a crash-free empty-profile baseline |
| `test_cv_strength_route.py` | `/cv-strength` renders with the real profile and no internal implementation jargon (`profile.json`, "deterministic"); the sidebar links to it |
| `test_application_funnel.py` | `app/services/application_service._funnel_insight()`: offer takes priority over every other signal, a small sample gets a neutral "not enough data" message rather than a false CV-quality signal, many-applications/few-interviews points at CV/targeting, several-interviews/no-offers points at interview prep, a healthy funnel gets encouragement, and Second/Final Round both count toward "interview stage or later" alongside Interview/Offer |
| `test_status_transitions_route.py` | `/status/<id>/<status>` correctly decodes a URL-encoded multi-word status ("Second%20Round") back to the exact stored string; `/applications` and `/` render the new funnel stats/insight; `Withdrawn` is a valid, separately-counted status that doesn't count as interview-stage progress; every dashboard job card has a working Apply link to the real posting URL; the dashboard explains what "Profile Match" means and that it isn't a hiring probability |
| `test_interview_prep.py` | `/interview/<job_id>`: gated (no LLM call, no generation) before the job's saved application reaches "Interview" status; unlocks for Interview, Second Round, and Final Round alike; degrades to a `503` instead of crashing when the LLM is unavailable; the dashboard only shows the "Interview Prep" button once a job is actually ready; the bare `/interview` landing explains the gate |
| `test_cv_upload_hardening.py` | The master `profiles/profile.json` file is byte-identical before and after a CV upload+extraction (hashed directly, not assumed); uploads past the 24-hour retention window are cleaned up while recent ones are kept; the upload route rate-limits excessive attempts with a `429` |
| `test_project_tracking.py` | `app/database/project_tracker.py`/`app/services/project_service.py`: project creation, that status only ever changes via an explicit `update_status()` call (never a side effect of reading/creating a project), notes accumulate rather than overwrite, `get_verified_by_skill_key()` only returns Verified projects, `verified_skill_keys()` reflects status changes, and an unknown status is rejected |
| `test_project_routes.py` | `/projects/start/<job_id>/<skill_key>`, `/projects/start-general/<skill_key>` (the job-independent Layer 1 variant), `/projects`, `/projects/<id>`, `/projects/<id>/status/<status>`, `/projects/<id>/plan`, `/projects/<id>/ask`, `/projects/<id>/review`, `/projects/<id>/cv-bullet`: a Skill Gap recommendation links to starting a project, the CV-strength page uses the job-independent route, an unknown skill key 404s, status changes end-to-end through the real route (catching a real space-in-URL encoding bug found while building this), a CV bullet is gated to `Verified` status and grounded only in the project's own text, the AI coach's plan/ask/review actions all append to notes and each degrades gracefully (no `500`) when Ollama is unavailable, and an unknown project id 404s |
| `test_greenhouse_source.py` | `GreenhouseSource` field mapping against a mocked HTTP response |
| `test_persistence_integration.py`, `test_v1_search_integration.py` | V1 search + SQLite persistence, against a temporary database |
| `test_suitability.py`, `test_filter_and_matching.py` | V1 job-suitability scoring and filtering |

## Testing approach

- **Unit tests** for pure logic (normalization, dedupe keys, word-boundary
  matching, ranking tie-breaks) construct objects directly with no
  mocking needed.
- **Source tests** mock `requests`/HTTP at the boundary (see
  `test_greenhouse_source.py`'s `MockResponse` pattern) or, where the
  logic under test is pure HTML parsing (`test_duunitori_source.py`),
  pass a hand-written HTML string directly into `parse_job_detail()` -
  no mocking framework needed since the method takes HTML as an argument.
- **Route-level regression tests** (`test_routes_v2_job_ids.py`) monkeypatch
  the two functions `_search_jobs()` actually calls
  (`app.web.routes.v2_enabled`, `app.web.routes.create_v2_service`) rather
  than exercising a real Flask test client end-to-end, specifically to
  avoid a live network call inside the automated suite.
- **Full end-to-end route tests** (`test_dashboard_save_job.py`) do use a
  real Flask test client for the entire dashboard -> save -> applications
  round trip, still with `create_v2_service`/`v2_enabled` monkeypatched
  (no live network call) and the database isolated via
  `monkeypatch.chdir(tmp_path)`, since `ApplicationTracker` resolves its
  SQLite path relative to the current working directory.
- **Integration tests** (`test_persistence_integration.py`,
  `test_v1_search_integration.py`) use a temporary SQLite database
  (`tmp_path`), never the real `data/careerpilot.db`.

## What's deliberately outside the automated suite

```powershell
# Requires network access and contacts real job boards.
.\.venv\Scripts\python.exe test_sources.py

# Requires a running local Ollama service and an installed model.
.\.venv\Scripts\python.exe app\ai\test_llm.py
```

Both are excluded via `pyproject.toml`'s `testpaths = ["tests"]` and a
`live` pytest marker reserved for exactly this purpose. Live end-to-end
verification for this session's fixes (real V2 search results, a real
Flask dashboard request cycle, a real `/generate`/`/save` round trip) was
done manually against the live sources and a Flask test client, not added
to the automated suite, to keep the suite's "no live network calls, no
Ollama dependency" guarantee intact.

## Adding a test

Follow the existing per-file pattern above rather than introducing a new
one: pure-logic tests construct objects directly; source-parsing tests
pass a hand-written HTML/JSON fixture into the parsing method; anything
touching Flask routes monkeypatches at the function boundary the route
actually calls, not the whole HTTP stack, unless the test is specifically
about routing/URL behavior itself.
