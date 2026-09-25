"""
Memory layer module for AI Study Buddy Agent.
Handles persistence of learning sessions, generated study plans,
user progress tracking, and statistics using outputs/saved_results/memory.json.
Uses pathlib for cross-platform paths and UTF-8 encoding.
"""

import json
from typing import Dict, List, Any, Optional
from app.config import SAVED_RESULTS_DIR, FILE_ENCODING, ensure_directories

MEMORY_FILE = SAVED_RESULTS_DIR / "memory.json"

DEFAULT_MEMORY = {
    "sessions": {},
    "history": [],
    "statistics": {
        "total_sessions": 0,
        "topics_completed": 0,
        "total_days_planned": 0
    }
}


def load_memory() -> Dict[str, Any]:
    """Load memory from JSON file or return default structure if file does not exist."""
    ensure_directories()
    if not MEMORY_FILE.exists():
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()

    try:
        with open(MEMORY_FILE, "r", encoding=FILE_ENCODING) as f:
            data = json.load(f)
            # Ensure required top-level keys exist
            for key, val in DEFAULT_MEMORY.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception as e:
        print(f"[Warning] Failed to read memory.json ({e}). Re-initializing default memory.")
        return DEFAULT_MEMORY.copy()


def save_memory(data: Dict[str, Any]) -> None:
    """Save memory dictionary to memory.json formatted cleanly."""
    ensure_directories()
    try:
        with open(MEMORY_FILE, "w", encoding=FILE_ENCODING) as f:
            json.dump(data, f, indent=2, ensure_ascii=True)
    except Exception as e:
        print(f"[Error] Failed to write memory.json: {e}")


def record_session(
    session_id: str,
    topic: str,
    days: int,
    level: str,
    daily_minutes: int,
    output_type: str,
    plan: List[Dict[str, Any]],
    result: Dict[str, Any]
) -> Dict[str, Any]:
    """Record a new learning session into memory and update global stats."""
    mem = load_memory()
    
    session_entry = {
        "session_id": session_id,
        "topic": topic,
        "days": days,
        "level": level,
        "daily_minutes": daily_minutes,
        "output_type": output_type,
        "completed_days": [],
        "quiz_scores": {},
        "review_score": result.get("review", {}).get("score", 0),
        "saved_file": result.get("saved_file", ""),
        "plan_summary": [
            {"day": d.get("day"), "title": d.get("title")} for d in plan
        ] if plan else []
    }
    
    mem["sessions"][session_id] = session_entry
    mem["history"].append({
        "session_id": session_id,
        "topic": topic,
        "days": days,
        "level": level,
        "output_type": output_type,
        "review_score": session_entry["review_score"]
    })
    
    mem["statistics"]["total_sessions"] += 1
    mem["statistics"]["total_days_planned"] += days
    
    save_memory(mem)
    return session_entry


def update_progress(
    session_id: str,
    completed_days: List[int],
    quiz_scores: Dict[str, Any]
) -> Dict[str, Any]:
    """Update progress (completed days and quiz scores) for a given session."""
    mem = load_memory()
    if session_id in mem["sessions"]:
        session = mem["sessions"][session_id]
        session["completed_days"] = list(set(session.get("completed_days", []) + completed_days))
        session["quiz_scores"].update(quiz_scores)
        
        # Check if topic fully completed
        if len(session["completed_days"]) >= session["days"]:
            mem["statistics"]["topics_completed"] += 1

        save_memory(mem)
        return session
    else:
        return {"error": f"Session ID '{session_id}' not found in memory."}


def get_history() -> List[Dict[str, Any]]:
    """Return historical session summaries."""
    mem = load_memory()
    return mem.get("history", [])


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve details for a specific session ID."""
    mem = load_memory()
    return mem.get("sessions", {}).get(session_id)
