#!/usr/bin/env python3
"""
VibeLyrics Unified Runner
Run both backend and frontend with a single command. 
Setup is fully automated (cross-platform).

Usage:
    python3 run.py                  # Setup everything and run
    python3 run.py --skip-install   # Skip dependency installation
"""
import subprocess
import sys
import os
import time
import shutil
import venv
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND_DIR = ROOT / "frontend"
REQUIREMENTS = ROOT / "requirements.txt"
VENV_DIR = ROOT / ".venv"

# OS-specific executable paths
if os.name == 'nt':
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    VENV_PIP = VENV_DIR / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    VENV_PIP = VENV_DIR / "bin" / "pip"

BACKEND_PORT = 5001
FRONTEND_PORT = 5173


# ── Environment helpers ─────────────────────────────────────────────

def check_env_file():
    """Ensure .env exists, copy from .env.example if missing."""
    env_file = ROOT / ".env"
    env_example = ROOT / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print("[*] .env file not found. Copying from .env.example...")
            shutil.copy(env_example, env_file)
            print("[OK] Created .env file. Please remember to add your API keys later!")
        else:
            print("[!] .env is missing and .env.example not found.")


# ── Dependency helpers ──────────────────────────────────────────────

def setup_venv():
    """Create a virtual environment if it doesn't exist."""
    if not VENV_DIR.exists():
        print("[*] Creating Python virtual environment (.venv)...")
        venv.create(VENV_DIR, with_pip=True)
        print("[OK] Virtual environment created.")
    
    if not VENV_PYTHON.exists():
        print(f"[!] Virtual environment corrupted? {VENV_PYTHON} not found.")
        sys.exit(1)


def check_python_deps():
    """Install Python dependencies into the .venv from requirements.txt."""
    if not REQUIREMENTS.exists():
        print("[!] requirements.txt not found — skipping Python deps")
        return

    setup_venv()

    print("[*] Checking Python dependencies...")
    result = subprocess.run(
        [str(VENV_PIP), "install", "-r", str(REQUIREMENTS), "-q"],
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
    """Kill any process occupying a port (cross-platform)."""
    try:
        if os.name == 'nt':
            # Windows
            result = subprocess.run(
                f'netstat -ano | findstr :{port}', 
                capture_output=True, text=True, shell=True
            )
            lines = result.stdout.strip().split('\n')
            pids = set()
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5 and "LISTENING" in line:
                    pids.add(parts[-1])
            for pid in pids:
                if pid != "0":
                    subprocess.run(f'taskkill /F /PID {pid}', capture_output=True, shell=True)
                    print(f"[*] Killed process {pid} on port {port}")
        else:
            # macOS / Linux
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True
            )
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid.strip():
                    os.kill(int(pid.strip()), 9)
                    print(f"[*] Killed process {pid.strip()} on port {port}")
    except Exception as e:
        print(f"[DEBUG] Could not kill port {port}: {e}")
        pass  # Port is free or we lack permissions


# ── Server launchers ────────────────────────────────────────────────

def run_backend():
    """Run FastAPI backend with uvicorn via the virtual environment."""
    kill_port(BACKEND_PORT)
    return subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "backend.main:app",
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
    print("               == VibeLyrics v2.7.0 ==")
    print("          AI-Powered Lyric Writing Assistant")
    print("=" * 60)

    # Make sure env file is set up
    check_env_file()

    # Step 1: Install dependencies
    if not skip_install:
        check_python_deps()
        check_node_deps()
    else:
        print("[*] Skipping dependency installation (--skip-install)")
        # Still make sure venv exists if we try to run it
        if not VENV_PYTHON.exists():
            print("[!] Virtual environment not found. Please run without --skip-install first.")
            sys.exit(1)

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
        print("[*] Goodbye!\n")


if __name__ == "__main__":
    main()
