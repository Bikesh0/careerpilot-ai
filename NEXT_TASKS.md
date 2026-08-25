# CareerPilot AI - Next Tasks

Status as of 2026-08-25, after a career-family/career-intelligence
session (see `HANDOFF.md` for the detailed log). Priorities 1-7 below
are unchanged carryover from the 2026-08-19 audit-and-fix session.
Completed items from the prior version of this file are removed rather
than left checked - see git history for what they were.

## Priority 0 - career-family/career-intelligence session: COMPLETE, all six commits landed locally

A 2026-08-24/25 session built job-dedup improvements, Finland/Europe
geographic filtering, a UI-copy rename + Applications empty-state fix,
a substantially expanded skill-gap engine, and a new career-intelligence
layer (career families/tracks, an evidence-tier Living Career Profile,
application readiness, ATS/HR/technical-manager hiring perspective on
`/analyze/<job_id>`). Everything is implemented, tested (219 passed, see
"Known environment quirk" below), and all six commits are now landed
locally on `v2-development`, in order:

- `3072417` - Milestone 1: one-sentence career-family connector on a
  skill-gap recommendation, `/analyze/<job_id>`.
- `fcf1681` - Commit 1: application tracker column-order bug
  (`SELECT *` -> named columns, schema-drift protection), Ashby API
  field name fix (`description` -> `descriptionPlain`), V2's
  canonical-URL dedup signal (`app/search/v2/dedupe.py`/`job.py`).
- `acc946d` - Commit 2: Finland/Europe/Outside-Europe geographic scope
  filtering (`app/ai/geo_normalizer.py`), wired into both V1
  (`app/search/manager.py`) and V2 (`app/web/routes.py::_search_jobs`).
- `314e879` - Commit 3: "Skill Gap" -> "Career Fit & Growth" rename,
  and the Applications page empty-state fix.
- `464f402` - Commit 4: skill-gap engine expansion -
  `app/ai/skill_gap.py`'s catalog growth (incl. Finnish aliases),
  section-aware nice-to-have detection, the additive per-skill
  `evidence` field, project-continuity awareness, plus the new
  `app/ai/capability_graph.py`.
- `ad47892` - Commit 5: the career-intelligence layer -
  `app/ai/career_profile.py` (evidence-tier profile),
  `app/ai/career_tracks.py` (track ranking + job-family
  classification), `app/ai/application_readiness.py`,
  `app/ai/hiring_perspective.py` (ATS/HR/technical-manager view),
  wired into `/cv-strength`, the dashboard, and `/analyze/<job_id>`.
  See `docs/CAREER_INTELLIGENCE.md`.

**Do not reopen Milestone 1 or Commits 1-5** unless a future regression
actually requires it. Only remaining operational step: `git push origin
v2-development`, then confirm local `HEAD` matches
`origin/v2-development`.

## Known environment quirk - Windows pytest temp-directory permission

Bare `python -m pytest -q` currently errors on ~51 tests with
`PermissionError: [WinError 5] Access is denied:
'...\AppData\Local\Temp\pytest-of-terry'` - a pre-existing Windows
temp-directory permission issue, unrelated to any code in this repo and
not a regression. Use a writable `--basetemp` for the real result:
`python -m pytest -q --basetemp=<writable dir>`. Current real result:
**219 passed, 0 failed**.

## Priority 1 - Source coverage: Duunitori (disabled), Tyomarkkinatori, Work in Finland

Investigated this session with real browser network inspection
(`claude-in-chrome`), not just static-HTML guessing - see
`docs/DATA_SOURCES.md` for full detail. All three are now blocked on a
human/policy decision, not a technical unknown.

