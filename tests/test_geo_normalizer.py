from app.ai.geo_normalizer import (
    EUROPE,
    FINLAND,
    OUTSIDE_EUROPE,
    UNKNOWN,
    classify_location,
    is_excluded_by_default,
)


def test_finnish_city_classifies_as_finland():
    assert classify_location("Helsinki, Finland") == FINLAND
    assert classify_location("Espoo") == FINLAND


def test_european_country_classifies_as_europe():
    assert classify_location("Berlin, Germany") == EUROPE
    assert classify_location("Stockholm, Sweden") == EUROPE


def test_known_non_european_country_classifies_as_outside_europe():
    assert classify_location("San Francisco, United States") == OUTSIDE_EUROPE
    assert classify_location("Bangalore, India") == OUTSIDE_EUROPE


def test_unclassifiable_location_is_unknown_not_excluded():
    """
    Regression test for the product spec's explicit instruction: an
    UNKNOWN location (missing data, or a bare "Remote" with no country)
    must never be excluded by default - only a confidently-identified
    non-European location should be.
    """

    assert classify_location("") == UNKNOWN
    assert classify_location("Remote") == UNKNOWN

    assert is_excluded_by_default("") is False
    assert is_excluded_by_default("Remote") is False


def test_only_outside_europe_is_excluded_by_default():
    assert is_excluded_by_default("United States") is True
    assert is_excluded_by_default("Helsinki") is False
    assert is_excluded_by_default("Germany") is False


def test_finland_mention_wins_even_alongside_country_name():
    # "Helsinki, Finland" contains both a Finnish city and the country
    # name itself - either alone would already resolve to FINLAND, and
    # Finland is never itself in the Europe/outside-Europe lists, so
    # this just confirms no double-classification confusion.
    assert classify_location("Helsinki, Finland") == FINLAND
