"""
Stage 2 Individual Tool & Memory Integration Test Script.
Tests all 7 tools individually and verifies tool logging and memory persistence.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import check_ollama_health, ensure_directories
from app.tools import (
    study_planner,
    quiz_generator,
    notes_generator,
    content_reviewer,
    progress_saver,
    file_saver,
    memory_tool,
    reset_tool_calls,
    get_tools_called
)


def run_stage2_tests():
    print("=== STAGE 2: INDIVIDUAL TOOLS & MEMORY TEST ===", flush=True)
    ensure_directories()
    reset_tool_calls()

    if not check_ollama_health():
        print("[Error] Ollama health check failed. Aborting tests.", flush=True)
        sys.exit(1)

    print("\n--- Test 1: study_planner ---", flush=True)
    topic = "Python Basics"
    days = 2
    level = "beginner"
    daily_minutes = 60
    plan = study_planner(topic=topic, days=days, level=level, daily_minutes=daily_minutes)
    print(f"Result: Generated {len(plan)} day plan entries.", flush=True)

    print("\n--- Test 2: quiz_generator ---", flush=True)
    quiz = quiz_generator(topic=topic, plan=plan, days=days, n_questions=2)
    print(f"Result: Generated {len(quiz)} quiz questions.", flush=True)

    print("\n--- Test 3: notes_generator ---", flush=True)
    notes = notes_generator(topic=topic, plan=plan, days=days)
    print(f"Result: Generated {len(notes)} daily revision note entries.", flush=True)

    print("\n--- Test 4: content_reviewer ---", flush=True)
    sample_result = {
        "topic": topic,
        "days": days,
        "level": level,
        "daily_minutes": daily_minutes,
        "plan": plan,
        "quiz": quiz,
        "notes": notes
    }
    review = content_reviewer(sample_result)
    print(f"Result: Score = {review.get('score')}/10, Comments = {review.get('comments')}", flush=True)

    print("\n--- Test 5: file_saver ---", flush=True)
    saved_md = file_saver("# Study Plan\nDay 1: Python syntax", "test_plan.md", format="md")
    saved_json = file_saver(sample_result, "test_result.json", format="json")
    print(f"Result MD saved to: {saved_md}", flush=True)
    print(f"Result JSON saved to: {saved_json}", flush=True)

    print("\n--- Test 6: memory_tool & progress_saver ---", flush=True)
    mem_res = memory_tool(
        action="record_session",
        data={
            "session_id": "test_session_001",
            "topic": topic,
            "days": days,
            "level": level,
            "daily_minutes": daily_minutes,
            "output_type": "full",
            "plan": plan,
            "result": {"review": review, "saved_file": saved_json}
        }
    )
    print(f"Result recorded session: {mem_res.get('session_id')}", flush=True)

    prog_res = progress_saver(
        session_id="test_session_001",
        completed_days=[1],
        quiz_scores={"day_1": 100}
    )
    print(f"Result updated progress: Completed days = {prog_res.get('completed_days')}", flush=True)

    hist_res = memory_tool(action="get_history")
    print(f"Result memory history count: {len(hist_res.get('history', []))}", flush=True)

    print("\n--- Verified Tools Called Registry ---", flush=True)
    called = get_tools_called()
    print(f"Tools Called ({len(called)} total): {called}", flush=True)
    print("\n[SUCCESS] Stage 2 testing complete!", flush=True)


if __name__ == "__main__":
    run_stage2_tests()
