from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from governance_vocabulary.concepts.model import Decision, DomainRecord, canonical_json, stable_hash, utc_now
from governance_vocabulary.impact.analysis import ImpactAnalysis, evaluate_migration_gate


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(body + "\n", encoding="utf-8")
    return stable_hash(value)


def write_records(path: Path, records: Iterable[DomainRecord], decisions: Mapping[str, Decision]) -> int:
    rows = []
    for record in records:
        decision = decisions.get(record.record_id)
        rows.append({"record_id": record.record_id, "state": record.state, "version": record.version,
                     "source": record.source, "fingerprint": record.fingerprint,
                     "outcome": decision.outcome if decision else "", "score": decision.score if decision else ""})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "state", "version", "source", "fingerprint", "outcome", "score"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_rules(path: Path, decisions: Mapping[str, Decision]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "code", "passed", "score", "severity", "message"])
        writer.writeheader()
        for record_id, decision in sorted(decisions.items()):
            for result in decision.rule_results:
                writer.writerow({"record_id": record_id, "code": result.code, "passed": result.passed,
                                 "score": result.score, "severity": result.severity, "message": result.message})
                count += 1
    return count


def write_mapping_chains(path: Path, analysis: ImpactAnalysis) -> int:
    fieldnames = [
        "concept_id", "source_version", "target_version", "chain_complete",
        "reason_code", "chain_confidence", "resolved_target_concept", "hop_order",
        "mapping_id", "hop_source_version", "hop_source_concept",
        "hop_target_version", "hop_target_concept", "relation", "status", "confidence",
    ]
    rows = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for impact in analysis.impacts:
            chain = impact.chain
            if not chain.hops:
                writer.writerow({
                    "concept_id": impact.concept_id,
                    "source_version": chain.source_version,
                    "target_version": chain.target_version,
                    "chain_complete": chain.complete,
                    "reason_code": chain.reason_code,
                    "chain_confidence": chain.confidence,
                    "resolved_target_concept": chain.target_concept or "",
                    "hop_order": 0,
                })
                rows += 1
                continue
            for hop in chain.hops:
                writer.writerow({
                    "concept_id": impact.concept_id,
                    "source_version": chain.source_version,
                    "target_version": chain.target_version,
                    "chain_complete": chain.complete,
                    "reason_code": chain.reason_code,
                    "chain_confidence": chain.confidence,
                    "resolved_target_concept": chain.target_concept or "",
                    "hop_order": hop.order,
                    "mapping_id": hop.mapping_id,
                    "hop_source_version": hop.source_version,
                    "hop_source_concept": hop.source_concept,
                    "hop_target_version": hop.target_version,
                    "hop_target_concept": hop.target_concept,
                    "relation": hop.relation,
                    "status": hop.status,
                    "confidence": hop.confidence,
                })
                rows += 1
    return rows


def build_summary(records: list[DomainRecord], decisions: Mapping[str, Decision], snapshot: Mapping[str, Any],
                  impact_summary: Mapping[str, Any] | None = None) -> dict[str, Any]:
    outcomes: dict[str, int] = {}
    for decision in decisions.values():
        outcomes[decision.outcome] = outcomes.get(decision.outcome, 0) + 1
    scores = [decision.score for decision in decisions.values()]
    summary = {"product": '多国人工智能治理术语本体版本迁移库', "entity": 'governance_concept', "generated_at": utc_now(),
               "record_count": len(records), "decision_count": len(decisions), "outcomes": outcomes,
               "average_score": sum(scores) / len(scores) if scores else 0.0,
               "minimum_score": min(scores) if scores else 0.0, "maximum_score": max(scores) if scores else 0.0,
               "repository": snapshot}
    if impact_summary is not None:
        summary["impact_analysis"] = dict(impact_summary)
    return summary


def export_bundle(output: str | Path, records: list[DomainRecord], decisions: Mapping[str, Decision],
                  snapshot: Mapping[str, Any], events: list[dict[str, Any]],
                  analysis: ImpactAnalysis | None = None) -> dict[str, Any]:
    root = ensure_output(output)
    impact_summary = None
    if analysis is not None:
        gate = evaluate_migration_gate(analysis)
        impact_summary = {
            "analysis_id": analysis.analysis_id,
            "mapping_set_id": analysis.mapping_set_id,
            "mapping_set_fingerprint": analysis.mapping_set_fingerprint,
            "source_version": analysis.source_version,
            "target_version": analysis.target_version,
            "affected_concepts": list(analysis.affected_concepts),
            "comparable_concepts": list(analysis.comparable_concepts),
            "incomparable_concepts": list(analysis.incomparable_concepts),
            "reason_summary": dict(sorted(analysis.reason_summary.items())),
            "migration_gate": gate,
        }
    summary = build_summary(records, decisions, snapshot, impact_summary)
    record_count = write_records(root / "records.csv", records, decisions)
    rule_count = write_rules(root / "rules.csv", decisions)
    summary_hash = write_json(root / "summary.json", summary)
    decision_hash = write_json(root / "decisions.json", [value.as_dict() for _, value in sorted(decisions.items())])
    event_hash = write_json(root / "audit-events.json", events)
    files = {"summary.json": summary_hash, "decisions.json": decision_hash,
             "audit-events.json": event_hash}
    manifest = {"files": files, "record_rows": record_count,
                "rule_rows": rule_count, "created_at": utc_now()}
    if analysis is not None:
        impact_hash = write_json(root / "impact-analysis.json",
                                 {"analysis": analysis.as_dict(),
                                  "migration_gate": evaluate_migration_gate(analysis)})
        chain_rows = write_mapping_chains(root / "mapping-chains.csv", analysis)
        files["impact-analysis.json"] = impact_hash
        manifest["impact_rows"] = len(analysis.impacts)
        manifest["mapping_chain_rows"] = chain_rows
        manifest["impact_analysis_id"] = analysis.analysis_id
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


def verify_bundle(output: str | Path) -> list[str]:
    root = Path(output)
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return ["manifest.json is missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_hash = manifest.pop("manifest_hash", "")
    if stable_hash(manifest) != expected_manifest_hash:
        errors.append("manifest hash mismatch")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if stable_hash(value) != expected:
            errors.append(f"{name} hash mismatch")
    return errors
