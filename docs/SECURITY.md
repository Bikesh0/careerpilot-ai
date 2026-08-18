# Security

This document is written to be useful in a cybersecurity interview: what
was checked, what was found, what was fixed, and what's a known,
accepted limitation.

## TLS / certificate verification

**Policy**: `requests` is never called with `verify=False` anywhere in
this codebase (checked directly - zero occurrences). All HTTP requests go
through `WebSourceBase.get_page()`, which uses `requests`' default
verification behavior (the `certifi` CA bundle).

An earlier handoff document claimed Tyomarkkinatori failed with a TLS
certificate error. That claim was re-investigated from scratch rather than
trusted: a direct `requests.get()` against the same URL, using this
project's actual dependency stack, succeeded with a valid certificate. The
zero-results issue for that source is a client-side-JavaScript-rendering
problem, not a TLS problem - see `docs/DATA_SOURCES.md` for the full
investigation. No TLS verification was weakened to "fix" anything, because
nothing here was actually a TLS bug.

## SSRF / following untrusted links

**Found and fixed this session.** `DuunitoriSource`, `JoblySource`,
`TyomarkkinatoriSource`, and `WorkInFinlandSource` all follow links scraped
out of third-party HTML (`urljoin(self.BASE_URL, href)`) to fetch a job's
detail page. `urljoin()` leaves an **absolute** `href` untouched - if a
scraped page contained an absolute link to another host (a compromised ad,
a malicious embedded widget, an attacker-controlled URL disguised as a job
link), the scraper would previously fetch it as if it were a same-site job
posting, sending this project's `User-Agent` and following redirects
wherever that URL led.

**Fix**: `WebSourceBase.is_same_site(url)` compares the resolved URL's
`netloc` against the source's own `BASE_URL` before any detail-page fetch.
All four sources now skip a link whose resolved URL doesn't match their
own domain. Regression tests: `tests/test_source_domain_guard.py`.

## XSS / template rendering

Every Flask template is rendered through Jinja2's default autoescaping
(the project uses `.html` templates with no custom autoescape
configuration). Checked directly: **zero** uses of `| safe` or `Markup()`
anywhere in the codebase. Job titles, descriptions, and company names -
all untrusted, scraped, third-party content - are rendered as plain
`{{ variable }}` expressions and are HTML-escaped automatically.

## Flask debug mode

**Found and fixed this session.** `webapp.py` called `app.run(debug=True)`
unconditionally. Flask's debug mode enables the Werkzeug interactive
debugger, which allows arbitrary Python code execution from the browser if
the debugger is ever reachable from outside localhost, and it also leaks
full stack traces on any unhandled exception. It now defaults to **off**
and is opt-in via `FLASK_DEBUG=1` for local development.

## Secrets and credentials

