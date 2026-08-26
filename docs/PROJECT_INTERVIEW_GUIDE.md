# CareerPilot AI — Interview Guide

## Purpose and how to use this

This document exists so you (Bikesh) can explain CareerPilot AI
confidently and *accurately* in interviews — cybersecurity, software
engineering, cloud/DevOps, and AI-adjacent roles. It is not a script to
read aloud. It is a map of what the code actually does, why it was built
that way, and where the honest edges are, so you can explain it in your
own words and survive a follow-up question that goes one level deeper
than the first answer.

**Source-of-truth rule applied throughout**: every claim below was
checked against the actual code in this repository as of
`git log -1` → `ad47892` / `c2e95fa` on `v2-development`, not against
older documentation. Where the existing docs (`README.md`,
`docs/CAREER_INTELLIGENCE.md`, `docs/TESTING.md`, etc.) say something
the code doesn't currently back up, that's called out explicitly in
**"Where the docs and the code disagree"** below — don't repeat the
stale number in an interview without knowing it's stale.

Each section ends with **"Questions you should be ready for"** — these
are not answered for you. Practice answering them out loud, in your own
words, using the file/line pointers given. If you can't yet, that's the
signal to go re-read that one file, not to memorize a paragraph from
here.

---

## The 60-second pitch

CareerPilot AI is a Flask-based job-search and career-advisory tool I
built for my own cybersecurity/IT job search in Finland. It scrapes real
job boards, deduplicates and normalizes postings, scores them against my
actual profile with a transparent weighted formula (not a black box),
and then goes further than a typical job board: it tells me specifically
what skills I'm missing for a given posting, recommends real
certifications/courses/projects to close that gap, tracks projects I
actually build in response, and only unlocks AI-generated interview prep
once I've genuinely reached the interview stage for that job. Two
matching engines exist side by side — an older, heavily hand-tuned one
and a newer, cleaner one — and the dashboard picks whichever one actually
produced the job list, rather than me having to choose. Everything that
makes a factual claim (a certification exists, a skill is missing) is
deterministic Python, not an LLM; the LLM is only used for genuinely
open-ended generation (résumés, cover letters, interview questions,
project coaching), always grounded in my real profile data and gated
behind explicit conditions.

**If asked "what's the most interesting engineering decision in this
project"**, the strongest, most verifiable answer is the
`robots.txt` compliance story (see the Security section) — it's a real
finding, a real tradeoff, and a real decision I made under a concrete
cost (losing my largest job source), not a hypothetical.

---

## 30-Second Interview Answer

Use this when someone says "tell me briefly about a project you've
worked on" and you have about 30 seconds before they either dig deeper
or move on. This is deliberately a *different, shorter* answer than the
60-second pitch above — not that pitch mechanically trimmed — built
around the fewest facts that still land: what it is, the problem, the
approach, your contribution, one result.

> "CareerPilot AI is a job-search and career-advisory tool I built for
> my own cybersecurity job search in Finland. The core problem was that
> job boards don't tell you *why* a posting is a good fit, or what's
> actually missing from your profile. My approach was a Flask app that
> scrapes multiple job boards, deduplicates and scores postings against
> my real skills with a transparent, weighted formula — no black box —
> and then goes further, recommending real certifications and projects
> to close specific skill gaps. I designed and built the whole thing
> myself, and it's backed by 219 automated tests. It's the actual tool
> I use for my own job search today."

---

## 2-Minute Interview Answer

This expands naturally from the 30-second answer once someone says "go
on" or asks a follow-up like "how does it actually work." It's meant to
sound like spoken interview English — contractions, natural pacing — not
like reading documentation aloud.

> "The problem was genuinely my own: Finnish job boards are fragmented,
> none of them explain why a posting fits a specific candidate, and
> manually checking several sites while trying to figure out what
> skills you're missing is easy to fall behind on.
>
> I started with a first pipeline — I call it V1 — with a heavily
> hand-tuned matcher: tiered title categories, weighted skills, steep
> seniority penalties. It worked, but it was hard to extend cleanly, so
> I built a second, cleaner pipeline, V2. A `SourceRunner` runs each job
> source in isolation — mainly Jobly right now, since I ended up
> disabling my largest source, Duunitori, for a robots.txt compliance
> reason I'm happy to go into. Every source's raw output gets converted
> into one shared `CanonicalJob` dataclass, so normalization,
> deduplication, and scoring don't need to care which source a job came
> from. Deduplication checks two independent signals — a normalized
> title-company-location key, or a canonical URL with tracking
> parameters stripped — because either signal alone under-catches real
> duplicates. A geographic filter runs next — Finland first, Europe
> second, outside Europe excluded by default, but never excluding a
> location it can't confidently classify — and then a weighted
> `JobRanker` scores title match, skill overlap, location match, and
> seniority fit.
>
> Rather than deleting V1 once V2 worked, I kept both — the dashboard
> uses whichever matcher actually produced the job list for a given
> request, so V1's more elaborate, hand-tuned scoring stays available as
> a genuine fallback instead of me throwing away working logic just to
> make the architecture look tidier than it needed to be.
>
> More recently I built a career-intelligence layer on top of that: a
> six-tier evidence model per skill, from a bare claim up to a Verified,
> actually-built project; career-track ranking against my own profile; a
> five-tier application-readiness verdict; and a three-way
> hiring-perspective view — how an ATS, an HR recruiter, and a technical
> manager would each see the same application, kept deliberately
> separate, never blended into one score.
>
> The engineering challenge I'd actually lead with isn't a code bug —
> it's that I found, mid-project, that my largest job source was
> violating its own robots.txt policy. Disabling it cost real data, and
> that trade-off is the decision I'm proudest of in this project.
>
> Everything's backed by 219 automated tests, none of which touch a
> live network or a live LLM, and the real lesson I took from this
> project is that manual verification needs the exact same isolation
> discipline automated tests already have — I once polluted my own real
> database during manual testing and had to trace it back to prove the
> application code itself wasn't at fault."

---

## Architecture at a glance

```
profiles/profile.json (single source of truth: skills, target titles/
                        locations, experience, education, certs)
        |
        v
app/web/routes.py  (Flask blueprint, single file, ~1300 lines)
        |
        |-- CAREERPILOT_SEARCH_V2 env var enabled? ---------------------+
        |                                                               |
        v (V2 path, the default in practice)                            v (V1 fallback)
create_v2_service(profile)                                    SearchManager.search_jobs()
        |                                                               |
        v                                                               |
V2SearchService.search()                                                |
        |                                                               |
        v                                                               |
SourceRunner  -->  Jobly (only source with live results right now;      |
                    Tyomarkkinatori + Work in Finland return 0;          |
                    Duunitori implemented but deliberately unregistered)|
        |                                                               |
        v                                                               |
normalize_job() -> CanonicalJob                                          |
        |                                                               |
        v                                                               |
deduplicate_jobs()  (dedupe_key() OR canonical_url())                    |
        |                                                               |
        v                                                               |
geo filter (app/ai/geo_normalizer.py — outside-Europe excluded)          |
        |                                                               |
        v                                                               |
JobRanker (V2 title/skill/location/seniority weighted score)             |
        |                                                               |
        v                                                               |
[item.job for item in ranked], with V2's MatchResult stashed on          |
each job as `_v2_match`  <---------------------------------------------- +
        |
        v
_rank_jobs(): if every job carries a stashed _v2_match, present V2's
own score/reasons directly (_present_v2_ranked_jobs). Otherwise (V2
disabled, or V2 itself failed), run the exact same, untouched legacy
JobMatcher.rank_jobs() that predates V2.
        |
        v
templates/dashboard.html
```

**The one sentence that matters most architecturally**: *ownership of
scoring is decided by where the job data actually came from, not by
re-checking the feature flag a second time.* `app/web/routes.py`'s
`_rank_jobs()` (lines ~300–350) checks whether every job in the list
carries a stashed `_v2_match` attribute. If yes, V2 really did produce
this list, and its own score/matched-skills/reasons are reused directly,
in V2's own order — no second scoring pass. If no, the code falls back
to the legacy `JobMatcher`, completely unchanged from before V2 existed.
This is documented in depth in `docs/ARCHITECTURE.md`'s "The V1/V2
split" — read that section once before an interview if a question digs
into "why two matchers."

### Questions you should be ready for

- "Why keep two matchers instead of picking one?" — Answer using
  `docs/ARCHITECTURE.md`'s "Why two matchers exist instead of one": V1's
  tiered title scoring, skill weighting, and steeper seniority penalties
  were never ported into V2 because they're genuine design-philosophy
  differences, not gaps — porting them would mean re-deriving V1's
  hand-tuned weights inside V2 without the evidence trail that produced
  them.
- "Walk me through what happens when I load the dashboard." — Use the
  diagram above, but say it in your own words, and be ready to name the
  actual function (`_search_jobs`, `_rank_jobs`) at each step.
- "What happens if V2 search throws an exception halfway through?" —
  `_search_jobs()` catches it, logs it, and falls back to
  `manager.search_jobs()` (V1). `_rank_jobs()` also independently
  catches a failure in `_present_v2_ranked_jobs()` and falls back to the
  legacy matcher. Two separate fail-soft points, not one.

---

## Domain: Security

This is the strongest section of the project for a cybersecurity
interview — every finding below is a real bug or real policy decision
found and fixed in this codebase, not a textbook example.

### `robots.txt` compliance — the best story in this project

**What happened, concretely**: `DuunitoriSource`
(`app/search/sources/web_sources.py`) was built, shipped, and had
already been the **largest single source of collected jobs**. Only
later in the same session was `duunitori.fi/robots.txt` actually
checked. It disallows the generic `*` user-agent group entirely
(`Disallow: /`), with named exceptions only for specific crawlers
(Googlebot, Bingbot, etc.). This scraper sends a spoofed generic browser
`User-Agent` (`WebSourceBase.HEADERS`), which matches none of those
named exceptions — so it falls under the blanket disallow.

**What was done**: `DuunitoriSource` was unregistered from both
`app/search/manager.py`'s `SearchManager.searchers` and
`app/search/v2/registry.py`'s `SOURCE_REGISTRY` — confirmed directly by
reading both files; the class itself and its tests
(`tests/test_duunitori_source.py`) are untouched, only its
*registration* was removed. This was reported as a real tradeoff (losing
the largest job source) and the decision to disable it, not circumvent
it, was made explicitly — not unilaterally decided and not silently
fixed.

**The no-circumvention policy is explicit and worth quoting in an
interview**: spoofing a different crawler identity, switching
User-Agent while still not matching an allowlisted crawler, or scraping
the disallowed paths anyway were all treated as *out of scope*, not
"quick fixes for later." `docs/DATA_SOURCES.md` states this is treated
"the same way this project treats a TLS failure: not something to route
around."

