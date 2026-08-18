# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18 (session stopped mid-task at explicit user request - see
"Stop reason" below)

## Stop reason

The user asked to stop safely: save completed work to disk, do not
start another development task, update this file with exactly what was
done, and stop. This file reflects that exact state. Nothing below was
left half-edited - every commit listed passed the full test suite before
being made.

## Current branch

`v2-development`, pushed to `origin` (`https://github.com/Bikesh0/careerpilot-ai.git`).

## What was completed this session

Started from a repo where V2 search/matching/ranking had been built but
never committed, and the previous handoff notes (now known to be
partially wrong - see below) claimed 24 passing tests, ~43 collected
jobs, and a TLS failure on Tyomarkkinatori. Each of those claims was
independently re-verified rather than trusted, which is how the real
bugs below were found.

### Code fixes (7 commits, all tested and pushed)

1. **`ec741ac` - feat: complete V2 search foundation and fix ranking
   module collision.** Committed the previously-uncommitted V2
   ingestion/matching/ranking work. Also found and fixed a real bug:
   `app/search/v2/ranking.py` (a stray file) and `app/search/v2/ranking/`
   (a package) coexisted in the same directory; Python resolves the
   package first, so the *older*, buggier ranker was silently active
   (it crashed on any score tie where `posted_at` was `None` for one job
   and a real `datetime` for another - comparing `str` and `datetime`
   raises `TypeError`). Consolidated the better implementation into the
   package and deleted the shadowed file, plus an unused/superseded
   `pipeline.py`. Also fixed three packages using `_init_.py` instead of
   `__init__.py` (`app/database`, `app/search/sources`, `tests/utils`) -
   the `tests/utils/_init_.py` one contained a stray, syntactically-broken
   code fragment that would have crashed on import once correctly named,
   so it was emptied as part of the rename.

2. **`77b1f7b` - fix: repair corrupted profile.json.** `profiles/profile.json`
   was wrapped in a Markdown code fence (` ```json ... ``` `), making it
   invalid JSON. `ProfileLoader.load()` calls `json.load()` with no
   recovery, and `app/web/routes.py` silently caught the resulting
   exception and fell back to an **empty** profile. This was the root
   cause of most "ranking looks off" symptoms in the prior handoff -
   every job was being matched against 0 skills/titles/locations. Fixed
   the file; added `tests/test_profile_integrity.py` as a direct
   regression test.

