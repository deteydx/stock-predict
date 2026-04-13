#!/usr/bin/env python3
"""Run the backend and frontend development servers together."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the StockPredict backend and frontend development servers."
    )
    parser.add_argument("--backend-host", default="0.0.0.0", help="Backend bind host.")
    parser.add_argument("--backend-port", type=int, default=8000, help="Backend bind port.")
    parser.add_argument("--frontend-host", default="0.0.0.0", help="Frontend bind host.")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Frontend bind port.")
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable FastAPI auto-reload.",
    )
    return parser.parse_args()


def _pipenv_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PIPENV_IGNORE_VIRTUALENVS", "1")
    if not (ROOT / ".venv").exists():
        env.setdefault("PIPENV_VENV_IN_PROJECT", "0")
    return env


def resolve_backend_python() -> str:
    if os.environ.get("PIPENV_ACTIVE"):
        return sys.executable

    if which("pipenv") is None:
        raise RuntimeError("`pipenv` is not installed or not on PATH.")

    result = subprocess.run(
        ["pipenv", "--py"],
        cwd=ROOT,
        env=_pipenv_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    python_path = result.stdout.strip()
    if result.returncode != 0 or not python_path:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            "Pipenv environment is not ready. Run `pipenv install --dev` first."
            + (f"\n{detail}" if detail else "")
        )
    return python_path


def check_prerequisites() -> None:
    if which("npm") is None:
        raise RuntimeError("`npm` is not installed or not on PATH.")
    if not FRONTEND_DIR.exists():
        raise RuntimeError(f"Frontend directory not found: {FRONTEND_DIR}")
    if not (FRONTEND_DIR / "node_modules").exists():
        raise RuntimeError(
            "Frontend dependencies are missing. Run `npm install` in `frontend/` first."
        )
    resolve_backend_python()


def start_process(
    name: str,
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    kwargs: dict[str, object] = {
        "cwd": str(cwd),
        "env": env,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "bufsize": 1,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    process = subprocess.Popen(command, **kwargs)
    assert process.stdout is not None
    threading.Thread(
        target=stream_output,
        args=(name, process.stdout),
        daemon=True,
    ).start()
    return process


def stream_output(name: str, stream) -> None:
    prefix = f"[{name}] "
    for line in iter(stream.readline, ""):
        print(f"{prefix}{line}", end="", flush=True)
    stream.close()


def stop_process(name: str, process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.terminate()
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)

    print(f"[runner] stopped {name}", flush=True)


def main() -> int:
    args = parse_args()

    try:
        check_prerequisites()
        backend_python = resolve_backend_python()
    except RuntimeError as exc:
        print(f"[runner] {exc}", file=sys.stderr)
        return 1

    backend_cmd = [
        backend_python,
        "-m",
        "stockpredict",
        "serve",
        "--host",
        args.backend_host,
        "--port",
        str(args.backend_port),
    ]
    if not args.no_reload:
        backend_cmd.append("--reload")

    frontend_cmd = [
        "npm",
        "run",
        "dev",
        "--",
        "--host",
        args.frontend_host,
        "--port",
        str(args.frontend_port),
    ]

    frontend_env = os.environ.copy()
    frontend_env["VITE_API_PROXY_TARGET"] = f"http://127.0.0.1:{args.backend_port}"

    print(f"[runner] backend:  http://127.0.0.1:{args.backend_port}", flush=True)
    print(f"[runner] frontend: http://127.0.0.1:{args.frontend_port}", flush=True)
    print("[runner] press Ctrl+C to stop both services", flush=True)

    processes = {
        "backend": start_process("backend", backend_cmd, ROOT, env=os.environ.copy()),
        "frontend": start_process("frontend", frontend_cmd, FRONTEND_DIR, env=frontend_env),
    }

    interrupted = False
    try:
        while True:
            for name, process in processes.items():
                exit_code = process.poll()
                if exit_code is not None:
                    print(f"[runner] {name} exited with code {exit_code}", flush=True)
                    return exit_code
            time.sleep(0.5)
    except KeyboardInterrupt:
        interrupted = True
        print("\n[runner] shutting down...", flush=True)
        return 0
    finally:
        for name, process in processes.items():
            stop_process(name, process)
        if interrupted:
            print("[runner] all services stopped", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
