# Data Sources

Four source classes live in `app/search/sources/web_sources.py`, share a
`WebSourceBase` (shared `requests` session config, TLS verification always
on, per-request 20s timeout, a same-domain guard on any link the scraper
follows). Only three are currently **registered** and actually run - see
"Duunitori" below for why. Every source's `.search()` method catches its
own exceptions internally and returns whatever it collected (possibly an
empty list) rather than raising - `SourceRunner` additionally catches
anything that slips through, so one broken source never takes down the
others.

**`robots.txt` compliance is checked per source, not assumed.** This
became a session-defining finding - see "Duunitori" below - and the
policy going forward is: before registering (or re-registering) any
source, fetch and read its `robots.txt` against the exact paths the
scraper will hit, for the exact user-agent group the scraper's request
will actually match (not just whichever group looks most permissive).

## Duunitori - implemented, tested, **disabled** pending compliance

**Collection** (code unchanged, just not registered - see below): for
each of 15 hardcoded search terms, fetches the listing page, extracts
links matching `/tyopaikat/tyo/`, filters by `title_is_relevant()` (a
substring check against ~40 security/IT job title patterns), then
fetches each detail page for the real title/company/location/description
via JSON-LD (`application/ld+json`, schema.org `JobPosting`).

**Bug found and fixed earlier this session**: Duunitori's own JSON-LD
`title` field does not contain the posted job title - it contains an
internal occupation-taxonomy slug (e.g. `"tietoturva-asiantuntija"` for a
posting actually titled "Staff Security Engineer"). Confirmed by fetching
a live detail page and comparing the JSON-LD `title` key against the
page's `<h1>`. `parse_job_detail()` now prefers `<h1>`. Regression test:
`tests/test_duunitori_source.py`.

**Disabled, later the same session, once `robots.txt` was actually
checked**: `duunitori.fi/robots.txt` states:

```
User-agent: *
Disallow: /

User-agent: Googlebot
Disallow: 
Disallow: /api/
...
(and similarly permissive groups for Bingbot, AhrefsBot, Baiduspider,
DuckDuckBot, Slurp, Twitterbot, YandexBot, ChatGPT-User, GPTBot,
Mediapartners-Google, facebookexternalhit, Claude-User, Claude-SearchBot)
```

`DuunitoriSource` sends a spoofed generic browser `User-Agent`
(`WebSourceBase.HEADERS`), not one of those specifically-named,
allowlisted crawlers. Per the `robots.txt` standard, a crawler that
doesn't match a named group falls back to the `*` group - `Disallow: /`
- everything. This scraper had been running (and was fixed and
re-verified multiple times) in violation of that policy for the entire
session, because `robots.txt` was never checked until a later
investigation into Tyomarkkinatori's own `robots.txt` prompted checking
the others too.

**Action taken**: `DuunitoriSource` was unregistered from both
`app/search/v2/registry.py`'s `SOURCE_REGISTRY` and
`app/search/manager.py`'s `SearchManager.searchers` - it no longer runs
in either V1 or V2 search. The class itself, its title-extraction fix,
and its tests (`tests/test_duunitori_source.py`,
`tests/test_source_domain_guard.py`) are all untouched and still pass;
only its *registration* was removed, specifically so re-enabling it
later is a one-line change once the underlying question is resolved.
Regression tests confirming it's excluded:
`tests/test_robots_txt_compliance.py`.

**This was a user decision, not a unilateral one.** The finding was
reported directly, with the real tradeoff stated plainly (Duunitori had
been the largest single source of collected jobs), and disabling it was
the option chosen. Confirmed again in a follow-up instruction: keep it
disabled, and do not scrape a source when its `robots.txt` explicitly
disallows generic crawlers.

**Policy: no circumvention.** Spoofing a different crawler identity to
match one of `robots.txt`'s named allowlist entries, switching the
User-Agent while still not being that crawler, or scraping the disallowed
paths anyway are all out of scope - not evaluated as options, not
partially implemented, not left as a "quick fix" for later. `robots.txt`
disallowing this scraper's user-agent group is treated the same way this
project treats a TLS failure: not something to route around.

