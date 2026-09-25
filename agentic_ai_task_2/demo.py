"""
Interactive CLI Interface for AI Study Buddy Agent.
Prompting user for learning topic, days, target level, daily study minutes, and output format type.
Implements interactive input validation with clear plain ASCII error messages.
Runs from project root: python demo.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.agent import run_study_buddy_agent, validate_agent_input
from app.config import check_ollama_health


def print_banner() -> None:
    """Print ASCII header banner for CLI interface."""
    print("=" * 64)
    print("           AI STUDY BUDDY AGENT - TERMINAL INTERFACE           ")
    print("   Fully Local Agentic AI Curriculum & Quiz Generator (Ollama)  ")
    print("=" * 64)


def prompt_user_inputs():
    """Interactively prompt user for inputs with real-time validation loops."""
    # 1. Topic input
    while True:
        topic_input = input("\nEnter learning topic (e.g. 'Object Detection in 7 days'): ").strip()
        if topic_input:
            break
        print("[Error] Topic cannot be empty. Please enter a valid learning goal.")

    # 2. Days input
    while True:
        days_str = input("Enter number of days (1 to 30) [Default: 7]: ").strip()
        if not days_str:
            days_val = 7
            break
        try:
            days_val = int(days_str)
            if 1 <= days_val <= 30:
                break
            print("[Error] Days must be an integer between 1 and 30.")
        except ValueError:
            print("[Error] Invalid integer. Please enter a number between 1 and 30.")

    # 3. Level input
    while True:
        level_input = input("Enter skill level (beginner | intermediate | advanced) [Default: beginner]: ").strip().lower()
        if not level_input:
            level_val = "beginner"
            break
        if level_input in ("beginner", "intermediate", "advanced"):
            level_val = level_input
            break
        print("[Error] Invalid level. Please enter 'beginner', 'intermediate', or 'advanced'.")

    # 4. Daily minutes input
    while True:
        mins_str = input("Enter daily study time in minutes (15 to 480) [Default: 60]: ").strip()
        if not mins_str:
            mins_val = 60
            break
        try:
            mins_val = int(mins_str)
            if 15 <= mins_val <= 480:
                break
            print("[Error] Daily minutes must be an integer between 15 and 480.")
        except ValueError:
            print("[Error] Invalid integer. Please enter a number between 15 and 480.")

    # 5. Output type input
    output_type_options = {
        "1": "full",
        "2": "plan_and_quiz",
        "3": "plan_and_notes",
        "4": "plan_only"
    }
    print("\nSelect Output Type:")
    print("  1. full (Study Plan + Practice Quiz + Revision Notes)")
    print("  2. plan_and_quiz (Study Plan + Practice Quiz)")
    print("  3. plan_and_notes (Study Plan + Revision Notes)")
    print("  4. plan_only (Study Plan Only)")
    
    while True:
        choice = input("Enter choice (1-4) [Default: 1 (full)]: ").strip()
        if not choice:
            out_type_val = "full"
            break
        if choice in output_type_options:
            out_type_val = output_type_options[choice]
            break
        if choice in output_type_options.values():
            out_type_val = choice
            break
        print("[Error] Invalid selection. Choose 1, 2, 3, or 4.")

    return topic_input, days_val, level_val, mins_val, out_type_val


def display_agent_result(result: dict) -> None:
    """Pretty-print the agent result in plain ASCII format."""
    if "error" in result:
        print(f"\n[Execution Failed]: {result['error']}")
        return

    print("\n" + "=" * 64)
    print("                  FINAL AGENT GENERATED OUTPUT                 ")
    print("=" * 64)
    print(f"Topic:          {result.get('topic')}")
    print(f"Duration:       {result.get('days')} Days")
    print(f"Level:          {result.get('level').title()}")
    print(f"Daily Minutes:  {result.get('daily_minutes')} mins")
    print(f"Output Type:    {result.get('output_type')}")
    print(f"Review Score:   {result.get('review', {}).get('score', 0)}/10")
    print(f"Saved Result:   {result.get('saved_file')}")
    print(f"Tools Called:   {', '.join(result.get('tools_called', []))}")
    print("-" * 64)

    # Display Plan
    print("\n--- STUDY PLAN HIGHLIGHTS ---")
    for day_item in result.get("plan", []):
        print(f"\nDay {day_item.get('day')}: {day_item.get('title')}")
        print("  Goals:")
        for goal in day_item.get("goals", []):
            print(f"    - {goal}")
        print("  Activities:")
        for act in day_item.get("activities", []):
            print(f"    - {act.get('task')} ({act.get('minutes')} mins)")
        print("  Resources:")
        for res in day_item.get("resources", []):
            print(f"    - {res}")

    # Display Quiz if present
    quiz = result.get("quiz", [])
    if quiz:
        print("\n--- PRACTICE QUIZ SAMPLE ---")
        for q in quiz[:3]:  # Display first 3 questions
            print(f"\n[Day {q.get('day')}] {q.get('question')}")
            if q.get("options"):
                for opt in q.get("options"):
                    print(f"  {opt}")
            print(f"  Answer: {q.get('answer')}")

    # Display Notes if present
    notes = result.get("notes", [])
    if notes:
        print("\n--- REVISION NOTES SAMPLE ---")
        for n in notes[:2]:  # Display first 2 note entries
            print(f"\nDay {n.get('day')} Summary: {n.get('summary')}")
            for kp in n.get("key_points", []):
                print(f"  * {kp}")

    print("\n" + "=" * 64)
    print("Plan and outputs successfully generated and saved to disk.")
    print("=" * 64 + "\n")


def main():
    print_banner()

    # Pre-check Ollama environment
    if not check_ollama_health():
        sys.exit(1)

    # Gather validated user input
    topic, days, level, daily_minutes, output_type = prompt_user_inputs()

    print(f"\n[CLI]: Launching Study Buddy Agent for '{topic}'...")
    print(f"Parameters: {days} Days | Level: {level} | Daily Mins: {daily_minutes} | Format: {output_type}")

    # Run Agent workflow
    result = run_study_buddy_agent(
        topic=topic,
        days=days,
        level=level,
        daily_minutes=daily_minutes,
        output_type=output_type
    )

    # Display output
    display_agent_result(result)


if __name__ == "__main__":
    main()
