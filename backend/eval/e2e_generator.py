"""A fixed local generator used only by the opt-in paired evaluation."""

import hashlib
import json
import os
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx

from app.common.llm import BaseLLMProvider, GenerationResponse


class LocalEvaluationProvider(BaseLLMProvider):
    name = "local-evaluation"

    def __init__(self, path: Path, configuration: dict[str, Any]) -> None:
        self.path, self.configuration = path, configuration
        self.model = str(configuration["model"])
        self.cached: dict[str, dict[str, Any]] = {}
        self.last: dict[str, Any] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self.cached[row["input_sha256"]] = row

    async def complete(self, system: str, user: str) -> GenerationResponse:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "keep_alive": "15m",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {
                key: self.configuration[key]
                for key in ("temperature", "seed", "num_ctx", "num_predict")
            },
        }
        identity = hashlib.sha256(
            json.dumps(
                {"request": payload, "model_digest": self.configuration["model_digest"]},
                sort_keys=True,
            ).encode()
        ).hexdigest()
        before = time.perf_counter()
        reused = identity in self.cached
        row: dict[str, Any]
        if reused:
            row = self.cached[identity]
        else:
            async with httpx.AsyncClient(
                timeout=900, trust_env=False, follow_redirects=False
            ) as client:
                tags = (await client.get("http://host.docker.internal:11436/api/tags")).json()
                digest = next(
                    (m["digest"] for m in tags["models"] if m["name"] == self.model), None
                )
                if digest != self.configuration["model_digest"]:
                    raise ValueError("local generation model digest changed")
                response = await client.post(
                    "http://host.docker.internal:11436/api/chat", json=payload
                )
                response.raise_for_status()
                body = response.json()
            if body.get("model") != self.model or body.get("done") is not True:
                raise ValueError("local generator substituted its model or did not complete")
            text = body.get("message", {}).get("content")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("local model returned no answer")
            row = {
                "input_sha256": identity,
                "model": self.model,
                "text": text,
                "prompt_tokens": body.get("prompt_eval_count"),
                "completion_tokens": body.get("eval_count"),
                "done_reason": body.get("done_reason"),
                "generation_seconds": time.perf_counter() - before,
                "options": payload["options"],
                "thinking": False,
            }
            if (
                row["prompt_tokens"] is None
                or row["prompt_tokens"]
                >= self.configuration["num_ctx"] - self.configuration["num_predict"]
            ):
                raise ValueError("prompt may have reached the local context limit")
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            self.cached[identity] = row
        self.last = {
            **row,
            "reused_identical_prompt": reused,
            "current_call_seconds": time.perf_counter() - before,
        }
        return GenerationResponse(
            row["text"], row["model"], row["prompt_tokens"], row["completion_tokens"]
        )

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        yield (await self.complete(system, user)).text
