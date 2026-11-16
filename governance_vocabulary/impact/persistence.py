"""Persistence for versioned mapping sets and impact analysis reports.

The tables deliberately keep every adopted mapping version and every published
impact report. Historical mappings and reference reports must remain verifiable
against the mapping version that was current when they were produced, even
after a newer mapping set supersedes them.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from governance_vocabulary.concepts.model import ContractError, canonical_json, stable_hash, utc_now
from governance_vocabulary.impact.analysis import ImpactAnalysis, evaluate_migration_gate
from governance_vocabulary.impact.model import MappingSet

MAPPING_SCHEMA = """
CREATE TABLE IF NOT EXISTS mapping_sets(
    set_id TEXT PRIMARY KEY,
    vocabulary_version TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    status TEXT NOT NULL,
    mapping_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mapping_edges(
    set_id TEXT NOT NULL,
    mapping_id TEXT NOT NULL,
    version_no INTEGER NOT NULL,
    edge_json TEXT NOT NULL,
    stored_at TEXT NOT NULL,
    PRIMARY KEY(set_id, mapping_id, version_no)
);
CREATE TABLE IF NOT EXISTS impact_reports(
    analysis_id TEXT PRIMARY KEY,
    mapping_set_id TEXT NOT NULL,
    mapping_set_fingerprint TEXT NOT NULL,
    report_json TEXT NOT NULL,
    gate_json TEXT NOT NULL,
    report_hash TEXT NOT NULL,
    generated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mapping_version ON mapping_sets(vocabulary_version, created_at);
CREATE INDEX IF NOT EXISTS idx_impact_mapping_set ON impact_reports(mapping_set_id, generated_at);
"""


class ImpactRepository:
    """Read/write access for mapping sets and impact reports on a shared DB."""

    def __init__(self, connection_factory):
        # The connection factory is the ``Repository.connect`` callable so both
        # repositories share one sqlite database and one audit chain.
        self._connect = connection_factory

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(MAPPING_SCHEMA)

    def save_mapping_set(self, mapping_set: MappingSet, repository: Any, status: str = "adopted") -> str:
        if status not in ("proposed", "adopted", "deprecated"):
            raise ContractError("unsupported mapping set status")
        with repository.transaction() as connection:
            existing = connection.execute(
                "SELECT fingerprint FROM mapping_sets WHERE set_id=?", (mapping_set.set_id,)
            ).fetchone()
            if existing:
                if existing[0] != mapping_set.fingerprint:
                    raise ContractError("mapping set id reused with different content")
                return mapping_set.fingerprint
            now = utc_now()
            connection.execute(
                "INSERT INTO mapping_sets(set_id,vocabulary_version,fingerprint,status,mapping_json,created_at) VALUES(?,?,?,?,?,?)",
                (
                    mapping_set.set_id,
                    mapping_set.vocabulary_version,
                    mapping_set.fingerprint,
                    status,
                    canonical_json(mapping_set.as_dict()),
                    now,
                ),
            )
            for version_no, edge in enumerate(mapping_set.mappings, start=1):
                connection.execute(
                    "INSERT INTO mapping_edges(set_id,mapping_id,version_no,edge_json,stored_at) VALUES(?,?,?,?,?)",
                    (
                        mapping_set.set_id,
                        edge.mapping_id,
                        version_no,
                        canonical_json(edge.as_dict()),
                        now,
                    ),
                )
            repository.append_event(
                connection,
                "mapping_set.saved",
                mapping_set.set_id,
                len(mapping_set.mappings),
                {
                    "vocabulary_version": mapping_set.vocabulary_version,
                    "fingerprint": mapping_set.fingerprint,
                    "status": status,
                    "mapping_count": len(mapping_set.mappings),
                },
            )
        return mapping_set.fingerprint

    def get_mapping_set(self, set_id: str) -> MappingSet | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT mapping_json FROM mapping_sets WHERE set_id=?", (set_id,)
            ).fetchone()
        if not row:
            return None
        return MappingSet.from_dict(json.loads(row[0]))

    def latest_mapping_set(self, vocabulary_version: str | None = None) -> MappingSet | None:
        with self._connect() as connection:
            if vocabulary_version:
                row = connection.execute(
                    "SELECT mapping_json FROM mapping_sets WHERE vocabulary_version=? ORDER BY created_at DESC, set_id DESC LIMIT 1",
                    (vocabulary_version,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT mapping_json FROM mapping_sets ORDER BY created_at DESC, set_id DESC LIMIT 1"
                ).fetchone()
        if not row:
            return None
        return MappingSet.from_dict(json.loads(row[0]))

    def list_mapping_sets(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT set_id,vocabulary_version,fingerprint,status,created_at FROM mapping_sets ORDER BY created_at, set_id"
            ).fetchall()
        return [dict(row) for row in rows]

    def save_impact_report(
        self,
        analysis: ImpactAnalysis,
        repository: Any,
    ) -> str:
        gate = evaluate_migration_gate(analysis)
        report_hash = stable_hash(analysis.as_dict())
        with repository.transaction() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO impact_reports(analysis_id,mapping_set_id,mapping_set_fingerprint,report_json,gate_json,report_hash,generated_at) VALUES(?,?,?,?,?,?,?)",
                (
                    analysis.analysis_id,
                    analysis.mapping_set_id,
                    analysis.mapping_set_fingerprint,
                    canonical_json(analysis.as_dict()),
                    canonical_json(gate),
                    report_hash,
                    analysis.generated_at,
                ),
            )
            repository.append_event(
                connection,
                "impact_report.saved",
                analysis.analysis_id,
                1,
                {
                    "mapping_set_id": analysis.mapping_set_id,
                    "mapping_set_fingerprint": analysis.mapping_set_fingerprint,
                    "report_hash": report_hash,
                    "gate": gate["decision"],
                },
            )
        return report_hash

    def get_impact_report(self, analysis_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT report_json,gate_json,report_hash,mapping_set_fingerprint FROM impact_reports WHERE analysis_id=?",
                (analysis_id,),
            ).fetchone()
        if not row:
            return None
        report = json.loads(row[0])
        return {
            "report": report,
            "gate": json.loads(row[1]),
            "report_hash": row[2],
            "mapping_set_fingerprint": row[3],
        }

    def list_impact_reports(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT analysis_id,mapping_set_id,mapping_set_fingerprint,report_hash,generated_at FROM impact_reports ORDER BY generated_at, analysis_id"
            ).fetchall()
        return [dict(row) for row in rows]

    def _recompute_mapping_set_fingerprint(self, connection: sqlite3.Connection, set_id: str) -> str | None:
        """Rebuild the mapping-set fingerprint from the individual edge rows."""
        row = connection.execute(
            "SELECT vocabulary_version, mapping_json FROM mapping_sets WHERE set_id=?", (set_id,)
        ).fetchone()
        if row is None:
            return None
        edge_rows = connection.execute(
            "SELECT edge_json FROM mapping_edges WHERE set_id=? ORDER BY version_no", (set_id,)
        ).fetchall()
        edges = [json.loads(item[0]) for item in edge_rows]
        body = json.loads(row[1])
        body["mappings"] = edges
        return stable_hash(body)

    def verify_historical_report(self, analysis_id: str) -> dict[str, Any]:
        """Re-verify a stored report against its recorded mapping version.

        The check recomputes the report hash and rebuilds the mapping-set
        fingerprint from the individual stored mapping edges. A mismatch means
        the mapping chain the report relied on no longer matches the stored
        history and the report must not be treated as comparable evidence.
        """

        stored = self.get_impact_report(analysis_id)
        if stored is None:
            raise ContractError("unknown impact report")
        report = stored["report"]
        errors: list[str] = []
        if stable_hash(report) != stored["report_hash"]:
            errors.append("impact report hash mismatch")
        if not isinstance(report, dict) or "mapping_set_id" not in report:
            errors.append("impact report content is unreadable")
            return {
                "analysis_id": analysis_id,
                "ok": False,
                "errors": errors,
                "mapping_set_id": "",
                "mapping_set_fingerprint": stored["mapping_set_fingerprint"],
                "verified_at": utc_now(),
            }
        mapping_set = self.get_mapping_set(report["mapping_set_id"])
        if mapping_set is None:
            errors.append("historical mapping set is missing")
        else:
            if mapping_set.fingerprint != stored["mapping_set_fingerprint"]:
                errors.append("mapping set fingerprint does not match the recorded version")
            if mapping_set.fingerprint != report["mapping_set_fingerprint"]:
                errors.append("report mapping fingerprint does not match the stored mapping set")
            with self._connect() as connection:
                recomputed = self._recompute_mapping_set_fingerprint(
                    connection, report["mapping_set_id"]
                )
            if recomputed is None:
                errors.append("historical mapping set is missing")
            elif recomputed != report["mapping_set_fingerprint"]:
                errors.append("stored mapping edges do not reproduce the recorded fingerprint")
            if stored["mapping_set_fingerprint"] != report["mapping_set_fingerprint"]:
                errors.append("recorded mapping fingerprint diverges from the report evidence")
        return {
            "analysis_id": analysis_id,
            "ok": not errors,
            "errors": errors,
            "mapping_set_id": report["mapping_set_id"],
            "mapping_set_fingerprint": stored["mapping_set_fingerprint"],
            "verified_at": utc_now(),
        }


def install_impact_schema(repository: Any) -> "ImpactRepository":
    """Attach the impact tables to an existing vocabulary repository."""
    impact_repository = ImpactRepository(repository.connect)
    impact_repository.initialize()
    return impact_repository
