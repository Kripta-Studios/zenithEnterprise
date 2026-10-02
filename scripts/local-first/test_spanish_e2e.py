"""Cumulative Jev spending and interrupted requests must survive a new benchmark ledger."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spanish_e2e import SessionLedger
from spanish_rerank import RESERVATION, Ledger


class CumulativeBudgetTests(unittest.TestCase):
    def test_prior_spend_is_counted_before_new_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            parent, current = Path(directory) / "prior.jsonl", Path(directory) / "new.jsonl"
            old = Ledger(parent, "prior-panel")
            call = old.reserve("public-prior-pair")
            old.finish(
                {
                    "event": "finish",
                    "call": call,
                    "identity": "public-prior-pair",
                    "input_tokens": 64000,
                }
            )
            with patch("spanish_e2e.MAX_DOLLARS", RESERVATION * 1.5):
                new = SessionLedger(current, "new-panel", parent)
                with self.assertRaisesRegex(RuntimeError, "cumulative dollar"):
                    new.reserve("new-public-pair")
                self.assertEqual(new.calls, 0)

    def test_prior_calls_are_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            parent, current = Path(directory) / "prior.jsonl", Path(directory) / "new.jsonl"
            old = Ledger(parent, "prior-panel")
            old.reserve("unknown-prior-outcome")
            with (
                patch("spanish_e2e.MAX_CALLS", 1),
                self.assertRaisesRegex(RuntimeError, "cumulative call"),
            ):
                SessionLedger(current, "new-panel", parent).reserve("new-public-pair")

    def test_interrupted_current_call_cannot_be_resent_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            parent, current = Path(directory) / "prior.jsonl", Path(directory) / "new.jsonl"
            old = Ledger(parent, "prior-panel")
            old.reserve("public-prior-pair")
            SessionLedger(current, "new-panel", parent).reserve("interrupted-public-pair")
            with self.assertRaisesRegex(RuntimeError, "unknown paid outcome"):
                SessionLedger(current, "new-panel", parent)


if __name__ == "__main__":
    unittest.main()
