"""Cumulative Jev spending and interrupted requests must survive a new benchmark ledger."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spanish_e2e import SessionLedger, replay
from spanish_e2e_pairs import combine, prepare
from spanish_rerank import RESERVATION, Ledger, save


class CumulativeBudgetTests(unittest.TestCase):
    def test_grandparent_budget_cannot_be_lost_during_a_technical_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = Ledger(root / "first.jsonl", "first-panel")
            first.reserve("unknown-first")
            second = SessionLedger(root / "second.jsonl", "second-panel", first.path)
            second.reserve("unknown-second")
            with patch("spanish_e2e.MAX_CALLS", 2):
                third = SessionLedger(root / "third.jsonl", "third-panel", second.path)
                self.assertEqual(third.prior_calls, 2)
                self.assertEqual(third.prior_cost, RESERVATION * 2)
                with self.assertRaisesRegex(RuntimeError, "cumulative call"):
                    third.reserve("third")

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


class ReplayTests(unittest.TestCase):
    def test_changed_source_is_scored_fresh_while_exact_pairs_keep_their_original_score(self):
        import hashlib
        import json
        from copy import deepcopy

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = {
                "protocol": {},
                "cases": [
                    {
                        "id": "q",
                        "question": "public",
                        "candidates": [
                            {"filename": "a.txt", "char_start": 0, "char_end": 3, "text": "abc"},
                            {"filename": "b.txt", "char_start": 0, "char_end": 3, "text": "def"},
                        ],
                    }
                ],
            }
            save(root / "old.json", old)
            save(
                root / "old-scores.json",
                {
                    "panel_sha256": hashlib.sha256((root / "old.json").read_bytes()).hexdigest(),
                    "queries": {"q": {"scores": [0.7, 0.9]}},
                },
            )
            changed = deepcopy(old)
            changed["cases"][0]["candidates"][1]["text"] = "xyz"
            save(root / "new.json", changed)
            count = prepare(
                root / "new.json",
                root / "old.json",
                root / "old-scores.json",
                root / "plan.json",
                root / "pending.json",
            )
            self.assertEqual(count, 1)
            pending = json.loads((root / "pending.json").read_text(encoding="utf-8"))
            self.assertEqual([h["text"] for h in pending["cases"][0]["candidates"]], ["xyz"])
            save(
                root / "fresh.json",
                {
                    "panel_sha256": hashlib.sha256(
                        (root / "pending.json").read_bytes()
                    ).hexdigest(),
                    "queries": {"q": {"scores": [0.2]}},
                },
            )
            combine(
                root / "new.json", root / "plan.json", root / "fresh.json", root / "output.json"
            )
            result = json.loads((root / "output.json").read_text(encoding="utf-8"))
            self.assertEqual(result["queries"]["q"]["scores"], [0.7, 0.2])

    def test_changed_passage_cannot_reuse_a_paid_score(self):
        import hashlib
        from copy import deepcopy

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = {
                "protocol": {},
                "cases": [
                    {
                        "id": "q",
                        "question": "public",
                        "candidates": [
                            {
                                "filename": "public.txt",
                                "char_start": 0,
                                "char_end": 3,
                                "text": "abc",
                            }
                        ],
                    }
                ],
            }
            save(root / "old.json", old)
            save(
                root / "scores.json",
                {
                    "panel_sha256": hashlib.sha256((root / "old.json").read_bytes()).hexdigest(),
                    "queries": {"q": {"scores": [0.7]}},
                },
            )
            changed = deepcopy(old)
            changed["cases"][0]["candidates"][0]["text"] = "xyz"
            save(root / "new.json", changed)
            with self.assertRaisesRegex(ValueError, "unscored source span"):
                replay(
                    root / "new.json", root / "output.json", root / "old.json", root / "scores.json"
                )
            self.assertFalse((root / "output.json").exists())


if __name__ == "__main__":
    unittest.main()
