from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from governance_vocabulary.concepts.model import ContractError
from governance_vocabulary.curation_workbench import Application, load_fixture, run, verify
from governance_vocabulary.impact.analysis import (
    USAGE_METRICS,
    analyze_impact,
    affected_downstream,
    evaluate_migration_gate,
    resolve_chain,
)
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
    ConceptMapping,
    MappingSet,
    UsageSnapshot,
    mapping_set_from_fixture,
    references_from_fixture,
    snapshots_from_fixture,
)
from governance_vocabulary.impact.persistence import ImpactRepository
from governance_vocabulary.registry.vocabulary_store import Repository
from governance_vocabulary.versions.migration import decide, impact_blocks_migration, plan_transition

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "impact_acceptance.json"
SOURCE = "vocab-v1"
TARGET = "vocab-v2"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def analysis_from_fixture():
    fixture = load()
    mapping_set = mapping_set_from_fixture(fixture)
    snapshots = snapshots_from_fixture(fixture)
    references = references_from_fixture(fixture)
    return analyze_impact(mapping_set, SOURCE, TARGET, snapshots, references), mapping_set


class MappingModelTests(unittest.TestCase):
    def test_mapping_requires_known_relation_and_status(self):
        with self.assertRaises(ContractError):
            ConceptMapping("m1", SOURCE, "a", TARGET, "b", relation="guessed")
        with self.assertRaises(ContractError):
            ConceptMapping("m1", SOURCE, "a", TARGET, "b", status="retired")
        with self.assertRaises(ContractError):
            ConceptMapping("m1", SOURCE, "a", TARGET, "b", confidence=1.5)

    def test_mapping_set_rejects_duplicate_ids(self):
        edge = ConceptMapping("m1", SOURCE, "a", TARGET, "b")
        with self.assertRaises(ContractError):
            MappingSet("set-1", TARGET, (edge, edge))

    def test_mapping_set_from_fixture_round_trip_and_fingerprint(self):
        mapping_set = mapping_set_from_fixture(load())
        self.assertEqual(mapping_set.set_id, "mapping-set-v1-to-v2")
        self.assertEqual(mapping_set.fingerprint, MappingSet.from_dict(mapping_set.as_dict()).fingerprint)
        self.assertTrue(mapping_set.adopted_equivalent())

    def test_mapping_set_section_is_optional(self):
        self.assertIsNone(mapping_set_from_fixture({"records": []}))
        self.assertEqual(snapshots_from_fixture({"records": []}), ())


class ChainResolutionTests(unittest.TestCase):
    def setUp(self):
        self.mapping_set = mapping_set_from_fixture(load())

    def test_adopted_equivalent_chain_is_complete(self):
        chain = resolve_chain(self.mapping_set, SOURCE, "algorithm-transparency", TARGET)
        self.assertTrue(chain.complete)
        self.assertEqual(chain.target_concept, "algorithmic-transparency")
        self.assertEqual(chain.reason_code, REASON_MIGRATION)
        self.assertEqual(len(chain.hops), 1)
        self.assertEqual(chain.hops[0].mapping_id, "map-algorithm-transparency")
        self.assertEqual(chain.confidence, 0.95)

    def test_related_link_keeps_no_equivalent_state(self):
        chain = resolve_chain(self.mapping_set, SOURCE, "automated-decision", TARGET)
        self.assertFalse(chain.complete)
        self.assertIsNone(chain.target_concept)
        self.assertEqual(chain.reason_code, REASON_NO_EQUIVALENT)
        self.assertEqual(chain.hops[0].relation, RELATION_RELATED)

    def test_unadopted_equivalent_link_is_not_traversable(self):
        chain = resolve_chain(self.mapping_set, SOURCE, "biometric-risk", TARGET)
        self.assertFalse(chain.complete)
        self.assertEqual(chain.reason_code, REASON_UNADOPTED_LINK)

    def test_missing_mapping_is_a_coverage_gap(self):
        chain = resolve_chain(self.mapping_set, SOURCE, "never-mapped-concept", TARGET)
        self.assertFalse(chain.complete)
        self.assertEqual(chain.reason_code, REASON_MAPPING_GAP)
        self.assertEqual(chain.hops, ())

    def test_multi_hop_chain_walks_intermediate_versions(self):
        edges = (
            ConceptMapping("h1", "v1", "a", "v1.5", "a2", status="adopted", confidence=0.8),
            ConceptMapping("h2", "v1.5", "a2", "v2", "a3", status="adopted", confidence=0.5),
        )
        mapping_set = MappingSet("hop-set", "v2", edges)
        chain = resolve_chain(mapping_set, "v1", "a", "v2")
        self.assertTrue(chain.complete)
        self.assertEqual([hop.mapping_id for hop in chain.hops], ["h1", "h2"])
        self.assertAlmostEqual(chain.confidence, 0.4)

    def test_chain_detects_cycles(self):
        edges = (
            ConceptMapping("c1", "v1", "a", "v1.5", "b", status="adopted"),
            ConceptMapping("c2", "v1.5", "b", "v1", "a", status="adopted"),
        )
        mapping_set = MappingSet("cycle-set", "v2", edges)
        chain = resolve_chain(mapping_set, "v1", "a", "v2")
        self.assertFalse(chain.complete)
        self.assertEqual(chain.reason_code, REASON_CHAIN_CYCLE)

    def test_same_version_chain_is_identity(self):
        chain = resolve_chain(self.mapping_set, SOURCE, "algorithm-transparency", SOURCE)
        self.assertTrue(chain.complete)
        self.assertEqual(chain.target_concept, "algorithm-transparency")
        self.assertEqual(chain.hops, ())


class ImpactAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.analysis, self.mapping_set = analysis_from_fixture()

    def test_affected_concepts_cover_mapping_sides_and_references(self):
        affected = set(self.analysis.affected_concepts)
        # Both sides of every mapping edge are affected.
        self.assertIn("algorithm-transparency", affected)
        self.assertIn("algorithmic-transparency", affected)
        # A downstream concept only reached through references is affected.
        self.assertIn("model-audit", affected)
        self.assertIn("model-assurance", affected)

    def test_reference_graph_is_transitive(self):
        references = {"d": ("c",), "c": ("b",), "b": ("a",)}
        mapping_set = MappingSet(
            "ref-set", TARGET,
            (ConceptMapping("r1", SOURCE, "a", TARGET, "a2", status="adopted"),),
        )
        result = affected_downstream(mapping_set, SOURCE, ["a"], references)
        self.assertEqual(set(result), {"a", "a2", "b", "c", "d"})

    def test_comparable_stats_distinguish_migration_from_data_change(self):
        impacts = {item.concept_id: item for item in self.analysis.impacts}
        stable = impacts["algorithm-transparency"]
        self.assertTrue(stable.comparable)
        self.assertTrue(all(item.status == STAT_COMPARABLE for item in stable.comparisons))
        self.assertEqual({item.reason_code for item in stable.comparisons}, {REASON_MIGRATION})

        changed = impacts["data-governance"]
        self.assertTrue(changed.comparable)
        self.assertEqual({item.reason_code for item in changed.comparisons}, {REASON_DATA_CHANGE})
        count = next(item for item in changed.comparisons if item.metric == "usage_count")
        self.assertEqual((count.source_value, count.target_value), (86.0, 97.0))

    def test_no_equivalent_is_retained_as_incomparable_not_silently_reused(self):
        impacts = {item.concept_id: item for item in self.analysis.impacts}
        verdict = impacts["automated-decision"]
        self.assertFalse(verdict.comparable)
        for comparison in verdict.comparisons:
            self.assertEqual(comparison.status, STAT_INCOMPARABLE)
            self.assertEqual(comparison.reason_code, REASON_NO_EQUIVALENT)
            self.assertIsNone(comparison.target_value)
            # The old value must never be copied into the target side.
            self.assertNotEqual(comparison.source_value, comparison.target_value)

    def test_mapping_gap_and_unadopted_link_are_incomparable(self):
        impacts = {item.concept_id: item for item in self.analysis.impacts}
        self.assertEqual(
            {item.reason_code for item in impacts["biometric-risk"].comparisons},
            {REASON_UNADOPTED_LINK},
        )
        self.assertEqual(
            {item.reason_code for item in impacts["automated-decision-review"].comparisons},
            {REASON_MAPPING_GAP},
        )

    def test_missing_target_snapshot_is_incomparable(self):
        fixture = load()
        mapping_set = mapping_set_from_fixture(fixture)
        snapshots = tuple(
            snapshot
            for snapshot in snapshots_from_fixture(fixture)
            if not (snapshot.vocabulary_version == TARGET and snapshot.concept_id == "data-stewardship")
        )
        analysis = analyze_impact(
            mapping_set, SOURCE, TARGET, snapshots, references_from_fixture(fixture)
        )
        impacts = {item.concept_id: item for item in analysis.impacts}
        self.assertEqual(
            {item.reason_code for item in impacts["data-governance"].comparisons},
            {REASON_SNAPSHOT_MISSING},
        )
        self.assertFalse(impacts["data-governance"].comparable)

    def test_every_impact_carries_two_metrics_and_reason_summary_matches(self):
        for impact in self.analysis.impacts:
            self.assertEqual([item.metric for item in impact.comparisons], list(USAGE_METRICS))
        counted = {}
        for impact in self.analysis.impacts:
            for code in impact.reason_codes:
                counted[code] = counted.get(code, 0) + 1
        self.assertEqual(counted, self.analysis.reason_summary)

    def test_analysis_is_deterministic_and_fingerprinted(self):
        again, _ = analysis_from_fixture()
        self.assertEqual(again.analysis_id, self.analysis.analysis_id)
        self.assertEqual(again.fingerprint, self.analysis.fingerprint)

    def test_analysis_requires_source_mappings(self):
        mapping_set = MappingSet(
            "other", TARGET,
            (ConceptMapping("x", "other-version", "a", TARGET, "b", status="adopted"),),
        )
        with self.assertRaises(ContractError):
            analyze_impact(mapping_set, SOURCE, TARGET, ())

    def test_duplicate_snapshots_are_rejected(self):
        snapshots = (
            UsageSnapshot(SOURCE, "a", 1.0, 0.1, "2026-09-30T00:00:00+00:00"),
            UsageSnapshot(SOURCE, "a", 2.0, 0.2, "2026-10-31T00:00:00+00:00"),
        )
        with self.assertRaises(ContractError):
            analyze_impact(self.mapping_set, SOURCE, TARGET, snapshots)

    def test_multi_hop_target_inherits_chain_and_stays_comparable(self):
        edges = (
            ConceptMapping("h1", "v1", "a", "v1.5", "a2", status="adopted", confidence=0.8),
            ConceptMapping("h2", "v1.5", "a2", "v2", "a3", status="adopted", confidence=0.5),
        )
        mapping_set = MappingSet("hop-set", "v2", edges)
        snapshots = (
            UsageSnapshot("v1", "a", 10.0, 0.2, "2026-09-30T00:00:00+00:00"),
            UsageSnapshot("v2", "a3", 10.0, 0.2, "2026-10-31T00:00:00+00:00"),
        )
        analysis = analyze_impact(mapping_set, "v1", "v2", snapshots)
        impacts = {item.concept_id: item for item in analysis.impacts}
        # Both the source concept and the final multi-hop target are comparable.
        self.assertIn("a3", impacts)
        self.assertTrue(impacts["a"].comparable)
        self.assertTrue(impacts["a3"].comparable)
        self.assertEqual(impacts["a3"].chain.target_concept, "a3")
        self.assertEqual(len(impacts["a3"].chain.hops), 2)