**A second, more nuanced finding on the same theme**:
`TyomarkkinatoriSource`'s job listings load via client-side JavaScript
and aren't in the static HTML this project's `requests`+BeautifulSoup
scraper fetches. Real browser network inspection found the site's own
internal JSON API (`POST /api/jobpostingfulltext/search/v2/search`) —
unauthenticated, and a working integration against it was built and
**verified live** (4 real jobs, correctly matched). It was **not
shipped**, because `tyomarkkinatori.fi/robots.txt` states
`Disallow: /api/`. The reasoning explicitly stated: an endpoint being
technically public and unauthenticated doesn't override the site
operator's stated crawling policy. This is a genuinely strong answer to
"tell me about a time you found something you could technically do but
chose not to."

**Jobly**, by contrast, has a compliant `robots.txt` but specifies
`Crawl-delay: 10` for the generic group — the scraper wasn't honoring
it. Fixed by adding a 10-second sleep after every request in
`JoblySource.get_page()` (confirmed by reading the code —
`app/search/sources/web_sources.py` lines ~675–681). This is why a full
Jobly search now takes several minutes, not seconds — an accepted,
deliberate cost of compliance.

### SSRF — following a scraped link off-domain

Every source class (`DuunitoriSource`, `JoblySource`,
`TyomarkkinatoriSource`, `WorkInFinlandSource`) follows links scraped out
of third-party HTML via `urljoin(self.BASE_URL, href)`. `urljoin()`
leaves an **absolute** `href` untouched — so a scraped page containing
an absolute link to another host (a compromised ad, an
attacker-controlled URL disguised as a job link) would previously be
fetched as if it were a same-site job posting.

**Fix, verified directly in code**: `WebSourceBase.is_same_site(url)`
(`app/search/sources/web_sources.py` lines ~114–130) compares the
resolved URL's `netloc` against the source's own `BASE_URL` before any
detail-page fetch, and every source calls it before following a link.
Covered by `tests/test_source_domain_guard.py`.

### Other verified security findings (all confirmed by direct code inspection, not assumed)

- **TLS**: `requests` is never called with `verify=False` anywhere —
  zero occurrences, checked directly. A prior handoff document
  incorrectly attributed Tyomarkkinatori's zero results to a TLS
  failure; that was re-investigated from scratch and found to be false
  (the real cause is client-side rendering, above) — a good example of
  not trusting inherited documentation without verifying it yourself.
- **Flask debug mode**: `webapp.py` used to call
  `app.run(debug=True)` unconditionally — the Werkzeug interactive
  debugger allows arbitrary code execution from the browser if ever
  reachable from outside localhost. Now off by default, opt-in via
  `FLASK_DEBUG=1`.
- **Path traversal / upload handling**: `/settings/upload-cv`
  (`app/web/routes.py::_save_uploaded_cv`) never uses the
  client-supplied filename to build a path — only the extension is
  checked against an allow-list (`.pdf`, `.docx`); the file is always
  written to a fresh `uuid4().hex` name. Verified with a test that
  uploads a file literally named `"../../evil.docx"` and asserts it
  can't escape `data/cv_uploads/`.
- **DoS / hung requests**: the Ollama call path had no timeout at all
  originally (via a since-removed duplicate class, `AIEngine`) and
  could hang a Flask request indefinitely against a slow local model.
  Consolidated onto one client class, `app.ai.llm.LocalLLM`, with a
  default 30s timeout (`OLLAMA_TIMEOUT`), returning a clear failure
  instead of hanging.
- **No CSRF protection** — genuinely still true today, verified by
  reading `app/web/routes.py`: `/save/<id>`, `/status/<id>/<status>`,
  `/delete/<id>` are plain `GET` routes with no token. This is an
  honest, currently-open gap (see "Known limitations" below), not
  something to hide if asked directly — the mitigating context is that
  there's no authentication layer at all (single-user local tool), so
  the actual severity depends entirely on deployment context.
- **No hardcoded secrets** — checked directly, zero occurrences; Ollama
  config comes from environment variables with defaults.

### Questions you should be ready for

- "How do you decide whether an endpoint being technically reachable
  means it's okay to use?" — Use the Tyomarkkinatori story. Public +
  unauthenticated ≠ permitted; `robots.txt`'s stated policy is the
  signal that matters.
- "What's an SSRF risk you've actually fixed, not just studied?" — Use
  `is_same_site()`. Be ready to say *why* `urljoin()` alone doesn't
  protect against it (it only resolves relative paths; it passes
  absolute URLs through untouched).
