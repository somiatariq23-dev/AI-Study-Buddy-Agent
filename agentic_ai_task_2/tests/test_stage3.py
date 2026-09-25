"""
Stage 3 Agent Workflow Integration Test.
Tests the 7-step agent workflow in app/agent.py including validation, planning, tool execution, review, improvement, file saving, and output schema.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.agent import run_study_buddy_agent, validate_agent_input


def run_stage3_tests():
    print("=== STAGE 3: AGENT WORKFLOW TEST ===", flush=True)

    print("\n--- Test 1: Input Validation Failure Handling ---", flush=True)
    is_val, err, _ = validate_agent_input("", 5, "beginner", 60, "full")
    print(f"Validation Empty Topic Result: is_valid={is_val}, err={err}", flush=True)
    
    is_val, err, _ = validate_agent_input("Python", 50, "beginner", 60, "full")
    print(f"Validation Out-of-bounds Days Result: is_valid={is_val}, err={err}", flush=True)

    print("\n--- Test 2: Full Agent Execution Workflow ---", flush=True)
    topic = "Object Detection Basics"
    days = 3
    level = "beginner"
    daily_minutes = 60
    output_type = "full"

    result = run_study_buddy_agent(
        topic=topic,
        days=days,
        level=level,
        daily_minutes=daily_minutes,
        output_type=output_type
    )

    print("\n--- Test 3: Output Schema Verification ---", flush=True)
    required_keys = ["topic", "days", "level", "daily_minutes", "output_type", "plan", "quiz", "notes", "review", "tools_called", "saved_file"]
    missing_keys = [k for k in required_keys if k not in result]
    
    if not missing_keys:
        print("[Schema Check Passed]: All required schema keys present.", flush=True)
        print(f"Topic: {result['topic']}")
        print(f"Days: {result['days']} (Plan entries = {len(result['plan'])})")
        print(f"Quiz Questions: {len(result['quiz'])}")
        print(f"Notes Summaries: {len(result['notes'])}")
        print(f"Review Score: {result['review']['score']}/10")
        print(f"Tools Called: {result['tools_called']}")
        print(f"Saved File Path: {result['saved_file']}")
        print("\n[SUCCESS] Stage 3 Agent Workflow test completed successfully!", flush=True)
    else:
        print(f"[Schema Check Failed]: Missing keys: {missing_keys}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    run_stage3_tests()
