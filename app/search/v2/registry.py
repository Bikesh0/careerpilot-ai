from dataclasses import dataclass
from typing import List, Type

from app.search.sources.web_sources import (
    JoblySource,
    TyomarkkinatoriSource,
    WorkInFinlandSource,
)


@dataclass(frozen=True)
class SourceDefinition:
    name: str
    source_class: Type


# DuunitoriSource is deliberately not registered here.
#
# duunitori.fi/robots.txt disallows the generic "*" user-agent group
# (Disallow: /), and this scraper identifies itself with a spoofed
# browser User-Agent, not one of the specifically-named crawlers the
# site allowlists (Googlebot, Bingbot, etc.). It was previously
# registered and running in violation of that policy. The class itself
# is unchanged and still fully tested in isolation
# (tests/test_duunitori_source.py, tests/test_source_domain_guard.py)
# - only its registration here was removed, so it can be re-enabled
# once this is resolved. See docs/DATA_SOURCES.md and docs/SECURITY.md.
SOURCE_REGISTRY: List[SourceDefinition] = [
    SourceDefinition("Jobly", JoblySource),
    SourceDefinition("Tyomarkkinatori", TyomarkkinatoriSource),
    SourceDefinition("Work in Finland", WorkInFinlandSource),
]


def get_source_definitions() -> List[SourceDefinition]:
    return list(SOURCE_REGISTRY)


def get_source_names() -> List[str]:
    return [definition.name for definition in SOURCE_REGISTRY]


def create_sources():
    return [
        definition.source_class()
        for definition in SOURCE_REGISTRY
    ]
