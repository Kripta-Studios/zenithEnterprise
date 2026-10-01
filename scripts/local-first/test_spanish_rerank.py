"""Accounting and metric regressions for the paid, public-data-only evaluation."""

import tempfile
import unittest
from pathlib import Path
from spanish_rerank import Ledger, MAX_CALLS, MAX_DOLLARS, RESERVATION, metrics


class EvaluationTests(unittest.TestCase):
    def test_interrupted_dispatch_keeps_its_full_charge_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            first = Ledger(path, "frozen")
            first.reserve("q|p")
            resumed = Ledger(path, "frozen")
            self.assertEqual(resumed.calls, 1)
            self.assertEqual(resumed.cost, RESERVATION)
            resumed.reserve("q|another")
            self.assertEqual(resumed.calls, 2)

    def test_usage_settles_charge_and_preserves_completed_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            ledger = Ledger(path, "frozen")
            call = ledger.reserve("q|p")
            ledger.finish(
                {
                    "event": "finish",
                    "call": call,
                    "identity": "q|p",
                    "input_tokens": 100,
                    "score": 0.8,
                    "seconds": 0.1,
                }
            )
            resumed = Ledger(path, "frozen")
            self.assertLess(resumed.cost, RESERVATION)
            self.assertEqual(resumed.results["q|p"]["score"], 0.8)
            with self.assertRaises(ValueError):
                Ledger(path, "other")

    def test_both_authorized_ceilings_stop_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Ledger(Path(directory) / "ledger", "frozen")
            ledger.calls = MAX_CALLS
            with self.assertRaises(RuntimeError):
                ledger.reserve("q|p")
            ledger.calls = 0
            ledger.charges[1] = MAX_DOLLARS - RESERVATION / 2
            with self.assertRaises(RuntimeError):
                ledger.reserve("q|p")

    def test_metrics_include_positives_absent_from_the_shortlist(self):
        query = {"candidates": [{"relevance": 0}, {"relevance": 1}], "total_relevant": 2}
        first = metrics(query, [0, 1])
        improved = metrics(query, [1, 0])
        self.assertEqual(first["mrr8"], 0.5)
        self.assertEqual(improved["mrr8"], 1)
        self.assertEqual(first["recall8"], 0.5)
        self.assertEqual(improved["recall8"], 0.5)
        self.assertLess(improved["ndcg8"], 1)
        self.assertGreater(improved["ndcg8"], first["ndcg8"])


if __name__ == "__main__":
    unittest.main()