- "What would you fix first if you kept working on this?" — CSRF
  protection is the honest, correct answer — you have the receipts
  (`docs/SECURITY.md`'s "Known limitations", `NEXT_TASKS.md`).

---

## Domain: Software Engineering

### Word-boundary matching — a real, findable bug and its fix

`app/search/v2/matching/signals.py::_contains_term()` and
`app/ai/skill_gap.py`'s own independent `_contains_term()` both tokenize
text and check for an *exact, contiguous token-sequence match* — not a
substring match. This is deliberate: a naive `"java" in text.lower()`
check would match inside `"javascript"`. The fix is tokenization plus
exact-token comparison, not a regex word-boundary hack (`\bjava\b` would
still have its own edge cases with punctuation).

A related, more subtle bug found while building the skill-gap feature
(`app/ai/skill_gap.py`'s module-level comment, verified by reading the
code): `app/search/v2/matching/signals.py`'s normalizer keeps periods in
its allowed character set — harmless for matching a short skill string
against a whole text blob, but `skill_gap.py` tokenizes real
sentence-level text from job postings, where a skill is very often the
last word before a period (`"...experience with Terraform."`). Keeping
the period glues it onto the token (`"terraform."`), which then never
equals the alias `"terraform"`. `skill_gap.py`'s own normalizer strips
periods entirely for exactly this reason — the two modules deliberately
use *slightly different* normalization rules because they solve
genuinely different problems, not because of inconsistency.

**This is a good "walk me through a bug you found" story**: it shows you
understand tokenization isn't a solved problem you can copy-paste
between two similar-looking use cases without checking the actual input
shape.

### Deduplication — two independent implementations, deliberately not shared

V1 (`app/search/manager.py`) uses a three-tier check: source+ID,
canonical URL, and a content fingerprint that includes description text
(so two genuinely different postings with the same title+company+location
aren't merged). V2 (`app/search/v2/dedupe.py`) uses two signals —
`dedupe_key()` (source+external_id, or normalized title+company+location)
**or** `canonical_url()` (same URL, tracking parameters stripped) —
either one matching is enough to treat a job as a duplicate.

**A real, documented limitation, not swept under the rug**: during live
testing, two Jobly postings appeared with reordered but near-identical
titles at two different URLs (`"IT Systems and Cyber Security
Specialist, Forcit Defence, Tampere"` vs. `"FORCIT Defence, IT Systems
and Cyber Security Specialist"`). `dedupe_key()` requires an *exact*
normalized title match with no external id — these weren't merged. This
was a deliberate tradeoff: fuzzy/token-set title matching risks merging
genuinely different postings that happen to share the same words. Good
material for "how do you think about precision vs. recall in a
deduplication system."

### Testing philosophy — verified by direct inspection of `pyproject.toml` and multiple test files

The actual current test count is **219 passed** (verified live via
`pytest -q --basetemp=<dir>` on this machine — see "Where the docs and
the code disagree" below for why some docs still say 148). Key
disciplines, all confirmed by reading the actual test files:

- **No test performs a live network request or calls Ollama.** Route
  tests that would otherwise trigger a real V2 search monkeypatch the
  two functions `_search_jobs()` actually calls
  (`v2_enabled`, `create_v2_service`), not the whole HTTP stack.
- **Persistence tests always use an isolated database** — `tmp_path` /
  `monkeypatch.chdir(tmp_path)` — never the real `data/careerpilot.db`.
  This project has a real, documented incident where a *manual*
  verification session (not the automated suite) wrote to the real
  database instead of an isolated copy, producing a job that appeared
  to have jumped straight to "Interview" status with no application
  ever submitted. The root cause was traced directly (no code path
  changes a status automatically — verified by reading
  `update_status()`'s only caller), the polluted rows were found and
  cleared with the user's explicit confirmation, and "any manual
  verification touching persistence must use an isolated working
  directory" became a documented rule afterward
  (`docs/PRODUCT_VISION.md`'s "Investigated" section). This is a strong,
  honest story about process discipline learned from a real mistake,
  not a hypothetical.
- **Regression tests are written for the actual bug, not the general
  class of bug** — e.g.
  `tests/test_v2_ranking.py::test_rank_does_not_crash_when_posted_at_is_mixed_none_and_datetime`
  exists because comparing a real `datetime` against a fallback `""`
  string in a sort key raises `TypeError` in Python 3 the moment two
  jobs tie on score with mixed presence/absence of `posted_at`.

### Questions you should be ready for

- "Tell me about a bug you found through your own testing discipline,
  not because something crashed in production." — The `posted_at`
  tie-break `TypeError` is a clean example: found and fixed before it
  ever surfaced as a real crash, with a regression test that
  specifically reproduces the mixed-type comparison.
- "How do you decide what to mock vs. what to test end-to-end?" — Use
  `docs/TESTING.md`'s testing-approach section: pure logic gets no
  mocking at all; anything touching Flask routes monkeypatches at the
  function boundary the route actually calls, not the whole HTTP stack,
  unless the test is specifically about routing itself.
- "What's a time you shipped something, found it was subtly wrong, and
  had to walk it back?" — The database-pollution incident above is a
  genuine, non-defensive answer.

---

## Domain: Cloud / DevOps

**Be honest about scope here** — this project's cloud/DevOps content is
real but concentrated in two places: what it *models* (the skill catalog
and career tracks) and how it *configures itself* (environment
variables, no hardcoded infra). It is **not** a containerized,
CI/CD-deployed cloud application itself — say that plainly if asked, and
pivot to what actually is true.

**What's genuinely true, verified by reading the code**:

- **No Docker, no CI/CD** — confirmed directly: no `Dockerfile`, no
  `docker-compose.yml`, no `.github/workflows` directory. This is a
  documented, honest gap (`docs/TECHNOLOGY_STACK.md`'s "Optional / not
  currently used" section), not an oversight to hide.
- **Configuration is entirely environment-variable-driven** —
  `CAREERPILOT_SEARCH_V2`, `FLASK_DEBUG`, `OLLAMA_HOST`, `OLLAMA_MODEL`,
  `OLLAMA_TIMEOUT`, `OLLAMA_MAX_TOKENS` — no hardcoded config, sensible
  defaults, all read at the actual call site (verified in
  `app/ai/llm.py`, `webapp.py`).
- **SQLite, deliberately, not Postgres** — a zero-setup, single-user,
  embedded database, an explicit and reasoned choice for this project's
  actual scale (`docs/TECHNOLOGY_STACK.md`), not "hasn't gotten to it
  yet."
- **The cloud/DevOps *domain content*** — `app/ai/skill_gap.py`'s
  `SKILL_CATALOG` covers AWS, Azure, Google Cloud, Docker, Kubernetes,
  Terraform, Ansible, CI/CD, Infrastructure as Code — each with real
  certifications (AWS Cloud Practitioner, CKA, Terraform Associate,
  AZ-900, etc.) and a genuine hands-on project idea, not invented ones
  (see the "AI" domain section below for exactly how "never invented"
  is enforced). If a cloud/DevOps interviewer asks about this project,
  the honest framing is: *this project's engineering is Python/Flask
  application development with real scraping/security discipline; its
  subject-matter content happens to cover cloud/DevOps skills because
  that's the candidate's own target domain.*
- **`app/search/v2/matching/matcher.py`'s seniority/experience-penalty
  logic and `app/ai/geo_normalizer.py`'s country classification** are
  the closest things to "infrastructure-adjacent" logic in the app
  itself — deterministic rule engines, not infrastructure.

### Questions you should be ready for

- "What would deploying this to production actually require?" — No CI,
  no containerization, no CSRF, no session isolation for multiple
  visitors, range-pinned (not hash-pinned) dependencies. Be ready to
  name these as a checklist, from `docs/SECURITY.md`'s "Exposing this
  app to testers via a tunnel" section, which already goes through
  exactly this checklist for a *limited*, trusted-tester deployment
  (not a public one).
- "Why SQLite and not Postgres/MySQL?" — Single-user, zero-setup,
  matches actual current scale; explicitly noted as "not suitable if
  this ever became multi-user/concurrent" in
  `docs/TECHNOLOGY_STACK.md` — you already know the limit and when
  you'd revisit it.

---

## Domain: AI / LLM Integration

This is the section where the project's most deliberate design boundary
lives, and it's worth being precise about it, because "when do you use
an LLM vs. not" is a very live interview question right now.

### The zero-LLM boundary — the single most important design decision to be able to explain

**Runtime AI is local Ollama only** — no OpenAI/Anthropic/any hosted API
anywhere in the codebase (verified: `requirements.txt` only lists
`ollama>=0.4,<1.0`; grepped the source for any hosted-provider usage).

**Used for** (four call sites, all confirmed by reading
`app/web/routes.py`'s route bodies): résumé generation
(`/generate/<id>`), cover-letter generation (`/coverletter/<id>`), CV
data extraction on upload (`/settings/upload-cv`), interview-question
generation (`/interview/<job_id>`, gated), and AI project coaching
(`/projects/<id>/plan`, `/ask`, `/review`, `/cv-bullet`).

**Explicitly NOT used for**: matching, ranking, deduplication,
filtering, search, skill-gap analysis, CV-strength analysis, or (this
session's additions) the Living Career Profile, career-track ranking,
application readiness, or hiring perspective. **All of the
career-intelligence layer built this session is deterministic Python —
confirmed directly by reading every import in `app/ai/career_profile.py`,
`app/ai/career_tracks.py`, `app/ai/application_readiness.py`, and
`app/ai/hiring_perspective.py`: none of them imports `app.ai.llm` or
anything Ollama-related.**

**Why, in one sentence you should be able to say without notes**: a
hallucinated certification name is a false factual claim a real person
might act on; an LLM's answer to an open technical question is
understood by both parties to be generated guidance to be verified, the
same way any AI coding assistant's output is — those are different risk
categories, and the code boundary follows that distinction exactly.

**The one deliberate, narrower exception**: `ProjectCoach`
(`app/ai/project_coach.py`) is genuinely open-ended (planning, Q&A,
code review), not a templated document, and its `draft_cv_bullet()`
method is held to the strictest grounding of any call site — gated at
the *route* level (not just by prompt instruction) to only fire once a
project's status is `"Verified"`, and grounded only in that project's
own recorded text, never the wider profile.

### Hallucination prevention is a prompt-level control, stated honestly as such

Résumé/cover-letter prompts include: *"Do not invent experience, skills,
education or certifications. Use only information contained in the
candidate profile."* This is explicitly documented as a **prompt-level
instruction, not a technical guarantee** — nothing in the codebase
parses the model's output and cross-checks every claim against
`profiles/profile.json`. Saying this limitation out loud, unprompted, in
an interview is a stronger signal than pretending the system is airtight.

### Interview prep is gated — a product decision dressed as a technical one

`/interview/<job_id>` only calls the LLM if the job's saved application
status (via `ApplicationService.status_for_job_url()`) is `"Interview"`,
`"Second Round"`, `"Final Round"`, or `"Offer"`
(`INTERVIEW_STAGE_STATUSES` in `app/services/application_service.py`).
Every other status renders a plain explanation of the gate with **no AI
call made at all**. This is worth explaining as a product decision, not
just an engineering one: generating prep for an interview that may never
happen adds noise, not value, to a "calm advisor" product.

### Questions you should be ready for

- "When would you *not* use an LLM for a feature that seems like a
  natural fit for one?" — This is the skill-gap recommendation feature.
  Say the two-reason argument from `app/ai/skill_gap.py`'s own
  docstring: explainability/reproducibility, and hallucination risk on
  a factual claim category (certifications) that must be trustworthy.
- "How do you prevent an LLM from inventing a candidate's experience?"
  — Prompt-level instruction + supplying only real profile data +
  being honest that this is not a cryptographic guarantee.
- "What's the narrowest possible LLM feature you've built, and why is
  it narrow?" — `draft_cv_bullet()`: route-level gate to `Verified`
  status, grounded only in the project's own text, always review-only.

---

## The Career Intelligence layer (this session's work: Milestone 1 + Commits 1–5)

This is the newest, largest body of work in the repo — six commits
(`3072417`, `fcf1681`, `acc946d`, `314e879`, `464f402`, `ad47892`), all
landed on `v2-development` and pushed. It's worth understanding well
because it's the most recent thing you built and the most likely to come
up as "walk me through something you shipped recently."

### What it actually is, module by module (verified by reading each file directly)

- **`app/ai/career_profile.py`** — the "Living Career Profile." Six
  evidence *tiers* per profile skill (not a single strength number):
  `KNOWS` (bare claim), `STUDIED` (named in an education entry),
  `PRACTICED` (a tracked project underway, not yet Verified),
  `CERTIFIED` (named in certifications), `PROFESSIONAL_EXPERIENCE`
  (named in an experience entry), `BUILT` (backed by a Verified
  project — the strongest tier). A skill can carry more than one tier
  at once. This sits *alongside* `app/ai/cv_strength.py`'s existing
  Basic/Intermediate/Advanced score, not instead of it — one answers
  "how strong," this answers "what kind."
- **`app/ai/career_tracks.py`** — seven hand-curated tracks (SOC/Security
  Operations, Cybersecurity Analyst, Network Security, Penetration
  Testing, Cloud Security, DevSecOps, IT Support → Security), each
  mapped to a small set of `SKILL_CATALOG` keys. Two functions serve two
  opposite directions: `rank_career_tracks()` ranks tracks against the
  *profile* (for `/cv-strength`), `classify_job_family()` classifies a
  single *job posting* into a primary/secondary family (for
  `/analyze/<job_id>`). Two components, always shown separately, never
  blended: **profile fit** (weighted evidence-tier strength) and
  **market signal** (how often the track's skills appear across
  whatever jobs the app's own last search actually returned — `None`,
  not a misleading 0%, when no search has run yet).
- **`app/ai/application_readiness.py`** — five tiers (Apply now / Apply
  – stretch / Prepare, then apply / Low priority / Likely not a fit),
  computed from the dashboard's Profile Match score or (on the deep-dive
  page) Requirement Coverage. `EXCLUDE` is deliberately reserved for a
  **near-zero composite score only** — verified directly in
  `classify_application_readiness()`: `missing_required_count` is used
  only to make the reason text specific, never to push a job into
  `EXCLUDE` by itself. This matters because the product spec explicitly
  forbids years-of-experience alone excluding a job outright.
- **`app/ai/hiring_perspective.py`** — three separate views (ATS/keyword
  screening, HR/recruiter, Technical Manager), never blended into one
  score. Deliberately reuses existing logic rather than re-deriving it:
  the ATS view is a relabeled projection of `skill_gap.py`'s own
  required/nice-to-have coverage; the Technical Manager view reuses
  `skill_gap.py`'s own per-skill `evidence.level == "demonstrated"`
  field. Only the HR view is genuinely new logic, and it's kept
  strictly structural (title alignment, education presence, a stated
  experience-years requirement vs. entry count) — deliberately **not**
  an invented judgment about "credibility" or "professional
  presentation," which the app has no honest way to measure.
- **`app/ai/capability_graph.py`** — a small, explicitly non-exhaustive,
  hand-curated map of which skills are a meaningful head start toward
  which others (e.g. Docker → Kubernetes, AWS → IAM/Cloud Security).
  Used by `skill_gap.py` to produce `"related_transferable"` evidence
  instead of a flat "missing" when a genuinely adjacent skill exists.
- **`app/ai/geo_normalizer.py`** — classifies a job's free-text location
  into `FINLAND` / `EUROPE` / `OUTSIDE_EUROPE` / `UNKNOWN` using a
  verified, real country/city name list (23 Finland terms, 36 Europe
  entries, 21 outside-Europe entries — counted directly from the code).
  `UNKNOWN` (missing data, a bare "Remote" with no country) is
  **never** excluded — only a confidently-identified non-European
  location is. This is a real, deliberate anti-false-negative design
  choice worth being able to explain: excluding on missing information
  would silently drop real, relevant postings.

### A design decision worth being able to defend under questioning

**Why is `application_readiness` shown on the dashboard and
`/analyze/<job_id>` but explicitly *not* on `/cv-strength`?** Because
`/cv-strength` is the job-independent Layer 1 page and application
readiness is inherently job-specific — a synthetic "average readiness
across postings" wouldn't be grounded in any single real job, which
would conflict with the project's own no-fabrication principle. This was
a **closed decision made explicitly during this session**, not an
oversight — a good example of recognizing when a feature request doesn't
fit a page's actual purpose and saying so instead of building it anyway.

### Questions you should be ready for

- "Walk me through a recent feature you built end to end." — Use this
  section. Be ready to say which file does what without looking it up.
- "How did you decide the scope of the seven career tracks?" — Small
  and hand-curated deliberately, same reasoning as `SKILL_CATALOG`
  itself: a track-to-skill mapping asserted for dozens of tracks without
  real labour-market research behind it is noise dressed up as
  intelligence (this is `docs/CAREER_INTELLIGENCE.md`'s own stated
  reasoning, and it's a defensible one).
- "What did you explicitly decide *not* to build, and why?" — The
  "Career Research Engine" scope (continuous scraping of training
  providers, certification bodies, competitor analysis) was explicitly
  rejected for two reasons: provenance (every other module in the app
  is traceable to a real, already-legitimately-held data source; this
  would mean either unverified new scrapers or fabricated "research"),
  and the fact that a genuinely continuous refresh engine needs real
  scheduling/persistence infrastructure this session didn't build. This
  is documented in `docs/CAREER_INTELLIGENCE.md`'s "Explicitly out of
  scope."

---

## Where the docs and the code disagree (verified directly — code wins)

Per the source-of-truth rule for this document: these are real,
currently-existing discrepancies between what other docs in this repo
claim and what the code actually does, checked directly rather than
assumed. Don't repeat the stale numbers in an interview.

1. **Test count.** `README.md` ("148 tests, all fixture- or
   mock-backed") and `docs/TESTING.md` ("Current result: 148 passed")
   both understate the real, current number. Running
   `python -m pytest -q --basetemp=<dir>` on this machine right now
   returns **219 passed, 0 failed** across 43 test files. `README.md`
   and `docs/TESTING.md` were last updated before this session's five
   commits (Milestone 1 + Commits 1–5) added their own test files
   (`test_application_readiness.py`,
   `test_application_readiness_route.py`, `test_career_profile.py`,
   `test_career_tracks.py`, `test_career_tracks_route.py`,
   `test_hiring_perspective.py`, `test_hiring_perspective_route.py`,
   plus additions to existing skill-gap tests) — `HANDOFF.md` and
   `NEXT_TASKS.md` do correctly say 219, but `README.md`/
   `docs/TESTING.md` were not touched in this session and still show
   the older number. **If asked "how many tests does this project
   have," say 219, and mention it as of a specific recent check, not
   from memory of the README.**

2. **`SKILL_CATALOG` size.** `docs/CAREER_INTELLIGENCE.md` describes it
   as "~55 entries." Counting the actual dictionary in
   `app/ai/skill_gap.py` directly (`len(SKILL_CATALOG)`) gives **46**
   entries. This isn't a large discrepancy, but it's a real one — say
   "about 45 hand-curated skills" if asked, not "~55."

3. **Dashboard load behavior.** `docs/DEVELOPMENT.md` states "The
   dashboard triggers a live search against the real job sources on
   load," which was true when written but is no longer the complete
   picture: `app/web/routes.py` now has a `_v2_search_cache` (added in
   an earlier commit, `51ce897`, predating this session but still
   current, live code) with a 300-second TTL. A dashboard visit within 5
   minutes of the last search reuses the cached job list instead of
   re-running the full multi-source search (which, with Jobly's
   10-second-per-request crawl delay, can otherwise take minutes). The
   explicit `/search` action always forces a fresh search
   (`force_refresh=True`), bypassing the cache. **If asked "does every
   page load re-scrape the job boards," the accurate answer is "no —
   there's a 5-minute cache; only the first load or an explicit
   re-search action triggers a real scrape."**

4. **Minor code-level quirk, not a doc/code mismatch but worth knowing
   if you're asked to read the code live**: `app/ai/capability_graph.py`'s
   `CAPABILITY_GRAPH["aws"]` lists `"cloud security"` twice —
   `["iam", "cloud security", "cloud security"]`. It's harmless (the
   `related_skills()` function deduplicates via a `seen` list before
   returning), but if you're doing a live code walkthrough and land on
   this line, know what it is rather than being surprised by it — it's
   a copy-paste duplicate, not a logic bug.

---

## Interview Questions

This consolidates the "Questions you should be ready for" prompts from
every domain section above into one place, and — unlike those
scattered prompts, which deliberately left the answer for you to
formulate — every question here has an actual written answer, specific
to CareerPilot AI, plus a follow-up. Use these as a floor to practice
from, not a script to recite verbatim; say them in your own words.

### General Project Questions

#### Question: "Tell me briefly about a project you've worked on."

**What the interviewer is testing:** whether you can summarize your own
work clearly and confidently in a short amount of time, without
rambling or drowning them in detail before they've asked for it.

**Strong answer:** Use the 30-Second Interview Answer above almost
verbatim, then stop talking and let them ask a follow-up rather than
continuing into the 2-minute version unprompted.

**Possible follow-up:** "What made you decide to build this yourself
instead of just using LinkedIn or Indeed?"

**Follow-up answer:** Existing job boards let you filter by keyword, but
none of them explain *why* a posting is or isn't a good fit for your
specific profile, or tell you what's actually missing from your
background for a role you're close to but not quite qualified for. That
gap — between "here are some postings" and "here's what to actually do
about the ones you're not ready for yet" — is what the skill-gap and
career-intelligence layers exist to close.

#### Question: "What problem does CareerPilot AI solve, and for whom?"

**What the interviewer is testing:** whether you can articulate a real
user problem, not just a list of features.

**Strong answer:** It's built for one real user — me, a cybersecurity/IT
job seeker in Finland — and solves three concrete problems: job boards
are fragmented across sites with no unified search; neither shows you
*why* a posting is a good fit; and even when you find a good match with
a gap, there's no path from "you're missing Kubernetes" to actually
having real, demonstrable evidence of Kubernetes.

**Possible follow-up:** "Why build it for one user instead of making it
a general product from the start?"

**Follow-up answer:** Building for one real, specific user with real
data meant every design decision could be checked against an actual
need instead of a guessed one — the profile schema, the career tracks,
the certification catalog are all genuinely useful for *this* candidate
because they were built and checked against real postings this
candidate was actually looking at, not a generic persona.

#### Question: "Did you build this alone, and what was your role?"

**What the interviewer is testing:** ownership and honesty about scope,
especially since AI coding assistance is common now and interviewers
want to know what you actually understand vs. what a tool produced.

**Strong answer:** Yes, solo — I made the architectural decisions (V1/V2
coexistence, the zero-LLM boundary for factual claims, the geographic
filtering approach, the career-intelligence layer's scope), used an AI
coding assistant (Claude Code) for implementation support the way I'd
use any modern tooling, and personally verified the resulting behavior
against real code, real test runs, and in several cases real live
network traffic (browser inspection to find Tyomarkkinatori's actual
JSON API, for example).

**Possible follow-up:** "How do you know you actually understand code
you didn't type character-by-character yourself?"

**Follow-up answer:** Because this document exists — I went back through
the actual source files, ran the actual test suite, and counted things
like `SKILL_CATALOG`'s real entry count directly rather than trusting
whatever a prior summary claimed, and found real discrepancies doing
that (see "Where the docs and the code disagree"). That's the same
verification discipline I'd apply to any code I'm accountable for,
regardless of who typed it first.

#### Question: "What's the single most interesting engineering decision
in this project?"

**What the interviewer is testing:** whether you can identify and defend
a genuine trade-off, not just describe a feature.

**Strong answer:** The `robots.txt` compliance decision on Duunitori —
disabling my largest job source after finding it violated the site's
stated crawling policy, reporting the real cost honestly, and refusing
to circumvent the policy in any way (no crawler-identity spoofing, no
scraping the disallowed paths anyway). It's the clearest example in the
whole project of choosing to do the right thing under a real, visible
cost, not a hypothetical one.

**Possible follow-up:** "Wasn't that overly cautious? The site's public
content either way."

**Follow-up answer:** Public accessibility and permitted automated
access are different things — `robots.txt` is the site operator's
explicit statement of which automated agents they've consented to, and
treating "I could technically fetch this" as equivalent to "I'm allowed
to" is exactly the reasoning that got Duunitori registered in the first
place before I'd checked. I apply the same standard I'd want applied to
my own site's stated policy.

### Architecture Questions

#### Question: "Walk me through what happens when I load the
dashboard."

**What the interviewer is testing:** whether you actually understand
your own system's control flow, not just its feature list.

**Strong answer:** `app/web/routes.py`'s `dashboard()` route loads the
profile, calls `_search_jobs()`, which — if V2 is enabled — either
reuses a cached result (if the last search was under 5 minutes ago) or
runs the full V2 pipeline: collect from each registered source via
`SourceRunner`, normalize into `CanonicalJob`, deduplicate, filter by
geography, and rank with `JobRanker`. Each ranked job gets V2's own
match result stashed onto it. Then `_rank_jobs()` checks whether every
job in the list carries that stash — if so, it presents V2's own scores
directly, in V2's own order; if not, it falls back to the legacy
`JobMatcher`. Interview-readiness and application-readiness flags get
attached last, and the template renders.

**Possible follow-up:** "Why cache the search results at all instead of
always searching fresh?"

**Follow-up answer:** Jobly's scraper honors a 10-second crawl-delay per
request, so a full search can take several minutes — without caching,
every single dashboard visit, even seconds after the last one, would
re-trigger that full multi-minute search. The cache has a 5-minute TTL
and the explicit "Search Jobs" action always bypasses it, since forcing
a fresh search is the entire point of clicking that.

#### Question: "Why keep two matching engines instead of picking one?"

**What the interviewer is testing:** whether you understand the
difference between "technical debt" and "a genuine design difference
worth preserving."

**Strong answer:** V1's tiered title-category scoring, weighted-skill
importance, and steep seniority penalties are the product of real,
hand-tuned decisions specific to this candidate's profile — deleting
them to make V2 the only matcher would mean either losing that tuning
entirely or re-deriving it inside V2 without the evidence trail that
originally produced it. Instead, the dashboard uses whichever matcher
actually produced the job list for a given request — V2 by default, V1
as a genuine fallback if V2 is disabled or fails — so both stay
independently correct and testable.

**Possible follow-up:** "Isn't maintaining two matchers just more
surface area for bugs?"

**Follow-up answer:** It is more code, but the alternative — merging two
genuinely different scoring philosophies into one matcher — would risk
silently changing behavior that was already tuned and verified. The
actual integration cost was small: one adapter function
(`_present_v2_ranked_jobs`) and one ownership check
(`_rank_jobs`'s check for a stashed `_v2_match`); neither matcher's own
internals were touched.

#### Question: "What happens if V2 search throws an exception halfway
through?"

**What the interviewer is testing:** whether your system has real
failure handling or just an unstated assumption that things work.

**Strong answer:** `_search_jobs()` catches the exception, logs it, and
falls back to `manager.search_jobs()` (V1). Independently,
`_rank_jobs()` also catches a failure specifically in
`_present_v2_ranked_jobs()` and falls back to the legacy matcher in that
case too — two separate fail-soft points, not one shared one, so a
failure in presentation doesn't need to be the same kind of failure as a
failure in the search itself.

**Possible follow-up:** "What if a single job *source* fails, not the
whole pipeline?"

**Follow-up answer:** `SourceRunner.run_source()` catches per-source
exceptions independently and returns a `SourceRunResult` with the error
attached, so one broken source (say, Jobly timing out) never stops the
others from contributing jobs — it's logged, not fatal.

#### Question: "How do you decide which score to actually show the
user — V1's or V2's?"

**What the interviewer is testing:** understanding of a specific,
non-obvious integration mechanism, and whether you can explain *why*
that mechanism exists.

**Strong answer:** Ownership is decided by where the job data actually
came from, not by re-checking the `CAREERPILOT_SEARCH_V2` flag a second
time at render time. When V2 successfully produces a job list, each
`CanonicalJob` carries V2's own computed match result stashed directly
onto it. `_rank_jobs()` checks whether *every* job in the list carries
that stash; if so, V2 owns presentation entirely, in V2's own order,
with no second scoring pass through the legacy matcher.

**Possible follow-up:** "What if V2 scored *some* jobs but not others in
the same batch?"

**Follow-up answer:** That can't happen by construction — every job in a
V2-produced list gets the stash applied in the same loop
(`item.job._v2_match = item.match`) before the list is ever returned, so
the "every job carries a stash" check is really checking "did this list
come from V2 at all," not verifying job-by-job.

### Python / Software Engineering

#### Question: "How did you handle duplicate jobs coming from different
sources in CareerPilot?"

**What the interviewer is testing:** whether you can explain a real
data-engineering decision with its actual trade-offs, not just define
"deduplication" abstractly.

**Strong answer:** Two independent implementations exist because V1 and
V2 evolved separately. V1 (`app/search/manager.py`) uses a three-tier
check: source+ID match, canonical URL match, and a content fingerprint
that includes description text specifically so two genuinely different
jobs with the same title/company/location aren't merged. V2
(`app/search/v2/dedupe.py`) uses two signals — a normalized
title-company-location key (or source+external_id when available), or a
canonical URL with tracking parameters stripped — treating a match on
*either* signal as a duplicate, because either signal alone under-catches
real-world duplicate patterns.

**Possible follow-up:** "Give me a real case where your dedup logic
actually missed a duplicate."

**Follow-up answer:** During live testing, two Jobly postings for the
same role appeared with reordered but not identical titles — "IT
Systems and Cyber Security Specialist, Forcit Defence, Tampere" versus
"FORCIT Defence, IT Systems and Cyber Security Specialist" — at two
different URLs. The exact-match title key didn't catch it. That's a
deliberate tradeoff, not an oversight: fuzzy/token-set title matching
would risk merging genuinely different postings that happen to share
words, which is a worse failure mode than an occasional missed
near-duplicate.

#### Question: "Tell me about a subtle bug you found in your own
text-matching logic."

**What the interviewer is testing:** depth of debugging — did you fix
the obvious case, or find the non-obvious one underneath it.

**Strong answer:** I built exact-token-sequence matching so "Java"
wouldn't false-positive match inside "JavaScript" — real tokenization,
not a substring check. But reusing a similar normalizer for the
skill-gap feature, which reads whole sentences straight out of job
postings, surfaced a second, sneakier version of the same bug class:
the normalizer kept periods, and a skill name is very often the last
word before a period — "experience with Terraform." — so the period
glued onto the token and silently broke the match against the alias
"terraform." I gave that feature its own normalizer that strips periods,
deliberately diverging from the otherwise-similar one.

**Possible follow-up:** "Why not just fix the shared normalizer once,
for everyone?"

**Follow-up answer:** Because the two use cases genuinely differ: V2's
normalizer matches a short skill string against a whole concatenated
text blob, where a trailing period is rare and harmless; the skill-gap
feature tokenizes real natural-language sentences, where a trailing
period before a skill name is common. Making one normalizer serve both
correctly would mean adding conditional behavior to a function that's
supposed to be simple and predictable — a second, purpose-built
normalizer was the more honest fix.

#### Question: "How do you decide what to mock vs. what to test
end-to-end?"

**What the interviewer is testing:** testing judgment, not just
familiarity with mocking as a concept.

**Strong answer:** Pure logic (normalization, dedupe keys, word-boundary
matching, ranking tie-breaks) gets no mocking at all — it constructs
objects directly. Source-parsing tests pass a hand-written HTML/JSON
fixture straight into the parsing method, since the method itself takes
that as an argument. Anything touching Flask routes monkeypatches at the
exact function boundary the route calls (`v2_enabled`,
`create_v2_service`) rather than the whole HTTP stack — unless the test
is specifically *about* routing/URL behavior itself, in which case a
real Flask test client is used end-to-end, with the database isolated
via `tmp_path`/`monkeypatch.chdir`.

**Possible follow-up:** "Isn't monkeypatching a function a form of
testing the implementation instead of the behavior?"

**Follow-up answer:** It can be, which is why it's scoped to the two
specific functions `_search_jobs()` actually calls, not internals three
layers deeper — the test still exercises the real route logic, real
ranking, real template rendering; it only avoids the one thing that
would make the suite non-deterministic and network-dependent, which is
the live HTTP call itself.

#### Question: "What's a time you shipped something, found it was
subtly wrong, and had to walk it back?"

**What the interviewer is testing:** honesty about mistakes and whether
you have a real process for catching them.

**Strong answer:** A job appeared in my application tracker at
"Interview" status that I'd never actually applied to. I traced the only
code path that changes a status (one route, only reachable by an
explicit click) and proved the application code itself was innocent —
the real cause was my own manual testing hitting the real database
directly instead of an isolated copy, unlike the automated suite, which
always isolates via `tmp_path`. I found the exact polluted rows, asked
for confirmation before clearing real data even though I'd caused the
mess myself, and made "manual verification must use an isolated working
directory" a standing rule afterward.

**Possible follow-up:** "How do you make sure that rule actually sticks
instead of being forgotten under time pressure?"

**Follow-up answer:** Honestly, imperfectly — the same mistake happened
once more, immediately after the rule was established, during a
different manual smoke check, and was caught and corrected the same way
a second time. I don't claim the rule is bulletproof; I claim it's
documented, and that repeating a caught mistake once is a much smaller
failure than repeating an uncaught one indefinitely.

### Cybersecurity

#### Question: "How do you decide whether an endpoint being technically
reachable means it's okay to use?"

**What the interviewer is testing:** security judgment beyond "does the
technical control allow it."

**Strong answer:** Technical reachability and permission are different
questions. I found Tyomarkkinatori's own internal JSON search API,
confirmed it was unauthenticated and returned real, structured job data,
and built a working integration against it — verified live with four
real jobs. I didn't ship it, because the site's `robots.txt` explicitly
disallows `/api/`. An endpoint being public and requiring no
authentication doesn't override the site operator's stated crawling
policy — that's the same standard I'd want applied to my own systems.

**Possible follow-up:** "What would change your answer — what would make
it okay to use that endpoint?"

**Follow-up answer:** Either explicit permission from Tyomarkkinatori (a
real, stated go-ahead, ideally reflected in an updated `robots.txt` or a
written agreement), or an official, approved API meant for aggregators.
Both require a decision from a human on their side, not more engineering
on mine — I logged it as a "requires human decision" item rather than a
technical TODO.

#### Question: "What's an SSRF risk you've actually fixed, not just
studied?"

**What the interviewer is testing:** hands-on vulnerability discovery
and remediation, not textbook knowledge.

**Strong answer:** Every one of my four job-source scrapers follows
links scraped out of third-party HTML using `urljoin(self.BASE_URL,
href)`. `urljoin()` leaves an absolute `href` completely untouched — so
a scraped page with an absolute link to another host (a compromised ad,
an attacker-controlled URL disguised as a job posting) would previously
be fetched exactly as if it were a same-site posting. I added
`WebSourceBase.is_same_site(url)`, comparing the resolved URL's `netloc`
against the source's own base URL before any detail-page fetch, wired
into all four sources, and covered by a dedicated regression test file.

**Possible follow-up:** "Why didn't `urljoin()` already protect against
that?"

**Follow-up answer:** Because that's not what it's designed to do —
`urljoin()`'s job is to correctly *resolve* a relative URL against a
base URL, and it does that correctly. It was never meant to be a
security boundary, and treating a general-purpose parsing function as
one just because it "usually" produces same-site URLs is exactly the
kind of implicit assumption I try to check explicitly instead of trust.

#### Question: "What would you fix first, security-wise, if you kept
working on this?"

**What the interviewer is testing:** prioritization under real
constraints, not a wish list.

**Strong answer:** CSRF protection. `/save/<id>`, `/status/<id>/<status>`,
and `/delete/<id>` are plain `GET` routes with no token today — that's
acceptable right now because there's no authentication layer at all
(genuinely single-user, local tool), but it's the first thing that has
to change before this could be shared with even a small group of
trusted testers over a tunnel, per my own security checklist for that
scenario.

**Possible follow-up:** "Why hasn't it been fixed already if you already
know it's the top priority?"

**Follow-up answer:** Because the actual current severity is low — no
auth boundary exists to cross, so a CSRF attack's worst case today is
someone tricking a *tester* into saving or deleting a *tester-visible*
record, not compromising real credentials or data. It's sequenced
correctly as "must-fix before wider exposure," not "must-fix
immediately regardless of who can currently reach the app."

#### Question: "Walk me through how file uploads are handled securely."

**What the interviewer is testing:** concrete, code-level security
practice, not generic "we validate inputs" language.

**Strong answer:** `/settings/upload-cv` never uses the client-supplied
filename to build the destination path — only its extension is checked
against an allow-list (`.pdf`, `.docx`); the actual file on disk always
gets a fresh `uuid4().hex` name. I verified this directly with a test
that uploads a file literally named `"../../evil.docx"` and asserts the
saved path stays inside `data/cv_uploads/` and is never named
`evil.docx`. The upload is also capped at 10MB before being fully read
into memory, rate-limited to 20 attempts per minute per IP, and swept
for files older than 24 hours on every upload attempt, since CV uploads
are real personal data.

**Possible follow-up:** "What happens to the extracted data after
upload — does it touch the real profile?"

**Follow-up answer:** No — extracted data is displayed for review only.
`/settings/upload-cv` never writes to `profiles/profile.json`
automatically, verified with a regression test that hashes the real
profile file before and after an upload request and asserts it's
byte-identical. A bad or AI-hallucinated extraction can't silently
corrupt the profile everything else in the app depends on.

### Cloud / DevOps

#### Question: "What would deploying this to production actually
require?"

**What the interviewer is testing:** whether you can honestly assess
gaps in your own deployment story instead of overselling it.

**Strong answer:** No containerization (no `Dockerfile`), no CI/CD (no
`.github/workflows`), CSRF protection still missing, no per-visitor
session isolation, and dependencies are range-pinned rather than
hash-pinned. I have an explicit checklist for the more limited case of
sharing this with a small group of trusted testers via a tunnel — upload
hardening, rate limiting, no debug mode by default are already done —
but "production" in the general sense would need all of the above
first.

**Possible follow-up:** "If you had one week to prepare this for a
small internal beta with 5 real users, what would you prioritize?"

**Follow-up answer:** CSRF tokens on the three state-mutating routes
first, since that's the concrete, currently-open gap with real
(if low-severity today) impact; then confirming the tunnel-exposure
checklist end to end, since most of it — upload retention, rate
limiting, no debug mode — is already built and just needs verifying
together as a set, not each item revisited from scratch.

#### Question: "Why SQLite and not Postgres or MySQL?"

**What the interviewer is testing:** whether infrastructure choices are
deliberate or just defaults you never questioned.

**Strong answer:** Zero-setup, embedded, and genuinely matches this
project's actual scale — a single-user local tool. I've explicitly noted
in my own documentation that it's "not suitable if this ever became
multi-user/concurrent," so it's a choice I understand the limits of, not
one I've stopped thinking about.

**Possible follow-up:** "What would actually break first if this had 50
concurrent users?"

**Follow-up answer:** SQLite's write-concurrency model — it locks the
whole database file for writes, so 50 concurrent users saving jobs or
updating application statuses at once would start serializing on that
lock and degrade badly. That, combined with the lack of session
isolation (every user currently reads the one master profile), means
concurrency and multi-tenancy would both need solving together, not
separately.

#### Question: "How is configuration managed across environments?"

**What the interviewer is testing:** whether config is hardcoded or
properly externalized.

**Strong answer:** Entirely environment-variable-driven —
`CAREERPILOT_SEARCH_V2`, `FLASK_DEBUG`, `OLLAMA_HOST`, `OLLAMA_MODEL`,
`OLLAMA_TIMEOUT`, `OLLAMA_MAX_TOKENS` — each read at its actual call
site with a sensible default, so the app runs with zero required
configuration for a basic V1 search and test suite, and only needs
explicit env vars for the V2 pipeline and AI features.

**Possible follow-up:** "No `.env` file checked in — how do you make
sure secrets never leak into git?"

**Follow-up answer:** There are no secrets to leak in the first place —
no hardcoded API keys or tokens anywhere in the codebase, checked
directly with a pattern search — and `.gitignore` explicitly excludes
`.env`/`.env.*` (with only `.env.example` as a tracked exception).

### AI / Intelligent Features

#### Question: "When would you *not* use an LLM for a feature that
seems like a natural fit for one?"

**What the interviewer is testing:** judgment about LLM risk, not just
enthusiasm for using one everywhere.

**Strong answer:** The skill-gap recommendation feature — recommending
certifications, courses, and projects for a candidate's skill gaps —
reads naturally as generated text, and is exactly the case where
hallucination is least acceptable: inventing a certification, or
claiming one covers something it doesn't, would actively mislead someone
about their own career. Instead it's a small, hand-curated,
non-AI-generated catalog checked against the job and profile with
deterministic word-boundary matching — every recommendation is
"verified" by construction because a human picked it.

**Possible follow-up:** "Couldn't you just tell the LLM to only
recommend real certifications and check its output?"

**Follow-up answer:** I could try, but that shifts the guarantee from
"structurally impossible to hallucinate" to "hopefully didn't
hallucinate this time" — a prompt instruction is not a technical
guarantee, which I say explicitly elsewhere in this same project about
the résumé/cover-letter prompts. For a claim category like
certifications, where someone might actually act on the recommendation,
I chose the stronger guarantee.

#### Question: "How do you prevent an LLM from inventing a candidate's
experience?"

**What the interviewer is testing:** understanding of prompt-level
controls and their real limits.

**Strong answer:** The résumé and cover-letter prompts explicitly
instruct the model: "Do not invent experience, skills, education or
certifications. Use only information contained in the candidate
profile," and only real profile data is supplied as context — no
wider internet knowledge is asked for. But I say plainly, including in
my own documentation, that this is a prompt-level instruction, not a
technical guarantee — nothing in the codebase parses the model's output
and cross-checks every claim against the profile.

**Possible follow-up:** "So how would you actually catch it if the model
did hallucinate something?"

**Follow-up answer:** Today, only by the candidate reading the generated
document before using it — there's no automated verification pass. If I
extended this, the next step would be a structural check (does every
named skill/employer in the output actually appear in
`profiles/profile.json`), which is exactly the kind of guarantee the
skill-gap feature already has by *not* using an LLM at all for its
factual claims.

#### Question: "What's the narrowest possible LLM feature you've built,
and why is it narrow?"

**What the interviewer is testing:** whether you scope AI features
deliberately instead of maximally.

**Strong answer:** `draft_cv_bullet()` — drafting a CV bullet from a
completed practical project. It's gated at the *route* level, not just
by prompt instruction, to only fire once a project's status is
`"Verified"`; it's grounded only in that project's own recorded
title/description/notes, never the wider candidate profile; and the
result is always review-only — nothing writes to `profiles/profile.json`
automatically. Every one of those is a deliberate narrowing, not a
default.

**Possible follow-up:** "Why gate at the route level instead of just
trusting the prompt to only draft for verified work?"

**Follow-up answer:** Because a route-level gate is enforced by code
that always runs, regardless of what the prompt says or how the model
behaves that day — a prompt instruction is a request to the model, a
route check is a guarantee about what the server will and won't do. For
the one call site that touches CV-facing text directly, I wanted the
stronger guarantee.

#### Question: "Why is interview-prep generation gated instead of
always available?"

**What the interviewer is testing:** whether you connect a technical
gate to an actual product reasoning, not just describe the mechanism.

**Strong answer:** `/interview/<job_id>` only calls the LLM if that
job's saved application has actually reached "Interview," "Second
Round," "Final Round," or "Offer" status — checked via
`ApplicationService.status_for_job_url()`. Every other status renders a
plain explanation of the gate with no AI call made at all. It's a
product decision as much as a technical one: generating prep for an
interview that may never happen adds noise, not value, to what's meant
to be a calm advisor rather than a pressure-generating tool.

**Possible follow-up:** "Isn't gating a feature behind application
status just adding friction?"

**Follow-up answer:** It's adding friction on purpose, at the one point
where friction is actually useful — proactively pushing interview prep
for every saved job would turn a calm tool into an anxiety generator.
The gate also has a real technical side benefit: it means the Ollama
call, which has a real cost and latency, only happens when the feature
is genuinely needed.

### Testing and Quality

#### Question: "How many tests does this project have, and what do
they cover?"

**What the interviewer is testing:** whether your testing claims are
current and specific, or a stale number you're repeating from memory.

**Strong answer:** 219 passing tests across 43 test files, verified live
just now via `pytest -q --basetemp=<dir>` — not from memory, since I
found while writing this document that older docs in the same repo
(`README.md`, `docs/TESTING.md`) still say 148, from before this
session's additions. Coverage spans pure-logic unit tests (normalization,
dedupe, word-boundary matching, ranking tie-breaks), source-parsing
tests against hand-written HTML/JSON fixtures, route-level tests with
monkeypatched search functions, and full end-to-end Flask-test-client
flows with an isolated database.

**Possible follow-up:** "Why did the documentation get out of sync with
the real number?"

**Follow-up answer:** Because `README.md` and `docs/TESTING.md` weren't
touched during the session that added the new tests — only
`HANDOFF.md`/`NEXT_TASKS.md` were updated with the current 219 figure. It's
a small, honest example of documentation drift, and part of why I
verify numbers live against the code rather than trusting any single
doc, including this one, indefinitely.

#### Question: "Tell me about a bug you found through your own testing
discipline, not because something crashed in production."

**What the interviewer is testing:** proactive quality practice versus
reactive firefighting.

**Strong answer:** `JobRanker`'s tie-break sort previously compared a
real `datetime` against a fallback empty string directly when
`posted_at` was missing — which raises `TypeError` in Python 3 the
moment two jobs tie on score with mixed presence/absence of
`posted_at`. I found and fixed this — switching to a numeric timestamp
with 0.0 for missing dates — before it ever surfaced as a real crash,
and wrote a regression test that specifically reproduces the mixed-type
comparison.

**Possible follow-up:** "How did you even think to check that edge
case?"

**Follow-up answer:** By thinking about what real data actually looks
like rather than what a happy-path test fixture looks like — not every
scraped job posting has a parseable `posted_at` date, so "two jobs with
the same score, one with a date and one without" was a realistic
scenario worth constructing deliberately, not a purely theoretical
edge case.

#### Question: "How do you keep your test suite from silently drifting
out of sync with reality?"

**What the interviewer is testing:** whether you think about
documentation and test currency as an ongoing discipline, not a one-time
task.

**Strong answer:** Honestly, imperfectly — I found real drift while
building this very document: `README.md` and `docs/TESTING.md` say 148
tests, the actual current number is 219, because those two files simply
weren't touched when the newest test files were added. My response
wasn't to silently repeat the stale number; it was to run the suite
live, get the real number, and flag the discrepancy explicitly rather
than assume prior documentation was still accurate.

**Possible follow-up:** "So what would you actually do to prevent this
long-term?"

**Follow-up answer:** A CI pipeline that runs the suite and could, at
minimum, flag when a doc-stated test count diverges from the real
collected count — this project currently has no CI at all, which is
itself an honestly-documented gap. Short of that, the discipline I
actually practice is: verify a number against the code before repeating
it in an interview, rather than trusting any document, including my own
notes, by default.

### System Design

#### Question: "How did you decide the scope of the seven career
tracks?"

**What the interviewer is testing:** whether you can justify scope
decisions with reasoning, not just describe what exists.

**Strong answer:** Deliberately small and hand-curated, for the same
reason `SKILL_CATALOG` itself is: asserting a track-to-skill mapping for
dozens of tracks without real labour-market research behind each one
would be noise dressed up as intelligence. Seven tracks, each mapped to
a handful of real `SKILL_CATALOG` keys, is a set I can actually stand
behind as editorially defensible.

**Possible follow-up:** "How would you scale this to more tracks without
losing that editorial rigor?"

**Follow-up answer:** One track at a time, the same way the job-source
scrapers grew — pick one real, specific new career track, verify its
skill mapping against real postings for that track, add it, and only
then move to the next one, rather than generating a broad taxonomy in
one pass and hoping it holds up.

#### Question: "What did you explicitly decide *not* to build, and
why?"

**What the interviewer is testing:** scope discipline — can you say no
to a feature request for good reasons, or do you build everything asked
for.

**Strong answer:** A "Career Research Engine" — continuous scraping of
training providers, certification bodies, and competitor career-AI
products — was explicitly rejected for two reasons: provenance (every
other module in this app is traceable to a real, already-legitimately-
held data source; this would mean either unverified new scrapers or
fabricated "research" with no real source behind it, which conflicts
with the project's own anti-hallucination principle), and the fact that
a genuinely continuous refresh engine needs real scheduling and
persistence infrastructure that a same-session feature addition
shouldn't casually introduce.

**Possible follow-up:** "What would actually make that feature buildable
later?"

**Follow-up answer:** Picking one single, real, public, terms-compliant
source — a specific university's public course catalog API, or one
certification vendor's public exam list — and building one narrow,
verified integration for it, the same incremental way the existing job
sources were each added one at a time, rather than a generic "research
engine" for every category at once.

#### Question: "If you had to scale this to multiple users, what would
break first and what would you do about it?"

**What the interviewer is testing:** systems thinking about a concrete
scaling path, not an abstract "we'd use Kubernetes" answer.

**Strong answer:** Two things break simultaneously, not sequentially:
SQLite's write-concurrency (it locks the whole file for writes) under
real concurrent load, and the complete lack of session isolation — every
visitor currently reads and matches against the one master
`profiles/profile.json`. I'd solve them together, not separately: thread
a session-scoped profile through every route that currently calls
`_load_profile()`, add CSRF protection before any state-mutating route
is exposed beyond a trusted group, and only then reconsider whether
SQLite's concurrency model is actually the bottleneck at the real target
scale, rather than pre-emptively migrating to Postgres before I know
that's the actual constraint.

**Possible follow-up:** "Why not just start with Postgres now to avoid
a migration later?"

**Follow-up answer:** Because for a genuinely single-user local tool,
SQLite adds zero operational cost and Postgres would add real setup
overhead for a problem this project doesn't have yet — I'd rather make
that migration deliberately, once session isolation actually makes
multi-user use real, than carry unused infrastructure complexity on the
chance it's needed someday.

---

## STAR Stories

Five stories, each built from real, already-documented work in this
guide — none of these are invented for this section. Each cites the
exact section of this document it was constructed from, so you can go
re-read the fuller technical detail before using the story in an
interview.

### Story 1 — The Duunitori `robots.txt` compliance decision

**Source:** "Domain: Security" → "`robots.txt` compliance — the best
story in this project"

#### Situation

My job-search app's single largest source of collected postings was a
scraper, `DuunitoriSource`, that had already shipped, been fixed for a
title-extraction bug, and re-verified multiple times across the same
session.

#### Task

While later checking a different source's (`Tyomarkkinatori`)
`robots.txt` for an unrelated reason, I made it standard practice to
check `robots.txt` for every source going forward — including ones
already shipped — and needed to decide what to do about what that check
found.

#### Action

I checked `duunitori.fi/robots.txt` directly and found it disallows the
generic `*` user-agent group entirely (`Disallow: /`), with named
exceptions only for specific crawlers like Googlebot and Bingbot. My
scraper sent a spoofed generic browser User-Agent, matching none of
those named exceptions — meaning it had been running in violation of the
site's stated policy for the entire session. I reported this plainly,
including the real cost (it was the largest source of jobs), and
unregistered the source from both the V1 and V2 search pipelines rather
than working around the policy in any way — no spoofing a different
crawler identity, no switching to a still-non-allowlisted User-Agent, no
scraping the disallowed paths anyway.

#### Result

The scraper's code and tests remain intact and untouched, so it can be
re-enabled in one line the moment Duunitori grants explicit permission
or offers an official API. Today the app runs fully compliant, at the
real, accepted cost of a smaller job list.

#### Technical lesson

Checking `robots.txt` against the exact user-agent group a scraper's
real request will match — not just whichever group looks most
permissive — has to be standard practice for every source, both before
and after it ships, because policies (and my own earlier diligence) can
both turn out to be wrong at different times.

#### Interview version (45–90s)

"One of the strongest examples of judgment in this project isn't a bug —
it's a compliance decision. My biggest job source, a scraper I'd already
built, fixed, and re-verified multiple times, turned out to violate its
own site's `robots.txt` — it disallowed generic crawlers entirely, and
my scraper's User-Agent didn't match any of the named exceptions. I
found this by making a habit of checking `robots.txt` for every source,
including ones already shipped, after a similar check on a different
source. I reported it plainly — including that it was my largest source
of jobs — and disabled it rather than working around the policy in any
way. The code's still there, untouched, ready to re-enable the moment I
have real permission. It cost me real data, but it's the decision I'm
most confident defending in an interview."

### Story 2 — Fixing an SSRF-shaped gap in the job scrapers

**Source:** "Domain: Security" → "SSRF — following a scraped link
off-domain"

#### Situation

Four of my job-source scrapers follow links they scrape out of
third-party HTML to fetch each job's detail page, using
`urljoin(self.BASE_URL, href)` to resolve those links.

#### Task

I needed to make sure a scraped page couldn't make my scraper fetch an
arbitrary, attacker-controlled URL as if it were a real job posting.

#### Action

I found that `urljoin()` leaves an absolute `href` completely
untouched — so a scraped page containing an absolute link to another
host (a compromised ad, an embedded widget, a disguised attacker URL)
would previously be fetched exactly like a same-site job posting. I
added `WebSourceBase.is_same_site(url)`, which compares the resolved
URL's `netloc` against the source's own `BASE_URL` before any
detail-page fetch, and wired every one of the four source classes to
call it before following a link.

#### Result

A same-domain guard now sits in front of every detail-page fetch across
all four sources, covered by a dedicated regression test file
(`tests/test_source_domain_guard.py`) that checks both the accept and
reject cases per source.

#### Technical lesson

A general-purpose URL-joining function isn't a security boundary by
itself — `urljoin()` is correct and useful for what it does, but
"correct" and "safe against untrusted input" are different properties I
now have to check explicitly, not assume come bundled together.

#### Interview version (45–90s)

"I found a real SSRF-shaped gap in my own scraping code: every source
followed links pulled out of third-party HTML using `urljoin()`, which
happily passes an absolute URL straight through untouched. A scraped
page with a malicious absolute link would've been fetched exactly like a
real job posting. I added a same-domain check — comparing the resolved
URL's host against the source's own base URL — before any detail-page
fetch, across all four sources, and backed it with a dedicated test file
that checks both accept and reject cases. The lesson I took from it: a
function being 'correct' for parsing URLs doesn't make it safe against
untrusted input — those are two different questions I now check
separately, by habit."

### Story 3 — The word-boundary matching bug hiding inside a second,
similar-looking one

**Source:** "Domain: Software Engineering" → "Word-boundary matching —
a real, findable bug and its fix"

#### Situation

My skill-matching logic needed to check whether a job posting mentions a
specific skill, without a naive substring check falsely matching "Java"
inside "JavaScript."

#### Task

Build word-boundary-correct matching for that case, then extend the same
underlying idea to a second, harder context — sentence-level text pulled
from real job postings, for the skill-gap feature.

#### Action

I built tokenization plus exact contiguous-token-sequence matching
instead of a substring check or a regex word-boundary hack, which solved
the Java/JavaScript case cleanly. But while building the skill-gap
feature specifically, I found a second, subtler version of the same bug
class: the normalizer I'd been reusing kept periods in its allowed
character set — harmless when matching a short skill string against a
whole text blob, but the skill-gap feature tokenizes real sentences
where a skill name is very often the last word before a period —
"...experience with Terraform." Keeping the period glued it onto the
token ("terraform."), which then silently never matched the alias
"terraform." I gave the skill-gap feature its own normalizer that strips
periods entirely, deliberately diverging from the otherwise-similar
shared one.

#### Result

Both bugs are covered by direct regression tests, and the two modules
now intentionally use slightly different normalization rules for
genuinely different input shapes — a documented design choice, not an
inconsistency.

#### Technical lesson

Tokenization isn't a solved problem you can copy-paste between two
similar-looking use cases without checking the actual shape of the
input text — "matching a skill string" and "matching a skill mentioned
mid-sentence" are different problems that happen to look alike.

#### Interview version (45–90s)

"I built exact-token-sequence matching so 'Java' wouldn't false-positive
match inside 'JavaScript' — straightforward tokenization instead of a
substring or naive regex check. But reusing that same normalizer for a
different feature — one that reads whole sentences straight out of real
job postings — surfaced a second, sneakier bug: the normalizer kept
periods, and a skill name is very often the last word before a period,
so 'experience with Terraform.' silently never matched the alias
'terraform' because the period glued onto the token. I gave that feature
its own normalizer that strips periods, on purpose, instead of reusing
the same one everywhere. It taught me that two similar-looking matching
problems can have genuinely different correct answers depending on the
actual shape of the input."

### Story 4 — Tracing a false "Interview" status back to a testing
process gap, not a code bug

**Source:** "Domain: Software Engineering" → "Testing philosophy" (the
manual-verification database-pollution incident)

#### Situation

A job appeared in my application tracker showing "Interview" status,
even though I hadn't actually submitted an application or reached that
stage for it.

#### Task

Figure out whether this was a real defect in the application — something
automatically or incorrectly changing a status — before assuming the
code itself was broken.

#### Action

Rather than guessing, I traced the only code path that changes an
application's status: `update_status()`, called only from one route,
only ever reached by an explicit user click. There was no code anywhere
that changed a status automatically. I then reviewed what I had actually
done during manual verification earlier in the session and found the
real cause: my own manual testing had called routes directly against the
real database instead of an isolated copy — unlike the automated test
suite, which always isolates via `tmp_path`. I found the exact polluted
rows, and — since it was real user data, even if self-caused — asked for
explicit confirmation before clearing them rather than deciding
unilaterally.

#### Result

The application code was proven innocent, the polluted data was cleared
with confirmation, and "any manual verification touching persistence
must use an isolated working directory" became a documented rule going
forward, matching what the automated suite already enforced.

#### Technical lesson

A test suite that isolates state (`tmp_path`, `monkeypatch.chdir`) only
protects you during automated runs — manual verification needs the exact
same discipline, or you can convince yourself the application is broken
when it's actually your own test process that made the mess.

#### Interview version (45–90s)

"I once found a job in my tracker sitting at 'Interview' status that I'd
never actually applied to. Instead of assuming a bug, I traced the only
code path that ever changes a status — one route, only reachable by an
explicit click — and proved nothing in the app changes status
automatically. The real cause was me: earlier manual testing had hit the
real database directly instead of an isolated copy, the way my automated
tests always do. I found the exact polluted rows, asked before clearing
real data even though I'd caused the mess myself, and turned it into a
standing rule: manual verification needs the same isolation discipline
as automated tests. It's one of the more honest process lessons I can
point to."

### Story 5 — Integrating a second matching pipeline without deleting
the first

**Source:** "Architecture at a glance" (the `_v2_match` stash /
`_rank_jobs()` ownership-check design)

#### Situation

I had built a second, cleaner search-and-matching pipeline (V2) alongside
an older, heavily hand-tuned one (V1) that the live dashboard still
depended on.

#### Task

Integrate V2 into the dashboard without deleting V1's working, more
elaborate scoring logic, and without the two systems silently
double-scoring or contradicting each other on the same job.

#### Action

Instead of picking a winner, I decided ownership of a job's displayed
score should be determined by where the job data actually came from, not
by re-checking a feature flag a second time at render time. When V2
successfully produces a job list, each `CanonicalJob` gets V2's own
computed match result stashed directly onto it (`job._v2_match`). A
single function, `_rank_jobs()`, checks whether every job in the list
carries that stash — if so, it presents V2's own score and reasons
directly, preserving V2's own ranking order, with no second scoring
pass; if not (V2 disabled, or V2 itself failed), it falls through to the
exact same, untouched legacy `JobMatcher` that predates V2 entirely.

#### Result

Both matchers remain fully independent and testable, the dashboard never
shows a score that doesn't match its own reasons, and I verified this
live through the real Flask dashboard, not just by reading the code —
confirming V2's own reason strings ("Target job title matched", etc.)
render correctly when V2 is the actual source.

#### Technical lesson

When two systems solve the same problem with genuinely different design
philosophies, the right integration point is often "whoever actually did
the work owns the presentation," not a forced merge or a coin-flip
choice between them — that keeps both systems honest and independently
debuggable.

#### Interview version (45–90s)

"When I built a second, cleaner matching pipeline, I didn't delete the
older one — it had real, hand-tuned logic the new one didn't replicate.
Instead I made ownership of the displayed score depend on where the job
data actually came from: when the new pipeline succeeds, I stash its own
computed match result directly onto each job object, and one function
checks whether every job in the list carries that stash before deciding
whether to present the new pipeline's own score and reasons, or fall
back to the completely untouched legacy matcher. That way the dashboard
never shows a score that doesn't match its own explanation, and I
verified it live through the actual running app, not just by reading my
own code."

---

## Known limitations — good, honest "what would you improve" material

Pulled directly from the current `docs/SECURITY.md`, `NEXT_TASKS.md`,
and `docs/PRODUCT_VISION.md` — these are real, currently-true gaps, not
hedging:

- **No CSRF protection** on state-mutating routes (`/save/<id>`,
  `/status/<id>/<status>`, `/delete/<id>` are plain `GET` with no
  token). Acceptable today because there's no authentication layer at
  all (single-user local tool); would need addressing before any
  multi-user or internet-facing deployment.
- **No true multi-visitor session isolation.** Every visitor to a
  shared deployment sees the one master `profiles/profile.json`'s
  results. CV upload itself *is* isolated/rate-limited/auto-cleaned, but
  the dashboard/search/skill-gap pages are not session-scoped. Fixing
  this for real would mean threading a session-scoped profile through
  nearly every route in `app/web/routes.py` — a genuinely large,
  cross-cutting change, correctly not attempted piecemeal.
- **Duunitori disabled, Tyomarkkinatori/Work in Finland return 0
  results** — see the Security section above; both are policy-blocked,
  not unsolved engineering problems.
- **CV tailoring is a full LLM rewrite per job**, not the lighter,
  deterministic "reorder a stable master CV" approach the original
  product spec describes — a real, acknowledged gap between the spec
  and what was actually built, left as-is deliberately rather than
  risking destabilizing a working, tested feature under time pressure.
- **Required-vs-nice-to-have skill classification is a heuristic**
  (hedge-phrase detection per sentence/section), not a structural parse
  of the posting — a posting phrased unusually will default every
  detected skill to "required."
- **Substring false positives possible in certification-name
  matching** — e.g. "Networking" can match inside "Cisco **Networking**
  Academy" (a training provider's name, not a certification). Accepted
  as the same class of tradeoff the matchers make elsewhere; fixing it
  properly would need real semantic understanding, not more regex.
- **Range-pinned, not hash-pinned, dependencies**, and **no CI
  pipeline** — `pytest` run locally before pushing is the only current
  gate.

### Questions you should be ready for

- "What's a limitation you're aware of but haven't fixed, and why not
  yet?" — Pick CSRF or session isolation. Explain the real cost of
  fixing it properly (session-scoped profile threading through nearly
  every route) rather than a one-line patch, and why that's a
  deliberate sequencing decision, not neglect.
- "How do you decide what's 'good enough' to ship vs. what needs
  fixing first?" — Use the CV-tailoring example: a real gap between
  spec and implementation, explicitly documented rather than silently
  claimed as done, with the reasoning for not rearchitecting it under
  time pressure stated plainly.

---

## Quick-reference numbers (all verified live against the current codebase)

| Fact | Verified value | How verified |
| --- | --- | --- |
| Automated test count | 219 passed, 0 failed | `pytest -q --basetemp=<dir>` run directly |
| Test files | 43 | `ls tests/*.py` |
| `SKILL_CATALOG` entries | 46 | `len(SKILL_CATALOG)` |
| `CAPABILITY_GRAPH` entries | 17 | `len(CAPABILITY_GRAPH)` |
| Career tracks | 7 | `len(CAREER_TRACKS)` |
| Profile skills | 17 | `profiles/profile.json` |
| Profile target titles | 17 (13 English + 4 Finnish) | `profiles/profile.json` + `docs/MATCHING_AND_RANKING.md` |
| Profile target locations | 4 | `profiles/profile.json` |
| Excluded title terms (V2) | 29 | `JobMatcher.EXCLUDED_TITLE_TERMS` |
| Geo-normalizer: Finland terms | 23 | `geo_normalizer._FINLAND_TERMS` |
| Geo-normalizer: Europe entries | 36 | `geo_normalizer._EUROPE_COUNTRIES` |
| Landed commits this session | 6 (`3072417` → `c2e95fa`) | `git log --oneline` |
| Runtime LLM provider | Local Ollama only, zero hosted APIs | `requirements.txt`, direct grep |
| LLM call sites (runtime) | 4 route families: resume, cover letter, CV extraction, interview prep, plus project coaching | `app/web/routes.py` |
| Modules with zero LLM dependency | matching/ranking, dedup, skill-gap, CV-strength, career profile/tracks, application readiness, hiring perspective | verified: none import `app.ai.llm` |

---

## A note on how to actually use this before an interview

Don't read this document cover to cover the night before and try to
recall it. Instead:

1. Pick the domain(s) the interview is actually for.
2. Open the specific files this guide points to and re-read them once,
   so the explanation is coming from your own understanding of the code,
   not from memorizing this document's phrasing.
3. Answer the "Questions you should be ready for" out loud, in your own
   words, before the interview — if you stumble, that's exactly the
   signal for what to re-read.
4. If asked something this guide doesn't cover, it's fine to say "let me
   think through that from what I remember of the code" and reason from
   first principles — that's a stronger signal than a memorized answer
   anyway.

---

## One-Page Interview Cheat Sheet

Review this section, and only this section, in the last two minutes
before walking in.

- **Problem:** Finnish job boards are fragmented, none explain *why* a
  posting fits a specific candidate, and manually tracking skill gaps
  across postings is easy to fall behind on.
- **Architecture:** Flask app; two coexisting search/match pipelines
  (V1 hand-tuned, V2 clean-architecture) — dashboard uses whichever one
  actually produced the job list; `SourceRunner` → `CanonicalJob`
  normalization → dual-signal dedup → geo filter → weighted `JobRanker`.
- **Technologies:** Python 3.10–3.12, Flask, `requests` + BeautifulSoup4
  (scraping), SQLite (persistence), local Ollama LLM (generation only),
  python-docx/PyMuPDF (documents), pytest (219 tests, 43 files).
- **My contribution:** Solo — architecture, all matching/dedup/security
  logic, the zero-LLM career-intelligence layer (six-tier evidence model,
  career tracks, application readiness, hiring perspective), and every
  fix described in this document, verified directly against the code and
  live test runs, not assumed.
- **Hardest problem:** Discovering my largest job source
  (`DuunitoriSource`) had been violating its own `robots.txt` policy for
  an entire session, after it had already shipped and been re-verified
  multiple times — and disabling it anyway, at a real cost.
- **Important engineering decision:** Ownership of a job's displayed
  score is decided by where the job data actually came from
  (`job._v2_match` stashed by V2, checked by `_rank_jobs()`), not by a
  second feature-flag check — lets both matchers stay independent and
  fully working rather than forcing a merge or deleting one.
- **Security issue:** Fixed an SSRF-shaped gap — `urljoin()` passed
  absolute scraped URLs through untouched, so a malicious link could be
  fetched as if it were a same-site job posting; fixed with a
  same-domain guard (`is_same_site()`) before every detail-page fetch,
  across all four scrapers.
- **Testing:** 219 passing tests, zero live network calls, zero Ollama
  calls in the suite; persistence tests always use an isolated database
  after a real incident where manual testing polluted the live one.
- **Result:** A working tool I actually use for my own job search —
  transparent scoring, real gap-to-certification-to-project
  recommendations, gated interview prep, and (this session) a full
  career-intelligence layer, all shipped as six reviewed, individually
  tested commits.
- **Next improvement:** CSRF protection on the three state-mutating
  routes (`/save`, `/status`, `/delete`) — the clearest, most defensible
  "what would you fix next."
- **Technical terms I should remember:** `CanonicalJob`, `dedupe_key()` /
  `canonical_url()`, word-boundary (exact-token) matching, `_v2_match`
  stash, `SourceRunner`, `robots.txt` `Disallow`/`Crawl-delay`,
  `is_same_site()` (SSRF guard), zero-LLM design boundary, six-tier
  evidence model (KNOWS/STUDIED/PRACTICED/CERTIFIED/
  PROFESSIONAL_EXPERIENCE/BUILT), application-readiness five tiers,
  ATS/HR/Technical-Manager hiring perspective.
