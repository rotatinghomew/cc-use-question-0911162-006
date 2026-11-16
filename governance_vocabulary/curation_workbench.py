from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from governance_vocabulary.concepts.model import ContractError, Decision, DomainRecord, records_from_fixture, stable_hash
from governance_vocabulary.registry.vocabulary_store import Repository
from governance_vocabulary.versions.migration import advance_for_outcome, decide
from governance_vocabulary.contracts.usage_report import export_bundle, verify_bundle
from governance_vocabulary.mappings.composition import derive_context
from governance_vocabulary.impact.analysis import analyze_impact, evaluate_migration_gate
from governance_vocabulary.impact.model import (
    mapping_set_from_fixture,
    references_from_fixture,
    snapshots_from_fixture,
)
from governance_vocabulary.impact.persistence import ImpactRepository

from governance_vocabulary.semantic_signal.semantic_stability import augment_context


class Application:
    def __init__(self, database: str | Path, context: Mapping[str, Any] | None = None):
        self.repository = Repository(database)
        self.impact_repository = ImpactRepository(self.repository.connect)
        self.context = dict(context or {})

    def build_impact_analysis(self, fixture: Mapping[str, Any]) -> dict[str, Any] | None:
        """Build, persist and gate the cross-version impact analysis.

        Returns ``None`` when the fixture carries no mapping set, preserving
        the legacy behaviour for fixtures that do not describe a migration.
        """
        mapping_set = mapping_set_from_fixture(fixture)
        if mapping_set is None:
            return None
        source_version = str(fixture.get("source_version", "")).strip()
        target_version = str(
            fixture.get("target_version") or mapping_set.vocabulary_version
        ).strip()
        if not source_version:
            raise ContractError("impact analysis requires source_version")
        if source_version == target_version:
            raise ContractError("impact analysis requires distinct source and target versions")

        self.impact_repository.save_mapping_set(mapping_set, self.repository)
        snapshots = snapshots_from_fixture(fixture)
        references = references_from_fixture(fixture)
        analysis = analyze_impact(
            mapping_set,
            source_version,
            target_version,
            snapshots,
            references,
        )
        self.impact_repository.save_impact_report(analysis, self.repository)
        gate = evaluate_migration_gate(analysis)
        return {"analysis": analysis, "gate": gate}

    def ingest(self, record: DomainRecord) -> DomainRecord:
        current = self.repository.get_record(record.record_id)
        if current is None:
            self.repository.save_record(record)
            return record
        if current.fingerprint == record.fingerprint:
            return current
        replacement = DomainRecord(record.record_id, record.payload, current.state,
                                   current.version + 1, record.occurred_at, record.source)
        self.repository.save_record(replacement, expected_version=current.version)
        return replacement

    def process(self, record: DomainRecord, impact_gate: Mapping[str, Any] | None = None) -> tuple[DomainRecord, Decision]:
        stored = self.ingest(record)
        context = dict(self.context)
        context.update(derive_context(stored, self.repository))
        context.update(augment_context(stored, self.repository))
        if impact_gate is not None:
            context["impact_gate"] = dict(impact_gate)
        decision = decide(stored, context)
        self.repository.save_decision(decision)
        advanced = advance_for_outcome(stored, decision)
        if advanced.fingerprint != stored.fingerprint:
            self.repository.save_record(advanced, expected_version=stored.version)
        return advanced, decision

    def run_fixture(self, fixture: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
        records = records_from_fixture(fixture)
        fixture_hash = stable_hash(fixture)
        run_id = self.repository.begin_run(fixture_hash, len(records))
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            return completed

        impact = self.build_impact_analysis(fixture)
        impact_gate = impact["gate"] if impact is not None else None
        analysis = impact["analysis"] if impact is not None else None

        decisions: dict[str, Decision] = {}
        final_records: list[DomainRecord] = []
        for record in records:
            final_record, decision = self.process(record, impact_gate)
            final_records.append(final_record)
            decisions[record.record_id] = decision
        snapshot = self.repository.snapshot()
        if snapshot["chain_errors"]:
            raise ContractError("audit chain verification failed")
        manifest = export_bundle(output, final_records, decisions, snapshot,
                                 self.repository.event_rows(), analysis)
        result = {"run_id": run_id, "fixture_hash": fixture_hash, "records": len(final_records),
                  "decisions": len(decisions), "manifest": manifest, "snapshot": snapshot}
        if impact is not None:
            result["impact_analysis"] = {
                "analysis_id": analysis.analysis_id,
                "analysis_fingerprint": analysis.fingerprint,
                "gate": impact_gate,
                "affected_concepts": list(analysis.affected_concepts),
                "comparable_concepts": list(analysis.comparable_concepts),
                "incomparable_concepts": list(analysis.incomparable_concepts),
                "reason_summary": dict(sorted(analysis.reason_summary.items())),
            }
        self.repository.finish_run(run_id, result)
        return result

    def inspect(self) -> dict[str, Any]:
        return {"snapshot": self.repository.snapshot(), "records": [record.__dict__ for record in self.repository.list_records()],
                "decisions": self.repository.decision_rows(),
                "mapping_sets": self.impact_repository.list_mapping_sets(),
                "impact_reports": self.impact_repository.list_impact_reports()}

    def verify_historical_report(self, analysis_id: str) -> dict[str, Any]:
        return self.impact_repository.verify_historical_report(analysis_id)


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read fixture: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value


def run(fixture_path: str | Path, database: str | Path, output: str | Path,
        context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return Application(database, context).run_fixture(load_fixture(fixture_path), output)


def verify(database: str | Path, output: str | Path) -> dict[str, Any]:
    repository = Repository(database)
    impact_repository = ImpactRepository(repository.connect)
    chain_errors = repository.verify_chain()
    bundle_errors = verify_bundle(output)
    result = {"ok": not chain_errors and not bundle_errors, "chain_errors": chain_errors,
              "bundle_errors": bundle_errors, "snapshot": repository.snapshot(),
              "impact_reports": impact_repository.list_impact_reports()}
    return result
