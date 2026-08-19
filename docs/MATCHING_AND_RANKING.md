# Matching and Ranking

CareerPilot AI has **two** independent matchers, described separately
below. `docs/ARCHITECTURE.md`'s "The V1/V2 split" explains why both exist
and **which one actually drives the dashboard for a given request**: V2's
own matcher/ranker when V2 search succeeds (the normal case with
`CAREERPILOT_SEARCH_V2=1`), the V1 matcher as a genuine fallback when V2
is disabled or its search/ranking itself fails. This isn't a permanent
50/50 split by design - it's the result of a deliberate integration that
gives V2 ownership of its own output without deleting V1's more elaborate
logic. Three specific gaps identified when that integration first shipped
(Finnish-language titles, an exclusion list for unrelated roles, an
experience-requirement penalty) have since been closed - see "Ported from
V1" below; the remaining differences are in "Known edge cases and
limitations."

## V2 matcher (`app/search/v2/matching/`)

### Inputs

- `profile_skills`: `profiles/profile.json["skills"]` (17 entries)
- `target_titles`: `profiles/profile.json["target_titles"]` (17 entries -
  13 English plus 4 Finnish, added this session; see "Ported from V1"
  below)
- `target_locations`: `profiles/profile.json["target_locations"]` (4 entries)

### Skill normalization and word-boundary matching

`normalize_skill()` (`app/search/v2/matching/signals.py`) lowercases,
expands `&` to `and`, collapses `/`, `_`, `-` to spaces, strips anything
that isn't `a-z0-9+#. `, and collapses whitespace. `_contains_term()` then
tokenizes both the searched text and the term on whitespace and checks for
an exact, contiguous token-sequence match - not a substring match. This is
what makes `"Java"` not match `"JavaScript"`: `"javascript"` is a single
token after normalization, and it never equals the token `"java"`.
`"C++"` and `"C#"` survive normalization intact (`+` and `#` are in the
allowed character set) and are distinguished from bare `"C"`.
`tests/test_v2_matching_regressions.py` covers this directly.

`find_skill_matches(job, profile_skills)` builds one combined text blob
from the job's title, description, company, location, skills, and tags,
then checks each profile skill against it with `_contains_term`.

### Title and location matching

`title_matches()`/`location_matches()` use the same normalized
word-boundary check against the job's `title`/`location` field only (not
the full text blob).

### Seniority detection

`JobMatcher._detect_seniority()` (`app/search/v2/matching/matcher.py`)
checks the job title first, then falls back to the description at half
weight, against an ordered term list (director > manager > architect >
lead > senior > mid > junior > entry > intern). Each level maps to a fixed
score:

| Level | Score |
| --- | --- |
| intern | 100 |
| junior / entry | 90 |
| unspecified | 70 |
| mid | 60 |
| senior | 35 |
| lead | 20 |
| manager / architect | 10 |
| director | 5 |

### Score formula

```
score = title_score   * 0.40
      + skill_score    * 0.35
      + location_score * 0.15
      + seniority_score * 0.10
      - experience_requirement_penalty
```

- `title_score`: 100 if any target title matches, else 0 (binary, not
  partial credit).
- `skill_score`: `matched_skills / total_profile_skills * 100`.
- `location_score`: 100 if any target location matches, else 0.
- `seniority_score`: from the table above.
- `experience_requirement_penalty`: see "Ported from V1" below - not
  part of the weighted sum, subtracted afterward, same as V1.

Before any of this runs, the job's title is checked against
`EXCLUDED_TITLE_TERMS` - a match short-circuits scoring entirely (see
"Ported from V1").

