# Matching and Ranking

CareerPilot AI currently has **two** independent matchers, described
separately below. `docs/ARCHITECTURE.md` explains why both exist and which
one actually drives the dashboard today (short answer: the V1 matcher,
`app.ai.matcher.JobMatcher`).

## V2 matcher (`app/search/v2/matching/`)

### Inputs

- `profile_skills`: `profiles/profile.json["skills"]` (17 entries)
- `target_titles`: `profiles/profile.json["target_titles"]` (13 entries)
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
```

- `title_score`: 100 if any target title matches, else 0 (binary, not
  partial credit).
- `skill_score`: `matched_skills / total_profile_skills * 100`.
- `location_score`: 100 if any target location matches, else 0.
- `seniority_score`: from the table above.

The result is clamped to `[0, 100]` and rounded to 2 decimals. Human
-readable `reasons` are generated alongside the score (e.g. "Target job
title matched", "Matched 6 profile skills", "junior seniority is a good
fit", "4 profile skills not found").

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

## Missing-data behavior

Both matchers treat missing profile data (empty skills/titles/locations)
as *zero contribution*, not as a penalty or an error - a job with no
matching skills still gets scored on title/location/seniority alone. This
is why the `profiles/profile.json` corruption bug was so quiet: an empty
profile didn't raise an error anywhere in the matching path, it just
silently produced near-flat, uninformative scores for every job.

## Known edge cases and limitations

- V2's title matching is binary (100 or 0) with no partial credit for a
  close-but-not-exact title; V1's tiered system is the more forgiving one
  and is what users actually see.
- V2's title/skill matching has no Finnish-language term list; V1's does.
  Since V1 is what's displayed, this gap is currently masked, but it means
  `V2SearchService.search()` used directly (its public, tested API) will
  under-score Finnish-titled postings relative to what the dashboard shows
  for the same job.
- Neither matcher currently reads `employment_type` or `remote` as a
  scoring signal, even though `CanonicalJob` carries both fields.
