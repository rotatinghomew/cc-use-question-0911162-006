from __future__ import annotations
import json
import unittest
from pathlib import Path
from governance_vocabulary.semantic_signal.semantic_stability import semantic_stability, peer_distribution

class Record:
    def __init__(self,payload): self.payload=payload

class DomainSignalTests(unittest.TestCase):
    def setUp(self):
        fixture=json.loads((Path(__file__).resolve().parents[2]/'fixtures'/'acceptance.json').read_text(encoding='utf-8'))
        self.payload=fixture['records'][0]['payload']
    def test_signal_is_bounded_and_explainable(self):
        signal=semantic_stability(self.payload)
        self.assertGreaterEqual(signal.score,0.0); self.assertLessEqual(signal.score,1.0)
        self.assertIn(signal.severity,{'info','warning','critical'}); self.assertTrue(signal.evidence)
    def test_peer_distribution_tracks_records(self):
        other=dict(self.payload); other['language_code']='group-b'
        result=peer_distribution([Record(self.payload),Record(other)])
        self.assertEqual(result['count'],2)
    def test_input_change_is_observable(self):
        base=semantic_stability(self.payload); changed=dict(self.payload)
        changed['cycle_count']=0
        changed['ambiguous_links']=0
        changed_signal=semantic_stability(changed)
        self.assertTrue(base.score != changed_signal.score or base.severity != changed_signal.severity)

if __name__=='__main__': unittest.main()
