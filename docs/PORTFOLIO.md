# Portfolio Value

## What this project demonstrates

### Python

A multi-module application spanning web scraping, data normalization,
matching algorithms, a web dashboard, document generation, and a test
suite - not a single script. Uses dataclasses, environment-based
configuration, and clean separation between deterministic logic and
external-service calls (LLM, HTTP).

### Flask

A working multi-route web application (dashboard, search, per-job
actions, application tracking) with a Blueprint-based structure and a
deliberate debug-mode security default.

### Web scraping / data ingestion

Four real-world scrapers against four different Finnish job boards, each
with a different underlying content model discovered through direct
investigation (Duunitori/Jobly: server-rendered HTML with JSON-LD;
Tyomarkkinatori/Work in Finland: client-side-rendered SPAs). Includes
JSON-LD structured-data parsing, HTML fallback extraction, and a
same-domain safety check on every followed link.

### Data normalization

A canonical job model (`CanonicalJob`) that different sources' raw output
is converted into: consistent title/company/location casing, Finnish
legal-suffix (`Oy`/`Oyj`) stripping, skill/tag deduplication that
preserves first-seen spelling, and safe ISO-date parsing.

### Deduplication

Two independent deduplication strategies exist in the codebase (V2's
key-based approach; V1's three-tier source-id/URL/content-fingerprint
approach), each with an explicit, documented rationale for how
conservative they are and why (see `docs/ARCHITECTURE.md`).

### Search / matching algorithms

Two matchers, each with weighted multi-signal scoring (title, skills,
location, seniority), word-boundary text matching that specifically
avoids substring false positives (`"Java"` vs. `"JavaScript"`), and
human-readable score explanations. Verified with live data, not just unit
tests in isolation.

### Testing

57 tests, fixture/mock-backed, zero live network calls or LLM
dependencies in the automated suite. Several tests are direct regression
tests written *because* a specific bug was found and root-caused live
(e.g. `test_profile_integrity.py`, `test_duunitori_source.py`,
`test_routes_v2_job_ids.py`, `test_robots_txt_compliance.py`) - not
generic coverage, but tests that encode "this exact failure must not
happen again" with the reasoning in
the docstring.

### Git / GitHub

A commit history with meaningful, scoped commits, each explaining the
*why* behind a fix (root cause, not just the change), pushed to a real
GitHub remote on a feature branch.

### Secure development practices

A concrete, evidence-based security pass (not a checklist exercise):
found and fixed an SSRF-adjacent link-following bug, a Flask debug-mode
default, and an unbounded external request that could hang a web
request - each verified live, not assumed. Documented what was checked
and came back clean (XSS, secrets, subprocess/eval usage) alongside what
was found and fixed.

### Cybersecurity domain relevance

The project's own subject matter (matching a cybersecurity candidate to
security-engineering roles) overlaps directly with its own security
practices - the `docs/SECURITY.md` document was written to double as
interview material for the domain the tool is built for.

### AI integration, used appropriately

A local-only LLM integration (no hosted API dependency) used narrowly for
language generation (resume/cover letter text), explicitly *not* for
matching or ranking, with hallucination-prevention instructions in the
prompts and a hard, tested timeout so an unavailable/slow model degrades
gracefully instead of breaking the application.

### Software architecture / honest technical debt

The two matchers (V1, V2) weren't silently resolved by picking a winner
and deleting the other - the gap was documented first (which one
actually drove the dashboard, and why), then closed with a small,
targeted integration: the dashboard now uses whichever matcher actually
produced the job list, decided by data ownership (a stashed match result
on the job object) rather than by re-checking a feature flag or
duplicating scoring logic. What V2 still doesn't replicate from V1
(Finnish-language title terms, an exclusion list, experience-requirement
penalties) is called out explicitly as a known, currently-live behavior
difference rather than swept under the "V2 is done" label - the kind of
judgment call a senior engineer documents rather than either ignores or
claims is fully resolved before it is.

### Error handling

Every job source isolates its own failures (a broken source returns an
empty list, logged, rather than crashing the whole search); AI generation
failures return a clear 503 instead of hanging or crashing; profile
loading falls back safely (though that fallback being *silent* was itself
a bug found and fixed this session - see `docs/SECURITY.md`).

## How to explain this project in an interview

**What problem does it solve?**
"Finnish job boards are fragmented and don't explain why a posting is a
good fit. I built a tool that collects postings from multiple sources,
scores them against my actual skills and target roles with a transparent,
weighted algorithm, and can draft a tailored resume and cover letter for
whichever job I pick."

**Why did you build a V2 search architecture instead of extending V1?**
"V1 mixed scraping, deduplication, and scoring together per-source, which
made it hard to reason about or test in isolation. V2 introduces a
canonical job model that every source normalizes into, so
normalization/dedup/matching/ranking are each independently testable and
source-agnostic. I kept V1's matcher in place rather than deleting it,
because it already had years of informal tuning - Finnish-language title
terms, an exclusion list, seniority-specific penalties - that V2's
matcher doesn't have yet. That's an explicit interim state, documented,
not an accident."

