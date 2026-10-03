"""A health response alone must not release the expensive evaluation stages."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import docker_checks
from spanish_e2e_runtime import completed_scores, ready


class ReadinessTests(unittest.TestCase):
    def test_health_requires_identity_and_a_real_neutral_embedding(self):
        calls = []

        def response(request, **kwargs):
            url = request if isinstance(request, str) else request.full_url
            calls.append(url)
            body = (
                []
                if url.endswith("/health")
                else (
                    {"model_id": "pinned-local-model"} if url.endswith("/info") else [[0.0] * 1024]
                )
            )
            return io.BytesIO(json.dumps(body).encode())

        with patch("spanish_e2e_runtime.urllib.request.urlopen", side_effect=response):
            result = ready("http://local", "embed", 30, lambda **data: None)
        self.assertEqual(result["info"]["model_id"], "pinned-local-model")
        self.assertEqual(calls, ["http://local/health", "http://local/info", "http://local/embed"])

    def test_invalid_embedding_stops_before_pipeline(self):
        with (
            patch(
                "spanish_e2e_runtime.urllib.request.urlopen",
                side_effect=[io.BytesIO(b"[]"), io.BytesIO(b"{}"), io.BytesIO(b"[[0]]")],
            ),
            self.assertRaisesRegex(ValueError, "malformed"),
        ):
            ready("http://local", "embed", 30, lambda **data: None)

    def test_timeout_is_bounded_and_retains_progress(self):
        clock = [0.0]
        progress = []
        with (
            patch("spanish_e2e_runtime.time.monotonic", side_effect=lambda: clock[0]),
            patch(
                "spanish_e2e_runtime.time.sleep",
                side_effect=lambda n: clock.__setitem__(0, clock[0] + n),
            ),
            patch("spanish_e2e_runtime.urllib.request.urlopen", side_effect=OSError),
            self.assertRaisesRegex(TimeoutError, "exceeded 5s"),
        ):
            ready("http://local", "embed", 5, lambda **data: progress.append(data))
        self.assertEqual(clock[0], 5)
        self.assertEqual(len(progress), 3)


class ScoreResumeTests(unittest.TestCase):
    def test_changed_order_is_rejected_before_reuse(self):
        with tempfile.TemporaryDirectory(prefix="zenith-e2e-resume-") as directory:
            root = Path(directory)
            panel = root / "candidates.json"
            data = {"cases": [{"id": "q", "candidates": [{"id": "a"}, {"id": "b"}]}]}
            panel.write_text(json.dumps(data))
            score = {
                "panel_sha256": hashlib.sha256(panel.read_bytes()).hexdigest(),
                "queries": {"q": {"scores": [0.2, 0.9]}},
            }
            for arm in ("bge", "jev"):
                (root / f"{arm}-scores.json").write_text(json.dumps(score))
            self.assertTrue(completed_scores(panel, root))
            data["cases"][0]["candidates"].reverse()
            panel.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "resumed capture"):
                completed_scores(panel, root)

    def test_incomplete_or_boolean_scores_are_not_complete(self):
        with tempfile.TemporaryDirectory(prefix="zenith-e2e-resume-") as directory:
            root = Path(directory)
            panel = root / "candidates.json"
            panel.write_text(json.dumps({"cases": [{"id": "q", "candidates": [{}, {}]}]}))
            self.assertFalse(completed_scores(panel, root))
            for values in ([0.5], [0.5, True]):
                (root / "bge-scores.json").write_text(
                    json.dumps(
                        {
                            "panel_sha256": hashlib.sha256(panel.read_bytes()).hexdigest(),
                            "queries": {"q": {"scores": values}},
                        }
                    )
                )
                with self.assertRaisesRegex(ValueError, "incomplete or malformed"):
                    completed_scores(panel, root)


class DockerExitTests(unittest.TestCase):
    def test_failed_child_records_its_exit_and_fails_the_helper(self):
        with tempfile.TemporaryDirectory(prefix="zenith-e2e-runtime-") as directory:
            root = Path(directory)
            destination = root / "records"

            def execute(command, **kwargs):
                if command[0] == "git":
                    archive = next(value[9:] for value in command if value.startswith("--output="))
                    Path(archive).write_bytes(b"test archive")
                    return SimpleNamespace(returncode=0)
                return SimpleNamespace(returncode=4)

            with (
                patch(
                    "sys.argv",
                    ["docker_checks", str(root), "failure", str(destination), "--only", "tests"],
                ),
                patch(
                    "docker_checks.subprocess.check_output",
                    side_effect=[b"head", b"tree", b"image"],
                ),
                patch("docker_checks.subprocess.run", side_effect=execute),
                redirect_stdout(io.StringIO()),
                self.assertRaises(SystemExit) as failure,
            ):
                docker_checks.main()
            self.assertEqual(failure.exception.code, 1)
            record = json.loads((destination / "failure-docker-checks.json").read_text())
            self.assertEqual(record["commands"][0]["exit"], 4)


if __name__ == "__main__":
    unittest.main()
