"""A health response alone must not release the expensive evaluation stages."""

import io
import json
import unittest
from unittest.mock import patch

from spanish_e2e_runtime import ready


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


if __name__ == "__main__":
    unittest.main()