The result is clamped to `[0, 100]` and rounded to 2 decimals. Human
-readable `reasons` are generated alongside the score (e.g. "Target job
title matched", "Matched 6 profile skills", "junior seniority is a good
fit", "4 profile skills not found").

### Ported from V1

Three specific V1-only behaviors were ported into V2's matcher this
session, closing the gap identified when V2 first took over dashboard
presentation (see "The V1/V2 split" in `docs/ARCHITECTURE.md`):

- **Finnish-language title terms** - ported as **data, not code**. V1
  hardcodes Finnish terms (`"tietoturva-asiantuntija"`,
  `"kyberturvallisuusasiantuntija"`, etc.) directly into its
  `PRIMARY_TITLES` Python constant. V2's title matching has no hardcoded
  vocabulary of its own - it matches against whatever `target_titles` the
  profile supplies - so the equivalent fix is adding those same Finnish
  terms to `profiles/profile.json["target_titles"]` (4 entries added:
  `"Tietoturva-asiantuntija"`, `"Tietoturva-analyytikko"`,
  `"Kyberturvallisuusasiantuntija"`, `"Kyberturvallisuus"`) rather than
  hardcoding them into `app/search/v2/matching/matcher.py`. This keeps
  the profile as the single source of truth for candidate-specific data
  (personal target titles are not a matcher-code concern) rather than
  reintroducing the anti-pattern V2 was built to avoid. Test:
  `tests/test_profile_integrity.py::test_profile_target_titles_include_finnish_terms`.
- **`EXCLUDED_TITLE_TERMS`** - ported as **code**, verbatim from V1's
  list (marketing, sales, HR, design, legal, etc. - not profile-specific,
  so it belongs in `JobMatcher`, not the profile). A title match
  short-circuits `score_job()`: the job gets `score=0.0`,
  `MatchResult.excluded=True`, and a specific reason string, without
  computing skill/location/seniority at all. `JobRanker.rank()` then
  drops any excluded job from the ranked output entirely - not merely a
  low score, a real exclusion, matching V1's `continue`-and-skip
  behavior. Tests: `tests/test_v2_matching_regressions.py::test_excluded_title_terms_score_zero_and_are_flagged`,
  `::test_job_ranker_drops_excluded_jobs_entirely`.
- **Required-experience penalty** - ported as **code**, verbatim
  thresholds from V1's `_experience_requirement_penalty` (7+ years: -20,
  5+: -15, 4+: -11, 3+: -7, 2+: -3), driven by a new
  `extract_required_experience_years()` signal (same regex patterns as
  V1's `_extract_required_experience`) run against the job's combined
  text. Subtracted from the weighted score before the final `[0, 100]`
  clamp. Tests:
  `tests/test_v2_matching_regressions.py::test_extract_required_experience_years_finds_the_highest_figure`,
  `::test_experience_requirement_penalizes_the_score`.

**Not ported, by deliberate scope decision** (see "Known edge cases and
limitations" below for why): V1's tiered title-category scoring
(`PRIMARY`/`SECONDARY`/`RELATED`/generic-security-term), weighted skill
importance (`SKILL_WEIGHTS`), the skill alias table, and V1's much
steeper seniority mismatch penalties. These are genuine design
differences between the two matchers' philosophies, not gaps - see
`docs/ARCHITECTURE.md`'s "Why two matchers exist instead of one."

### Ranking / tie-breaking

`JobRanker.rank()` sorts by
`(score, title_score, skill_score, location_score, posted_at_timestamp)`,
all descending, and assigns a sequential `rank` starting at 1. Using a
numeric timestamp (0.0 for missing `posted_at`) rather than comparing a
`datetime` against a fallback string was a deliberate fix during this
session - the previous tie-break compared `datetime` and `""` directly,
which raises `TypeError` in Python 3 the moment two jobs with the same
score have mixed presence/absence of `posted_at`. See
`tests/test_v2_ranking.py::test_rank_does_not_crash_when_posted_at_is_mixed_none_and_datetime`.

### Verified live results

After fixing `profiles/profile.json` (it was invalid JSON, causing the app
to silently match against an *empty* profile - see `docs/SECURITY.md`/git
history) and a Duunitori title-extraction bug (see `docs/DATA_SOURCES.md`),
a live V2 search against the real profile produced a top-20 list
consisting entirely of genuinely relevant, correctly-titled security/cloud
roles ("Staff Security Engineer", "Cyber Security Engineer", "Security
Engineer, SecOps", ...), ordered with title+skill+location matches
consistently ranked above generic cloud/DevOps roles with no title match.
This was verified by running `V2SearchService.search()` directly against
the live sources, not assumed from reading the code.

**Re-verified through the actual Flask dashboard** after the V1/V2
ranking-unification change: a live `GET /` with `CAREERPILOT_SEARCH_V2=1`
against the real profile shows the same top result ("Staff Security
Engineer", 74%) with V2's own reason strings rendered directly on the
page ("Target job title matched", "Matched 6 profile skills", "Target
location matched", "11 profile skills not found") - not the legacy
matcher's differently-worded output. See `docs/ARCHITECTURE.md`'s "The
V1/V2 split."

**Note**: both verifications above ran while Duunitori was still an
active source - "Staff Security Engineer" was a Duunitori posting.
Duunitori was disabled later the same session for `robots.txt`
compliance (see `docs/DATA_SOURCES.md`), so a live search today only
returns Jobly results and won't show this exact example. The scoring
*mechanism* verified here is unaffected by which source produced a
job - re-verified again post-disable with Jobly-only results (14 jobs,
correctly matched and ranked) in `docs/DATA_SOURCES.md`.

## V1 matcher - what the dashboard actually shows (`app/ai/matcher.py`)

This is a considerably larger, hand-tuned matcher built specifically for
this candidate's profile. Key differences from the V2 matcher:

- **Title matching is tiered, not binary.** `PRIMARY_TITLES` (SOC
  analyst, security engineer, etc. - including Finnish terms like
  `"tietoturva-asiantuntija"` and `"kyberturvallisuusasiantuntija"`) score
  40 points; `SECONDARY_TITLES` (cloud/DevOps/sysadmin roles) score 27;
  `RELATED_TITLES` score 20; a generic security term anywhere in the title
  scores 15, in the description only, 8.
- **An explicit exclusion list** (`EXCLUDED_TITLE_TERMS`) immediately skips
  obviously unrelated postings (marketing, sales, HR, legal, design, etc.)
  before scoring.
- **Skills are weighted, not counted equally** (`SKILL_WEIGHTS`): security-
  specific skills (SIEM, incident response, firewall) weigh up to 3.0,
  general technical skills (Python, Git) as low as 1.5, capped at 25
  points total. Skill matching also expands a small alias table (e.g.
  `"kubernetes"` matches `"k8s"`, `"gcp"` matches `"google cloud
  platform"`).
- **Seniority is a penalty, not just a score component**, and is
  additive on top of everything else: senior (-15), lead (-28), manager
  (-32), architect (-30), director (-40), with a small bonus (+5/+6) for
  junior/intern roles. A required-experience regex
  (`_extract_required_experience`) also penalizes postings explicitly
  asking for 2+ years, scaling up to -20 for 7+ years.
- **Location scoring favors specific home cities**: Helsinki (20), Espoo
  (19), Vantaa (18) outrank a generic "somewhere in Finland" match (10);
  explicit remote/hybrid terms score 14-16.
- **Final score**: sum of all bonuses minus all penalties, clamped to
  `[0, 100]`, rounded. `match_quality` buckets the score into
  Excellent/Strong/Good/Moderate/Weak/Poor for display.

This matcher operates on whatever job list `_search_jobs()` returns
(V2-collected `CanonicalJob` objects when V2 is enabled, V1 `Job` objects
otherwise) via `_normalise_job()`, which reads common attributes off
either a dict or an object.

## Skill-gap analysis vs. matcher `missing_skills` (`app/ai/skill_gap.py`)

This is a **separate feature from both matchers above**, reachable from
the dashboard via a "Skill Gap" button on each job card
(`/analyze/<job_id>`), not part of the ranking pipeline. It exists
because neither matcher's `missing_skills` answers the question a human
means by "skill gap":

- V1/V2 `missing_skills` = profile skills that this *specific job's*
  text doesn't happen to repeat. A skill the job never mentions but the
  candidate has is "missing" by this definition - which is backwards
  from what "skill gap" means in normal usage, and a posting asking for
  a skill entirely absent from the profile (e.g. Terraform, if it's
  never been added to `profiles/profile.json`) never appears in either
  matcher's output at all. It's invisible, not merely unscored.
- `app/ai/skill_gap.analyze_skill_gap(profile, job)` answers the actual
  question: does this job ask for something the candidate doesn't
  demonstrate anywhere in their profile? It checks the job's text
  against a curated taxonomy of skills, and the *candidate's* skills,
  experience descriptions, certifications, and summary text (not just
  the bare `skills` list) for evidence of each one.

### Required vs. nice-to-have

Job postings rarely have clean, machine-parseable "Requirements" /
"Nice to have" sections once reduced to plain text. Instead of relying
on section headers, `analyze_skill_gap()` splits the job text into
sentences/lines and checks each one independently for a hedging phrase
("nice to have", "preferred", "a plus", "bonus", "desirable", "optional",
...). A skill mentioned in a hedged sentence is nice-to-have; anywhere
else, it's treated as required. This is a heuristic, not a real parser -
see "Known limitations" below.

### Word-boundary matching, and a bug found and fixed in it

`app/ai/skill_gap.py` has its own small `_normalize`/`_contains_term`
pair rather than importing the equivalent helpers from
`app/search/v2/matching/signals.py` - deliberately decoupled, mirroring
the precedent `app/ai/matcher.py` already set with its own independent
word-boundary matcher (V2's internals stay owned by V2's pipeline).

One real difference from V2's version, found while building this
feature: V2's `normalize_skill()` keeps periods in the allowed character
set (`[^a-z0-9+#. ]+`). That's harmless for V2's use case (matching a
short skill string like `"C#"` against a whole concatenated text blob),
but this feature tokenizes real natural-language *sentences* pulled
straight from job postings, where a skill name is very often the last
word before a full stop - `"...experience with Terraform."`. Keeping the
period there glues it onto the token (`"terraform."`), which then never
exactly equals the alias token (`"terraform"`), silently hiding the
match. `app/ai/skill_gap.py`'s normalizer strips periods entirely instead
- verified with `tests/test_skill_gap.py::test_trailing_sentence_punctuation_does_not_hide_a_skill_mention`,
which fails against the period-preserving version of the regex.

### Recommendation catalog

`SKILL_CATALOG` (`app/ai/skill_gap.py`) is a small, hand-curated,
~30-entry dict covering skills relevant to this profile's domain (Linux,
networking, cloud platforms, containers, SIEM/security tooling,
incident response, pentesting, compliance, etc.). Each entry has
detection aliases plus real, well-known, currently-existing
certifications, courses, and a realistic hands-on project idea - nothing
invented, and every certification's "why" describes only what it
actually, publicly covers. **This is why the feature makes zero LLM
calls** (see docs/AI.md): a recommendation is exactly the kind of claim
that must not be hallucinated, and a hand-curated catalog is verifiable
by construction, with no separate "AI-generated" content to mix in or
mislabel. A few entries (e.g. Git, VPN) have no real standalone
certification and deliberately list an empty `certifications` array
rather than inventing one -
`tests/test_skill_gap.py::test_recommendations_never_claim_certifications_that_are_absent`
guards this directly.

Missing skills are prioritized required-first, then by a rough
`effort_days` estimate (quickest realistic effort first) - see
`tests/test_skill_gap.py::test_priority_actions_lead_with_required_gaps_ordered_by_effort`.

### CV/profile evidence check

For a skill the job wants that the candidate *does* have somewhere in
their profile, the feature checks **where**: only in the bare `skills`
list, only in an experience entry's text, or both. A skill claimed in
the skills list but never demonstrated in any experience entry is
flagged with a note suggesting the candidate add a concrete example -
it never invents one. This is the CV-improvement mechanism, and it's
strictly a cross-reference of data already in `profiles/profile.json` -
no new claims are ever added.

### Known limitations

- **Curated taxonomy, not job-text extraction.** A skill the job
  mentions that isn't one of the ~30 `SKILL_CATALOG` keys is invisible
  to this feature entirely - the tradeoff was made deliberately (a
  curated list is deterministic, has no hallucination risk, and is easy
  to audit; a per-job LLM call to extract arbitrary requirements would
  add latency, cost, and a real hallucination surface for exactly the
  kind of claim - "you need X certification" - that must be trustworthy).
- **Required vs. nice-to-have is a heuristic**, not a structural parse of
  the posting. A posting phrased unusually (no hedging language at all,
  or hedging language this list doesn't recognize) will default every
  detected skill to "required".
- **No live course/certification verification.** The catalog is
  hand-checked as of this writing, not checked against a live API - a
  certification could be renamed or retired after the fact. There's no
  paid API involved by design (see docs/AI.md), so this is a static,
  periodically-reviewable list, not a live-verified one.

## Missing-data behavior

Both matchers treat missing profile data (empty skills/titles/locations)
as *zero contribution*, not as a penalty or an error - a job with no
matching skills still gets scored on title/location/seniority alone. This
is why the `profiles/profile.json` corruption bug was so quiet: an empty
profile didn't raise an error anywhere in the matching path, it just
silently produced near-flat, uninformative scores for every job.

## Known edge cases and limitations

- **Resolved this session**: V2 previously had no Finnish-language title
  recognition, no exclusion list, and no experience-requirement penalty -
  a Finnish-titled posting scored `title_score=0` under V2 even when V1
  would have recognized it, and an obviously unrelated posting (e.g.
  "Marketing Manager") could still surface with a nonzero score. All
  three are now ported (see "Ported from V1" above) and live-verified
  against the real profile and real sources.
- V2's title matching is still binary (100 or 0) with no partial credit
  for a close-but-not-exact title; V1's tiered
  `PRIMARY`/`SECONDARY`/`RELATED` system is more forgiving. Not ported -
  see `docs/ARCHITECTURE.md`'s "Why two matchers exist instead of one"
  for why this is a design difference, not treated as a remaining gap to
  close by default.
- V2's skill matching treats every profile skill as equally weighted;
  V1's `SKILL_WEIGHTS` favors security-specific skills over general
  technical ones, and V1 also expands a small alias table (e.g.
  `"kubernetes"` matches `"k8s"`). Not ported, same reasoning.
- V2's seniority handling is a percentage-weighted score component (10%
  of the total); V1 applies much steeper flat-point penalties for
  senior/lead/manager/architect/director roles on top of everything
  else. Both down-rank senior roles for this early-career-focused
  profile, just by different amounts - not ported, same reasoning.
- Neither matcher currently reads `employment_type` or `remote` as a
  scoring signal, even though `CanonicalJob` carries both fields.
