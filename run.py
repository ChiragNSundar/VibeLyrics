#!/usr/bin/env python3
"""
VibeLyrics Unified Runner
Run both backend and frontend with a single command.

Usage:
    python3 run.py          # Run everything
    python3 run.py --skip-install   # Skip dependency installation
"""
import subprocess
import sys
import os
import time
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND_DIR = ROOT / "frontend"
REQUIREMENTS = ROOT / "requirements.txt"
BACKEND_PORT = 5001
FRONTEND_PORT = 5173


# ── Dependency helpers ──────────────────────────────────────────────

def check_python_deps():
    """Install Python dependencies from requirements.txt if needed."""
    if not REQUIREMENTS.exists():
        print("[!] requirements.txt not found — skipping Python deps")
        return

    print("[*] Checking Python dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS), "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[!] pip install failed:\n{result.stderr}")
        print("[!] Continuing anyway — some features may not work")
    else:
        print("[OK] Python dependencies ready")


def check_node_deps():
    """Install Node.js dependencies if node_modules is missing."""
    if not shutil.which("npm"):
        print("[!] npm not found — skipping frontend deps (install Node.js first)")
        return False

    if not (FRONTEND_DIR / "node_modules").exists():
        print("[*] Installing frontend dependencies (npm install)...")
        result = subprocess.run(
            "npm install",
            cwd=FRONTEND_DIR,
            shell=True
        )
        if result.returncode != 0:
            print("[!] npm install failed — frontend may not start")
            return False
    print("[OK] Frontend dependencies ready")
    return True


def kill_port(port: int):
    """Kill any process occupying a port (macOS/Linux)."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split("\n")
        for pid in pids:
            if pid.strip():
                os.kill(int(pid.strip()), 9)
                print(f"[*] Killed process {pid.strip()} on port {port}")
    except Exception:
        pass  # Port is free


# ── Server launchers ────────────────────────────────────────────────

def run_backend():
    """Run FastAPI backend with uvicorn on port 5001."""
    kill_port(BACKEND_PORT)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--reload", "--port", str(BACKEND_PORT)],
        cwd=ROOT
    )


def run_frontend():
    """Run React + Vite frontend dev server."""
    return subprocess.Popen(
        "npm run dev",
        cwd=FRONTEND_DIR,
        shell=True
    )


# ── Main ────────────────────────────────────────────────────────────

def main():
    skip_install = "--skip-install" in sys.argv

    print("\n" + "=" * 60)
    print("               🎤 VibeLyrics v2.4.0")
    print("          AI-Powered Lyric Writing Assistant")
    print("=" * 60)

    # Step 1: Install dependencies
    if not skip_install:
        check_python_deps()
        check_node_deps()
    else:
        print("[*] Skipping dependency installation (--skip-install)")

    print()
    print(f"  Backend:  http://localhost:{BACKEND_PORT}  (FastAPI + Uvicorn)")
    print(f"  Frontend: http://localhost:{FRONTEND_PORT}  (React + Vite)")
    print(f"  API Docs: http://localhost:{BACKEND_PORT}/docs")
    print("=" * 60 + "\n")

    processes = []

    try:
        # Step 2: Start backend
        print("[*] Starting FastAPI backend...")
        backend = run_backend()
        processes.append(("Backend", backend))
        time.sleep(2)

        # Step 3: Start frontend
        print("[*] Starting React frontend...")
        frontend = run_frontend()
        processes.append(("Frontend", frontend))

        print("\n[OK] Both servers running! Press Ctrl+C to stop.\n")

        # Wait — if either exits, report it
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"\n[!] {name} exited with code {ret}")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
                print(f"  → Stopped {name}")
        # Wait for graceful shutdown
        for name, proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("[*] Goodbye! 🎵\n")


if __name__ == "__main__":
    main()
