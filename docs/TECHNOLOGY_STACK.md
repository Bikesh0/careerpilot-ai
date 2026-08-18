# Technology Stack

Every entry below was confirmed directly against this repository -
`requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, and actual
imports in the source - not assumed from what a project like this would
typically use. Nothing is listed unless it's actually present.

## Runtime dependencies

Required for CareerPilot AI to run (`requirements.txt`).

| Technology | Purpose | Where used | Why chosen | Configuration | Limitations |
| --- | --- | --- | --- | --- | --- |
| **Python 3.10-3.12** | Application language | Entire codebase | Mature ecosystem for scraping, data processing, and Flask; the source uses 3.10+ type-syntax (`list[str]`, `X \| None`) so 3.10 is the floor. Verified working on 3.12.13. | Declared in `pyproject.toml` (`requires-python = ">=3.10,<3.13"`) | None encountered |
| **Flask 3.x** | Web dashboard framework | `webapp.py`, `app/web/routes.py`, `templates/` | Lightweight, no unneeded structure for a single-user local tool | Blueprint-based (`web` blueprint); debug mode off by default, opt-in via `FLASK_DEBUG=1` (see `docs/SECURITY.md`) | No CSRF protection on state-changing routes - acceptable for a local, unauthenticated single-user tool, not for a multi-user deployment |
| **requests 2.x** | HTTP client for scraping and the local Ollama client's transport | `app/search/sources/*.py`, `app/search/v2/` (indirectly, via the source classes) | Standard, well-understood HTTP library; default TLS verification is exactly what this project needs and never overrides it | Per-request 20s timeout in `WebSourceBase`; TLS verification always on (see `docs/SECURITY.md`) | Static HTML only - cannot execute JavaScript, which is why two of the four job sources currently return zero results (see `docs/DATA_SOURCES.md`) |
| **beautifulsoup4 4.x** | HTML parsing | `app/search/sources/web_sources.py` and other V1 source files | Standard Python HTML parsing library; used with the stdlib `html.parser` backend (no `lxml` dependency needed) | None beyond the parser choice | Parses whatever HTML is served - cannot recover data that only exists after client-side JS execution |
| **ollama (Python client) 0.4.x** | Local LLM client | `app/ai/llm.py` (`LocalLLM` - the single Ollama wrapper class in this codebase) | Talks to a locally-running Ollama server - no hosted API, no API key, keeps candidate data on the local machine by default | `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `OLLAMA_MAX_TOKENS` env vars (see `docs/AI.md`) | Requires Ollama installed and running locally with a model pulled; without it, generation features return a clear "unavailable" response rather than working |
| **python-docx 1.1.x** | `.docx` document generation and parsing | `app/documents/resume_template.py` (generation), `app/parsers/cv_parser.py` (`.docx` CV parsing via `/settings/upload-cv`) | Standard library for reading/writing Word documents in Python | None | `.docx` only - doesn't handle legacy `.doc` |
| **PyMuPDF 1.24.x** (imported as `pymupdf`, aliased `fitz`) | PDF text extraction | `app/parsers/cv_parser.py`, reachable via `/settings/upload-cv` | Fast, reliable PDF text extraction | None | None encountered |
| **SQLite** (Python stdlib `sqlite3`) | Saved-job / application-tracking persistence | `app/database/database.py`, `app/database/application_tracker.py` | Zero-setup embedded database, appropriate for a single-user local tool | Database file at `data/careerpilot.db` (gitignored) | Not suitable if this ever became multi-user/concurrent |
| **Jinja2** (bundled with Flask) | Template rendering | `templates/*.html` | Ships with Flask; default autoescaping is relied on directly for XSS protection against scraped job content (see `docs/SECURITY.md`) | Default autoescape on; no template uses `\| safe` or `Markup()` | None encountered |
| **Bootstrap 5.3.7** (CDN, not a Python/npm dependency) | Base CSS/JS framework for layout, loaded via `<link>`/`<script>` in `templates/base.html` | Every page (sidebar layout, base styling); the dashboard itself layers a large custom inline `<style>` block on top | Fast to get a clean base layout without a build step | Loaded from `cdn.jsdelivr.net` - requires internet access to load correctly; not vendored locally | No project-authored JavaScript exists anywhere in this codebase - confirmed directly; Bootstrap's bundled JS is the only script on any page |

## Development tools

Used to build and verify CareerPilot AI; not required to run it.

| Technology | Purpose | Where used |
| --- | --- | --- |
| **pytest 8.x** | Automated test suite | `tests/`, configured in `pyproject.toml` (`testpaths = ["tests"]`, a `live` marker for tests deliberately excluded from the default run) |
| **Git / GitHub** | Version control, remote hosting | Full project history; remote at `github.com/Bikesh0/careerpilot-ai` |
| **Claude Code (Claude Sonnet 5)** | AI development assistant | Used across multiple sessions for repository analysis, bug investigation, implementation, test-writing, and documentation. **Not** a runtime dependency of the application - see `docs/AI.md` for the explicit distinction between this and the application's own Ollama integration |

## Optional / not currently used

Explicitly not part of this project, called out here so nothing is assumed:

- **No hosted LLM API** (OpenAI, Anthropic, etc.) - local Ollama only.
- **No browser automation** (Playwright, Selenium) - `app/automation/playwright_bot.py`
  exists as an empty placeholder file; neither package is installed
  (confirmed: `pip show playwright selenium` reports neither installed).
  This is why the two JavaScript-rendered job sources currently return
  zero results (see `docs/DATA_SOURCES.md`).
- **No Docker** - no `Dockerfile` or `docker-compose.yml` in the
  repository.
- **No CI** - no `.github/workflows` directory; `pytest` is run manually.
- **No PostgreSQL or any non-SQLite database.**
- **No custom JavaScript** - confirmed via direct search of every
  template; the only `<script>` tag in the codebase loads Bootstrap's
  bundled JS from a CDN.
