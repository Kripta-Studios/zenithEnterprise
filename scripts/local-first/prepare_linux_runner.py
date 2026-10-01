"""Reuse cached Linux dependencies in a disposable Docker test runner."""

import subprocess


def main() -> None:
    source = subprocess.Popen(
        [
            "wsl",
            "-d",
            "Ubuntu-24.04",
            "--",
            "tar",
            "--exclude=./lib/python3.12/site-packages/nvidia",
            "--exclude=./lib/python3.12/site-packages/torch",
            "--exclude=./lib/python3.12/site-packages/triton",
            "-C",
            "/home/alvaro/zenith-local-first-20261001/proxy-final/backend/.venv",
            "-cf",
            "-",
            ".",
        ],
        stdout=subprocess.PIPE,
    )
    assert source.stdout is not None
    copied = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            "0",
            "-i",
            "--entrypoint",
            "tar",
            "-v",
            "zenith-lf-check-env-lean:/deps",
            "trace-it-backend:ci",
            "-C",
            "/deps",
            "-xf",
            "-",
        ],
        check=False,
        stdin=source.stdout,
    )
    source.stdout.close()
    assert source.wait() == 0
    assert copied.returncode == 0
    print(
        "Copied cached Linux environment without offline GPU evaluation wheels "
        "to zenith-lf-check-env-lean",
        flush=True,
    )


if __name__ == "__main__":
    main()