No hardcoded API keys, tokens, or passwords anywhere in the codebase
(checked directly with a pattern search). Local LLM configuration
(`OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `OLLAMA_MAX_TOKENS`) is
read from environment variables with sane defaults. `.gitignore` excludes
`.env`/`.env.*` (with an explicit `.env.example` exception). No `.env` file
or anything secret-shaped was found tracked in git.

## Subprocess / command injection

No use of `subprocess`, `os.system`, `eval()`, `exec()`, or `pickle.load`
anywhere in `app/` (checked directly). Document generation
(`python-docx`) and CV parsing (`PyMuPDF`) operate on file contents in
Python, not shell commands.

## Path handling

`app/parsers/cv_parser.py` (`CVParser.parse(file_path)`) opens a file path
directly with no path-traversal guard of its own - safety here comes from
its caller, not from `CVParser` itself.

**Now a live attack surface**: `/settings/upload-cv`
(`app/web/routes.py`) accepts a file upload and is the only route that
calls `CVParser.parse()`. The client-supplied filename is **never** used
to build the destination path - `_save_uploaded_cv()` only reads its
extension (checked against an allow-list: `.pdf`, `.docx`) and writes to
a freshly generated `uuid4().hex` filename under `data/cv_uploads/`, so a
filename like `"../../evil.docx"` cannot escape that directory (verified
directly: `tests/test_cv_upload.py` uploads a file with that exact name
and asserts the saved path stays inside `data/cv_uploads/` and is never
named `evil.docx`). The upload is also capped at 10MB
(`app.config["MAX_CONTENT_LENGTH"]` in `webapp.py`) to reject a trivially
abusive upload before it's fully read into memory. `data/cv_uploads/` -
which holds real personal documents (name, contact info, work history)
once this is actually used - is in `.gitignore`, found and fixed during
this session's final security review: the directory didn't exist yet in
this repository, but nothing had explicitly excluded it, so a future
uploaded CV could have been accidentally committed by a broad `git add`.

Extracted CV data is displayed for review only - `/settings/upload-cv`
never writes to `profiles/profile.json` automatically, so a bad or
AI-hallucinated extraction can't silently corrupt the profile that
matching, resumes, and cover letters depend on.

`app/web/actions.py` (`WebActions`) remains unused - nothing in the
codebase imports it outside its own file.

## Respecting `robots.txt`

This project checks and respects `robots.txt` before scraping a source,
the same way it never disables TLS verification to make a source "work."
Two real findings this session, one caught before shipping and one found
in an already-shipped, heavily-relied-upon source:

- **Tyomarkkinatori** (caught before shipping): its internal JSON search
  API is unauthenticated and technically reachable, and a working
  scraper against it was built and verified live (see
  `docs/DATA_SOURCES.md`). It was reverted rather than shipped, because
  `tyomarkkinatori.fi/robots.txt` explicitly states `Disallow: /api/`. An
  endpoint being public and requiring no authentication doesn't override
  the site operator's stated crawling policy.
- **Duunitori** (found in already-running code): `duunitori.fi/robots.txt`
  disallows the generic `*` user-agent group entirely (`Disallow: /`),
  with specific exceptions only for a named allowlist of crawlers
  (Googlebot, Bingbot, etc.). `DuunitoriSource` sends a spoofed generic
  browser `User-Agent`, which matches none of those named exceptions and
  therefore falls under the `*` group's blanket disallow. This scraper
  had already been shipped, fixed, and re-verified multiple times
  earlier in this session before `robots.txt` was checked at all. Once
  found, it was reported directly rather than silently fixed or silently
  left running - disabling it was a real tradeoff (it had been the
  largest single source of collected jobs) and was the user's decision to
  make, not a unilateral one. It's now unregistered from both V1 and V2
  search (code intact, not deleted - see `docs/DATA_SOURCES.md` for how
  to re-enable it correctly).

**Jobly**, by contrast, has a compliant `robots.txt` (no `Disallow` on
the paths this project scrapes) but specifies `Crawl-delay: 10`, which
the scraper wasn't honoring - fixed by adding a 10-second pause after
every request in `JoblySource.get_page()`.

The lesson applied going forward: check `robots.txt` for the *exact*
user-agent group a scraper's actual request will match (not just
whichever group looks most permissive) before treating a source as
compliant, whether it's new or already shipped.

## AI-generated content

Resume and cover-letter prompts (`app/ai/resume_builder.py`,
`app/ai/cover_letter_builder.py`) explicitly instruct the model not to
invent experience, education, certifications, or skills, and to use only
the supplied profile data. This is a prompt-level control, not a
cryptographic guarantee - see `docs/AI.md` for the full discussion of this
tradeoff and why deterministic code (not the LLM) owns matching/ranking/
filtering.

## Denial-of-service / hung requests

**Found and fixed this session.** The resume/cover-letter generation
path called `ollama.chat()` with no timeout at all (via a since-removed
duplicate class, `AIEngine`). Live-tested: in an environment where the
local Ollama service responds very slowly, this could block a Flask
request indefinitely. It was first hardened with a bounded daemon-thread
watchdog, then that duplicate class was consolidated away entirely -
every AI call site now goes through the single `app.ai.llm.LocalLLM`
(default 30s timeout, configurable via `OLLAMA_TIMEOUT`), returning a
clear failure instead of hanging. See `docs/AI.md`.

## Dependency posture

Runtime dependencies (`requirements.txt`) are pinned to major-version
ranges (`Flask>=3.0,<4.0`, etc.), not exact pins - a reasonable choice for
a single-maintainer local tool, though it means a `pip install` today and
in six months can resolve different patch versions. No automated
dependency-vulnerability scanning is configured (no `dependabot.yml`, no
CI at all currently - see `docs/DEVELOPMENT.md`).

## Known limitations (stated honestly)

- No CSRF protection on the Flask routes that mutate state (`/save/<id>`,
  `/status/<id>/<status>`, `/delete/<id>` are plain `GET` routes with no
  token). Acceptable for a single-user local tool with no authentication
  layer at all; would need addressing before any multi-user or
  internet-facing deployment.
- No authentication/authorization anywhere - by design, this is a local,
  single-user tool.
- Runtime dependencies are range-pinned, not hash-pinned or lock-filed.
