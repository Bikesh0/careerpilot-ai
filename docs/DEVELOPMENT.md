# Development

## Cloning and environment setup

```powershell
git clone https://github.com/Bikesh0/careerpilot-ai.git
cd careerpilot-ai
git checkout v2-development

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` pulls in `requirements.txt` (runtime deps) plus
`pytest`. Supported Python: 3.10-3.12 (the source uses 3.10+ type-syntax
features); this repository was developed and verified against 3.12.13.

## Configuration

No `.env` file is required for the test suite or for a basic V1 search.
For the V2 pipeline and for AI features, set:

```powershell
$env:CAREERPILOT_SEARCH_V2 = "1"   # enable V2 search
$env:OLLAMA_HOST = "http://127.0.0.1:11434"   # only if not default
$env:OLLAMA_MODEL = "llama3.1"                # only if not auto-detected
$env:FLASK_DEBUG = "1"             # only for local debugging
```

See the full variable table in `README.md`'s Configuration section.

## Running the Flask dashboard

```powershell
$env:CAREERPILOT_SEARCH_V2 = "1"
.\.venv\Scripts\python.exe webapp.py
```

Visit `http://127.0.0.1:5000/`. The dashboard triggers a live search
against the real job sources on load. Currently only Jobly returns
results (Duunitori is disabled pending `robots.txt` compliance;
Tyomarkkinatori and Work in Finland return 0 - see
`docs/DATA_SOURCES.md`), and Jobly's scraper deliberately pauses 10
seconds after every request to honor its `robots.txt` `Crawl-delay` -
expect a full dashboard load to take several minutes, not seconds.

## Running a V2 search directly (no Flask)

Useful for iterating on matching/ranking without waiting on the full
dashboard render:

```powershell
$env:CAREERPILOT_SEARCH_V2 = "1"
.\.venv\Scripts\python.exe -c "
from app.ai.profile_loader import ProfileLoader
from app.search.v2.factory import create_v2_service

profile = ProfileLoader().load()
service = create_v2_service(profile=profile)
ranked = service.search(limit=20)
for item in ranked:
    print(item.rank, item.match.score, item.job.title, item.job.source)
"
```

## Running the CLI job agent (V1 path)

```powershell
.\.venv\Scripts\python.exe main.py
```

## Running tests

```powershell
$env:TEMP = "$PWD\.pytest-tmp"
$env:TMP = "$PWD\.pytest-tmp"
New-Item -ItemType Directory -Force .\.pytest-tmp | Out-Null
.\.venv\Scripts\python.exe -m pytest -q
```

See `docs/TESTING.md` for what's covered and the testing approach.

## Compilation / syntax checks

After any structural change to a Python module:

```powershell
.\.venv\Scripts\python.exe -m py_compile <changed_file.py>
```

## Debugging

- `print()` is used throughout for operational logging (source
  success/failure counts, AI request warnings, profile-load failures) -
  there is no structured logging framework in this codebase. When
  debugging, redirect stdout in a small script (as in the V2-search
  snippet above) rather than parsing dashboard HTML by hand.
- AI generation failures degrade gracefully (a 503 with a plain-text
  message) rather than crashing - if `/generate/<id>` or
  `/coverletter/<id>` returns that message, check whether Ollama is
  running and whether `OLLAMA_TIMEOUT` is long enough for your local
  model's actual response time.
- If the dashboard's job-action links (`Generate Resume` / `Cover Letter`
  / `Save Job`) ever point to a URL with no trailing id again, that's the
  exact failure mode fixed in `tests/test_routes_v2_job_ids.py` -
  `manager.latest_jobs` must be populated whenever a job list is served.

## Git workflow

- Work happens on `v2-development`; `main` holds the released V1.0
  baseline.
- Commit messages follow Conventional-Commits-style prefixes (`feat:`,
  `fix:`, `security:`, `docs:`, `chore:`, `test:`) and explain *why*, not
  just *what* - see the git log for the actual pattern used in this
  session's fixes.
- Before committing: run the full test suite, review `git status`/`git
  diff` for anything unexpected (generated files, credentials, stray
  debug output), and confirm `.gitignore` covers what shouldn't be
  tracked (local SQLite DB, generated resumes/cover letters, pytest
  scratch directories).
- There is no CI configured (`.github/workflows` doesn't exist). Running
  `pytest` locally before pushing is the only gate.
