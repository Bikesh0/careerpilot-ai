# Data Sources

All four sources live in `app/search/sources/web_sources.py`, share a
`WebSourceBase` (shared `requests` session config, TLS verification always
on, per-request 20s timeout, a same-domain guard on any link the scraper
follows), and are registered for the V2 pipeline in
`app/search/v2/registry.py`. Every source's `.search()` method catches its
own exceptions internally and returns whatever it collected (possibly an
empty list) rather than raising - `SourceRunner` additionally catches
anything that slips through, so one broken source never takes down the
others (verified: a live run with Tyomarkkinatori/Work in Finland
returning 0 jobs still produced 45 jobs from the other two sources).

## Duunitori - working, verified live

**Collection**: For each of 15 hardcoded search terms, fetches the listing
page, extracts links matching `/tyopaikat/tyo/`, filters by
`title_is_relevant()` (a substring check against ~40 security/IT job title
patterns), then fetches each detail page for the real title/company/
location/description via JSON-LD (`application/ld+json`, schema.org
`JobPosting`).

**Bug found and fixed this session**: Duunitori's own JSON-LD `title`
field does not contain the posted job title - it contains an internal
occupation-taxonomy slug (e.g. `"tietoturva-asiantuntija"` for a posting
actually titled "Staff Security Engineer"). This was confirmed by fetching
a live detail page and comparing the JSON-LD `title` key against the
page's `<h1>`. Trusting the JSON-LD field meant most Duunitori postings
scored `title_score = 0` in the V2 matcher even for genuinely relevant
roles. `parse_job_detail()` now prefers `<h1>` and only falls back to the
JSON-LD field if no heading is present. Regression test:
`tests/test_duunitori_source.py`.

**Status**: working. A live search collected 35 jobs across the 15 search
terms.

## Jobly - working, verified live

**Collection**: same pattern as Duunitori (per-search-term listing page,
JSON-LD detail-page parsing), against `jobly.fi`. No title-extraction bug
was found here - spot-checked detail pages returned real, specific titles
("OT Cybersecurity Engineer", "Cloud Security Architect", etc.) directly
from JSON-LD.

**Status**: working. A live search collected 17 jobs.

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

**Status**: known limitation. Fixing this for real requires either
reverse-engineering the site's internal API (fragile, can break without
notice) or driving a real/headless browser (Playwright/Selenium - neither
is currently a project dependency; `app/automation/playwright_bot.py`
exists as an empty placeholder file and is not wired to anything). Per
this project's own rule against introducing dependencies without a
concrete, scoped reason, that decision is left to a future task rather
than made unilaterally here.

## Work in Finland - returns 0 jobs; root cause identified

**Investigation**: The open-jobs page fetches successfully (`200`, ~2MB of
HTML) and *does* contain a Next.js `__NEXT_DATA__` JSON blob - unlike
Tyomarkkinatori, this site does server-render its initial data. But that
blob's `pageProps.page` object is a generic Magnolia CMS content tree
(`"mgnl:template"` keys, nested `"@nodes"`), not a list of job postings.
The actual job listings are rendered by a widget/component that fetches
them client-side after hydration, which is outside what the embedded
`__NEXT_DATA__` payload contains.

**Status**: known limitation, same underlying cause as Tyomarkkinatori
(client-side-rendered job data) and the same fix path (a real API
integration or headless browser, not currently a project dependency).

## Source-level diagnostics

`SourceRunner.run_source()` returns a `SourceRunResult(source, jobs,
error)` per source and logs `"[<source>] normalized N jobs"` /
`"[<source>] source failed: <error>"` for each one; `IngestionPipeline`
(unused/superseded, see git history) had an equivalent `SourceResult`.
There is currently no persisted or dashboard-visible source-status report
beyond these log lines - a reasonable next step if source reliability
becomes a recurring debugging need (see `NEXT_TASKS.md`).
