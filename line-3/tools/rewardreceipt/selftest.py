#!/usr/bin/env python3
"""Offline checks for receipt verification and tamper detection."""

import json
from pathlib import Path
import unittest

import rewardreceipt as rr


class ReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = rr.rs.read_json(rr.ROOT / "example.json")
        cls.metadata = rr.rs.read_json(rr.ROOT / "zto-mainnet.json")
        cls.report = rr.rs.allocate(cls.request, cls.metadata)

    def test_exact_zto_receipt(self):
        receipt = rr.verify(self.request, self.report, self.metadata)
        self.assertEqual(receipt["token"]["address"], rr.rs.TOKENS["zto"])
        self.assertEqual(receipt["budget_units"], "1000000000000000000")
        self.assertEqual(receipt["contributors"], 3)
        self.assertEqual(sum(int(a["units"]) for a in self.report["allocations"]),
                         int(receipt["budget_units"]))

    def test_canonical_hash_independent_of_key_order(self):
        self.assertEqual(rr.digest(self.request), rr.digest(json.loads(
            json.dumps({"contributors": self.request["contributors"], "budget": "1"}))))

    def test_changed_unit_rejected(self):
        altered = json.loads(json.dumps(self.report))
        altered["allocations"][0]["units"] = "333333333333333333"
        with self.assertRaises(rr.rs.Invalid):
            rr.verify(self.request, altered, self.metadata)

    def test_changed_token_capture_rejected(self):
        altered = dict(self.metadata, block_number=self.metadata["block_number"] + 1)
        with self.assertRaises(rr.rs.Invalid):
            rr.verify(self.request, self.report, altered)

    def test_added_claim_rejected(self):
        altered = dict(self.report, paid=True)
        with self.assertRaises(rr.rs.Invalid):
            rr.verify(self.request, altered, self.metadata)

    def test_numeric_type_substitution_rejected(self):
        altered = dict(self.report, rounding_units_distributed=True)
        self.assertEqual(altered["rounding_units_distributed"],
                         self.report["rounding_units_distributed"])
        with self.assertRaises(rr.rs.Invalid):
            rr.verify(self.request, altered, self.metadata)

    def test_changed_weights_rejected(self):
        altered = json.loads(json.dumps(self.request))
        altered["contributors"][0]["weight"] = "2"
        with self.assertRaises(rr.rs.Invalid):
            rr.verify(altered, self.report, self.metadata)

    def test_duplicate_json_keys_rejected_by_reader(self):
        with self.assertRaises(rr.rs.Invalid):
            rr.rs.parse_json(b'{"budget":"1","budget":"2"}')


if __name__ == "__main__":
    unittest.main(verbosity=2)
