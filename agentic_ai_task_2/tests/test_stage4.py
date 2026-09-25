"""
Stage 4 CLI Interface Automated Test Script.
Runs demo.py using subprocess with piped stdin inputs to verify terminal flow.
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_stage4_cli_test():
    print("=== STAGE 4: CLI INTERFACE DEMO TEST ===", flush=True)
    
    # Input sequence: topic, days, level, daily_minutes, output_type choice (4 = plan_only)
    input_text = "SQL Fundamentals\n2\nbeginner\n30\n4\n"
    
    cmd = [sys.executable, "-u", "demo.py"]
    
    proc = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    
    stdout, stderr = proc.communicate(input=input_text, timeout=600)
    
    print("\n--- CLI OUTPUT START ---")
    print(stdout)
    print("--- CLI OUTPUT END ---")
    
    if proc.returncode == 0 and "FINAL AGENT GENERATED OUTPUT" in stdout:
        print("\n[SUCCESS] Stage 4 CLI demo test executed cleanly!", flush=True)
    else:
        print(f"\n[ERROR] CLI test failed with return code {proc.returncode}.", flush=True)
        if stderr:
            print(f"Stderr: {stderr}")
        sys.exit(1)

if __name__ == "__main__":
    run_stage4_cli_test()