**Possible future resolution** (either of these, not a code change on its
own):

1. **Obtain Duunitori's explicit permission** - contact them directly
   about their crawling policy for this kind of aggregation, and get an
   actual go-ahead (ideally reflected in an updated `robots.txt` or a
   written agreement), before re-enabling anything.
2. **Use an official/approved API**, if Duunitori offers one for job
   aggregators - this would be a distinct integration (proper API
   credentials, its own terms of use), not the scraper this project
   already has.

Only once one of those is actually in place: add the source back to both
registries and re-verify live before considering it "working" again.

## Jobly - working, verified live, now `Crawl-delay`-compliant

**Collection**: same pattern Duunitori used (per-search-term listing
page, JSON-LD detail-page parsing), against `jobly.fi`. No
title-extraction bug was found here - spot-checked detail pages returned
real, specific titles ("OT Cybersecurity Engineer", "Cloud Security
Architect", etc.) directly from JSON-LD.

**`robots.txt`**: standard Drupal boilerplate, `Crawl-delay: 10` for the
generic `*` group, with `Disallow` limited to system/admin paths
(`/admin/`, `/user/login/`, etc.) - none of which are what
`JoblySource` scrapes (`/tyopaikat/`, `/tyopaikka/`). The job-listing and
detail pages this project fetches are not disallowed.

**Found and fixed alongside the Duunitori investigation**: the scraper
was not honoring `Crawl-delay: 10` at all - no pause between requests.
`JoblySource.get_page()` now sleeps 10 seconds after every request
(overriding `WebSourceBase.get_page()`), so a full search (14 search
terms plus one detail-page fetch per matching job) now takes several
minutes instead of seconds - a deliberate, accepted cost of compliance,
not a bug. Regression test (mocked, doesn't actually sleep 10s in the
suite): `tests/test_robots_txt_compliance.py`.

**Status**: working. A live search (before the crawl-delay change)
collected 17 jobs.

**Known limitation - possible same-source near-duplicates**: during live
testing, two Jobly postings appeared with reordered but near-identical
titles ("IT Systems and Cyber Security Specialist, Forcit Defence,
Tampere" vs. "FORCIT Defence, IT Systems and Cyber Security Specialist"),
at two different URLs. `CanonicalJob.dedupe_key()` requires an exact
normalized title match when there's no external id, so these were not
merged. This is a deliberate tradeoff (see `docs/ARCHITECTURE.md`) rather
than an oversight - fuzzy title matching would risk merging genuinely
different postings.

## Tyomarkkinatori - returns 0 jobs; root cause identified, not a TLS problem

The previous handoff documentation described this as a TLS certificate
verification failure. That was re-investigated from scratch this session:

- A direct `requests.get()` call to the search URL, using this project's
  actual dependency stack (`requests` + `certifi`), **succeeds** (`200`,
  ~160KB of HTML). No TLS error was reproducible through the code path
  this project actually uses.
- A *different* check - `ssl.create_default_context()` with no explicit
  CA bundle, which falls back to the OS certificate store instead of
  `certifi` - does fail with a self-signed-certificate error in this
  development sandbox. That's a property of the sandbox's OS trust store,
  not of `tyomarkkinatori.fi`, and it's not the code path
  `TyomarkkinatoriSource` uses.
- The **actual** reason `TyomarkkinatoriSource.search()` returns 0 jobs:
  the fetched HTML page has 255 `<a>` tags, none of them job postings -
  they're all navigation/footer/language-switcher links. There is no
  `__NEXT_DATA__` or embedded JSON blob either. The job listings on this
  page are loaded by client-side JavaScript after page load (an API call
  the static HTML doesn't reveal), which `requests`+BeautifulSoup cannot
  execute.

**Status**: known limitation - and, as of this session, a deliberately
*not*-taken option, not an unexplored one.

Using a real browser (Chrome, via the `claude-in-chrome` tool) to inspect
actual network traffic on the search page found the site's own internal
JSON API: `POST /api/jobpostingfulltext/search/v2/search`. It's
unauthenticated and, called with a minimal body
(`{"query": "<term>", "paging": {"page": 0, "pageSize": N}}`), returns
real, structured job postings - title, employer, application URL,
municipalities, publish date - genuinely different companies from
Duunitori/Jobly (verified live: Comatec Mobility Oy, Academic Work
Finland Oy, Landis+Gyr EMEA). A working `TyomarkkinatoriSource`
implementation against this endpoint was built and verified end-to-end
(4 real jobs, correctly matched and ranked by V2).

**It was not shipped.** `tyomarkkinatori.fi/robots.txt` explicitly
states:

```
User-agent: *
Disallow: /api/
```

That covers the exact endpoint this would have used. The API being
technically public and unauthenticated doesn't override the site
operator's explicitly stated crawling policy - `Disallow: /api/` is a
direct signal that automated access to that path isn't wanted, and
respecting `robots.txt` is the standard, expected practice here,
consistent with this project's broader security/ethics stance (no
`verify=False`, no bypassing access controls) even though technically
nothing would have broken. The implementation was reverted rather than
committed.

Note that `robots.txt` does **not** disallow the search *page* itself
(`/henkiloasiakkaat/avoimet-tyopaikat`) - only `/api/` - so the current
HTML-scraping approach (which returns 0 results because the page's data
loads client-side) remains the compliant option; it simply doesn't work
without executing JavaScript.

**If this is worth pursuing further**: the compliant path is asking
Tyomarkkinatori directly whether a public API/data-sharing agreement
exists for aggregators (many public employment services do offer this
through an official channel), not scraping `/api/` against its stated
policy, and not switching to a headless browser against the page itself
either, since that would still be automated access to a resource the
operator has partially fenced off. This needs a human decision, not a
unilateral code change - logged in `NEXT_TASKS.md`.

## Work in Finland - returns 0 jobs; root cause identified

**Investigation**: The open-jobs page fetches successfully (`200`, ~2MB of
HTML) and *does* contain a Next.js `__NEXT_DATA__` JSON blob - unlike
Tyomarkkinatori, this site does server-render its initial data. But that
blob's `pageProps.page` object is a generic Magnolia CMS content tree
(`"mgnl:template"` keys, nested `"@nodes"`), not a list of job postings.
The actual job listings are rendered by a widget/component that fetches
them client-side after hydration, which is outside what the embedded
`__NEXT_DATA__` payload contains.

**Status**: known limitation, same underlying symptom as Tyomarkkinatori
(client-side-rendered job data) - but the likely value of fixing it is
low, found by inspecting real browser network traffic: the open-jobs
page's requests for company logo images resolve directly to
`www.jobly.fi/sites/default/files/...` - i.e. the "Open jobs" widget
appears to be **backed by Jobly's own listings**, not an independent job
source. This project already scrapes Jobly directly (`JoblySource`), so
a working Work in Finland scraper would likely surface largely redundant
postings rather than new coverage. Not confirmed with full certainty
(would need to compare a complete job-for-job listing, not just observed
asset URLs), but strong enough evidence to deprioritize building a
separate scraper for this source until/unless that's checked more
rigorously and shows meaningful non-overlap.

## Source-level diagnostics

`SourceRunner.run_source()` returns a `SourceRunResult(source, jobs,
error)` per source and logs `"[<source>] normalized N jobs"` /
`"[<source>] source failed: <error>"` for each one. There is currently no
persisted or dashboard-visible source-status report beyond these log
lines - a reasonable next step if source reliability becomes a recurring
debugging need (see `NEXT_TASKS.md`).

## Compliance posture is unaffected by how the app is deployed

Exposing the Flask app itself via a tunnel for a small group of testers
(see `docs/SECURITY.md`) doesn't change anything about how these
scrapers behave - they still run from wherever the Python process is
hosted, still send the same `robots.txt`-checked requests, and still
respect the same `Crawl-delay`/`Disallow` rules regardless of who's
looking at the resulting dashboard. Duunitori stays disabled and
Tyomarkkinatori's `/api/` path stays unused under a tunnel exactly as
they do locally - there is no scenario in which deploying this app
differently would make circumventing `robots.txt` acceptable.
