from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any, Iterable, Mapping

from governance_vocabulary.concepts.model import DomainRecord, bounded, finite_number


def _numeric(payload: Mapping[str, Any], key: str) -> float:
    value = payload.get(key, 0.0)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return finite_number(value)
    text = str(value).strip()
    tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
    return float(min(100, len(text) + len(set(tokens)) * 5))


def definition_quality(record: DomainRecord) -> float:
    diameter = _numeric(record.payload, "definition_count")
    mass = _numeric(record.payload, "usage_count")
    bruise = _numeric(record.payload, "ambiguous_links")
    coverage = _numeric(record.payload, "contract_coverage")
    shape_fit = bounded(1.0 - abs(diameter - 72.0) / 90.0)
    mass_fit = bounded(1.0 - abs(mass - 105.0) / 160.0)
    bruise_penalty = bounded(bruise / 40.0)
    return bounded(shape_fit * 0.34 + mass_fit * 0.26 + bounded(coverage) * 0.30 + (1.0 - bruise_penalty) * 0.10)


def mapping_quality(record: DomainRecord) -> float:
    sweetness = bounded(_numeric(record.payload, "mapping_confidence") / 24.0)
    void_penalty = bounded(_numeric(record.payload, "cycle_count") / 20.0)
    review_confidence = bounded(_numeric(record.payload, "review_confidence"))
    adoption_share = bounded(_numeric(record.payload, "adoption_share"))
    return bounded(sweetness * 0.35 + (1.0 - void_penalty) * 0.25 + review_confidence * 0.25 + adoption_share * 0.15)


def adoption_profile(record: DomainRecord) -> dict[str, float]:
    exterior = definition_quality(record)
    interior = mapping_quality(record)
    freshness = bounded(1.0 - _numeric(record.payload, "deprecation_age_days") / 240.0)
    combined = bounded(exterior * 0.45 + interior * 0.45 + freshness * 0.10)
    premium = bounded((combined - 0.58) / 0.42)
    standard = bounded(1.0 - abs(combined - 0.55) / 0.45)
    processing = bounded(1.0 - premium - standard * 0.45)
    total = premium + standard + processing
    return {"premium": premium / total, "standard": standard / total, "processing": processing / total}


def vocabulary_calibration(records: Iterable[DomainRecord]) -> dict[str, float]:
    rows = list(records)
    if not rows:
        return {"exterior_mean": 0.0, "interior_mean": 0.0, "dispersion": 0.0, "sample_count": 0.0}
    exterior = [definition_quality(row) for row in rows]
    interior = [mapping_quality(row) for row in rows]
    combined = [(left + right) / 2.0 for left, right in zip(exterior, interior)]
    return {"exterior_mean": statistics.fmean(exterior), "interior_mean": statistics.fmean(interior),
            "dispersion": statistics.pstdev(combined) if len(combined) > 1 else 0.0,
            "sample_count": float(len(rows))}


def concept_drift(records: Iterable[DomainRecord]) -> dict[str, float]:
    groups: dict[str, list[float]] = defaultdict(list)
    for record in records:
        groups[str(record.payload.get("concept_id", "unknown"))].append(mapping_quality(record))
    means = {origin: statistics.fmean(values) for origin, values in groups.items()}
    spread = max(means.values()) - min(means.values()) if means else 0.0
    return {"origin_count": float(len(means)), "quality_spread": spread, "drift_risk": bounded(spread * 2.0)}


def derive_context(record: DomainRecord, repository: Any) -> dict[str, float]:
    probabilities = adoption_profile(record)
    history = repository.list_records()
    calibration = vocabulary_calibration(history or [record])
    drift = concept_drift(history or [record])
    return {"grade_consistency_weight": 0.8 + probabilities["premium"] * 0.3,
            "inspection_coverage_weight": 0.7 + definition_quality(record) * 0.4,
            "false_release_risk_weight": 1.2 - mapping_quality(record) * 0.4,
            "origin_drift_weight": 0.8 + drift["drift_risk"] * 0.5,
            "calibration_need_weight": 0.8 + calibration["dispersion"] * 0.8}

# Compatibility names retained for callers of the original public API.
grade_probability = adoption_profile
batch_calibration = vocabulary_calibration
origin_drift = concept_drift