- [ ] **Duunitori** (highest impact - this was the largest source of
      collected jobs): implemented, tested, and was working, but stays
      **disabled** because `duunitori.fi/robots.txt` disallows this
      scraper's generic User-Agent (`Disallow: /` for the `*` group,
      with named exceptions only for specific bots like Googlebot). This
      was found *after* the scraper had already shipped and been
      re-verified multiple times earlier in the same session - not
      caught proactively. Disabled at the user's explicit direction, and
      confirmed again in a follow-up instruction to keep it disabled.
      **No circumvention path is in scope**: not spoofing a different
      crawler's identity, not switching User-Agent while still not
      being an allowlisted crawler, not scraping the disallowed paths
      anyway. The only two paths to re-enabling it: (1) obtain
      Duunitori's explicit permission (contact them directly about their
      crawling policy, ideally reflected in an updated `robots.txt` or a
      written agreement), or (2) use an official/approved API if
      Duunitori offers one for aggregators - a distinct integration with
      its own credentials and terms, not this scraper. Only once one of
      those is actually in place: re-add `DuunitoriSource` to both
      `app/search/v2/registry.py`'s `SOURCE_REGISTRY` and
      `app/search/manager.py`'s `SearchManager.searchers`, and re-verify
      live.
- [ ] **Tyomarkkinatori**: its internal JSON search API was found,
      confirmed working, and a full `TyomarkkinatoriSource`
      implementation against it was built and verified live (4 real,
      correctly-matched jobs from companies not covered by
      Duunitori/Jobly) - then **reverted, not shipped**, because
      `tyomarkkinatori.fi/robots.txt` explicitly disallows `/api/`. This
      needs a human decision: either get explicit permission/an official
      API agreement from Tyomarkkinatori, or accept this source stays at
      0 results. Do not re-implement against `/api/` without that
      permission - the code approach itself already works, this is purely
      a policy/permission question now.
- [ ] **Work in Finland**: likely not worth separate investment - its
      "Open jobs" widget's assets load directly from `jobly.fi`, strongly
      suggesting its listings are already covered by the existing
      `JoblySource`. Worth a rigorous side-by-side comparison before
      fully closing this out, but do not prioritize building a scraper
      for it without first confirming meaningful non-overlap with Jobly.
- [ ] Playwright/headless-browser automation remains untaken for all
      three - not because it's technically hard, but because it
      wouldn't change the `robots.txt` situation for Duunitori or
      Tyomarkkinatori (a headless browser hitting the same disallowed
      path/user-agent group is still disallowed automated access) and is
      unlikely to add value for Work in Finland given the Jobly-overlap
      finding above.
- [ ] **Process note for whoever picks this up**: check `robots.txt`
      for every source - new *and already-shipped* - against the exact
      path and exact user-agent group the scraper's real request will
      match, before trusting a source as compliant. This wasn't done
      proactively for Duunitori/Jobly when they were first built; it
      should be standard practice from here on, including re-checking
      periodically since `robots.txt` can change.

## Priority 2 - Merge reviewed CV data into the profile

The CV-upload path itself is done (`/settings/upload-cv` - see
`docs/PRODUCT_VISION.md`, `docs/SECURITY.md`). It deliberately stops at
review - nothing writes to `profiles/profile.json` yet.

- [ ] Design and build an "accept these fields" step (per-field or
      per-section, not a single blind merge, so a bad or
      AI-hallucinated extraction can't silently corrupt the profile
      everything else depends on).

## Priority 2b - Fix the resume/cover-letter output directory mismatch

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

## Priority 3 - Source-level diagnostics

- [ ] `SourceRunner` already isolates and logs per-source success/failure,
      but there's no dashboard-visible or persisted status report beyond
      log lines. Only worth building if source reliability becomes a
      recurring debugging pain point - see `docs/DATA_SOURCES.md`.

## Priority 4 - Skill-gap catalog maintenance (low urgency)

The skill-gap/recommendation feature (`app/ai/skill_gap.py`,
`/analyze/<job_id>`) is implemented and tested - see
`docs/MATCHING_AND_RANKING.md`'s "Skill-gap analysis" section. Two
follow-ups, neither urgent:

- [ ] `SKILL_CATALOG` covers ~30 skills relevant to this profile's
      domain. A job requirement using a skill name outside that list is
      currently invisible to this feature. Worth expanding if a real
      posting is found asking for something not covered, not worth
      pre-emptively guessing at.
- [ ] The catalog's certifications/courses are hand-checked as of
      2026-08-19, not live-verified against any API (deliberately - see
      docs/AI.md). Worth a periodic manual review so a renamed/retired
      certification doesn't go stale unnoticed. If this is ever extended
      with an LLM-generated personalized narrative, it must be clearly
      labeled as AI-generated and kept separate from the curated
      catalog - see docs/AI.md's "Skill-gap recommendations make zero
      LLM calls, by design".

