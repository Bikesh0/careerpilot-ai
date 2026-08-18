# CareerPilot AI - Next Tasks

Status as of 2026-08-18, after a full audit-and-fix session. See
`HANDOFF.md` for the detailed session log and `PROJECT_STATE.md` for
current state. Completed items from the prior version of this file are
removed rather than left checked - see git history for what they were.

## Priority 1 - Port V1-only matching logic into V2's matcher

The dashboard now shows V2's own score/matched-skills/reasons whenever
V2 search succeeds, instead of always re-scoring through the legacy
matcher - done 2026-08-18 (`app/web/routes.py._present_v2_ranked_jobs()`,
see `docs/ARCHITECTURE.md`'s "The V1/V2 split"). This closed the
ranking-ownership gap but opened a real, visible one: V2's matcher still
lacks V1's Finnish-language title terms, exclusion list, and
experience-requirement penalties, so a Finnish-titled posting (or an
obviously-unrelated one V1 would have excluded) now scores differently
depending on whether V2 succeeded or fell back to V1 for that request.

- [ ] Port `app/ai/matcher.py`'s `SENIORITY_TERMS`-adjacent Finnish
      title terms, `EXCLUDED_TITLE_TERMS`, and the required-experience
      regex/penalty into `app/search/v2/matching/matcher.py`, so V2's
      own scoring doesn't regress relative to V1's when V2 is the
      source. See `docs/MATCHING_AND_RANKING.md`'s "Known edge cases and
      limitations" for the exact gap.
- [ ] Add regression tests in `tests/test_v2_matching_regressions.py`
      covering the ported behaviors (a Finnish-titled job scoring
      correctly, an excluded-title job being filtered/penalized,
      experience-requirement penalty applied) directly against V2's
      matcher.

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

Not implemented. Scoped this session (2026-08-18), and it's a bigger,
different feature than it first looks like - read this before building
it:

- [ ] **Semantic gap, not just a missing UI**: both matchers'
      `missing_skills` mean "profile skills not mentioned in *this job's*
      text" - i.e. skills you have that this posting doesn't happen to
      repeat. That's the *inverse* of what "skill gap" naturally means
      here: skills *the job wants that you don't have*. Genuinely
      unpossessed skills (e.g. a posting asking for Terraform, which
      isn't in the profile at all) never appear in `missing_skills` today
      - they're invisible to the current matcher entirely.
- [ ] Building the real feature needs requirement extraction *from the
      job posting text* - either a curated skill taxonomy to scan job
      descriptions against (deterministic, more maintenance, no
      hallucination risk) or an LLM call per job (flexible, but adds
      per-job AI latency/cost and hallucination risk that needs
      guarding against, consistent with `docs/AI.md`'s "deterministic
      for matching" principle - lean toward the taxonomy approach unless
      there's a strong reason not to).
- [ ] Only after that: map an actually-missing skill to a suggestion.
      Keep suggestions realistic (a day to about a week - a short
      course, a small lab, a focused GitHub project) and never fabricate
      a completed certification. A small curated dict (skill ->
      suggestion), similar in spirit to `SKILL_WEIGHTS`/the alias table
      already in `app/ai/matcher.py`, is safer than asking an LLM to
      invent a learning plan.

## Priority 5 - Source-level diagnostics

- [ ] `SourceRunner` already isolates and logs per-source success/failure,
      but there's no dashboard-visible or persisted status report beyond
      log lines. Only worth building if source reliability becomes a
      recurring debugging pain point - see `docs/DATA_SOURCES.md`.

## Priority 6 - Final verification pass

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
