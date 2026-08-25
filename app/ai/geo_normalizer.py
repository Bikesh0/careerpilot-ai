"""
Classifies a job's free-text location into FINLAND / EUROPE /
OUTSIDE_EUROPE / UNKNOWN.

Nothing today does this: both matchers (V1's app/ai/matcher.py,
V2's app/search/v2/matching/signals.py) only do free-text matching
against the profile's own target_locations - there's no concept of
"is this even in Europe" anywhere (confirmed by reading both directly,
and documented as "not fully built" in docs/PRODUCT_VISION.md's
"Geographic priority" section). This exists to close that gap without
touching either matcher's scoring formula - both are tested and
working, and a location-priority *tier* is a different, additive
concern from a location-priority *score*.

Classification is a plain, verifiable lookup against real country/city
names - deliberately not fuzzy, not LLM-based, and not claiming any
precision beyond what a country/city name list can offer. A location
string with no recognizable country/city at all (e.g. a bare "Remote"
with nothing else) is UNKNOWN, not silently dropped into any other
tier - the caller decides what to do with UNKNOWN (this module never
excludes anything itself).
"""

FINLAND = "FINLAND"
EUROPE = "EUROPE"
OUTSIDE_EUROPE = "OUTSIDE_EUROPE"
UNKNOWN = "UNKNOWN"

# Real, well-known Finnish cities relevant to this profile's job search
# (see profiles/profile.json's target_locations, and the wider set of
# cities Finnish job boards commonly list) plus "Finland"/"Suomi"
# themselves.
_FINLAND_TERMS = [
    "finland", "suomi",
    "helsinki", "espoo", "vantaa", "tampere", "turku", "oulu",
    "jyvaskyla", "jyväskylä", "lahti", "kuopio", "pori", "joensuu",
    "lappeenranta", "hameenlinna", "hämeenlinna", "vaasa", "seinajoki",
    "seinäjoki", "rovaniemi", "kotka", "salo",
]

# EU + EEA + UK + Switzerland - the common "Europe" scope for a job
# search targeting EU/EEA work-authorized candidates. Deliberately a
# country-name list, not a city list: enumerating every European city
# accurately is a much larger, error-prone undertaking, while country
# names are a small, unambiguous, verifiable set.
_EUROPE_COUNTRIES = [
    "austria", "belgium", "bulgaria", "croatia", "cyprus", "czechia",
    "czech republic", "denmark", "estonia", "france", "germany",
    "greece", "hungary", "ireland", "italy", "latvia", "lithuania",
    "luxembourg", "malta", "netherlands", "poland", "portugal",
    "romania", "slovakia", "slovenia", "spain", "sweden",
    "iceland", "liechtenstein", "norway", "switzerland",
    "united kingdom", "uk", "england", "scotland", "wales",
]

# A curated list of the specific non-European countries that job-board
# source metadata has actually mislabeled into "Europe" results before
# (per the product spec's own examples) - kept small and explicit
# rather than attempting an exhaustive "rest of the world" list, since
# anything not matched by FINLAND/EUROPE above and not in this list
# falls through to UNKNOWN rather than a guessed classification.
_OUTSIDE_EUROPE_COUNTRIES = [
    "united states", "usa", "u.s.a", "u.s.", "canada", "china",
    "india", "united arab emirates", "uae", "singapore", "australia",
    "japan", "brazil", "mexico", "south africa", "hong kong",
    "south korea", "philippines", "vietnam", "indonesia", "pakistan",
]

_REMOTE_TERMS = ["remote", "hybrid", "work from anywhere"]


def _normalize(value):
    return " ".join(str(value or "").casefold().split())


def _contains_any(text, terms):
    return any(term in text for term in terms)


def classify_location(location_text):
    """
    Returns one of FINLAND / EUROPE / OUTSIDE_EUROPE / UNKNOWN.

    Checked in priority order - Finland first, since a Finnish city
    name is a stronger, more specific signal than a country-level
    match, and a posting can legitimately mention both ("Helsinki,
    Finland - EU applicants only").
    """

    text = _normalize(location_text)

    if not text:
        return UNKNOWN

    if _contains_any(text, _FINLAND_TERMS):
        return FINLAND

    if _contains_any(text, _EUROPE_COUNTRIES):
        return EUROPE

    if _contains_any(text, _OUTSIDE_EUROPE_COUNTRIES):
        return OUTSIDE_EUROPE

    if _contains_any(text, _REMOTE_TERMS):
        return UNKNOWN

    return UNKNOWN


def is_excluded_by_default(location_text):
    """
    True only for a confidently-classified non-European location -
    "Priority: 1. Finland 2. Europe 3. Outside Europe excluded by
    default" from the product spec. UNKNOWN is deliberately NOT
    excluded: a location this module can't confidently classify (e.g.
    a bare "Remote" with no country, or missing location data
    entirely) is a data-quality gap, not evidence the job is outside
    Europe - excluding on missing information would silently drop
    real, relevant postings.
    """

    return classify_location(location_text) == OUTSIDE_EUROPE
