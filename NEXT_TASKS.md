# CareerPilot AI - Next Tasks

Status as of 2026-08-18, after a full audit-and-fix session. See
`HANDOFF.md` for the detailed session log and `PROJECT_STATE.md` for
current state. Completed items from the prior version of this file are
removed rather than left checked - see git history for what they were.

## Priority 1 - Unify V1/V2 ranking on the dashboard

- [ ] Decide between: (a) render V2's `RankedJob.to_dict()` output
      directly on the dashboard, or (b) port V1 `JobMatcher`'s
      Finnish-language title terms, exclusion list, and
      experience-requirement penalties into V2's matcher, then retire V1.
      Both options and their tradeoffs are documented in
      `docs/ARCHITECTURE.md`'s "The V1/V2 split" section - read that
      first, this is a real design decision, not a quick swap.
- [ ] Whichever direction is chosen, add regression tests covering the
      specific V1-only behaviors (Finnish title terms, exclusion list,
      seniority penalties) if they need to be preserved.

## Priority 2 - Real data from the two zero-result sources

- [ ] Tyomarkkinatori and Work in Finland both return 0 jobs because
      their listings are loaded by client-side JavaScript, not present
      in the static HTML fetched today - root-caused in
      `docs/DATA_SOURCES.md`, not a TLS issue (that was disproved this
      session; do not revisit `verify=False` as a fix).
- [ ] Investigate whether either site exposes an internal JSON API that
      could be called directly (would need real browser devtools network
      inspection to discover, not guessable from static HTML).
- [ ] If no API is found, evaluate adding Playwright as a scoped,
      justified new dependency (not currently installed -
      `app/automation/playwright_bot.py` is an empty placeholder).
      Weigh this against the added complexity/dependency surface before
      committing to it.

## Priority 3 - Merge reviewed CV data into the profile

The CV-upload path itself is done (`/settings/upload-cv` - see
`docs/PRODUCT_VISION.md`, `docs/SECURITY.md`). It deliberately stops at
review - nothing writes to `profiles/profile.json` yet.

- [ ] Design and build an "accept these fields" step (per-field or
      per-section, not a single blind merge, so a bad or
      AI-hallucinated extraction can't silently corrupt the profile
      everything else depends on).

## Priority 3b - Fix the resume/cover-letter output directory mismatch

- [ ] `app/web/actions.py`'s `WebActions.latest_resume()`/
      `latest_cover_letter()` glob `resumes/`/`cover_letters/`, but
      `app/ai/resume_generator.py`/`cover_letter_generator.py` actually
      save generated documents to `output/`. `WebActions` would never
      find anything even if wired up to a route. Found while fixing the
      broken sidebar navigation links (2026-08-18); not fixed at the
      time since it's a separate, unrelated gap. Either point
      `WebActions` at `output/` or make the generators write to
      `resumes/`/`cover_letters/` - whichever matches the intended
      final layout - then it becomes a genuine candidate for the bare
      `/resume`/`/coverletter` routes to show the most recently
      generated document instead of just redirecting to the dashboard.

## Priority 4 - Skill-gap / quick-improvement feature

- [ ] Not implemented. V2's `MatchResult.missing_skills` already computes
      the data needed; V1's `match_details` currently exposes only a
      count/ratio, not the list - see `docs/PRODUCT_VISION.md`.
- [ ] When built: keep suggestions realistic (a day to about a week - a
      short course, a small lab, a focused GitHub project), and never
      fabricate a completed certification.

## Priority 5 - Source-level diagnostics

- [ ] `SourceRunner` already isolates and logs per-source success/failure,
      but there's no dashboard-visible or persisted status report beyond
      log lines. Only worth building if source reliability becomes a
      recurring debugging pain point - see `docs/DATA_SOURCES.md`.

## Priority 6 - Consolidate the two Ollama wrapper classes

- [ ] `app/ai/llm.py` (`LocalLLM`) and `app/ai/ai_engine.py` (`AIEngine`)
      are two separate implementations of the same
      "call-a-local-model-without-hanging" pattern. `AIEngine` was
      hardened this session to match `LocalLLM`'s reliability behavior,
      but the duplication itself remains. Consolidating would need
      `LocalLLM.ask()` to support an optional system-prompt parameter (it
      currently only takes one combined prompt) before every call site
      using `AIEngine` can switch over. Low urgency - both are now
      equally safe, this is a cleanup, not a bug fix.

## Priority 7 - Final verification pass

- [ ] Full repo-wide `py_compile` check (not yet run across every file
      this session, only on files actually changed).
- [ ] Final documentation audit: re-read every file listed in
      `PROJECT_STATE.md`'s Documentation section against the code as it
      exists at that point, since further changes may have landed since
      this file was written.
- [ ] Confirm `git status` is clean and everything is pushed before
      declaring the project "complete" for a portfolio review.

## Explicitly not planned right now

- Multi-user support / authentication - this is a single-user local
  tool by design.
- A hosted LLM provider (OpenAI/Anthropic/etc.) - local Ollama only, by
  design; see `docs/AI.md`.
- CI/CD - no automated pipeline is configured; not adding one without a
  specific reason to.
