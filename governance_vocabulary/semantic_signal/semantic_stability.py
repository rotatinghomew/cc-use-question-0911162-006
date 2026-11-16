from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class DomainSignal:
    code: str
    score: float
    severity: str
    evidence: dict[str, Any]

def number(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = float(payload.get(key, default))
    except (TypeError, ValueError):
        return default
    return default if value != value or value in (float('inf'), float('-inf')) else value

def ratio(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = number(payload, key, default)
    if value > 1.0:
        value /= 100.0
    return max(0.0, min(1.0, value))

def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

def semantic_stability(payload:Mapping[str,Any])->DomainSignal:
    confidence=ratio(payload,'mapping_confidence'); review=ratio(payload,'review_confidence'); coverage=ratio(payload,'contract_coverage'); adoption=ratio(payload,'adoption_share')
    ambiguity=max(0.0,number(payload,'ambiguous_links')); cycles=max(0.0,number(payload,'cycle_count')); definitions=max(1.0,number(payload,'definition_count',1)); usage=max(0.0,number(payload,'usage_count'))
    graph_penalty=min(1.0,(ambiguity+cycles*2)/definitions); usage_weight=min(1.0,usage/1000.0)
    score=clamp(confidence*.28+review*.20+coverage*.20+adoption*.12+(1-graph_penalty)*.15+usage_weight*.05)
    severity='critical' if cycles>0 else 'warning' if ambiguity>definitions*.25 or confidence<.5 else 'info'
    return DomainSignal('semantic_stability',score,severity,{'cycle_count':cycles,'ambiguity_share':ambiguity/definitions,'contract_coverage':coverage,'usage_weight':usage_weight})

def peer_distribution(records:Iterable[Any],group_field:str='language_code')->dict[str,Any]:
    rows=[semantic_stability(getattr(r,'payload',r)) for r in records]
    return {'count':len(rows),'cyclic':sum(s.evidence['cycle_count']>0 for s in rows),'minimum':min((s.score for s in rows),default=0.0)}

def augment_context(record:Any,repository:Any)->dict[str,Any]:
    signal=semantic_stability(record.payload); peers=peer_distribution(repository.list_records())
    return {'domain_signal':signal.score,'domain_severity':signal.severity,'cyclic_vocabularies':peers['cyclic'],'minimum_stability':peers['minimum']}