**How did you decide who owns ranking when both a V1 and a V2 matcher
exist?**
"I traced the actual data flow first instead of guessing: V2 computed
its own score and then the dashboard silently discarded it and re-scored
through V1 every time, regardless of whether V2 had succeeded. The fix
wasn't to delete either matcher - it was to stop throwing V2's result
away. Now the job object carries whichever matcher actually produced it,
and the dashboard reads that instead of re-deciding based on a flag. If
V2 search fails for any reason, the exact same V1 fallback that existed
before still runs, untouched. I proved this with tests that use reason
text only V2's matcher produces, and a job description that V1 and V2
would score very differently - so a passing test only makes sense if
V2's real output reached the page."

**How does the search pipeline work?**
"Each source scrapes its own site into a common `CanonicalJob` shape, one
failure doesn't stop the others, results get deduplicated by an external
ID when available or by normalized title/company/location otherwise, then
scored against my profile on title match, skill overlap, location, and
seniority."

**How do you handle duplicate jobs?**
"Two independent strategies, both deliberately conservative - I'd rather
show a near-duplicate than silently merge two genuinely different
postings that happen to share a title. I found a real example of that
tradeoff during testing (two Jobly listings for what's probably the same
role, with reordered title text) and documented it as a known limitation
instead of reaching for a fuzzy-match fix that could cause false merges
elsewhere."

**How do you handle failed sources?**
"Every source's `.search()` catches its own exceptions and returns
whatever it collected; the runner catches anything that slips through.
Two of my four sources currently return zero results - not because
they're broken, but because their job listings are loaded by
client-side JavaScript my static scraper can't execute. I verified that
directly rather than trusting the previous 'TLS error' assumption in the
handoff notes, which turned out to be wrong."

**Why didn't you disable TLS verification?**
"Because it wasn't actually a TLS problem - I re-verified from scratch and
the real cause was JS-rendered content. Disabling verification would have
been fixing the wrong thing while creating a real vulnerability."

**Where is AI used?**
"Only for resume and cover-letter text generation, via a local Ollama
model - never for matching or ranking, which need to be deterministic and
explainable. I also found and fixed a real bug where that AI call had no
timeout and could hang a web request indefinitely."

**How did you test it?**
"63 automated tests, all mock/fixture-backed - no live network calls or
LLM dependency in the suite. Several are regression tests I wrote
specifically after finding and root-causing a real bug live (a corrupted
profile file, a scraper reading the wrong title field, broken dashboard
links, a saved-jobs duplicate bug, a silently-discarded V2 score), each
with a docstring explaining the failure it prevents - and each one I
verified against the real, live dashboard afterward, not just the test
suite in isolation."

**What would you improve next?**
"Get real data out of Duunitori and Tyomarkkinatori - both need the
site's explicit permission or an official API before I'd revisit them;
I'm not going to route around a `robots.txt` disallow just to get more
results. Build the review-to-profile merge step for the CV upload
feature - it currently stops at showing you what it extracted,
deliberately, rather than silently rewriting your profile. And if I ever
want full parity between the two matchers, port V1's tiered title
scoring and weighted skills into V2 too - though that's a deliberate
design-philosophy decision, not just a missing feature, so I'd want a
real reason before doing it."

**How did you decide what to port from V1 into V2's matcher, and what
to leave out?**
"I ported three things that were clear gaps, not design choices:
Finnish-language title recognition, an exclusion list for obviously
unrelated roles, and an experience-requirement penalty. But I didn't
copy the Finnish terms into V2's Python code - V1 hardcodes them as a
constant, which is exactly the 'personal data baked into source code'
pattern this project avoids everywhere else. V2's title matching has no
hardcoded vocabulary at all; it matches against whatever the profile
supplies. So the right port was adding those Finnish terms to the
profile's target_titles, not writing a parallel hardcoded list in
matcher code. I left out V1's tiered title scoring and weighted skills
entirely - those aren't gaps, they're a different scoring philosophy,
and re-deriving someone's hand-tuned weights inside a second matcher
without the evidence that produced them would just be guessing."

**Tell me about a mistake you caught in your own work.**
"Duunitori was the largest of my job sources - the one I'd fixed and
re-verified multiple times earlier in the same session. I never checked
its `robots.txt`. While investigating a completely different source
(Tyomarkkinatori, where I'd found a working internal API but its
`robots.txt` disallowed it), I decided to check the others too, purely
for consistency. Duunitori's `robots.txt` disallows the generic
crawler group entirely, with named exceptions for specific bots -
Googlebot, Bingbot, and so on - that my scraper's spoofed browser
User-Agent didn't match. It had been running against that policy the
whole time. I didn't quietly patch it and move on - I stopped, explained
exactly what I'd found and why it mattered, and let the person I was
working with decide whether to disable it, since that's a real product
tradeoff (it was roughly half the job coverage), not just a code fix.
They chose to disable it. I think that sequence - catching it, not
hiding it, and not deciding unilaterally on something with that much
impact - is the part worth talking about, more than the bug itself."
