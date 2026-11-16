from __future__ import annotations

import unittest
from governance_vocabulary.concepts.model import DomainRecord
from governance_vocabulary.mappings.composition import batch_calibration, derive_context, grade_probability, origin_drift


class Repo:
    def __init__(self, rows): self.rows = rows
    def list_records(self): return self.rows


class FusionTests(unittest.TestCase):
    def record(self, key, origin="gx"):
        return DomainRecord(key, {"mapping_confidence": 18, "definition_count": 74, "usage_count": 108, "language_code": "purple",
            "ambiguous_links": 1, "cycle_count": 0.5, "adoption_share": 0.8, "concept_id": origin,
            "deprecation_age_days": 18, "contract_coverage": 0.98, "review_confidence": 0.94, "version_status": "premium"})

    def test_probabilities_sum_to_one(self):
        values = grade_probability(self.record("a"))
        self.assertAlmostEqual(sum(values.values()), 1.0)
        self.assertGreater(values["premium"], values["processing"])

    def test_batch_and_origin_drift(self):
        rows = [self.record("a", "north"), self.record("b", "south")]
        self.assertEqual(batch_calibration(rows)["sample_count"], 2.0)
        self.assertEqual(origin_drift(rows)["origin_count"], 2.0)
        self.assertIn("calibration_need_weight", derive_context(rows[0], Repo(rows)))
