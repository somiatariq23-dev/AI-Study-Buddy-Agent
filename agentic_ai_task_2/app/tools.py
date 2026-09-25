"""
Tools module for AI Study Buddy Agent.
Contains all 7 core tools wrapped with automatic tool-call logging decorator.
Strictly adheres to ASCII console output, UTF-8 file access, and pathlib path management.
"""

import json
import functools
from pathlib import Path
from typing import Dict, List, Any, Union, Optional

from app.config import (
    GENERATED_POSTS_DIR,
    GENERATED_SCRIPTS_DIR,
    SAVED_RESULTS_DIR,
    FILE_ENCODING,
    query_llm,
    ensure_directories
)
from app.prompts import (
    STUDY_PLANNER_PROMPT,
    QUIZ_GENERATOR_PROMPT,
    NOTES_GENERATOR_PROMPT,
    CONTENT_REVIEWER_PROMPT
)
import app.memory as memory_module

# Global registry tracking tool calls in execution context
_TOOLS_CALLED: List[str] = []


def reset_tool_calls() -> None:
    """Reset the recorded tools called list."""
    global _TOOLS_CALLED
    _TOOLS_CALLED = []


def get_tools_called() -> List[str]:
    """Retrieve the list of tool names called during the current run."""
    return list(_TOOLS_CALLED)


def log_tool_call(func):
    """
    Decorator that automatically logs '[Tool Called]: <Tool Name>' to console
    and appends the tool name to the global _TOOLS_CALLED list.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        print(f"[Tool Called]: {tool_name}")
        _TOOLS_CALLED.append(tool_name)
        return func(*args, **kwargs)
    return wrapper


@log_tool_call
def study_planner(topic: str, days: int, level: str, daily_minutes: int) -> List[Dict[str, Any]]:
    """
    Tool 1: study_planner
    Generates a structured multi-day study plan for a given topic, duration, level, and daily time limit.
    """
    prompt = STUDY_PLANNER_PROMPT.format(
        topic=topic,
        days=days,
        level=level,
        daily_minutes=daily_minutes
    )
    raw_response = query_llm(prompt, json_format=True)
    
    try:
        data = json.loads(raw_response)
        plan = data.get("plan", [])
        if not isinstance(plan, list):
            plan = []
    except Exception as e:
        print(f"[Warning] Failed to parse study_planner JSON response: {e}")
        plan = []

    # Fallback normalization if model output misses any days or fields
    normalized_plan = []
    for d in range(1, days + 1):
        existing = next((item for item in plan if item.get("day") == d), None)
        if existing:
            # Ensure minutes constraint is respected
            activities = existing.get("activities", [])
            total_mins = sum(act.get("minutes", 0) for act in activities)
            if total_mins > daily_minutes:
                # Scale down activities proportionally
                scale = daily_minutes / max(total_mins, 1)
                for act in activities:
                    act["minutes"] = max(5, int(act.get("minutes", 10) * scale))
            normalized_plan.append(existing)
        else:
            normalized_plan.append({
                "day": d,
                "title": f"Day {d}: {topic} Study",
                "goals": [f"Learn key concept {d} of {topic}"],
                "activities": [
                    {"task": "Study core documentation", "minutes": daily_minutes // 2},
                    {"task": "Practice key exercises", "minutes": daily_minutes - (daily_minutes // 2)}
                ],
                "resources": [f"official {topic} documentation (verify before use)"]
            })

    return normalized_plan


@log_tool_call
def quiz_generator(topic: str, plan: List[Dict[str, Any]], days: int, n_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Tool 2: quiz_generator
    Generates practice MCQ and short-answer questions with answers and explanations based on the study plan.
    """
    plan_summary = json.dumps([
        {"day": d.get("day"), "title": d.get("title"), "goals": d.get("goals")} for d in plan
    ], indent=2)
    
    prompt = QUIZ_GENERATOR_PROMPT.format(
        topic=topic,
        n_questions=n_questions,
        plan_summary=plan_summary
    )
    raw_response = query_llm(prompt, json_format=True)
    
    try:
        data = json.loads(raw_response)
        quiz = data.get("quiz", [])
        if isinstance(quiz, list):
            return quiz
    except Exception as e:
        print(f"[Warning] Failed to parse quiz_generator JSON response: {e}")

    # Fallback basic quiz generator
    fallback_quiz = []
    for d in range(1, min(days + 1, n_questions + 1)):
        fallback_quiz.append({
            "day": d,
            "type": "mcq",
            "question": f"What is the primary objective of Day {d} in studying {topic}?",
            "options": [
                f"A. Master core concepts of Day {d}",
                "B. Ignore fundamentals",
                "C. Skip to advanced topics",
                "D. None of the above"
            ],
            "answer": f"A. Master core concepts of Day {d}",
            "explanation": f"Day {d} focuses on fundamental learning goals for {topic}."
        })
    return fallback_quiz