3. **`2c6e924` - fix: correct Duunitori job titles and restrict scrapers
   to their own domain.** Live-tested each source and found Duunitori's
   JSON-LD `JobPosting.title` field holds an internal occupation-taxonomy
   slug (e.g. `"tietoturva-asiantuntija"`), not the real posted title
   (confirmed against a live page: the real title, "Staff Security
   Engineer", was only in the page's `<h1>`). This was silently zeroing
   `title_score` for most Duunitori postings. Fixed to prefer `<h1>`.
   Also added a same-domain check (`is_same_site`) before following any
   scraped link, across all four sources, since `urljoin()` leaves an
   absolute off-domain `href` untouched otherwise. Tests:
   `tests/test_duunitori_source.py`, `tests/test_source_domain_guard.py`.

4. **`2c5ff37` - security: disable Flask debug mode unless explicitly
   enabled.** `webapp.py` had `app.run(debug=True)` hardcoded. Now
   defaults off, opt-in via `FLASK_DEBUG=1`.

5. **`f8bc7ba` - chore: ignore stray database, generated documents, and
   local scratch dirs.** Untracked a stale root-level `careerpilot.db`
   (superseded by the actively-used, already-gitignored
   `data/careerpilot.db` - confirmed via code, not assumed), a tracked
   generated resume file, and added `.pytest_cache/`, `.pytest-tmp/`,
   `.pytest_tmp/`, and `.careerpilot-v2-backup-*/` to `.gitignore`.
   Deleted the (untracked) backup directories and the now-obsolete
   `apply.ps1` bulk-patch script.

6. **`b29ccd1` - fix: repair dashboard job actions and bound AI generation
   requests.** Live-tested the dashboard with `CAREERPILOT_SEARCH_V2=1`
   via a Flask test client and found the Generate Resume / Cover Letter /
   Save Job links were **all broken**: `CanonicalJob` has no `id` field,
   and `manager.latest_jobs` (which `/generate`, `/coverletter`, and
   `/save` all resolve ids through) was never populated when V2 search
   succeeded. Fixed by assigning sequential local ids to V2 results and
   registering them on `manager.latest_jobs`, same convention V1 already
   used. Separately found that `AIEngine.ask()` (the actual code path
   behind the resume/cover-letter buttons) called `ollama.chat()` with no
   timeout - reproduced live, it hung a request indefinitely when the
   local model was slow. Rewrote it to use the same bounded
   daemon-thread watchdog already used by `app.ai.llm.LocalLLM`
   elsewhere in the codebase (default 30s, `OLLAMA_TIMEOUT`-configurable),
   and made `/generate`/`/coverletter` return a `503` with a clear
   message instead of hanging or crashing. Verified live: the fixed
   route returned in exactly the configured timeout (5.0s when
   `OLLAMA_TIMEOUT=5`) instead of hanging for minutes. Test:
   `tests/test_routes_v2_job_ids.py`.

7. **`6aa0ed2` - docs: add architecture, matching, security, testing, AI,
   and portfolio docs.** See "Documentation" below.

### Verified live (not just unit-tested)

- A real V2 search against the real profile, post-fixes, produces a
  sensible top-20: relevant, correctly-titled security/cloud roles,
  properly ordered. 45 unique jobs collected (35 Duunitori, 17 Jobly, 0
  Tyomarkkinatori, 0 Work in Finland - both zero-result sources
  root-caused, not just observed; see `docs/DATA_SOURCES.md`).
- Dashboard loads (200), job-action links now resolve to real ids.
- `/save/<id>` -> `/applications` shows the saved job with status
  "Saved" - full save-job round trip verified.
- `/generate/<id>` verified in both directions: succeeded (200) with the
  old unbounded code (took several minutes - local Ollama in this sandbox
  is genuinely very slow, not broken), and now fails fast and gracefully
  (503 in ~5s) with the bounded-timeout fix, tested with
  `OLLAMA_TIMEOUT=5`.
- Re-investigated the prior handoff's TLS claim for Tyomarkkinatori from
  scratch: not reproducible through this project's actual `requests` +
  `certifi` code path. The real cause of both zero-result sources is
  client-side-JavaScript-rendered job listings, confirmed by inspecting
  the actual fetched HTML/JSON for each site.

### Documentation (committed in `6aa0ed2`)

Done: `README.md` (full rewrite), `docs/ARCHITECTURE.md`,
`docs/MATCHING_AND_RANKING.md`, `docs/DATA_SOURCES.md`,
`docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT.md`,
`docs/AI.md`, `docs/PRODUCT_VISION.md`, `docs/PORTFOLIO.md`.

**Not done** (see "Exact next task" below):
- `docs/TECHNOLOGY_STACK.md` - not started.
- `PROJECT_STATE.md`, `NEXT_TASKS.md`, `CHANGELOG.md` - still contain
  their **pre-session** content, which is now stale/inaccurate (they
  still say "24 passed", describe the TLS-failure theory for
  Tyomarkkinatori as fact, and don't mention any of the fixes above).
  Do not treat their current content as accurate. `README.md` and the
  `docs/` set are accurate as of this handoff; these three are not yet
  updated to match.

## Test result

**39 passed**, 0 failed, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```
(24 baseline + 15 new regression tests added this session, one per bug
fixed, each with a docstring explaining the exact failure it prevents.)

## Files changed this session

See commits `ec741ac` through `6aa0ed2` on `v2-development` for the
complete, exact diff (`git log --stat ec741ac^..6aa0ed2`). Summary of
what's touched: `app/search/v2/*`, `app/search/sources/web_sources.py`,
`app/web/routes.py`, `app/ai/ai_engine.py`, `app/ai/resume_builder.py`,
`app/ai/cover_letter_builder.py`, `webapp.py`, `profiles/profile.json`,
`.gitignore`, `app/database/__init__.py` and `app/search/sources/__init__.py`
and `tests/utils/__init__.py` (renamed from `_init_.py`), 8 new test
files, `README.md`, and 9 new `docs/*.md` files.

## Current git status

Working tree is clean except for four pre-existing stub files that
predate this session and were **not** updated:
```
?? CHANGELOG.md
?? NEXT_TASKS.md
?? PROJECT_STATE.md
```
(`HANDOFF.md` itself, this file, is about to be committed as the final
act of this session.) All code and documentation changes described
above are committed and pushed to `origin/v2-development`. Nothing is
uncommitted or at risk of being lost.

## Known, honestly-documented limitations (not bugs to "fix" blindly)

- The dashboard displays scores from the legacy `app.ai.matcher.JobMatcher`,
  not V2's own matcher - a real, current architectural state, not an
  oversight. See `docs/ARCHITECTURE.md`'s "The V1/V2 split" section
  before changing this; it requires a real design decision (documented
  there), not a quick swap.
- Tyomarkkinatori and Work in Finland return 0 results because their job
  listings are client-side-JavaScript-rendered; fixing this needs either
  their internal API (undiscovered) or a headless-browser dependency
  (not currently installed). Do not "fix" this with `verify=False` or
  similar - it was never a TLS issue.
- `CVParser`/`ProfileExtractor`/`WebActions` are fully implemented but not
  wired to any Flask route - real, working code, just not exposed yet.

## Exact next task

Resume with, in order:

1. **`docs/TECHNOLOGY_STACK.md`** - the one doc file from the original
   scope not yet written. Table of technology / purpose / runtime vs.
   dev / where used. All the source material for this is already
   gathered in this session's investigation (requirements.txt,
   requirements-dev.txt, pyproject.toml, and every module read - see
   `docs/AI.md`, `docs/ARCHITECTURE.md` for what's actually used).
2. **Refresh `PROJECT_STATE.md`, `NEXT_TASKS.md`, `CHANGELOG.md`** to
   match reality: current test count (39), the V1/V2 dashboard split,
   the real root cause for both zero-result sources, and the fixes list
   above. Do not carry forward their current stale claims (24 tests,
   TLS-failure theory) without correcting them first.
3. Then continue down the original task list: final `py_compile` pass
   repo-wide, a final honest documentation audit (section 44 of the
   original instructions - verify every doc file still matches the code
   as of whatever's changed since), and the final summary report.

## Handoff protocol

The next session should read `README.md` and everything in `docs/`
first (accurate as of this handoff) - not `PROJECT_STATE.md`/
`NEXT_TASKS.md`/`CHANGELOG.md`, which are stale until step 2 above is
done. The repository and its git history are the source of truth over
any prior AI conversation, this file included where they disagree.
