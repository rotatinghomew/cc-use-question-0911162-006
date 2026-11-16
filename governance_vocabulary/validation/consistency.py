from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from governance_vocabulary.concepts.model import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        tokens = [item for item in text.replace(',', ' ').replace(';', ' ').split() if item]
        return float(min(100, len(text) + len(set(tokens)) * 5))

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    severity = 'info' if passed else ('critical' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, severity, message, evidence)

def check_mapping_confidence_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_mapping_confidence_presence_threshold', 10.333)
    return _result('check_mapping_confidence_presence', adjusted, threshold, True, 'validates mapping_confidence presence',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_mapping_confidence_range_threshold', 12.667)
    return _result('check_mapping_confidence_range', adjusted, threshold, True, 'validates mapping_confidence range',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_mapping_confidence_stability_threshold', 15.0)
    return _result('check_mapping_confidence_stability', adjusted, threshold, False, 'validates mapping_confidence stability',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_mapping_confidence_freshness_threshold', 17.333)
    return _result('check_mapping_confidence_freshness', adjusted, threshold, True, 'validates mapping_confidence freshness',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_mapping_confidence_coverage_threshold', 19.667)
    return _result('check_mapping_confidence_coverage', adjusted, threshold, True, 'validates mapping_confidence coverage',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_mapping_confidence_consistency_threshold', 22.0)
    return _result('check_mapping_confidence_consistency', adjusted, threshold, False, 'validates mapping_confidence consistency',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_mapping_confidence_risk_threshold', 24.333)
    return _result('check_mapping_confidence_risk', adjusted, threshold, True, 'validates mapping_confidence risk',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_mapping_confidence_confidence_threshold', 26.667)
    return _result('check_mapping_confidence_confidence', adjusted, threshold, True, 'validates mapping_confidence confidence',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_mapping_confidence_dependency_threshold', 29.0)
    return _result('check_mapping_confidence_dependency', adjusted, threshold, False, 'validates mapping_confidence dependency',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_mapping_confidence_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'mapping_confidence')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_mapping_confidence_readiness_threshold', 31.333)
    return _result('check_mapping_confidence_readiness', adjusted, threshold, True, 'validates mapping_confidence readiness',
                   {'field': 'mapping_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_definition_count_presence_threshold', 9.333)
    return _result('check_definition_count_presence', adjusted, threshold, True, 'validates definition_count presence',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_definition_count_range_threshold', 11.667)
    return _result('check_definition_count_range', adjusted, threshold, False, 'validates definition_count range',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_definition_count_stability_threshold', 14.0)
    return _result('check_definition_count_stability', adjusted, threshold, True, 'validates definition_count stability',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_definition_count_freshness_threshold', 16.333)
    return _result('check_definition_count_freshness', adjusted, threshold, True, 'validates definition_count freshness',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_definition_count_coverage_threshold', 18.667)
    return _result('check_definition_count_coverage', adjusted, threshold, False, 'validates definition_count coverage',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_definition_count_consistency_threshold', 21.0)
    return _result('check_definition_count_consistency', adjusted, threshold, True, 'validates definition_count consistency',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_definition_count_risk_threshold', 23.333)
    return _result('check_definition_count_risk', adjusted, threshold, True, 'validates definition_count risk',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_definition_count_confidence_threshold', 25.667)
    return _result('check_definition_count_confidence', adjusted, threshold, False, 'validates definition_count confidence',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_definition_count_dependency_threshold', 28.0)
    return _result('check_definition_count_dependency', adjusted, threshold, True, 'validates definition_count dependency',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_definition_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'definition_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_definition_count_readiness_threshold', 30.333)
    return _result('check_definition_count_readiness', adjusted, threshold, True, 'validates definition_count readiness',
                   {'field': 'definition_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_usage_count_presence_threshold', 8.333)
    return _result('check_usage_count_presence', adjusted, threshold, False, 'validates usage_count presence',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_usage_count_range_threshold', 10.667)
    return _result('check_usage_count_range', adjusted, threshold, True, 'validates usage_count range',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_usage_count_stability_threshold', 13.0)
    return _result('check_usage_count_stability', adjusted, threshold, True, 'validates usage_count stability',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_usage_count_freshness_threshold', 15.333)
    return _result('check_usage_count_freshness', adjusted, threshold, False, 'validates usage_count freshness',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_usage_count_coverage_threshold', 17.667)
    return _result('check_usage_count_coverage', adjusted, threshold, True, 'validates usage_count coverage',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_usage_count_consistency_threshold', 20.0)
    return _result('check_usage_count_consistency', adjusted, threshold, True, 'validates usage_count consistency',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_usage_count_risk_threshold', 22.333)
    return _result('check_usage_count_risk', adjusted, threshold, False, 'validates usage_count risk',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_usage_count_confidence_threshold', 24.667)
    return _result('check_usage_count_confidence', adjusted, threshold, True, 'validates usage_count confidence',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_usage_count_dependency_threshold', 27.0)
    return _result('check_usage_count_dependency', adjusted, threshold, True, 'validates usage_count dependency',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_usage_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'usage_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_usage_count_readiness_threshold', 29.333)
    return _result('check_usage_count_readiness', adjusted, threshold, False, 'validates usage_count readiness',
                   {'field': 'usage_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_language_code_presence_threshold', 31.667)
    return _result('check_language_code_presence', adjusted, threshold, True, 'validates language_code presence',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_language_code_range_threshold', 9.667)
    return _result('check_language_code_range', adjusted, threshold, True, 'validates language_code range',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_language_code_stability_threshold', 12.0)
    return _result('check_language_code_stability', adjusted, threshold, False, 'validates language_code stability',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_language_code_freshness_threshold', 14.333)
    return _result('check_language_code_freshness', adjusted, threshold, True, 'validates language_code freshness',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_language_code_coverage_threshold', 16.667)
    return _result('check_language_code_coverage', adjusted, threshold, True, 'validates language_code coverage',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_language_code_consistency_threshold', 19.0)
    return _result('check_language_code_consistency', adjusted, threshold, False, 'validates language_code consistency',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_language_code_risk_threshold', 21.333)
    return _result('check_language_code_risk', adjusted, threshold, True, 'validates language_code risk',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_language_code_confidence_threshold', 23.667)
    return _result('check_language_code_confidence', adjusted, threshold, True, 'validates language_code confidence',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_language_code_dependency_threshold', 26.0)
    return _result('check_language_code_dependency', adjusted, threshold, False, 'validates language_code dependency',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_language_code_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'language_code')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_language_code_readiness_threshold', 28.333)
    return _result('check_language_code_readiness', adjusted, threshold, True, 'validates language_code readiness',
                   {'field': 'language_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_ambiguous_links_presence_threshold', 30.667)
    return _result('check_ambiguous_links_presence', adjusted, threshold, True, 'validates ambiguous_links presence',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_ambiguous_links_range_threshold', 8.667)
    return _result('check_ambiguous_links_range', adjusted, threshold, False, 'validates ambiguous_links range',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_ambiguous_links_stability_threshold', 11.0)
    return _result('check_ambiguous_links_stability', adjusted, threshold, True, 'validates ambiguous_links stability',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_ambiguous_links_freshness_threshold', 13.333)
    return _result('check_ambiguous_links_freshness', adjusted, threshold, True, 'validates ambiguous_links freshness',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_ambiguous_links_coverage_threshold', 15.667)
    return _result('check_ambiguous_links_coverage', adjusted, threshold, False, 'validates ambiguous_links coverage',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_ambiguous_links_consistency_threshold', 18.0)
    return _result('check_ambiguous_links_consistency', adjusted, threshold, True, 'validates ambiguous_links consistency',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_ambiguous_links_risk_threshold', 20.333)
    return _result('check_ambiguous_links_risk', adjusted, threshold, True, 'validates ambiguous_links risk',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_ambiguous_links_confidence_threshold', 22.667)
    return _result('check_ambiguous_links_confidence', adjusted, threshold, False, 'validates ambiguous_links confidence',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_ambiguous_links_dependency_threshold', 25.0)
    return _result('check_ambiguous_links_dependency', adjusted, threshold, True, 'validates ambiguous_links dependency',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_ambiguous_links_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'ambiguous_links')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_ambiguous_links_readiness_threshold', 27.333)
    return _result('check_ambiguous_links_readiness', adjusted, threshold, True, 'validates ambiguous_links readiness',
                   {'field': 'ambiguous_links', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_cycle_count_presence_threshold', 29.667)
    return _result('check_cycle_count_presence', adjusted, threshold, False, 'validates cycle_count presence',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_cycle_count_range_threshold', 32.0)
    return _result('check_cycle_count_range', adjusted, threshold, True, 'validates cycle_count range',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_cycle_count_stability_threshold', 10.0)
    return _result('check_cycle_count_stability', adjusted, threshold, True, 'validates cycle_count stability',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_cycle_count_freshness_threshold', 12.333)
    return _result('check_cycle_count_freshness', adjusted, threshold, False, 'validates cycle_count freshness',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_cycle_count_coverage_threshold', 14.667)
    return _result('check_cycle_count_coverage', adjusted, threshold, True, 'validates cycle_count coverage',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_cycle_count_consistency_threshold', 17.0)
    return _result('check_cycle_count_consistency', adjusted, threshold, True, 'validates cycle_count consistency',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_cycle_count_risk_threshold', 19.333)
    return _result('check_cycle_count_risk', adjusted, threshold, False, 'validates cycle_count risk',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_cycle_count_confidence_threshold', 21.667)
    return _result('check_cycle_count_confidence', adjusted, threshold, True, 'validates cycle_count confidence',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_cycle_count_dependency_threshold', 24.0)
    return _result('check_cycle_count_dependency', adjusted, threshold, True, 'validates cycle_count dependency',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_cycle_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'cycle_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_cycle_count_readiness_threshold', 26.333)
    return _result('check_cycle_count_readiness', adjusted, threshold, False, 'validates cycle_count readiness',
                   {'field': 'cycle_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_adoption_share_presence_threshold', 28.667)
    return _result('check_adoption_share_presence', adjusted, threshold, True, 'validates adoption_share presence',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_adoption_share_range_threshold', 31.0)
    return _result('check_adoption_share_range', adjusted, threshold, True, 'validates adoption_share range',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_adoption_share_stability_threshold', 9.0)
    return _result('check_adoption_share_stability', adjusted, threshold, False, 'validates adoption_share stability',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_adoption_share_freshness_threshold', 11.333)
    return _result('check_adoption_share_freshness', adjusted, threshold, True, 'validates adoption_share freshness',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_adoption_share_coverage_threshold', 13.667)
    return _result('check_adoption_share_coverage', adjusted, threshold, True, 'validates adoption_share coverage',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_adoption_share_consistency_threshold', 16.0)
    return _result('check_adoption_share_consistency', adjusted, threshold, False, 'validates adoption_share consistency',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_adoption_share_risk_threshold', 18.333)
    return _result('check_adoption_share_risk', adjusted, threshold, True, 'validates adoption_share risk',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_adoption_share_confidence_threshold', 20.667)
    return _result('check_adoption_share_confidence', adjusted, threshold, True, 'validates adoption_share confidence',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_adoption_share_dependency_threshold', 23.0)
    return _result('check_adoption_share_dependency', adjusted, threshold, False, 'validates adoption_share dependency',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adoption_share_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adoption_share')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_adoption_share_readiness_threshold', 25.333)
    return _result('check_adoption_share_readiness', adjusted, threshold, True, 'validates adoption_share readiness',
                   {'field': 'adoption_share', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_concept_id_presence_threshold', 27.667)
    return _result('check_concept_id_presence', adjusted, threshold, True, 'validates concept_id presence',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_concept_id_range_threshold', 30.0)
    return _result('check_concept_id_range', adjusted, threshold, False, 'validates concept_id range',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_concept_id_stability_threshold', 8.0)
    return _result('check_concept_id_stability', adjusted, threshold, True, 'validates concept_id stability',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_concept_id_freshness_threshold', 10.333)
    return _result('check_concept_id_freshness', adjusted, threshold, True, 'validates concept_id freshness',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_concept_id_coverage_threshold', 12.667)
    return _result('check_concept_id_coverage', adjusted, threshold, False, 'validates concept_id coverage',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_concept_id_consistency_threshold', 15.0)
    return _result('check_concept_id_consistency', adjusted, threshold, True, 'validates concept_id consistency',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_concept_id_risk_threshold', 17.333)
    return _result('check_concept_id_risk', adjusted, threshold, True, 'validates concept_id risk',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_concept_id_confidence_threshold', 19.667)
    return _result('check_concept_id_confidence', adjusted, threshold, False, 'validates concept_id confidence',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_concept_id_dependency_threshold', 22.0)
    return _result('check_concept_id_dependency', adjusted, threshold, True, 'validates concept_id dependency',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_concept_id_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'concept_id')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_concept_id_readiness_threshold', 24.333)
    return _result('check_concept_id_readiness', adjusted, threshold, True, 'validates concept_id readiness',
                   {'field': 'concept_id', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_deprecation_age_days_presence_threshold', 26.667)
    return _result('check_deprecation_age_days_presence', adjusted, threshold, False, 'validates deprecation_age_days presence',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_deprecation_age_days_range_threshold', 29.0)
    return _result('check_deprecation_age_days_range', adjusted, threshold, True, 'validates deprecation_age_days range',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_deprecation_age_days_stability_threshold', 31.333)
    return _result('check_deprecation_age_days_stability', adjusted, threshold, True, 'validates deprecation_age_days stability',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_deprecation_age_days_freshness_threshold', 9.333)
    return _result('check_deprecation_age_days_freshness', adjusted, threshold, False, 'validates deprecation_age_days freshness',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_deprecation_age_days_coverage_threshold', 11.667)
    return _result('check_deprecation_age_days_coverage', adjusted, threshold, True, 'validates deprecation_age_days coverage',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_deprecation_age_days_consistency_threshold', 14.0)
    return _result('check_deprecation_age_days_consistency', adjusted, threshold, True, 'validates deprecation_age_days consistency',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_deprecation_age_days_risk_threshold', 16.333)
    return _result('check_deprecation_age_days_risk', adjusted, threshold, False, 'validates deprecation_age_days risk',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_deprecation_age_days_confidence_threshold', 18.667)
    return _result('check_deprecation_age_days_confidence', adjusted, threshold, True, 'validates deprecation_age_days confidence',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_deprecation_age_days_dependency_threshold', 21.0)
    return _result('check_deprecation_age_days_dependency', adjusted, threshold, True, 'validates deprecation_age_days dependency',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deprecation_age_days_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deprecation_age_days')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_deprecation_age_days_readiness_threshold', 23.333)
    return _result('check_deprecation_age_days_readiness', adjusted, threshold, False, 'validates deprecation_age_days readiness',
                   {'field': 'deprecation_age_days', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_contract_coverage_presence_threshold', 25.667)
    return _result('check_contract_coverage_presence', adjusted, threshold, True, 'validates contract_coverage presence',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_contract_coverage_range_threshold', 28.0)
    return _result('check_contract_coverage_range', adjusted, threshold, True, 'validates contract_coverage range',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_contract_coverage_stability_threshold', 30.333)
    return _result('check_contract_coverage_stability', adjusted, threshold, False, 'validates contract_coverage stability',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_contract_coverage_freshness_threshold', 8.333)
    return _result('check_contract_coverage_freshness', adjusted, threshold, True, 'validates contract_coverage freshness',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_contract_coverage_coverage_threshold', 10.667)
    return _result('check_contract_coverage_coverage', adjusted, threshold, True, 'validates contract_coverage coverage',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_contract_coverage_consistency_threshold', 13.0)
    return _result('check_contract_coverage_consistency', adjusted, threshold, False, 'validates contract_coverage consistency',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_contract_coverage_risk_threshold', 15.333)
    return _result('check_contract_coverage_risk', adjusted, threshold, True, 'validates contract_coverage risk',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_contract_coverage_confidence_threshold', 17.667)
    return _result('check_contract_coverage_confidence', adjusted, threshold, True, 'validates contract_coverage confidence',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_contract_coverage_dependency_threshold', 20.0)
    return _result('check_contract_coverage_dependency', adjusted, threshold, False, 'validates contract_coverage dependency',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_contract_coverage_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'contract_coverage')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_contract_coverage_readiness_threshold', 22.333)
    return _result('check_contract_coverage_readiness', adjusted, threshold, True, 'validates contract_coverage readiness',
                   {'field': 'contract_coverage', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_review_confidence_presence_threshold', 24.667)
    return _result('check_review_confidence_presence', adjusted, threshold, True, 'validates review_confidence presence',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_review_confidence_range_threshold', 27.0)
    return _result('check_review_confidence_range', adjusted, threshold, False, 'validates review_confidence range',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_review_confidence_stability_threshold', 29.333)
    return _result('check_review_confidence_stability', adjusted, threshold, True, 'validates review_confidence stability',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_review_confidence_freshness_threshold', 31.667)
    return _result('check_review_confidence_freshness', adjusted, threshold, True, 'validates review_confidence freshness',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_review_confidence_coverage_threshold', 9.667)
    return _result('check_review_confidence_coverage', adjusted, threshold, False, 'validates review_confidence coverage',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_review_confidence_consistency_threshold', 12.0)
    return _result('check_review_confidence_consistency', adjusted, threshold, True, 'validates review_confidence consistency',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_review_confidence_risk_threshold', 14.333)
    return _result('check_review_confidence_risk', adjusted, threshold, True, 'validates review_confidence risk',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_review_confidence_confidence_threshold', 16.667)
    return _result('check_review_confidence_confidence', adjusted, threshold, False, 'validates review_confidence confidence',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_review_confidence_dependency_threshold', 19.0)
    return _result('check_review_confidence_dependency', adjusted, threshold, True, 'validates review_confidence dependency',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_confidence_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_confidence')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_review_confidence_readiness_threshold', 21.333)
    return _result('check_review_confidence_readiness', adjusted, threshold, True, 'validates review_confidence readiness',
                   {'field': 'review_confidence', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_version_status_presence_threshold', 23.667)
    return _result('check_version_status_presence', adjusted, threshold, False, 'validates version_status presence',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_version_status_range_threshold', 26.0)
    return _result('check_version_status_range', adjusted, threshold, True, 'validates version_status range',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_version_status_stability_threshold', 28.333)
    return _result('check_version_status_stability', adjusted, threshold, True, 'validates version_status stability',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_version_status_freshness_threshold', 30.667)
    return _result('check_version_status_freshness', adjusted, threshold, False, 'validates version_status freshness',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_version_status_coverage_threshold', 8.667)
    return _result('check_version_status_coverage', adjusted, threshold, True, 'validates version_status coverage',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_version_status_consistency_threshold', 11.0)
    return _result('check_version_status_consistency', adjusted, threshold, True, 'validates version_status consistency',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_version_status_risk_threshold', 13.333)
    return _result('check_version_status_risk', adjusted, threshold, False, 'validates version_status risk',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_version_status_confidence_threshold', 15.667)
    return _result('check_version_status_confidence', adjusted, threshold, True, 'validates version_status confidence',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_version_status_dependency_threshold', 18.0)
    return _result('check_version_status_dependency', adjusted, threshold, True, 'validates version_status dependency',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_version_status_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'version_status')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_version_status_readiness_threshold', 20.333)
    return _result('check_version_status_readiness', adjusted, threshold, False, 'validates version_status readiness',
                   {'field': 'version_status', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_mapping_confidence_presence,
    check_mapping_confidence_range,
    check_mapping_confidence_stability,
    check_mapping_confidence_freshness,
    check_mapping_confidence_coverage,
    check_mapping_confidence_consistency,
    check_mapping_confidence_risk,
    check_mapping_confidence_confidence,
    check_mapping_confidence_dependency,
    check_mapping_confidence_readiness,
    check_definition_count_presence,
    check_definition_count_range,
    check_definition_count_stability,
    check_definition_count_freshness,
    check_definition_count_coverage,
    check_definition_count_consistency,
    check_definition_count_risk,
    check_definition_count_confidence,
    check_definition_count_dependency,
    check_definition_count_readiness,
    check_usage_count_presence,
    check_usage_count_range,
    check_usage_count_stability,
    check_usage_count_freshness,
    check_usage_count_coverage,
    check_usage_count_consistency,
    check_usage_count_risk,
    check_usage_count_confidence,
    check_usage_count_dependency,
    check_usage_count_readiness,
    check_language_code_presence,
    check_language_code_range,
    check_language_code_stability,
    check_language_code_freshness,
    check_language_code_coverage,
    check_language_code_consistency,
    check_language_code_risk,
    check_language_code_confidence,
    check_language_code_dependency,
    check_language_code_readiness,
    check_ambiguous_links_presence,
    check_ambiguous_links_range,
    check_ambiguous_links_stability,
    check_ambiguous_links_freshness,
    check_ambiguous_links_coverage,
    check_ambiguous_links_consistency,
    check_ambiguous_links_risk,
    check_ambiguous_links_confidence,
    check_ambiguous_links_dependency,
    check_ambiguous_links_readiness,
    check_cycle_count_presence,
    check_cycle_count_range,
    check_cycle_count_stability,
    check_cycle_count_freshness,
    check_cycle_count_coverage,
    check_cycle_count_consistency,
    check_cycle_count_risk,
    check_cycle_count_confidence,
    check_cycle_count_dependency,
    check_cycle_count_readiness,
    check_adoption_share_presence,
    check_adoption_share_range,
    check_adoption_share_stability,
    check_adoption_share_freshness,
    check_adoption_share_coverage,
    check_adoption_share_consistency,
    check_adoption_share_risk,
    check_adoption_share_confidence,
    check_adoption_share_dependency,
    check_adoption_share_readiness,
    check_concept_id_presence,
    check_concept_id_range,
    check_concept_id_stability,
    check_concept_id_freshness,
    check_concept_id_coverage,
    check_concept_id_consistency,
    check_concept_id_risk,
    check_concept_id_confidence,
    check_concept_id_dependency,
    check_concept_id_readiness,
    check_deprecation_age_days_presence,
    check_deprecation_age_days_range,
    check_deprecation_age_days_stability,
    check_deprecation_age_days_freshness,
    check_deprecation_age_days_coverage,
    check_deprecation_age_days_consistency,
    check_deprecation_age_days_risk,
    check_deprecation_age_days_confidence,
    check_deprecation_age_days_dependency,
    check_deprecation_age_days_readiness,
    check_contract_coverage_presence,
    check_contract_coverage_range,
    check_contract_coverage_stability,
    check_contract_coverage_freshness,
    check_contract_coverage_coverage,
    check_contract_coverage_consistency,
    check_contract_coverage_risk,
    check_contract_coverage_confidence,
    check_contract_coverage_dependency,
    check_contract_coverage_readiness,
    check_review_confidence_presence,
    check_review_confidence_range,
    check_review_confidence_stability,
    check_review_confidence_freshness,
    check_review_confidence_coverage,
    check_review_confidence_consistency,
    check_review_confidence_risk,
    check_review_confidence_confidence,
    check_review_confidence_dependency,
    check_review_confidence_readiness,
    check_version_status_presence,
    check_version_status_range,
    check_version_status_stability,
    check_version_status_freshness,
    check_version_status_coverage,
    check_version_status_consistency,
    check_version_status_risk,
    check_version_status_confidence,
    check_version_status_dependency,
    check_version_status_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'critical': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'critical': sum(item.severity == 'critical' for item in results)}
