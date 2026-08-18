# CareerPilot AI - Session Handoff

## Last Updated

2026-08-18

## Current branch

`v2-development`, fully pushed to `origin`
(`https://github.com/Bikesh0/careerpilot-ai.git`). Working tree clean.

## Current state

The full project-completion pass is done, plus five follow-up fixes made
while continuing autonomously down `NEXT_TASKS.md`: a user-reported
saved-jobs bug, a self-discovered navigation bug, the CV upload feature,
unifying V1/V2 ranking on the dashboard, and - most recently -
consolidating the two Ollama wrapper classes.

## Most recent: Ollama wrapper consolidation

`app/ai/llm.py`'s `LocalLLM` and `app/ai/ai_engine.py`'s `AIEngine` were
two independent implementations of the same fail-soft local-model
pattern. Gave `LocalLLM.ask()` an optional `system` parameter (backward
compatible), migrated all three `AIEngine` call sites
(`ResumeBuilder`, `CoverLetterBuilder`, `ProfileExtractor`) onto
`LocalLLM`, and removed `ai_engine.py` entirely (confirmed unused
elsewhere first). Side effect, verified live: `AIEngine` had a hardcoded
`model="llama3.1"` with no auto-detection; `LocalLLM` auto-detects the
actually-installed model, so this is a small real improvement, not just
a refactor. All three call sites still degrade gracefully within the
configured `OLLAMA_TIMEOUT`, verified live. No test changes needed (the
suite mocks at the builder-method level). Full suite: 54 passed
(unchanged - this was a pure internal consolidation).

## Everything completed this session, most recent first

1. **Ollama wrapper consolidation** (above).
2. **V1/V2 ranking unification** - the dashboard now shows V2's own
   score/matched-skills/reasons whenever V2 search succeeds (verified
   live against the real profile: top result "Staff Security Engineer"
   at 74% with V2's exact reason strings), instead of always re-scoring
   through the legacy matcher. Legacy mode is untouched when V2 is
   disabled or fails. See `docs/ARCHITECTURE.md`'s "The V1/V2 split."
   Known, now-visible tradeoff logged as `NEXT_TASKS.md` Priority 1:
   V2's matcher still lacks V1's Finnish-language title terms, exclusion
   list, and experience-requirement penalties.
3. **CV upload** - `/settings` + `/settings/upload-cv`, safe file
   handling (UUID filenames, path-traversal-proof, verified), 10MB cap,
   review-only (never auto-writes to `profiles/profile.json`).
4. **Broken sidebar navigation** - 4 of 8 links 404'd; fixed, two
   dead/duplicate templates removed.
5. **Saved jobs not saving correctly** (user-reported) - no duplicate
   detection on the actual save path, and `job_url` silently dropped.
   Both fixed.

## Verification

Test result: **54 passed**, run via:
```powershell
$env:TEMP = "$PWD\.pytest-tmp"; $env:TMP = "$PWD\.pytest-tmp"
.\.venv\Scripts\python.exe -m pytest -q
```

Repo-wide `python -m compileall app tests *.py`: clean.

## Documentation updated this round

`docs/AI.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`,
`docs/TECHNOLOGY_STACK.md` (all `AIEngine` references reframed as
historical - it no longer exists - plus a stale `CVParser`-not-wired-up
claim in `TECHNOLOGY_STACK.md` found and fixed, missed in an earlier
pass), `NEXT_TASKS.md` (Priority 6 removed), `CHANGELOG.md`, this file.

## Known, honestly-documented limitations (carried forward)

- V2's matcher lacks V1's Finnish-language title terms, exclusion list,
  and experience-requirement penalties - a live, visible difference in
  dashboard results depending on whether V2 succeeded (`NEXT_TASKS.md`
  Priority 1).
- Tyomarkkinatori and Work in Finland return 0 results (client-side
  JavaScript rendering, not TLS - see `docs/DATA_SOURCES.md`).
- CV upload stops at review; nothing merges extracted data into
  `profiles/profile.json` yet (`NEXT_TASKS.md` Priority 3).
- `WebActions.latest_resume()`/`latest_cover_letter()` point at the wrong
  directory relative to where documents are actually generated
  (`NEXT_TASKS.md` Priority 3b).
- `ApplicationTracker`'s database path is resolved relative to the
  current working directory, not the project root.

## Exact next task

Continuing per the user's explicit instruction to proceed through the
remaining release priorities without stopping: real data from the two
JS-rendered job sources (`NEXT_TASKS.md` Priority 2 - needs either
browser-based network inspection to find an internal API, not yet
attempted, or a scoped decision to add Playwright), then final security
review, final integration testing, documentation review, and release
audit, per the user's explicit list. Priority 1 (porting V1 logic into
V2's matcher) and Priority 3/3b/4/5 remain queued in `NEXT_TASKS.md` in
priority order for whichever comes next after those.

## Handoff protocol

Read `README.md` and everything in `docs/` first - both are accurate as
of this update. The repository and its git history remain the source of
truth over any prior AI conversation, this file included where they
disagree.
