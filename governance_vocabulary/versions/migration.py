from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from governance_vocabulary.concepts.model import ContractError, Decision, DomainRecord, RuleResult, bounded
from governance_vocabulary.quality.calibration import grouped_metrics, record_score
from governance_vocabulary.validation.consistency import evaluate

STATES = ['proposed', 'curated', 'versioned', 'mapped', 'adopted', 'deprecated']
TRANSITIONS = {state: tuple(STATES[i + 1:i + 3]) for i, state in enumerate(STATES)}


def impact_gate(context: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the recorded cross-version impact gate, if one is in context."""
    gate = context.get('impact_gate')
    if not isinstance(gate, Mapping):
        return None
    return dict(gate)


def impact_blocks_migration(context: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    """Explain whether the impact analysis blocks a migration decision.

    The gate only blocks when the stored analysis reports incomparable
    statistics. The reason codes are returned verbatim so callers can tell a
    missing equivalent (no_equivalent / mapping_gap) apart from an adopted
    mapping that is still pending (unadopted_link) or a genuine data change
    observed on comparable chains.
    """
    gate = impact_gate(context)
    if gate is None:
        return False, ()
    reasons = tuple(str(code) for code in gate.get('blocking_reason_codes', ()))
    blocked = gate.get('decision') == 'hold' or bool(reasons)
    return blocked, reasons


@dataclass(frozen=True)
class TransitionPlan:
    from_state: str
    to_state: str
    allowed: bool
    reasons: tuple[str, ...]
    score: float

def allowed_targets(state: str) -> tuple[str, ...]:
    if state not in TRANSITIONS:
        raise ContractError('unknown workflow state')
    return TRANSITIONS[state]

def plan_transition(record: DomainRecord, target: str, context: Mapping[str, Any] | None = None) -> TransitionPlan:
    context = context or {}
    if target not in STATES:
        raise ContractError('unknown target state')
    scorecard = record_score(record, context)
    reasons: list[str] = []
    structurally_allowed = target in allowed_targets(record.state)
    if not structurally_allowed:
        reasons.append('transition is not adjacent in the lifecycle')
    threshold = float(context.get('transition_threshold', 0.42))
    if scorecard['score'] < threshold:
        reasons.append('record score is below the transition threshold')
    blocked, impact_reasons = impact_blocks_migration(context)
    if blocked:
        reasons.append('impact analysis blocks migration: ' + ','.join(impact_reasons))
    return TransitionPlan(record.state, target, structurally_allowed and not reasons, tuple(reasons or ['eligible']), scorecard['score'])

def apply_transition(record: DomainRecord, target: str, context: Mapping[str, Any] | None = None) -> DomainRecord:
    plan = plan_transition(record, target, context)
    if not plan.allowed:
        raise ContractError('; '.join(plan.reasons))
    return record.with_state(target)

def guard_mapping_confidence_grade_consistency_01(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_mapping_confidence_grade_consistency_01_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_grade_consistency_01' + (':passed' if allowed else ':blocked')

def guard_definition_count_inspection_coverage_02(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_definition_count_inspection_coverage_02_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_inspection_coverage_02' + (':passed' if allowed else ':blocked')

def guard_usage_count_false_release_risk_03(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_usage_count_false_release_risk_03_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_false_release_risk_03' + (':passed' if allowed else ':blocked')

def guard_language_code_origin_drift_04(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_language_code_origin_drift_04_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_origin_drift_04' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_feedback_latency_05(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_ambiguous_links_feedback_latency_05_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_feedback_latency_05' + (':passed' if allowed else ':blocked')

def guard_cycle_count_lot_value_06(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_cycle_count_lot_value_06_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_lot_value_06' + (':passed' if allowed else ':blocked')

def guard_adoption_share_recall_exposure_07(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_adoption_share_recall_exposure_07_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_recall_exposure_07' + (':passed' if allowed else ':blocked')

def guard_concept_id_calibration_need_08(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_concept_id_calibration_need_08_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_calibration_need_08' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_grade_consistency_09(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_grade_consistency_09_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_grade_consistency_09' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_inspection_coverage_10(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_contract_coverage_inspection_coverage_10_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_inspection_coverage_10' + (':passed' if allowed else ':blocked')

def guard_review_confidence_false_release_risk_11(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_review_confidence_false_release_risk_11_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_false_release_risk_11' + (':passed' if allowed else ':blocked')

def guard_version_status_origin_drift_12(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_version_status_origin_drift_12_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_origin_drift_12' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_feedback_latency_13(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_mapping_confidence_feedback_latency_13_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_feedback_latency_13' + (':passed' if allowed else ':blocked')

def guard_definition_count_lot_value_14(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_definition_count_lot_value_14_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_lot_value_14' + (':passed' if allowed else ':blocked')

def guard_usage_count_recall_exposure_15(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_usage_count_recall_exposure_15_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_recall_exposure_15' + (':passed' if allowed else ':blocked')

def guard_language_code_calibration_need_16(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_language_code_calibration_need_16_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_calibration_need_16' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_grade_consistency_17(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_ambiguous_links_grade_consistency_17_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_grade_consistency_17' + (':passed' if allowed else ':blocked')

def guard_cycle_count_inspection_coverage_18(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_cycle_count_inspection_coverage_18_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_inspection_coverage_18' + (':passed' if allowed else ':blocked')

def guard_adoption_share_false_release_risk_19(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_adoption_share_false_release_risk_19_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_false_release_risk_19' + (':passed' if allowed else ':blocked')

def guard_concept_id_origin_drift_20(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_concept_id_origin_drift_20_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_origin_drift_20' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_feedback_latency_21(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_feedback_latency_21_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_feedback_latency_21' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_lot_value_22(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_contract_coverage_lot_value_22_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_lot_value_22' + (':passed' if allowed else ':blocked')

def guard_review_confidence_recall_exposure_23(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_review_confidence_recall_exposure_23_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_recall_exposure_23' + (':passed' if allowed else ':blocked')

def guard_version_status_calibration_need_24(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_version_status_calibration_need_24_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_calibration_need_24' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_grade_consistency_25(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_mapping_confidence_grade_consistency_25_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_grade_consistency_25' + (':passed' if allowed else ':blocked')

def guard_definition_count_inspection_coverage_26(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_definition_count_inspection_coverage_26_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_inspection_coverage_26' + (':passed' if allowed else ':blocked')

def guard_usage_count_false_release_risk_27(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_usage_count_false_release_risk_27_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_false_release_risk_27' + (':passed' if allowed else ':blocked')

def guard_language_code_origin_drift_28(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_language_code_origin_drift_28_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_origin_drift_28' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_feedback_latency_29(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_ambiguous_links_feedback_latency_29_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_feedback_latency_29' + (':passed' if allowed else ':blocked')

def guard_cycle_count_lot_value_30(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_cycle_count_lot_value_30_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_lot_value_30' + (':passed' if allowed else ':blocked')

def guard_adoption_share_recall_exposure_31(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_adoption_share_recall_exposure_31_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_recall_exposure_31' + (':passed' if allowed else ':blocked')

def guard_concept_id_calibration_need_32(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_concept_id_calibration_need_32_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_calibration_need_32' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_grade_consistency_33(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_grade_consistency_33_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_grade_consistency_33' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_inspection_coverage_34(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_contract_coverage_inspection_coverage_34_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_inspection_coverage_34' + (':passed' if allowed else ':blocked')

def guard_review_confidence_false_release_risk_35(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_review_confidence_false_release_risk_35_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_false_release_risk_35' + (':passed' if allowed else ':blocked')

def guard_version_status_origin_drift_36(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_version_status_origin_drift_36_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_origin_drift_36' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_feedback_latency_37(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_mapping_confidence_feedback_latency_37_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_feedback_latency_37' + (':passed' if allowed else ':blocked')

def guard_definition_count_lot_value_38(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_definition_count_lot_value_38_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_lot_value_38' + (':passed' if allowed else ':blocked')

def guard_usage_count_recall_exposure_39(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_usage_count_recall_exposure_39_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_recall_exposure_39' + (':passed' if allowed else ':blocked')

def guard_language_code_calibration_need_40(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_language_code_calibration_need_40_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_calibration_need_40' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_grade_consistency_41(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_ambiguous_links_grade_consistency_41_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_grade_consistency_41' + (':passed' if allowed else ':blocked')

def guard_cycle_count_inspection_coverage_42(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_cycle_count_inspection_coverage_42_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_inspection_coverage_42' + (':passed' if allowed else ':blocked')

def guard_adoption_share_false_release_risk_43(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_adoption_share_false_release_risk_43_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_false_release_risk_43' + (':passed' if allowed else ':blocked')

def guard_concept_id_origin_drift_44(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_concept_id_origin_drift_44_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_origin_drift_44' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_feedback_latency_45(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_feedback_latency_45_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_feedback_latency_45' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_lot_value_46(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_contract_coverage_lot_value_46_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_lot_value_46' + (':passed' if allowed else ':blocked')

def guard_review_confidence_recall_exposure_47(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_review_confidence_recall_exposure_47_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_recall_exposure_47' + (':passed' if allowed else ':blocked')

def guard_version_status_calibration_need_48(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_version_status_calibration_need_48_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_calibration_need_48' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_grade_consistency_49(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_mapping_confidence_grade_consistency_49_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_grade_consistency_49' + (':passed' if allowed else ':blocked')

def guard_definition_count_inspection_coverage_50(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_definition_count_inspection_coverage_50_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_inspection_coverage_50' + (':passed' if allowed else ':blocked')

def guard_usage_count_false_release_risk_51(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_usage_count_false_release_risk_51_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_false_release_risk_51' + (':passed' if allowed else ':blocked')

def guard_language_code_origin_drift_52(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_language_code_origin_drift_52_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_origin_drift_52' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_feedback_latency_53(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_ambiguous_links_feedback_latency_53_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_feedback_latency_53' + (':passed' if allowed else ':blocked')

def guard_cycle_count_lot_value_54(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_cycle_count_lot_value_54_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_lot_value_54' + (':passed' if allowed else ':blocked')

def guard_adoption_share_recall_exposure_55(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_adoption_share_recall_exposure_55_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_recall_exposure_55' + (':passed' if allowed else ':blocked')

def guard_concept_id_calibration_need_56(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_concept_id_calibration_need_56_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_calibration_need_56' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_grade_consistency_57(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_grade_consistency_57_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_grade_consistency_57' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_inspection_coverage_58(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_contract_coverage_inspection_coverage_58_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_inspection_coverage_58' + (':passed' if allowed else ':blocked')

def guard_review_confidence_false_release_risk_59(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_review_confidence_false_release_risk_59_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_false_release_risk_59' + (':passed' if allowed else ':blocked')

def guard_version_status_origin_drift_60(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_version_status_origin_drift_60_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_origin_drift_60' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_feedback_latency_61(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_mapping_confidence_feedback_latency_61_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_feedback_latency_61' + (':passed' if allowed else ':blocked')

def guard_definition_count_lot_value_62(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_definition_count_lot_value_62_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_lot_value_62' + (':passed' if allowed else ':blocked')

def guard_usage_count_recall_exposure_63(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_usage_count_recall_exposure_63_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_recall_exposure_63' + (':passed' if allowed else ':blocked')

def guard_language_code_calibration_need_64(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_language_code_calibration_need_64_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_calibration_need_64' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_grade_consistency_65(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_ambiguous_links_grade_consistency_65_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_grade_consistency_65' + (':passed' if allowed else ':blocked')

def guard_cycle_count_inspection_coverage_66(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_cycle_count_inspection_coverage_66_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_inspection_coverage_66' + (':passed' if allowed else ':blocked')

def guard_adoption_share_false_release_risk_67(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_adoption_share_false_release_risk_67_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_false_release_risk_67' + (':passed' if allowed else ':blocked')

def guard_concept_id_origin_drift_68(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_concept_id_origin_drift_68_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_origin_drift_68' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_feedback_latency_69(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_feedback_latency_69_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_feedback_latency_69' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_lot_value_70(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_contract_coverage_lot_value_70_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_lot_value_70' + (':passed' if allowed else ':blocked')

def guard_review_confidence_recall_exposure_71(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_review_confidence_recall_exposure_71_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_recall_exposure_71' + (':passed' if allowed else ':blocked')

def guard_version_status_calibration_need_72(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_version_status_calibration_need_72_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_calibration_need_72' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_grade_consistency_73(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_mapping_confidence_grade_consistency_73_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_grade_consistency_73' + (':passed' if allowed else ':blocked')

def guard_definition_count_inspection_coverage_74(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_definition_count_inspection_coverage_74_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_inspection_coverage_74' + (':passed' if allowed else ':blocked')

def guard_usage_count_false_release_risk_75(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_usage_count_false_release_risk_75_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_false_release_risk_75' + (':passed' if allowed else ':blocked')

def guard_language_code_origin_drift_76(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_language_code_origin_drift_76_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_origin_drift_76' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_feedback_latency_77(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_ambiguous_links_feedback_latency_77_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_feedback_latency_77' + (':passed' if allowed else ':blocked')

def guard_cycle_count_lot_value_78(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_cycle_count_lot_value_78_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_lot_value_78' + (':passed' if allowed else ':blocked')

def guard_adoption_share_recall_exposure_79(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_adoption_share_recall_exposure_79_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_recall_exposure_79' + (':passed' if allowed else ':blocked')

def guard_concept_id_calibration_need_80(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_concept_id_calibration_need_80_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_calibration_need_80' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_grade_consistency_81(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_grade_consistency_81_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_grade_consistency_81' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_inspection_coverage_82(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_contract_coverage_inspection_coverage_82_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_inspection_coverage_82' + (':passed' if allowed else ':blocked')

def guard_review_confidence_false_release_risk_83(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_review_confidence_false_release_risk_83_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_false_release_risk_83' + (':passed' if allowed else ':blocked')

def guard_version_status_origin_drift_84(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_version_status_origin_drift_84_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_origin_drift_84' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_feedback_latency_85(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_mapping_confidence_feedback_latency_85_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_feedback_latency_85' + (':passed' if allowed else ':blocked')

def guard_definition_count_lot_value_86(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_definition_count_lot_value_86_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_lot_value_86' + (':passed' if allowed else ':blocked')

def guard_usage_count_recall_exposure_87(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_usage_count_recall_exposure_87_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_recall_exposure_87' + (':passed' if allowed else ':blocked')

def guard_language_code_calibration_need_88(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_language_code_calibration_need_88_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_calibration_need_88' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_grade_consistency_89(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_ambiguous_links_grade_consistency_89_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_grade_consistency_89' + (':passed' if allowed else ':blocked')

def guard_cycle_count_inspection_coverage_90(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_cycle_count_inspection_coverage_90_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_inspection_coverage_90' + (':passed' if allowed else ':blocked')

def guard_adoption_share_false_release_risk_91(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_adoption_share_false_release_risk_91_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_false_release_risk_91' + (':passed' if allowed else ':blocked')

def guard_concept_id_origin_drift_92(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_concept_id_origin_drift_92_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_origin_drift_92' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_feedback_latency_93(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_feedback_latency_93_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_feedback_latency_93' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_lot_value_94(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_contract_coverage_lot_value_94_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_lot_value_94' + (':passed' if allowed else ':blocked')

def guard_review_confidence_recall_exposure_95(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_review_confidence_recall_exposure_95_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_recall_exposure_95' + (':passed' if allowed else ':blocked')

def guard_version_status_calibration_need_96(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_version_status_calibration_need_96_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_calibration_need_96' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_grade_consistency_97(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_mapping_confidence_grade_consistency_97_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_grade_consistency_97' + (':passed' if allowed else ':blocked')

def guard_definition_count_inspection_coverage_98(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_definition_count_inspection_coverage_98_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_inspection_coverage_98' + (':passed' if allowed else ':blocked')

def guard_usage_count_false_release_risk_99(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_usage_count_false_release_risk_99_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_false_release_risk_99' + (':passed' if allowed else ':blocked')

def guard_language_code_origin_drift_100(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_language_code_origin_drift_100_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_origin_drift_100' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_feedback_latency_101(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_ambiguous_links_feedback_latency_101_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_feedback_latency_101' + (':passed' if allowed else ':blocked')

def guard_cycle_count_lot_value_102(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_cycle_count_lot_value_102_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_lot_value_102' + (':passed' if allowed else ':blocked')

def guard_adoption_share_recall_exposure_103(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_adoption_share_recall_exposure_103_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_recall_exposure_103' + (':passed' if allowed else ':blocked')

def guard_concept_id_calibration_need_104(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_concept_id_calibration_need_104_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_calibration_need_104' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_grade_consistency_105(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_grade_consistency_105_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_grade_consistency_105' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_inspection_coverage_106(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_contract_coverage_inspection_coverage_106_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_inspection_coverage_106' + (':passed' if allowed else ':blocked')

def guard_review_confidence_false_release_risk_107(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_review_confidence_false_release_risk_107_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_false_release_risk_107' + (':passed' if allowed else ':blocked')

def guard_version_status_origin_drift_108(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_version_status_origin_drift_108_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_origin_drift_108' + (':passed' if allowed else ':blocked')

def guard_mapping_confidence_feedback_latency_109(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_mapping_confidence_feedback_latency_109_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_mapping_confidence_feedback_latency_109' + (':passed' if allowed else ':blocked')

def guard_definition_count_lot_value_110(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_definition_count_lot_value_110_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_definition_count_lot_value_110' + (':passed' if allowed else ':blocked')

def guard_usage_count_recall_exposure_111(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_usage_count_recall_exposure_111_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_usage_count_recall_exposure_111' + (':passed' if allowed else ':blocked')

def guard_language_code_calibration_need_112(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_language_code_calibration_need_112_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_language_code_calibration_need_112' + (':passed' if allowed else ':blocked')

def guard_ambiguous_links_grade_consistency_113(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('grade_consistency', 0.0)
    floor = float(context.get('guard_ambiguous_links_grade_consistency_113_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_ambiguous_links_grade_consistency_113' + (':passed' if allowed else ':blocked')

def guard_cycle_count_inspection_coverage_114(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('inspection_coverage', 0.0)
    floor = float(context.get('guard_cycle_count_inspection_coverage_114_floor', 0.32))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_cycle_count_inspection_coverage_114' + (':passed' if allowed else ':blocked')

def guard_adoption_share_false_release_risk_115(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('false_release_risk', 0.0)
    floor = float(context.get('guard_adoption_share_false_release_risk_115_floor', 0.39))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_adoption_share_false_release_risk_115' + (':passed' if allowed else ':blocked')

def guard_concept_id_origin_drift_116(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('origin_drift', 0.0)
    floor = float(context.get('guard_concept_id_origin_drift_116_floor', 0.46))
    state_ok = STATES.index(record.state) <= STATES.index('curated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_concept_id_origin_drift_116' + (':passed' if allowed else ':blocked')

def guard_deprecation_age_days_feedback_latency_117(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('feedback_latency', 0.0)
    floor = float(context.get('guard_deprecation_age_days_feedback_latency_117_floor', 0.53))
    state_ok = STATES.index(record.state) <= STATES.index('versioned')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_deprecation_age_days_feedback_latency_117' + (':passed' if allowed else ':blocked')

def guard_contract_coverage_lot_value_118(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('lot_value', 0.0)
    floor = float(context.get('guard_contract_coverage_lot_value_118_floor', 0.6000000000000001))
    state_ok = STATES.index(record.state) <= STATES.index('mapped')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_contract_coverage_lot_value_118' + (':passed' if allowed else ':blocked')

def guard_review_confidence_recall_exposure_119(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('recall_exposure', 0.0)
    floor = float(context.get('guard_review_confidence_recall_exposure_119_floor', 0.67))
    state_ok = STATES.index(record.state) <= STATES.index('adopted')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_review_confidence_recall_exposure_119' + (':passed' if allowed else ':blocked')

def guard_version_status_calibration_need_120(record: DomainRecord, context: Mapping[str, Any]) -> tuple[bool, str]:
    metrics = context.get('_metrics') or grouped_metrics(record, context)
    value = metrics.get('calibration_need', 0.0)
    floor = float(context.get('guard_version_status_calibration_need_120_floor', 0.25))
    state_ok = STATES.index(record.state) <= STATES.index('deprecated')
    allowed = state_ok and value >= min(1.0, floor)
    return allowed, 'guard_version_status_calibration_need_120' + (':passed' if allowed else ':blocked')

GUARDS: tuple[Callable[[DomainRecord, Mapping[str, Any]], tuple[bool, str]], ...] = (
    guard_mapping_confidence_grade_consistency_01,
    guard_definition_count_inspection_coverage_02,
    guard_usage_count_false_release_risk_03,
    guard_language_code_origin_drift_04,
    guard_ambiguous_links_feedback_latency_05,
    guard_cycle_count_lot_value_06,
    guard_adoption_share_recall_exposure_07,
    guard_concept_id_calibration_need_08,
    guard_deprecation_age_days_grade_consistency_09,
    guard_contract_coverage_inspection_coverage_10,
    guard_review_confidence_false_release_risk_11,
    guard_version_status_origin_drift_12,
    guard_mapping_confidence_feedback_latency_13,
    guard_definition_count_lot_value_14,
    guard_usage_count_recall_exposure_15,
    guard_language_code_calibration_need_16,
    guard_ambiguous_links_grade_consistency_17,
    guard_cycle_count_inspection_coverage_18,
    guard_adoption_share_false_release_risk_19,
    guard_concept_id_origin_drift_20,
    guard_deprecation_age_days_feedback_latency_21,
    guard_contract_coverage_lot_value_22,
    guard_review_confidence_recall_exposure_23,
    guard_version_status_calibration_need_24,
    guard_mapping_confidence_grade_consistency_25,
    guard_definition_count_inspection_coverage_26,
    guard_usage_count_false_release_risk_27,
    guard_language_code_origin_drift_28,
    guard_ambiguous_links_feedback_latency_29,
    guard_cycle_count_lot_value_30,
    guard_adoption_share_recall_exposure_31,
    guard_concept_id_calibration_need_32,
    guard_deprecation_age_days_grade_consistency_33,
    guard_contract_coverage_inspection_coverage_34,
    guard_review_confidence_false_release_risk_35,
    guard_version_status_origin_drift_36,
    guard_mapping_confidence_feedback_latency_37,
    guard_definition_count_lot_value_38,
    guard_usage_count_recall_exposure_39,
    guard_language_code_calibration_need_40,
    guard_ambiguous_links_grade_consistency_41,
    guard_cycle_count_inspection_coverage_42,
    guard_adoption_share_false_release_risk_43,
    guard_concept_id_origin_drift_44,
    guard_deprecation_age_days_feedback_latency_45,
    guard_contract_coverage_lot_value_46,
    guard_review_confidence_recall_exposure_47,
    guard_version_status_calibration_need_48,
    guard_mapping_confidence_grade_consistency_49,
    guard_definition_count_inspection_coverage_50,
    guard_usage_count_false_release_risk_51,
    guard_language_code_origin_drift_52,
    guard_ambiguous_links_feedback_latency_53,
    guard_cycle_count_lot_value_54,
    guard_adoption_share_recall_exposure_55,
    guard_concept_id_calibration_need_56,
    guard_deprecation_age_days_grade_consistency_57,
    guard_contract_coverage_inspection_coverage_58,
    guard_review_confidence_false_release_risk_59,
    guard_version_status_origin_drift_60,
    guard_mapping_confidence_feedback_latency_61,
    guard_definition_count_lot_value_62,
    guard_usage_count_recall_exposure_63,
    guard_language_code_calibration_need_64,
    guard_ambiguous_links_grade_consistency_65,
    guard_cycle_count_inspection_coverage_66,
    guard_adoption_share_false_release_risk_67,
    guard_concept_id_origin_drift_68,
    guard_deprecation_age_days_feedback_latency_69,
    guard_contract_coverage_lot_value_70,
    guard_review_confidence_recall_exposure_71,
    guard_version_status_calibration_need_72,
    guard_mapping_confidence_grade_consistency_73,
    guard_definition_count_inspection_coverage_74,
    guard_usage_count_false_release_risk_75,
    guard_language_code_origin_drift_76,
    guard_ambiguous_links_feedback_latency_77,
    guard_cycle_count_lot_value_78,
    guard_adoption_share_recall_exposure_79,
    guard_concept_id_calibration_need_80,
    guard_deprecation_age_days_grade_consistency_81,
    guard_contract_coverage_inspection_coverage_82,
    guard_review_confidence_false_release_risk_83,
    guard_version_status_origin_drift_84,
    guard_mapping_confidence_feedback_latency_85,
    guard_definition_count_lot_value_86,
    guard_usage_count_recall_exposure_87,
    guard_language_code_calibration_need_88,
    guard_ambiguous_links_grade_consistency_89,
    guard_cycle_count_inspection_coverage_90,
    guard_adoption_share_false_release_risk_91,
    guard_concept_id_origin_drift_92,
    guard_deprecation_age_days_feedback_latency_93,
    guard_contract_coverage_lot_value_94,
    guard_review_confidence_recall_exposure_95,
    guard_version_status_calibration_need_96,
    guard_mapping_confidence_grade_consistency_97,
    guard_definition_count_inspection_coverage_98,
    guard_usage_count_false_release_risk_99,
    guard_language_code_origin_drift_100,
    guard_ambiguous_links_feedback_latency_101,
    guard_cycle_count_lot_value_102,
    guard_adoption_share_recall_exposure_103,
    guard_concept_id_calibration_need_104,
    guard_deprecation_age_days_grade_consistency_105,
    guard_contract_coverage_inspection_coverage_106,
    guard_review_confidence_false_release_risk_107,
    guard_version_status_origin_drift_108,
    guard_mapping_confidence_feedback_latency_109,
    guard_definition_count_lot_value_110,
    guard_usage_count_recall_exposure_111,
    guard_language_code_calibration_need_112,
    guard_ambiguous_links_grade_consistency_113,
    guard_cycle_count_inspection_coverage_114,
    guard_adoption_share_false_release_risk_115,
    guard_concept_id_origin_drift_116,
    guard_deprecation_age_days_feedback_latency_117,
    guard_contract_coverage_lot_value_118,
    guard_review_confidence_recall_exposure_119,
    guard_version_status_calibration_need_120,
)

def guard_report(record: DomainRecord, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    context = dict(context or {})
    context['_metrics'] = grouped_metrics(record, context)
    results = [guard(record, context) for guard in GUARDS]
    return {'passed': sum(item[0] for item in results), 'failed': sum(not item[0] for item in results),
            'messages': [item[1] for item in results]}

def decide(record: DomainRecord, context: Mapping[str, Any] | None = None) -> Decision:
    context = context or {}
    rules = evaluate(record, context)
    scorecard = record_score(record, context)
    guards = guard_report(record, context)
    effective_score = scorecard['score'] * 0.65 + float(context.get('domain_signal', 0.5)) * 0.35
    critical = sum(item.severity == 'critical' for item in rules)
    blocked, impact_reasons = impact_blocks_migration(context)
    if context.get('domain_severity') == 'critical':
        outcome = 'hold'
    elif critical:
        outcome = 'hold'
    elif blocked:
        outcome = 'hold'
    elif effective_score >= float(context.get('approve_threshold', 0.62)) and guards['passed'] >= guards['failed']:
        outcome = 'approve'
    elif effective_score >= float(context.get('review_threshold', 0.38)):
        outcome = 'review'
    else:
        outcome = 'reject'
    reasons = (f"score={effective_score:.6f}", f"critical={critical}",
               f"guards={guards['passed']}/{guards['passed'] + guards['failed']}")
    if blocked:
        reasons = reasons + ("impact_block=" + ",".join(impact_reasons),)
    return Decision(record.record_id, outcome, effective_score, reasons, rules, scorecard['metrics'])

def advance_for_outcome(record: DomainRecord, decision: Decision) -> DomainRecord:
    current = STATES.index(record.state)
    if decision.outcome == 'approve' and current + 1 < len(STATES):
        return record.with_state(STATES[current + 1])
    if decision.outcome == 'hold' and STATES[-1] != record.state:
        return record.with_state(STATES[-1])
    return record
