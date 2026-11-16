"""Cross-version impact analysis engine.

The engine is intentionally pure: given a versioned mapping set, the reference
graph between downstream concepts and the captured usage snapshots, it derives
which concepts are affected by the migration and which usage statistics remain
comparable. No value is ever carried over silently: a statistic that cannot be
traced through an *adopted equivalent* mapping chain is reported as
incomparable with an explicit reason code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from governance_vocabulary.concepts.model import ContractError, canonical_json, stable_hash, utc_now
from governance_vocabulary.impact.model import (
    REASON_CHAIN_CYCLE,
    REASON_DATA_CHANGE,
    REASON_MAPPING_GAP,
    REASON_MIGRATION,
    REASON_NO_EQUIVALENT,
    REASON_SNAPSHOT_MISSING,
    REASON_UNADOPTED_LINK,
    RELATION_EQUIVALENT,
    RELATION_RELATED,
    STAT_COMPARABLE,
    STAT_INCOMPARABLE,
    ChainHop,
    ConceptImpact,
    ConceptMapping,
    MappingChain,
    MappingSet,
    StatComparison,
    UsageSnapshot,
)

USAGE_METRICS = ("usage_count", "usage_share")

# Guard against pathological reference/mapping graphs.
MAX_CHAIN_HOPS = 64


def _index_snapshots(
    snapshots: Sequence[UsageSnapshot],
) -> dict[tuple[str, str], UsageSnapshot]:
    indexed: dict[tuple[str, str], UsageSnapshot] = {}
    for snapshot in snapshots:
        key = (snapshot.vocabulary_version, snapshot.concept_id)
        if key in indexed:
            raise ContractError(f"duplicate usage snapshot for {key}")
        indexed[key] = snapshot
    return indexed


def resolve_chain(
    mapping_set: MappingSet,
    source_version: str,
    source_concept: str,
    target_version: str,
) -> MappingChain:
    """Resolve the adopted-equivalent mapping chain between two versions.

    The returned chain always carries an explicit reason. When the chain is
    incomplete the ``target_concept`` is ``None`` and no statistic may be
    compared through it.
    """

    if source_version == target_version:
        return MappingChain(
            source_version,
            source_concept,
            target_version,
            source_concept,
            (),
            True,
            REASON_MIGRATION,
            1.0,
        )

    hops: list[ChainHop] = []
    visited: set[tuple[str, str]] = {(source_version, source_concept)}
    current_version = source_version
    current_concept = source_concept

    while len(hops) < MAX_CHAIN_HOPS:
        outgoing = mapping_set.outgoing(current_version, current_concept)
        if not outgoing:
            return MappingChain(
                source_version,
                source_concept,
                target_version,
                None,
                tuple(hops),
                False,
                REASON_MAPPING_GAP,
                _chain_confidence(hops),
            )

        next_mapping = _select_next_mapping(outgoing)
        if next_mapping is None:
            # An explicit non-equivalent link exists but nothing can carry the
            # statistic: this is the "no equivalent term yet" state, which must
            # be preserved rather than silently reusing the old value.
            reason = REASON_NO_EQUIVALENT
            related = next((item for item in outgoing if item.relation == RELATION_RELATED), None)
            if related is not None:
                hops.append(ChainHop.from_mapping(len(hops) + 1, related))
            return MappingChain(
                source_version,
                source_concept,
                target_version,
                None,
                tuple(hops),
                False,
                reason,
                _chain_confidence(hops),
            )

        if next_mapping.status != "adopted":
            hops.append(ChainHop.from_mapping(len(hops) + 1, next_mapping))
            return MappingChain(
                source_version,
                source_concept,
                target_version,
                None,
                tuple(hops),
                False,
                REASON_UNADOPTED_LINK,
                _chain_confidence(hops),
            )

        hops.append(ChainHop.from_mapping(len(hops) + 1, next_mapping))
        next_node = (next_mapping.target_version, next_mapping.target_concept)
        if next_node in visited:
            return MappingChain(
                source_version,
                source_concept,
                target_version,
                None,
                tuple(hops),
                False,
                REASON_CHAIN_CYCLE,
                _chain_confidence(hops),
            )
        visited.add(next_node)
        current_version, current_concept = next_node

        if current_version == target_version:
            return MappingChain(
                source_version,
                source_concept,
                target_version,
                current_concept,
                tuple(hops),
                True,
                REASON_MIGRATION,
                _chain_confidence(hops),
            )

    return MappingChain(
        source_version,
        source_concept,
        target_version,
        None,
        tuple(hops),
        False,
        REASON_CHAIN_CYCLE,
        _chain_confidence(hops),
    )


def _select_next_mapping(outgoing: Sequence[ConceptMapping]) -> ConceptMapping | None:
    equivalent = [item for item in outgoing if item.relation == RELATION_EQUIVALENT]
    if equivalent:
        # Deterministic preference: adopted first, then highest confidence, then id.
        return sorted(
            equivalent,
            key=lambda item: (
                0 if item.status == "adopted" else 1,
                -item.confidence,
                item.mapping_id,
            ),
        )[0]
    return None


def _chain_confidence(hops: Sequence[ChainHop]) -> float:
    if not hops:
        return 0.0
    product = 1.0
    for hop in hops:
        product *= hop.confidence
    return round(product, 12)


def affected_downstream(
    mapping_set: MappingSet,
    source_version: str,
    seed_concepts: Sequence[str],
    references: Mapping[str, Sequence[str]],
) -> tuple[str, ...]:
    """Collect every downstream concept touched by the migration.

    A concept is affected when one of its concepts appears on either side of a
    mapping edge originating at the source version, or when it references
    (transitively) such a concept through the ``references`` dependency graph.
    """

    mapped_sources = {
        item.source_concept
        for item in mapping_set.mappings
        if item.source_version == source_version
    }
    # Every node reachable from a source-version concept through the mapping
    # edges is affected, including intermediate and final target concepts.
    mapped_targets: set[str] = set()
    frontier = list(mapped_sources)
    seen: set[str] = set()
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        for edge in mapping_set.mappings:
            if edge.source_concept == current:
                mapped_targets.add(edge.target_concept)
                frontier.append(edge.target_concept)
    directly_affected = set(mapped_sources) | mapped_targets | set(seed_concepts)

    affected = set(directly_affected)
    frontier = list(directly_affected)
    while frontier:
        current = frontier.pop()
        for dependent, dependencies in references.items():
            if dependent in affected:
                continue
            if current in dependencies:
                affected.add(dependent)
                frontier.append(dependent)
    return tuple(sorted(affected))


def _compare_metric(
    metric: str,
    chain: MappingChain,
    source_snapshot: UsageSnapshot | None,
    target_snapshot: UsageSnapshot | None,
) -> StatComparison:
    source_value = getattr(source_snapshot, metric, None) if source_snapshot else None
    target_value = getattr(target_snapshot, metric, None) if target_snapshot else None

    if not chain.complete:
        return StatComparison(
            metric,
            STAT_INCOMPARABLE,
            chain.reason_code,
            source_value,
            None,
            False,
        )

    if source_snapshot is None or target_snapshot is None:
        return StatComparison(
            metric,
            STAT_INCOMPARABLE,
            REASON_SNAPSHOT_MISSING,
            source_value,
            target_value,
            False,
        )

    reason = REASON_DATA_CHANGE if source_value != target_value else REASON_MIGRATION
    return StatComparison(
        metric,
        STAT_COMPARABLE,
        reason,
        source_value,
        target_value,
        True,
    )


@dataclass(frozen=True)
class ImpactAnalysis:
    analysis_id: str
    mapping_set_id: str
    mapping_set_fingerprint: str
    source_version: str
    target_version: str
    vocabulary_version: str
    generated_at: str
    impacts: tuple[ConceptImpact, ...]
    affected_concepts: tuple[str, ...]
    comparable_concepts: tuple[str, ...]
    incomparable_concepts: tuple[str, ...]
    reason_summary: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "mapping_set_id": self.mapping_set_id,
            "mapping_set_fingerprint": self.mapping_set_fingerprint,
            "source_version": self.source_version,
            "target_version": self.target_version,
            "vocabulary_version": self.vocabulary_version,
            "generated_at": self.generated_at,
            "affected_concepts": list(self.affected_concepts),
            "comparable_concepts": list(self.comparable_concepts),
            "incomparable_concepts": list(self.incomparable_concepts),
            "reason_summary": dict(sorted(self.reason_summary.items())),
            "impacts": [item.as_dict() for item in self.impacts],
        }

    @property
    def fingerprint(self) -> str:
        body = self.as_dict()
        body.pop("generated_at", None)
        return stable_hash(body)


def analyze_impact(
    mapping_set: MappingSet,
    source_version: str,
    target_version: str,
    snapshots: Sequence[UsageSnapshot],
    references: Mapping[str, Sequence[str]] | None = None,
) -> ImpactAnalysis:
    """Produce the full cross-version impact analysis for one mapping set."""

    references = references or {}
    source_concepts = sorted(
        {
            item.source_concept
            for item in mapping_set.mappings
            if item.source_version == source_version
        }
    )
    if not source_concepts:
        raise ContractError("mapping set contains no mappings from the source version")

    snapshot_index = _index_snapshots(snapshots)
    affected = affected_downstream(mapping_set, source_version, source_concepts, references)

    # Resolve the chain for every source-side concept first. Target-side
    # concepts reached by a complete chain inherit that same chain (including
    # multi-hop chains) instead of being misreported as coverage gaps.
    source_chains: dict[str, MappingChain] = {
        concept_id: resolve_chain(mapping_set, source_version, concept_id, target_version)
        for concept_id in source_concepts
    }
    target_pairing: dict[str, str] = {}
    for concept_id, chain in source_chains.items():
        if chain.complete and chain.target_concept is not None:
            target_pairing.setdefault(chain.target_concept, concept_id)

    impacts: list[ConceptImpact] = []
    reason_summary: dict[str, int] = {}
    comparable: list[str] = []
    incomparable: list[str] = []

    source_concept_set = set(source_concepts)
    for concept_id in affected:
        paired_source = target_pairing.get(concept_id)
        if paired_source is not None:
            chain = source_chains[paired_source]
            chain_source = paired_source
        else:
            chain = source_chains.get(concept_id) or resolve_chain(
                mapping_set, source_version, concept_id, target_version
            )
            chain_source = concept_id
        source_snapshot = snapshot_index.get((source_version, chain_source))
        target_snapshot = None
        if chain.complete and chain.target_concept is not None:
            target_snapshot = snapshot_index.get((target_version, chain.target_concept))

        comparisons = tuple(
            _compare_metric(metric, chain, source_snapshot, target_snapshot)
            for metric in USAGE_METRICS
        )
        reason_codes = tuple(sorted({item.reason_code for item in comparisons}))
        for code in reason_codes:
            reason_summary[code] = reason_summary.get(code, 0) + 1

        concept_affected = chain_source in source_concept_set or bool(
            references.get(concept_id)
        ) or any(item != REASON_MIGRATION for item in reason_codes)
        impact = ConceptImpact(
            concept_id,
            source_version,
            target_version,
            concept_affected,
            chain,
            comparisons,
            reason_codes,
        )
        impacts.append(impact)
        if impact.comparable:
            comparable.append(concept_id)
        else:
            incomparable.append(concept_id)

    body = {
        "mapping_set_id": mapping_set.set_id,
        "mapping_set_fingerprint": mapping_set.fingerprint,
        "source_version": source_version,
        "target_version": target_version,
        "vocabulary_version": target_version,
        "affected_concepts": list(affected),
        "impacts": [item.as_dict() for item in impacts],
        "reason_summary": dict(sorted(reason_summary.items())),
    }
    analysis_id = stable_hash(canonical_json(body))[:24]
    return ImpactAnalysis(
        analysis_id,
        mapping_set.set_id,
        mapping_set.fingerprint,
        source_version,
        target_version,
        target_version,
        utc_now(),
        tuple(impacts),
        affected,
        tuple(sorted(comparable)),
        tuple(sorted(incomparable)),
        reason_summary,
    )


def evaluate_migration_gate(analysis: ImpactAnalysis) -> dict[str, Any]:
    """Turn the analysis into a go/hold decision input.

    The gate holds the migration whenever an affected concept has an
    incomparable statistic, and reports the reason codes so the team can
    distinguish a real data change from mapping coverage work that still needs
    to happen.
    """

    blocking_reasons = sorted(
        {
            code
            for impact in analysis.impacts
            if not impact.comparable
            for code in impact.reason_codes
        }
    )
    return {
        "decision": "hold" if blocking_reasons else "go",
        "affected_concept_count": len(analysis.affected_concepts),
        "comparable_concept_count": len(analysis.comparable_concepts),
        "incomparable_concept_count": len(analysis.incomparable_concepts),
        "blocking_reason_codes": blocking_reasons,
        "mapping_set_id": analysis.mapping_set_id,
        "mapping_set_fingerprint": analysis.mapping_set_fingerprint,
        "analysis_id": analysis.analysis_id,
        "analysis_fingerprint": analysis.fingerprint,
    }