## Priority 5 - Multi-visitor session isolation (needed before any public/untrusted demo)

Scoped and deliberately **not built** this session (2026-08-19) - see
`docs/PRODUCT_VISION.md`'s "Multi-visitor demo mode" and
`docs/SECURITY.md`'s "Exposing this app to testers via a tunnel". What's
already safe today: the master profile can't be overwritten by a
visitor's CV upload (verified with a direct test), and uploads
themselves are isolated/rate-limited/auto-cleaned. What's genuinely
missing:

- [ ] Session-scoped profile threading through every route in
      `app/web/routes.py` (`_load_profile()`, matching, skill-gap, CV
      strength, resume/cover-letter generation) so a visitor's own
      uploaded CV drives their own dashboard/search/skill-gap results,
      instead of everyone seeing the one master profile's results.
- [ ] CSRF protection on every state-mutating route (`/save/<id>`,
      `/status/<id>/<status>`, `/delete/<id>`) - required before this app
      is exposed to anyone beyond a small group of trusted testers who
      understand the current limitation.
- [ ] A concurrent-session test (two simultaneous visitors, each with
      their own uploaded CV, asserting neither sees the other's data and
      the master profile is untouched) - not meaningful to write until
      the session-scoping above actually exists.

This is a genuinely large, cross-cutting change - do not attempt a
partial version (e.g. session-scoping only some routes) without a clear
plan, since a half-isolated system is worse than a clearly-documented
single-profile one.

## Priority 6 - Deterministic CV tailoring (reorder, not regenerate)

The product spec describes tailoring as reordering/re-emphasizing a
~90%-stable master CV per job, not a full rewrite. `app/ai/resume_builder.py`
currently sends the whole profile to the LLM and asks it to rewrite
`summary`/`skills`/`experience` from scratch (grounded by prompt, but
still a full regeneration). Deliberately not rearchitected this session
- see `docs/PRODUCT_VISION.md`'s "CV tailoring" section for why. If
picked up: the safer path is likely a deterministic pass (reorder skills
by relevance to the target job's matched skills, reorder/select
experience bullets) with the LLM used only for light rewording, not
structural decisions - not a full replacement of the current approach
without first proving the deterministic version doesn't regress
resume quality.

## Priority 7 - Persistent, progressive skill-proficiency tracking (DONE for Verified projects; partial credit still open)

**Closed this session, for the main case**: `app/database/project_tracker.py`
+ `app/services/project_service.py` give exactly the "mark this project
complete to advance a skill" workflow this priority asked for - starting
a project from a skill-gap recommendation, tracking it through
`Planned -> In Progress -> Completed -> Verified`, and a `Verified`
project now upgrades that skill to `Advanced` on the CV-strength page
(`app/ai/cv_strength.py`'s `verified_skill_keys` parameter), even for a
skill not yet in the profile's declared list at all.

Still open, genuinely lower priority now that the main gap is closed:

- [ ] No partial credit for `In Progress` work - proficiency only moves
      once a project reaches `Verified`, all-or-nothing. A "started but
      not finished" state contributing something intermediate wasn't
      attempted - not clearly valuable enough to justify the added
      complexity yet.
- [ ] No fading-back-down: if a `Verified` project were later deleted or
      its status reverted, proficiency is recomputed fresh on the next
      page load anyway (not cached), so this is more a documentation
      note than an actual gap - worth confirming with a test if this
      area is revisited.

## Explicitly not planned right now

- A hosted LLM provider (OpenAI/Anthropic/etc.) - local Ollama only, by
  design; see `docs/AI.md`.
- CI/CD - no automated pipeline is configured; not adding one without a
  specific reason to.
- Gamification (streaks, badges, daily-pressure mechanics), bulk
  auto-apply, a native mobile app - explicitly out of scope per the
  product spec's "do not overbuild" section.
- Application readiness on `/cv-strength` - closed, not applicable by
  design: `/cv-strength` is the job-independent Layer 1 page, while
  application readiness (`app/ai/application_readiness.py`) is
  inherently job-specific (a match-score-driven "should I apply to this
  one" verdict). A synthetic average across postings would not be
  grounded in any single real job and would conflict with the project's
  no-fabrication principle. Resolved decision, not an open design
  question - do not revisit without a real reason.
