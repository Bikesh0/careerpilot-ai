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

**Current result: 39 passed**, in well under a second. No test in the
suite performs a live network request or calls Ollama.

## What's covered, by file

| File | Covers |
| --- | --- |
| `test_search_v2_core.py` | `CanonicalJob` normalization/dedupe: whitespace/case collapsing, Finnish `Oy`/`Oyj` suffix stripping, dedupe key composition, skill deduplication, invalid-date handling, remote/hybrid mapping |
| `test_v2_matching_regressions.py` | Word-boundary skill/title matching (the Java/JavaScript false-positive case), full `JobMatcher.score_job()` scoring |
| `test_v2_ranking.py` | `JobRanker`: the mixed-`datetime`/`None` tie-break crash regression, sequential rank assignment, `limit` handling, `to_dict()` shape, title-match ordering |
| `test_profile_integrity.py` | `profiles/profile.json` is valid JSON with the fields matching depends on, and `ProfileLoader` loads it successfully - a direct regression test for the Markdown-fence corruption bug fixed this session |
| `test_duunitori_source.py` | `DuunitoriSource.parse_job_detail()` prefers `<h1>` over the JSON-LD taxonomy-slug `title` field - a direct regression test for that bug |
| `test_source_domain_guard.py` | `WebSourceBase.is_same_site()` accepts same-domain links and rejects absolute off-domain links, per source |
| `test_routes_v2_job_ids.py` | `_search_jobs()` assigns sequential local ids to V2 results and registers them on `manager.latest_jobs` - a direct regression test for the broken Generate/Save dashboard links |
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
