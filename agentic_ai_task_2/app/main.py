"""
Streamlit Web Application for AI Study Buddy Agent.
Provides an intuitive UI for creating local LLM-powered study plans, quizzes, and notes.
Features interactive inputs, live agent step logging, expandable plan/tool call displays,
custom CSS styling, and result persistence.
Run with: streamlit run app/main.py
"""

import sys
import json
import io
from pathlib import Path
import streamlit as st

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.agent import run_study_buddy_agent, validate_agent_input
from app.config import check_ollama_health, MODEL_NAME, SAVED_RESULTS_DIR
from app.tools import get_tools_called, reset_tool_calls


def setup_page_config():
    """Set Streamlit page configuration and inject custom CSS."""
    st.set_page_config(
        page_title="AI Study Buddy Agent",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Inject custom CSS for premium modern UI styling
    st.markdown("""
    <style>
    /* Main theme customization */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        backdrop-filter: blur(8px);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Tool Call Log Badges */
    .tool-badge {
        display: inline-block;
        background: #1e293b;
        color: #38bdf8;
        border: 1px solid #0284c7;
        border-radius: 6px;
        padding: 4px 10px;
        font-family: monospace;
        font-size: 0.85rem;
        margin: 4px;
    }

    /* Activity Badges */
    .activity-pill {
        background: #334155;
        color: #f1f5f9;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* Primary Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        color: #ffffff;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    setup_page_config()

    st.markdown('<div class="main-title">🎓 AI Study Buddy Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Fully Local Agentic AI Curriculum & Practice Generator (Ollama)</div>', unsafe_allow_html=True)

    # Sidebar Parameters Form
    with st.sidebar:
        st.header("⚙️ Agent Settings")
        st.info(f"**Local Model:** `{MODEL_NAME}`\n**Ollama Server:** Localhost:11434")

        topic = st.text_input(
            "Learning Topic",
            placeholder="e.g. Object detection with YOLOv8",
            help="Enter any non-empty subject or learning goal."
        )

        days = st.slider("Duration (Days)", min_value=1, max_value=30, value=7)
        level = st.selectbox("Target Level", options=["beginner", "intermediate", "advanced"], index=0)
        daily_minutes = st.slider("Daily Study Limit (Mins)", min_value=15, max_value=480, value=60, step=15)
        
        output_type = st.selectbox(
            "Output Format Type",
            options=["full", "plan_and_quiz", "plan_and_notes", "plan_only"],
            format_func=lambda x: {
                "full": "Full (Plan + Quiz + Notes)",
                "plan_and_quiz": "Plan & Quiz Only",
                "plan_and_notes": "Plan & Notes Only",
                "plan_only": "Plan Only"
            }[x]
        )

        st.divider()
        generate_btn = st.button("🚀 Generate Study Plan", use_container_width=True)

    # Status check section
    if generate_btn:
        if not topic.strip():
            st.error("⚠️ Please enter a valid non-empty topic before generating!")
            return

        with st.status("🤖 Agent Execution in Progress...", expanded=True) as status:
            st.write("1. Validating input parameters...")
            is_valid, err, sanitized = validate_agent_input(topic, days, level, daily_minutes, output_type)
            if not is_valid:
                status.update(label="Validation Error!", state="error")
                st.error(err)
                return

            st.write("2. Checking local Ollama service health...")
            if not check_ollama_health():
                status.update(label="Ollama Health Check Failed!", state="error")
                st.error("Ensure Ollama service is running (`ollama serve`).")
                return

            st.write("3. Executing Agent workflow tools...")
            
            # Capture stdout logs to stream in expander
            log_capture = io.StringIO()
            sys_stdout_backup = sys.stdout
            sys.stdout = log_capture

            try:
                result = run_study_buddy_agent(
                    topic=sanitized["topic"],
                    days=sanitized["days"],
                    level=sanitized["level"],
                    daily_minutes=sanitized["daily_minutes"],
                    output_type=sanitized["output_type"]
                )
            finally:
                sys.stdout = sys_stdout_backup

            agent_logs = log_capture.getvalue()
            st.session_state["last_result"] = result
            st.session_state["agent_logs"] = agent_logs
            status.update(label="✨ Study Plan Generation Complete!", state="complete")

    # Display Output Results if present in session state
    if "last_result" in st.session_state and st.session_state["last_result"]:
        res = st.session_state["last_result"]
        logs = st.session_state.get("agent_logs", "")

        if "error" in res:
            st.error(res["error"])
            return

        st.markdown("---")
        
        # Summary Metric Row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("days")}</div><div class="metric-label">Days</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("level").title()}</div><div class="metric-label">Level</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("daily_minutes")}m</div><div class="metric-label">Daily Limit</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{res.get("review", {}).get("score", 0)}/10</div><div class="metric-label">Review Score</div></div>', unsafe_allow_html=True)
        with col5:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(res.get("tools_called", []))}</div><div class="metric-label">Tools Called</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Expandable Agent Plan & Tool Call Logs (REQUIRED BY SPEC)
        with st.expander("🔍 Agent Plan & Tool-Call Logs", expanded=False):
            st.subheader("Agent Execution Log")
            st.code(logs if logs else "Logs captured in console.", language="text")
            
            st.subheader("Tools Executed")
            badge_html = "".join([f'<span class="tool-badge">[Tool Called]: {t}</span>' for t in res.get("tools_called", [])])
            st.markdown(badge_html, unsafe_allow_html=True)

        # Tabbed Output Views
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Study Plan", "❓ Practice Quiz", "📝 Revision Notes", "⭐ Quality Review"])

        # Tab 1: Study Plan
        with tab1:
            st.subheader(f"Study Schedule: {res.get('topic')}")
            for day_item in res.get("plan", []):
                with st.expander(f"Day {day_item.get('day')}: {day_item.get('title')}", expanded=True):
                    st.markdown("**🎯 Learning Goals:**")
                    for g in day_item.get("goals", []):
                        st.markdown(f"- {g}")

                    st.markdown("**⏱️ Timed Activities:**")
                    for act in day_item.get("activities", []):
                        st.markdown(f"- **{act.get('task')}** `{act.get('minutes')} mins`")

                    st.markdown("**📚 Resources (Verify before use):**")
                    for r in day_item.get("resources", []):
                        st.markdown(f"- `{r}`")

        # Tab 2: Practice Quiz
        with tab2:
            quiz = res.get("quiz", [])
            if quiz:
                st.subheader("Practice Questions & Explanations")
                for idx, q in enumerate(quiz, 1):
                    st.markdown(f"### Q{idx} (Day {q.get('day')}): {q.get('question')}")
                    if q.get("options"):
                        for opt in q.get("options", []):
                            st.write(opt)
                    with st.expander("Show Answer & Explanation"):
                        st.success(f"**Answer:** {q.get('answer')}")
                        st.info(f"**Explanation:** {q.get('explanation')}")
                    st.divider()
            else:
                st.info("No quiz requested in output format.")

        # Tab 3: Revision Notes
        with tab3:
            notes = res.get("notes", [])
            if notes:
                st.subheader("Daily Concise Summaries & Key Points")
                for n in notes:
                    with st.expander(f"Day {n.get('day')} Notes", expanded=True):
                        st.write(n.get("summary"))
                        st.markdown("**Key Takeaways:**")
                        for kp in n.get("key_points", []):
                            st.markdown(f"- {kp}")
            else:
                st.info("No revision notes requested in output format.")

        # Tab 4: Reviewer Feedback
        with tab4:
            rev = res.get("review", {})
            st.subheader(f"Overall Content Score: {rev.get('score', 0)}/10")
            st.markdown("**Evaluator Comments:**")
            for c in rev.get("comments", []):
                st.markdown(f"- {c}")
            st.markdown("**Suggestions & Improvements:**")
            for s in rev.get("suggestions", []):
                st.markdown(f"- {s}")

        st.divider()
        
        # Save Result Button & Download Option
        col_s1, col_s2 = st.columns([1, 4])
        with col_s1:
            if st.button("💾 Save Result"):
                st.success(f"Result verified & saved to:\n`{res.get('saved_file')}`")
        with col_s2:
            st.download_button(
                label="📥 Download Result JSON",
                data=json.dumps(res, indent=2),
                file_name=f"{res.get('topic').lower().replace(' ', '_')}_result.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()
