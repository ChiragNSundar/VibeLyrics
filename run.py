#!/usr/bin/env python3
"""
VibeLyrics Unified Runner
Run both backend and frontend with a single command
"""
import subprocess
import sys
import os
import signal
import time
from pathlib import Path


def run_backend():
    """Run FastAPI backend with uvicorn"""
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "5001"],
        cwd=Path(__file__).parent
    )


def run_frontend():
    """Run React frontend dev server"""
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("[*] Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
    
    return subprocess.Popen(
        "npm run dev",
        cwd=frontend_dir,
        shell=True
    )


def main():
    """Run both servers"""
    print("\n" + "="*60)
    print("                   VibeLyrics 2.0")
    print("              AI-Powered Lyric Writing Assistant")
    print("="*60)
    print("  Backend:  http://localhost:5001  (FastAPI)")
    print("  Frontend: http://localhost:5173  (React + Vite)")
    print("  API Docs: http://localhost:5001/docs")
    print("="*60 + "\n")
    
    processes = []
    
    try:
        # Start backend
        print("[*] Starting FastAPI backend...")
        backend = run_backend()
        processes.append(backend)
        time.sleep(2)  # Give backend time to start
        
        # Start frontend
        print("[*] Starting React frontend...")
        frontend = run_frontend()
        processes.append(frontend)
        
        print("\n[OK] Both servers running! Press Ctrl+C to stop.\n")
        
        # Wait for processes
        for p in processes:
            p.wait()
            
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
        for p in processes:
            p.terminate()
        print("[*] Goodbye!")


if __name__ == "__main__":
    main()
