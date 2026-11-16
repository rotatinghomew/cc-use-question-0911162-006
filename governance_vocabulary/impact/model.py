"""Cross-version impact analysis domain model.

A vocabulary migration swaps a set of concept mappings. The governance team must
be able to answer, before adopting the new version:

* which downstream concepts are affected by the mapping changes;
* which historical usage statistics remain comparable across versions;
* which statistics are genuinely incomparable because no equivalent concept
  exists yet (they must never silently keep their old value);
* which mapping chain was used to reach that conclusion, so the decision can be
  replayed against the mapping version that was current at the time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from governance_vocabulary.concepts.model import (
    ContractError,
    identifier,
    stable_hash,
)

# Relation kinds recorded on a mapping edge. Only equivalent links can carry a
# usage statistic across versions; related links explain influence but never
# justify reusing an old value.
RELATION_EQUIVALENT = "equivalent"
RELATION_RELATED = "related"
ALLOWED_RELATIONS = (RELATION_EQUIVALENT, RELATION_RELATED)

# Lifecycle of a single mapping. Only adopted mappings participate in chain
# resolution and comparability decisions; proposed/deprecated edges stay
# visible for traceability but cannot justify a comparison.
MAPPING_STATUSES = ("proposed", "adopted", "deprecated")

# Comparability verdicts for one usage statistic.
STAT_COMPARABLE = "comparable"
STAT_INCOMPARABLE = "incomparable"

# Explicit reason codes. They separate the three explanations the using
# departments cannot distinguish on their own.
REASON_MIGRATION = "migration"
REASON_DATA_CHANGE = "data_change"
REASON_NO_EQUIVALENT = "no_equivalent"
REASON_MAPPING_GAP = "mapping_gap"
REASON_SNAPSHOT_MISSING = "snapshot_missing"
REASON_CHAIN_CYCLE = "chain_cycle"
REASON_UNADOPTED_LINK = "unadopted_link"


@dataclass(frozen=True)
class ConceptMapping:
    """A single directed mapping edge between two concept versions."""

    mapping_id: str
    source_version: str
    source_concept: str
    target_version: str
    target_concept: str
    relation: str = RELATION_EQUIVALENT
    status: str = "proposed"
    confidence: float = 0.0
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "mapping_id", identifier(self.mapping_id))
        object.__setattr__(self, "source_version", identifier(self.source_version))
        object.__setattr__(self, "source_concept", identifier(self.source_concept))
        object.__setattr__(self, "target_version", identifier(self.target_version))
        object.__setattr__(self, "target_concept", identifier(self.target_concept))
        if self.relation not in ALLOWED_RELATIONS:
            raise ContractError("unsupported mapping relation")
        if self.status not in MAPPING_STATUSES:
            raise ContractError("unsupported mapping status")
        confidence = float(self.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ContractError("mapping confidence must be within 0..1")
        object.__setattr__(self, "confidence", confidence)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConceptMapping":
        required = (
            "mapping_id",
            "source_version",
            "source_concept",
            "target_version",
            "target_concept",
        )
        missing = [name for name in required if not str(value.get(name, "")).strip()]
        if missing:
            raise ContractError(f"mapping missing required fields: {', '.join(missing)}")
        return cls(
            mapping_id=str(value["mapping_id"]),
            source_version=str(value["source_version"]),
            source_concept=str(value["source_concept"]),
            target_version=str(value["target_version"]),
            target_concept=str(value["target_concept"]),
            relation=str(value.get("relation", RELATION_EQUIVALENT)),
            status=str(value.get("status", "proposed")),
            confidence=float(value.get("confidence", 0.0) or 0.0),
            rationale=str(value.get("rationale", "")),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "source_version": self.source_version,
            "source_concept": self.source_concept,
            "target_version": self.target_version,
            "target_concept": self.target_concept,
            "relation": self.relation,
            "status": self.status,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class MappingSet:
    """An immutable, versioned collection of concept mappings."""

    set_id: str
    vocabulary_version: str
    mappings: tuple[ConceptMapping, ...]
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "set_id", identifier(self.set_id))
        object.__setattr__(self, "vocabulary_version", identifier(self.vocabulary_version))
        normalized = tuple(self.mappings)
        ids = [item.mapping_id for item in normalized]
        if len(ids) != len(set(ids)):
            raise ContractError("mapping set contains duplicate mapping identifiers")
        object.__setattr__(self, "mappings", normalized)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MappingSet":
        set_id = value.get("set_id")
        version = value.get("vocabulary_version")
        if not str(set_id or "").strip() or not str(version or "").strip():
            raise ContractError("mapping set requires set_id and vocabulary_version")
        raw_mappings = value.get("mappings")
        if not isinstance(raw_mappings, list) or not raw_mappings:
            raise ContractError("mapping set requires a non-empty mappings list")
        return cls(
            str(set_id),
            str(version),
            tuple(ConceptMapping.from_dict(item) for item in raw_mappings),
            str(value.get("description", "")),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "set_id": self.set_id,
            "vocabulary_version": self.vocabulary_version,
            "description": self.description,
            "mappings": [item.as_dict() for item in self.mappings],
        }

    @property
    def fingerprint(self) -> str:
        return stable_hash(self.as_dict())

    def adopted_equivalent(self) -> tuple[ConceptMapping, ...]:
        return tuple(
            item
            for item in self.mappings
            if item.status == "adopted" and item.relation == RELATION_EQUIVALENT
        )

    def outgoing(self, version: str, concept: str) -> tuple[ConceptMapping, ...]:
        return tuple(
            item
            for item in self.mappings
            if item.source_version == version and item.source_concept == concept
        )


@dataclass(frozen=True)
class ChainHop:
    """One auditable hop inside a resolved mapping chain."""

    order: int
    mapping_id: str
    source_version: str
    source_concept: str
    target_version: str
    target_concept: str
    relation: str
    status: str
    confidence: float

    @classmethod
    def from_mapping(cls, order: int, mapping: ConceptMapping) -> "ChainHop":
        return cls(
            order,
            mapping.mapping_id,
            mapping.source_version,
            mapping.source_concept,
            mapping.target_version,
            mapping.target_concept,
            mapping.relation,
            mapping.status,
            mapping.confidence,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "mapping_id": self.mapping_id,
            "source_version": self.source_version,
            "source_concept": self.source_concept,
            "target_version": self.target_version,
            "target_concept": self.target_concept,
            "relation": self.relation,
            "status": self.status,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class MappingChain:
    """Resolved chain from a source concept to a target-version concept."""

    source_version: str
    source_concept: str
    target_version: str
    target_concept: str | None
    hops: tuple[ChainHop, ...]
    complete: bool
    reason_code: str
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_version": self.source_version,
            "source_concept": self.source_concept,
            "target_version": self.target_version,
            "target_concept": self.target_concept,
            "complete": self.complete,
            "reason_code": self.reason_code,
            "confidence": self.confidence,
            "hops": [hop.as_dict() for hop in self.hops],
        }


@dataclass(frozen=True)
class UsageSnapshot:
    """A usage statistic captured for one concept on one vocabulary version."""

    vocabulary_version: str
    concept_id: str
    usage_count: float
    usage_share: float
    observed_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "vocabulary_version", identifier(self.vocabulary_version))
        object.__setattr__(self, "concept_id", identifier(self.concept_id))
        if not str(self.observed_at).strip():
            raise ContractError("usage snapshot requires observed_at")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "UsageSnapshot":
        required = ("vocabulary_version", "concept_id", "observed_at")
        missing = [name for name in required if not str(value.get(name, "")).strip()]
        if missing:
            raise ContractError(f"usage snapshot missing fields: {', '.join(missing)}")
        return cls(
            str(value["vocabulary_version"]),
            str(value["concept_id"]),
            float(value.get("usage_count", 0.0) or 0.0),
            float(value.get("usage_share", 0.0) or 0.0),
            str(value["observed_at"]),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "vocabulary_version": self.vocabulary_version,
            "concept_id": self.concept_id,
            "usage_count": self.usage_count,
            "usage_share": self.usage_share,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class StatComparison:
    """Comparability verdict for one usage metric of one concept."""

    metric: str
    status: str
    reason_code: str
    source_value: float | None
    target_value: float | None
    comparable: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "status": self.status,
            "reason_code": self.reason_code,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "comparable": self.comparable,
        }


@dataclass(frozen=True)
class ConceptImpact:
    """Impact verdict for a single downstream concept."""

    concept_id: str
    source_version: str
    target_version: str
    affected: bool
    chain: MappingChain
    comparisons: tuple[StatComparison, ...]
    reason_codes: tuple[str, ...]

    @property
    def comparable(self) -> bool:
        return bool(self.comparisons) and all(item.comparable for item in self.comparisons)

    def as_dict(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "source_version": self.source_version,
            "target_version": self.target_version,
            "affected": self.affected,
            "comparable": self.comparable,
            "reason_codes": list(self.reason_codes),
            "chain": self.chain.as_dict(),
            "comparisons": [item.as_dict() for item in self.comparisons],
        }


def mapping_set_from_fixture(value: Mapping[str, Any]) -> MappingSet | None:
    raw = value.get("mapping_set")
    if raw is None:
        return None
    return MappingSet.from_dict(raw)


def snapshots_from_fixture(value: Mapping[str, Any]) -> tuple[UsageSnapshot, ...]:
    raw = value.get("usage_snapshots")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ContractError("usage_snapshots must be a list")
    return tuple(UsageSnapshot.from_dict(item) for item in raw)


def references_from_fixture(value: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    raw = value.get("concept_references")
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ContractError("concept_references must be an object")
    result: dict[str, tuple[str, ...]] = {}
    for key, items in raw.items():
        if not isinstance(items, list):
            raise ContractError("concept_references entries must be lists")
        result[identifier(key)] = tuple(identifier(item) for item in items)
    return result