class MigrationGateTests(unittest.TestCase):
    def test_gate_holds_when_incomparable_stats_exist(self):
        analysis, _ = analysis_from_fixture()
        gate = evaluate_migration_gate(analysis)
        self.assertEqual(gate["decision"], "hold")
        self.assertIn(REASON_NO_EQUIVALENT, gate["blocking_reason_codes"])
        self.assertIn(REASON_MAPPING_GAP, gate["blocking_reason_codes"])
        self.assertIn(REASON_UNADOPTED_LINK, gate["blocking_reason_codes"])
        self.assertNotIn(REASON_DATA_CHANGE, gate["blocking_reason_codes"])

    def test_gate_go_when_all_chains_are_comparable(self):
        edges = (
            ConceptMapping("g1", SOURCE, "a", TARGET, "a2", status="adopted", confidence=0.9),
            ConceptMapping("g2", SOURCE, "b", TARGET, "b2", status="adopted", confidence=0.9),
        )
        mapping_set = MappingSet("go-set", TARGET, edges)
        snapshots = (
            UsageSnapshot(SOURCE, "a", 10.0, 0.2, "2026-09-30T00:00:00+00:00"),
            UsageSnapshot(TARGET, "a2", 12.0, 0.3, "2026-10-31T00:00:00+00:00"),
            UsageSnapshot(SOURCE, "b", 5.0, 0.1, "2026-09-30T00:00:00+00:00"),
            UsageSnapshot(TARGET, "b2", 5.0, 0.1, "2026-10-31T00:00:00+00:00"),
        )
        analysis = analyze_impact(mapping_set, SOURCE, TARGET, snapshots)
        gate = evaluate_migration_gate(analysis)
        self.assertEqual(gate["decision"], "go")
        self.assertEqual(gate["blocking_reason_codes"], [])

    def test_gate_participates_in_transition_plan_and_decision(self):
        analysis, _ = analysis_from_fixture()
        gate = evaluate_migration_gate(analysis)
        record = load_fixture(str(FIXTURE))  # ensure loader accepts the fixture
        from governance_vocabulary.concepts.model import records_from_fixture

        domain_record = records_from_fixture(record)[0]
        plan = plan_transition(domain_record, "curated", {"impact_gate": gate, "transition_threshold": 0.0})
        self.assertFalse(plan.allowed)
        self.assertTrue(any("impact analysis blocks" in reason for reason in plan.reasons))

        blocked, reasons = impact_blocks_migration({"impact_gate": gate})
        self.assertTrue(blocked)
        self.assertIn(REASON_NO_EQUIVALENT, reasons)

        decision = decide(domain_record, {"impact_gate": gate})
        self.assertEqual(decision.outcome, "hold")
        self.assertTrue(any("impact_block" in reason for reason in decision.reasons))

        # Without a gate the same record is not blocked on impact grounds.
        self.assertEqual(impact_blocks_migration({}), (False, ()))


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repository = Repository(Path(self.temp.name) / "state.sqlite3")
        self.impact = ImpactRepository(self.repository.connect)
        self.analysis, self.mapping_set = analysis_from_fixture()

    def test_mapping_set_is_persisted_and_idempotent(self):
        first = self.impact.save_mapping_set(self.mapping_set, self.repository)
        second = self.impact.save_mapping_set(self.mapping_set, self.repository)
        self.assertEqual(first, second)
        loaded = self.impact.get_mapping_set(self.mapping_set.set_id)
        self.assertEqual(loaded.fingerprint, self.mapping_set.fingerprint)
        with sqlite3.connect(self.repository.database) as connection:
            edge_count = connection.execute(
                "SELECT COUNT(*) FROM mapping_edges WHERE set_id=?", (self.mapping_set.set_id,)
            ).fetchone()[0]
        self.assertEqual(edge_count, len(self.mapping_set.mappings))

    def test_same_set_id_with_changed_content_is_rejected(self):
        self.impact.save_mapping_set(self.mapping_set, self.repository)
        tampered = MappingSet(
            self.mapping_set.set_id,
            self.mapping_set.vocabulary_version,
            self.mapping_set.mappings[:-1],
        )
        with self.assertRaises(ContractError):
            self.impact.save_mapping_set(tampered, self.repository)

    def test_impact_report_round_trip_and_historical_verification(self):
        self.impact.save_mapping_set(self.mapping_set, self.repository)
        report_hash = self.impact.save_impact_report(self.analysis, self.repository)
        stored = self.impact.get_impact_report(self.analysis.analysis_id)
        self.assertEqual(stored["report_hash"], report_hash)
        verification = self.impact.verify_historical_report(self.analysis.analysis_id)
        self.assertTrue(verification["ok"])
        self.assertEqual(verification["errors"], [])

    def test_historical_report_detects_mapping_tampering(self):
        self.impact.save_mapping_set(self.mapping_set, self.repository)
        self.impact.save_impact_report(self.analysis, self.repository)
        with sqlite3.connect(self.repository.database) as connection:
            # Rewrite an adopted mapping edge that the report relied on.
            connection.execute(
                "UPDATE mapping_edges SET edge_json=? WHERE set_id=? AND mapping_id=?",
                (
                    json.dumps({"mapping_id": "map-algorithm-transparency", "tampered": True}),
                    self.mapping_set.set_id,
                    "map-algorithm-transparency",
                ),
            )
            connection.execute(
                "UPDATE mapping_sets SET fingerprint=? WHERE set_id=?",
                ("0" * 64, self.mapping_set.set_id),
            )
        verification = self.impact.verify_historical_report(self.analysis.analysis_id)
        self.assertFalse(verification["ok"])
        self.assertTrue(verification["errors"])

    def test_historical_report_detects_report_tampering(self):
        self.impact.save_mapping_set(self.mapping_set, self.repository)
        self.impact.save_impact_report(self.analysis, self.repository)
        with sqlite3.connect(self.repository.database) as connection:
            connection.execute(
                "UPDATE impact_reports SET report_json=? WHERE analysis_id=?",
                ("{}", self.analysis.analysis_id),
            )
        verification = self.impact.verify_historical_report(self.analysis.analysis_id)
        self.assertFalse(verification["ok"])
        self.assertIn("impact report hash mismatch", verification["errors"])

    def test_unknown_report_verification_raises(self):
        with self.assertRaises(ContractError):
            self.impact.verify_historical_report("missing-analysis")


class EndToEndImpactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "impact.sqlite3"
        self.output = self.root / "output"

    def test_run_emits_impact_bundle_and_verified_chain(self):
        result = run(FIXTURE, self.database, self.output)
        self.assertIn("impact_analysis", result)
        self.assertTrue((self.output / "impact-analysis.json").is_file())
        self.assertTrue((self.output / "mapping-chains.csv").is_file())
        manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("impact-analysis.json", manifest["files"])
        self.assertEqual(manifest["impact_analysis_id"], result["impact_analysis"]["analysis_id"])
        verification = verify(self.database, self.output)
        self.assertTrue(verification["ok"])
        self.assertEqual(len(verification["impact_reports"]), 1)

    def test_incomparable_stats_hold_all_migration_decisions(self):
        run(FIXTURE, self.database, self.output)
        decisions = json.loads((self.output / "decisions.json").read_text(encoding="utf-8"))
        self.assertTrue(decisions)
        self.assertTrue(all(item["outcome"] == "hold" for item in decisions))
        self.assertTrue(any("impact_block" in reason for item in decisions for reason in item["reasons"]))

    def test_mapping_chains_csv_records_every_affected_concept(self):
        result = run(FIXTURE, self.database, self.output)
        import csv

        with (self.output / "mapping-chains.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        concepts = {row["concept_id"] for row in rows}
        self.assertEqual(concepts, set(result["impact_analysis"]["affected_concepts"]))
        no_equivalent = [row for row in rows if row["reason_code"] == REASON_NO_EQUIVALENT]
        self.assertTrue(no_equivalent)
        self.assertTrue(all(row["chain_complete"] == "False" for row in no_equivalent))

    def test_historical_report_remains_verifiable_after_newer_run(self):
        result = run(FIXTURE, self.database, self.output)
        analysis_id = result["impact_analysis"]["analysis_id"]
        # Re-running must reuse the stored run and keep the historical report intact.
        run(FIXTURE, self.database, self.output)
        application = Application(self.database)
        verification = application.verify_historical_report(analysis_id)
        self.assertTrue(verification["ok"])
        self.assertEqual(verification["mapping_set_id"], "mapping-set-v1-to-v2")

    def test_legacy_fixture_without_mapping_section_is_unchanged(self):
        legacy = Path(__file__).resolve().parents[2] / "fixtures" / "acceptance.json"
        legacy_output = self.root / "legacy-output"
        result = run(legacy, self.root / "legacy.sqlite3", legacy_output)
        self.assertNotIn("impact_analysis", result)
        manifest = json.loads((legacy_output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(manifest["files"]),
            {"summary.json", "decisions.json", "audit-events.json"},
        )
        self.assertFalse((legacy_output / "impact-analysis.json").exists())


if __name__ == "__main__":
    unittest.main()