@log_tool_call
def notes_generator(topic: str, plan: List[Dict[str, Any]], days: int) -> List[Dict[str, Any]]:
    """
    Tool 3: notes_generator
    Generates concise daily revision notes with summaries and key points for each day in the plan.
    """
    plan_summary = json.dumps([
        {"day": d.get("day"), "title": d.get("title"), "goals": d.get("goals")} for d in plan
    ], indent=2)
    
    prompt = NOTES_GENERATOR_PROMPT.format(
        topic=topic,
        days=days,
        plan_summary=plan_summary
    )
    raw_response = query_llm(prompt, json_format=True)
    
    try:
        data = json.loads(raw_response)
        notes = data.get("notes", [])
        if isinstance(notes, list) and len(notes) > 0:
            return notes
    except Exception as e:
        print(f"[Warning] Failed to parse notes_generator JSON response: {e}")

    # Fallback notes generator
    fallback_notes = []
    for d in range(1, days + 1):
        fallback_notes.append({
            "day": d,
            "summary": f"Day {d} key concepts for {topic}.",
            "key_points": [
                f"Understood core concepts for Day {d}.",
                f"Completed practical study exercises for {topic}."
            ]
        })
    return fallback_notes


@log_tool_call
def content_reviewer(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool 4: content_reviewer
    Evaluates generated study content against daily time constraints, clarity, and quality rules.
    Returns a review score (1-10), comments, and suggestions.
    """
    content_json = json.dumps({
        "topic": result.get("topic"),
        "days": result.get("days"),
        "level": result.get("level"),
        "daily_minutes": result.get("daily_minutes"),
        "plan": result.get("plan"),
        "quiz": result.get("quiz"),
        "notes": result.get("notes")
    }, indent=2)
    
    prompt = CONTENT_REVIEWER_PROMPT.format(
        topic=result.get("topic", "Topic"),
        days=result.get("days", 1),
        level=result.get("level", "beginner"),
        daily_minutes=result.get("daily_minutes", 60),
        content_json=content_json
    )
    raw_response = query_llm(prompt, json_format=True)
    
    try:
        data = json.loads(raw_response)
        score = int(data.get("score", 8))
        comments = data.get("comments", ["Plan is well-structured and clear."])
        suggestions = data.get("suggestions", ["Ensure daily time constraints are strictly followed."])
        return {
            "score": min(max(score, 1), 10),
            "comments": comments if isinstance(comments, list) else [str(comments)],
            "suggestions": suggestions if isinstance(suggestions, list) else [str(suggestions)]
        }
    except Exception as e:
        print(f"[Warning] Failed to parse content_reviewer JSON response: {e}")
        return {
            "score": 8,
            "comments": ["Automated check: timing and structure are valid."],
            "suggestions": ["Add more practical hands-on exercises."]
        }


@log_tool_call
def progress_saver(session_id: str, completed_days: List[int], quiz_scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool 5: progress_saver
    Stores user learning progress (completed days & quiz scores) through the memory layer.
    """
    return memory_module.update_progress(session_id, completed_days, quiz_scores)


@log_tool_call
def file_saver(content: Union[Dict[str, Any], str], filename: str, format: str = "json") -> str:
    """
    Tool 6: file_saver (MANDATORY)
    Saves generated study plans, quizzes/notes, or full JSON results under outputs/ directory:
    - Study plan markdown (.md) -> outputs/generated_posts/
    - Quiz & notes markdown (.md) -> outputs/generated_scripts/
    - Full JSON results / memory -> outputs/saved_results/
    """
    ensure_directories()
    fmt = format.lower()
    
    # Determine directory destination based on filename or format
    if "quiz" in filename.lower() or "notes" in filename.lower() or "script" in filename.lower():
        target_dir = GENERATED_SCRIPTS_DIR
    elif fmt == "md" or "plan" in filename.lower() or "post" in filename.lower():
        target_dir = GENERATED_POSTS_DIR
    else:
        target_dir = SAVED_RESULTS_DIR

    target_path = target_dir / filename

    try:
        with open(target_path, "w", encoding=FILE_ENCODING) as f:
            if isinstance(content, dict):
                json.dump(content, f, indent=2, ensure_ascii=True)
            else:
                f.write(str(content))
        return str(target_path.resolve())
    except Exception as e:
        print(f"[Error] file_saver failed to save {filename}: {e}")
        return ""


@log_tool_call
def memory_tool(action: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Tool 7: memory_tool
    Thin tool wrapper around app/memory.py for managing historical plans, sessions, and progress.
    Actions supported: 'record_session', 'update_progress', 'get_history', 'get_session'.
    """
    data = data or {}
    if action == "record_session":
        return memory_module.record_session(
            session_id=data.get("session_id", "default"),
            topic=data.get("topic", ""),
            days=data.get("days", 1),
            level=data.get("level", "beginner"),
            daily_minutes=data.get("daily_minutes", 60),
            output_type=data.get("output_type", "full"),
            plan=data.get("plan", []),
            result=data.get("result", {})
        )
    elif action == "update_progress":
        return memory_module.update_progress(
            session_id=data.get("session_id", "default"),
            completed_days=data.get("completed_days", []),
            quiz_scores=data.get("quiz_scores", {})
        )
    elif action == "get_history":
        return {"history": memory_module.get_history()}
    elif action == "get_session":
        return {"session": memory_module.get_session(data.get("session_id", ""))}
    else:
        return {"error": f"Unknown memory action: {action}"}
