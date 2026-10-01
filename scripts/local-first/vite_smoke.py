"""Exercise the actual Vite config against a local JSON upstream fixture."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
from http.client import HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

PREFIXES = [
    "auth",
    "query",
    "documents",
    "tenant",
    "search",
    "labels",
    "roles",
    "groups",
    "system",
    "analytics",
    "llm-config",
    "users",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    nonce = str(uuid4())

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = json.dumps({"fixture": nonce, "path": self.path}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *arguments: object) -> None:
            pass

    # Bind fails if an existing service owns port 8000; never take over that service.
    upstream = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    threading.Thread(target=upstream.serve_forever, daemon=True).start()
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        with (args.output / "vite-smoke-server.log").open("w", encoding="utf-8") as log:
            vite = subprocess.Popen(
                [
                    shutil.which("node") or "node",
                    "node_modules/vite/bin/vite.js",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "15173",
                    "--strictPort",
                ],
                cwd=args.source / "frontend",
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                deadline = time.monotonic() + 60
                while True:
                    try:
                        urllib.request.urlopen("http://127.0.0.1:15173", timeout=2).close()
                        break
                    except (OSError, HTTPException) as exc:
                        if time.monotonic() > deadline or vite.poll() is not None:
                            raise RuntimeError("Vite did not become ready") from exc
                        time.sleep(1)
                results = []
                for prefix in PREFIXES:
                    path = f"/{prefix}?smoke=1"
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:15173{path}", timeout=5
                    ) as response:
                        body = json.load(response)
                        assert body == {"fixture": nonce, "path": path}, body
                        results.append(
                            {"path": path, "status": response.status, "upstream_json": True}
                        )
                for prefix in ["health", "docs"]:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:15173/{prefix}", timeout=5
                    ) as response:
                        assert "text/html" in response.headers.get("Content-Type", "")
                        results.append(
                            {
                                "path": f"/{prefix}",
                                "status": response.status,
                                "intentional_spa": True,
                            }
                        )
                record = {
                    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.source)
                    .decode()
                    .strip(),
                    "config_sha256": hashlib.sha256(
                        (args.source / "frontend/vite.config.ts").read_bytes()
                    ).hexdigest(),
                    "upstream": "local JSON fixture; not the Zenith application",
                    "results": results,
                }
                (args.output / "vite-smoke.json").write_text(
                    json.dumps(record, indent=2), encoding="utf-8"
                )
                print(json.dumps(record))
            finally:
                vite.terminate()
                vite.wait(timeout=10)
    finally:
        upstream.shutdown()
        upstream.server_close()


if __name__ == "__main__":
    main()
