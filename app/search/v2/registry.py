from dataclasses import dataclass
from typing import List, Type

from app.search.sources.web_sources import (
    DuunitoriSource,
    JoblySource,
    TyomarkkinatoriSource,
    WorkInFinlandSource,
)


@dataclass(frozen=True)
class SourceDefinition:
    name: str
    source_class: Type


SOURCE_REGISTRY: List[SourceDefinition] = [
    SourceDefinition("Duunitori", DuunitoriSource),
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
