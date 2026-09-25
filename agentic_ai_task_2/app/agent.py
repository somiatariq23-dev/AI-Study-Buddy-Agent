"""
Agent core workflow module for AI Study Buddy Agent.
Implements the 7-step agentic workflow:
1. Input Reception & Validation
2. Planning Step (generates & prints explicit numbered plan)
3. Sequential Tool Execution with logging
4. Content Review Step (content_reviewer)
5. Single Improvement Step (refines output once based on review)
6. File & Memory Save Step (file_saver & memory_tool)
7. Final Output Schema Generation
"""

import json
import uuid
import re
from typing import Dict, List, Any, Tuple, Optional

from app.config import check_ollama_health, query_llm
from app.prompts import IMPROVEMENT_PROMPT
from app.tools import (
    study_planner,
    quiz_generator,
    notes_generator,
    content_reviewer,
    file_saver,
    memory_tool,
    reset_tool_calls,
    get_tools_called
)

VALID_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_OUTPUT_TYPES = {"full", "plan_and_quiz", "plan_and_notes", "plan_only"}


def validate_agent_input(
    topic: str,
    days: Any,
    level: str,
    daily_minutes: Any,
    output_type: str
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Step 1: Input Validation.
    Validates user input and returns (is_valid, error_message, sanitized_params).
    """
    # 1. Topic validation
    if not topic or not isinstance(topic, str) or not topic.strip():
        return False, "[Error] Topic must be a non-empty string (e.g., 'object detection').", {}

    topic_clean = topic.strip()

    # 2. Days validation
    try:
        days_int = int(days)
        if not (1 <= days_int <= 30):
            return False, f"[Error] Days must be an integer between 1 and 30 (got {days}).", {}
    except (ValueError, TypeError):
        return False, f"[Error] Days must be a valid integer between 1 and 30 (got '{days}').", {}

    # 3. Level validation
    if not level or not isinstance(level, str) or level.strip().lower() not in VALID_LEVELS:
        return False, f"[Error] Level must be one of: {', '.join(sorted(VALID_LEVELS))} (got '{level}').", {}

    level_clean = level.strip().lower()

    # 4. Daily minutes validation
    try:
        minutes_int = int(daily_minutes)
        if not (15 <= minutes_int <= 480):
            return False, f"[Error] Daily minutes must be an integer between 15 and 480 (got {daily_minutes}).", {}
    except (ValueError, TypeError):
        return False, f"[Error] Daily minutes must be a valid integer between 15 and 480 (got '{daily_minutes}').", {}

    # 5. Output type validation
    if not output_type or not isinstance(output_type, str) or output_type.strip().lower() not in VALID_OUTPUT_TYPES:
        return False, f"[Error] Output type must be one of: {', '.join(sorted(VALID_OUTPUT_TYPES))} (got '{output_type}').", {}

    output_type_clean = output_type.strip().lower()

    sanitized = {
        "topic": topic_clean,
        "days": days_int,
        "level": level_clean,
        "daily_minutes": minutes_int,
        "output_type": output_type_clean
    }
    return True, "", sanitized


def generate_execution_plan(output_type: str) -> List[str]:
    """Generate explicit numbered steps for the Agent's planning phase."""
    steps = [
        "Step 1: Validate input parameters (Topic, Days, Level, Daily Minutes, Output Type).",
        "Step 2: Generate multi-day study schedule using study_planner tool."
    ]
    
    if output_type in ("full", "plan_and_quiz"):
        steps.append("Step 3: Generate daily practice questions using quiz_generator tool.")
    
    if output_type in ("full", "plan_and_notes"):
        steps.append("Step 4: Generate daily revision notes using notes_generator tool.")
        
    steps.extend([
        "Step 5: Review generated plan quality and time constraints using content_reviewer tool.",
        "Step 6: Refine content weak spots using single improvement pass.",
        "Step 7: Persist study plan, quiz/notes, and results using file_saver tool.",
        "Step 8: Store session metadata and progress history using memory_tool."
    ])
    return steps


def run_study_buddy_agent(
    topic: str,
    days: int,
    level: str,
    daily_minutes: int,
    output_type: str
) -> Dict[str, Any]:
    """
    Main Agent Execution Function implementing Steps 1 to 7.
    """
    print("\n" + "=" * 60)
    print("=== AI STUDY BUDDY AGENT INITIALIZATION ===")
    print("=" * 60)

    # Step 1: Input Validation
    print("[Agent Step 1]: Validating input parameters...")
    is_valid, err_msg, params = validate_agent_input(topic, days, level, daily_minutes, output_type)
    if not is_valid:
        print(err_msg)
        return {"error": err_msg}

    topic = params["topic"]
    days = params["days"]
    level = params["level"]
    daily_minutes = params["daily_minutes"]
    output_type = params["output_type"]

    # Check Ollama status before tool calls
    if not check_ollama_health():
        return {"error": "Ollama service health check failed. Ensure Ollama is running."}

    # Reset tool tracking
    reset_tool_calls()

    # Step 2: Planning Phase
    print("\n[Agent Step 2]: Generating Execution Plan...")
    plan_steps = generate_execution_plan(output_type)
    for step in plan_steps:
        print(f"  {step}")

    # Step 3: Tool Execution Phase
    print("\n[Agent Step 3]: Executing Tools in Sequence...")
    
    # Tool 1: study_planner
    plan_data = study_planner(
        topic=topic,
        days=days,
        level=level,
        daily_minutes=daily_minutes
    )

    # Tool 2: quiz_generator (conditional)
    quiz_data = []
    if output_type in ("full", "plan_and_quiz"):
        n_questions = min(days * 2, 6)
        quiz_data = quiz_generator(
            topic=topic,
            plan=plan_data,
            days=days,
            n_questions=n_questions
        )

    # Tool 3: notes_generator (conditional)
    notes_data = []
    if output_type in ("full", "plan_and_notes"):
        notes_data = notes_generator(
            topic=topic,
            plan=plan_data,
            days=days
        )

    # Construct initial result
    current_result = {
        "topic": topic,
        "days": days,
        "level": level,
        "daily_minutes": daily_minutes,
        "output_type": output_type,
        "plan": plan_data,
        "quiz": quiz_data,
        "notes": notes_data,
        "review": {"score": 0, "comments": [], "suggestions": []},
        "tools_called": get_tools_called(),
        "saved_file": ""
    }

    # Step 4: Content Review Step
    print("\n[Agent Step 4]: Executing Content Review...")
    review_res = content_reviewer(current_result)
    current_result["review"] = review_res
    print(f"  Reviewer Score: {review_res['score']}/10")
    print(f"  Comments: {review_res['comments']}")
    print(f"  Suggestions: {review_res['suggestions']}")

    # Step 5: Improvement Step (One refinement pass based on review)
    print("\n[Agent Step 5]: Executing Single Improvement Step...")
    if review_res["score"] < 9 and review_res.get("suggestions"):
        print("  Applying reviewer suggestions to refine output content...")
        try:
            imp_prompt = IMPROVEMENT_PROMPT.format(
                result_json=json.dumps(current_result, indent=2),
                score=review_res["score"],
                comments=", ".join(review_res["comments"]),
                suggestions=", ".join(review_res["suggestions"])
            )
            revised_raw = query_llm(imp_prompt, json_format=True)
            revised_data = json.loads(revised_raw)
            
            if "plan" in revised_data and isinstance(revised_data["plan"], list) and len(revised_data["plan"]) == days:
                current_result["plan"] = revised_data["plan"]
            if "quiz" in revised_data and isinstance(revised_data["quiz"], list) and quiz_data:
                current_result["quiz"] = revised_data["quiz"]
            if "notes" in revised_data and isinstance(revised_data["notes"], list) and notes_data:
                current_result["notes"] = revised_data["notes"]
            
            print("  [Improvement Pass]: Successfully refined plan content.")
        except Exception as e:
            print(f"  [Warning]: Improvement pass encountered error: {e}. Retaining original content.")
    else:
        print("  Review score is high (>= 9). No improvement revision required.")

    # Step 6: Save Step
    print("\n[Agent Step 6]: Executing Save Step...")
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    topic_slug = re.sub(r'[^a-zA-Z0-9_]', '_', topic.lower()).strip('_')
    
    # 6a. Generate & Save Markdown Study Plan
    plan_md = f"# Study Plan: {topic.title()}\n"
    plan_md += f"**Level:** {level.title()} | **Duration:** {days} Days | **Daily Commitment:** {daily_minutes} mins\n\n"
    for day_obj in current_result["plan"]:
        plan_md += f"## Day {day_obj.get('day')}: {day_obj.get('title')}\n"
        plan_md += "**Goals:**\n"
        for g in day_obj.get("goals", []):
            plan_md += f"- {g}\n"
        plan_md += "\n**Activities:**\n"
        for act in day_obj.get("activities", []):
            plan_md += f"- {act.get('task')} ({act.get('minutes')} mins)\n"
        plan_md += "\n**Resources:**\n"
        for res in day_obj.get("resources", []):
            plan_md += f"- {res}\n"
        plan_md += "\n---\n\n"

    saved_plan_file = file_saver(plan_md, f"{topic_slug}_study_plan.md", format="md")

    # 6b. Save Quiz & Notes Markdown if generated
    if quiz_data or notes_data:
        script_md = f"# Revision & Assessment: {topic.title()}\n\n"
        if quiz_data:
            script_md += "## Practice Quiz\n"
            for idx, q in enumerate(quiz_data, 1):
                script_md += f"### Q{idx} (Day {q.get('day')}): {q.get('question')}\n"
                if q.get("options"):
                    for opt in q.get("options", []):
                        script_md += f"- {opt}\n"
                script_md += f"**Answer:** {q.get('answer')}\n"
                script_md += f"**Explanation:** {q.get('explanation')}\n\n"
        if notes_data:
            script_md += "## Daily Revision Notes\n"
            for n in notes_data:
                script_md += f"### Day {n.get('day')} Summary\n{n.get('summary')}\n"
                script_md += "**Key Points:**\n"
                for kp in n.get("key_points", []):
                    script_md += f"- {kp}\n"
                script_md += "\n"
        file_saver(script_md, f"{topic_slug}_quiz_notes.md", format="md")

    # 6c. Save Full JSON Result
    saved_json_file = file_saver(current_result, f"{topic_slug}_result.json", format="json")
    current_result["saved_file"] = saved_json_file

    # 6d. Save Session Memory
    memory_tool(
        action="record_session",
        data={
            "session_id": session_id,
            "topic": topic,
            "days": days,
            "level": level,
            "daily_minutes": daily_minutes,
            "output_type": output_type,
            "plan": current_result["plan"],
            "result": current_result
        }
    )

    # Update tools_called list in current_result
    current_result["tools_called"] = get_tools_called()

    # Step 7: Return final structured output
    print("\n[Agent Step 7]: Execution Complete. Returning Structured Output.")
    print("=" * 60 + "\n")
    return current_result
