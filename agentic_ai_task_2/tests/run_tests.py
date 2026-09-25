"""
Automated Test Runner for AI Study Buddy Agent.
Runs the agent on 10 specified topics with varied levels, durations, daily minutes, and output types.
Measures execution time, collects tools used, review scores, and saved file paths.
Generates/updates tests/test_cases.md markdown table automatically.
Run with: python tests/run_tests.py  or  python -m tests.run_tests
"""

import sys
import time
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.agent import run_study_buddy_agent
from app.config import check_ollama_health, TESTS_DIR, FILE_ENCODING

# 10 Specified Test Topics with Varied Configurations
TEST_CASES = [
    {
        "no": 1,
        "topic": "Object detection",
        "level": "beginner",
        "days": 5,
        "daily_minutes": 60,
        "output_type": "full"
    },
    {
        "no": 2,
        "topic": "Python basics",
        "level": "beginner",
        "days": 3,
        "daily_minutes": 45,
        "output_type": "plan_and_quiz"
    },
    {
        "no": 3,
        "topic": "SQL",
        "level": "intermediate",
        "days": 4,
        "daily_minutes": 30,
        "output_type": "plan_and_notes"
    },
    {
        "no": 4,
        "topic": "Machine learning",
        "level": "beginner",
        "days": 7,
        "daily_minutes": 90,
        "output_type": "full"
    },
    {
        "no": 5,
        "topic": "Neural networks",
        "level": "intermediate",
        "days": 5,
        "daily_minutes": 60,
        "output_type": "plan_and_quiz"
    },
    {
        "no": 6,
        "topic": "Data annotation",
        "level": "beginner",
        "days": 2,
        "daily_minutes": 30,
        "output_type": "plan_only"
    },
    {
        "no": 7,
        "topic": "FastAPI",
        "level": "intermediate",
        "days": 3,
        "daily_minutes": 60,
        "output_type": "full"
    },
    {
        "no": 8,
        "topic": "Git",
        "level": "beginner",
        "days": 2,
        "daily_minutes": 30,
        "output_type": "plan_and_notes"
    },
    {
        "no": 9,
        "topic": "Statistics",
        "level": "advanced",
        "days": 5,
        "daily_minutes": 45,
        "output_type": "plan_and_quiz"
    },
    {
        "no": 10,
        "topic": "Deep learning",
        "level": "advanced",
        "days": 7,
        "daily_minutes": 120,
        "output_type": "full"
    }
]


def run_all_test_cases():
    print("=" * 70, flush=True)
    print("      AI STUDY BUDDY AGENT - AUTOMATED TEST SUITE (10 TOPICS)      ", flush=True)
    print("=" * 70, flush=True)

    if not check_ollama_health():
        print("[Error] Ollama health check failed. Aborting test suite.", flush=True)
        sys.exit(1)

    results_table = []

    for tc in TEST_CASES:
        no = tc["no"]
        topic = tc["topic"]
        level = tc["level"]
        days = tc["days"]
        daily_minutes = tc["daily_minutes"]
        output_type = tc["output_type"]

        print(f"\n[{no}/10] Testing Topic: '{topic}' ({level.title()}, {days} Days, {daily_minutes} m/day, Format: {output_type})...", flush=True)
        
        start_time = time.time()
        res = run_study_buddy_agent(
            topic=topic,
            days=days,
            level=level,
            daily_minutes=daily_minutes,
            output_type=output_type
        )
        elapsed_sec = time.time() - start_time
        time_taken_str = f"{elapsed_sec:.1f}s"

        if "error" in res:
            print(f"  [Test Failed]: {res['error']}", flush=True)
            results_table.append({
                "no": no,
                "topic": topic,
                "level": level,
                "days": days,
                "daily_minutes": daily_minutes,
                "output_type": output_type,
                "tools_used": "Failed",
                "saved_file": "None",
                "review_score": "N/A",
                "time_taken": time_taken_str,
                "useful": "No"
            })
        else:
            tools_str = ", ".join(res.get("tools_called", []))
            score = res.get("review", {}).get("score", "N/A")
            saved_path = res.get("saved_file", "")
            
            print(f"  [Test Passed] Score: {score}/10 | Tools: [{tools_str}] | Time: {time_taken_str}", flush=True)
            print(f"  Saved File: {saved_path}", flush=True)

            results_table.append({
                "no": no,
                "topic": topic,
                "level": level,
                "days": days,
                "daily_minutes": daily_minutes,
                "output_type": output_type,
                "tools_used": tools_str,
                "saved_file": saved_path,
                "review_score": f"{score}/10",
                "time_taken": time_taken_str,
                "useful": ""  # Left empty for user judgment as requested
            })

    # Write Markdown table to tests/test_cases.md
    md_file_path = TESTS_DIR / "test_cases.md"
    
    md_content = "# AI Study Buddy Agent - Automated Test Execution Results\n\n"
    md_content += f"**Total Test Cases:** {len(results_table)}\n"
    md_content += f"**Execution Model:** Local Ollama\n\n"
    md_content += "| No | Topic | Level | Days | Min/day | Output type | Tools used | Saved file path | Review score | Time taken | Useful? |\n"
    md_content += "|---|---|---|---|---|---|---|---|---|---|---|\n"

    for r in results_table:
        md_content += f"| {r['no']} | {r['topic']} | {r['level']} | {r['days']} | {r['daily_minutes']} | {r['output_type']} | {r['tools_used']} | `{r['saved_file']}` | {r['review_score']} | {r['time_taken']} | {r['useful']} |\n"

    with open(md_file_path, "w", encoding=FILE_ENCODING) as f:
        f.write(md_content)

    print("\n" + "=" * 70, flush=True)
    print(f"[SUCCESS] All 10 test cases finished! Summary table saved to:\n  {md_file_path.resolve()}", flush=True)
    print("=" * 70 + "\n", flush=True)


if __name__ == "__main__":
    run_all_test_cases()
