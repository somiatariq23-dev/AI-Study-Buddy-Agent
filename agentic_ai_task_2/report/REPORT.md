# Technical & Engineering Report: AI Study Buddy Agent

> **Author**: AI Systems Engineer  
> **Project**: Autonomous Local Agentic AI Curriculum & Practice Generator  
> **Target LLM Model**: `llama3.2:latest` (Ollama Local Instance)  
> **Repository Path**: [`d:\projects\AI Study Buddy Agent\agentic_ai_task_2`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2)

---

## 1. Executive Summary

The **AI Study Buddy Agent** is an end-to-end local artificial intelligence assistant engineered to design structured, multi-day learning curricula, generate practice questions with explanations, produce daily revision notes, evaluate content quality, and manage persistent learning sessions. 

The application operates **100% locally** on top of the Ollama service, requiring zero third-party cloud API keys or internet connections for core inference. It provides two fully featured interfaces:
1. **Interactive Web Application**: Built with Streamlit, featuring custom CSS styling, live agent status expanders, metrics dashboards, expandable execution logs, and output download options.
2. **Terminal CLI Application**: A clean interactive terminal prompt interface supporting real-time input validation and ASCII outputs.

---

## 2. System Architecture & Component Design

The project is structured around a decoupled modular architecture separating prompt management, model inference, tool execution, session persistence, and presentation layers.

```
                   +---------------------------------------+
                   |   User Interface (Streamlit / CLI)    |
                   +-------------------+-------------------+
                                       |
                                       v
                   +-------------------+-------------------+
                   |   Input Validation Layer (agent.py)   |
                   +-------------------+-------------------+
                                       |
                                       v
                   +-------------------+-------------------+
                   |  7-Step Agent Workflow Controller     |
                   +-------------------+-------------------+
                                       |
          +----------------------------+----------------------------+
          |                            |                            |
          v                            v                            v
  +---------------+            +---------------+            +---------------+
  | study_planner |            | quiz_generator|            |notes_generator|
  +-------+-------+            +-------+-------+            +-------+-------+
          |                            |                            |
          +----------------------------+----------------------------+
                                       |
                                       v
                   +-------------------+-------------------+
                   |     content_reviewer (Score 1-10)     |
                   +-------------------+-------------------+
                                       |
                               (Score < 9/10?)
                                  /         \
                             (Yes)           (No)
                             /                  \
              +-------------v-------------+      |
              | Refinement Pass (Prompt)  |      |
              +-------------+-------------+      |
                            \                    /
                             v                  v
                   +-------------------+-------------------+
                   |     file_saver & memory_tool      |
                   +-------------------+-------------------+
                                       |
                                       v
                   +-------------------+-------------------+
                   | outputs/ & memory.json Persistence    |
                   +---------------------------------------+
```

### 2.1 The 7-Step Agentic Workflow Loop

1. **Input Validation (`validate_agent_input`)**: Verifies topic string non-emptiness, duration range (1-30 days), level validity (`beginner`, `intermediate`, `advanced`), daily limit range (15-480 minutes), and format type (`full`, `plan_and_quiz`, `plan_and_notes`, `plan_only`).
2. **Explicit Execution Planning (`generate_execution_plan`)**: Constructs an explicit numbered step-by-step execution roadmap before invoking model tools.
3. **Sequential Tool Execution**: Invokes custom LLM tool wrappers equipped with `@log_tool_call` decorator to track executed tools in real-time.
4. **Content Quality Review (`content_reviewer`)**: Passes the draft study plan, quiz, and notes to an evaluator prompt that scores the output from 1 to 10 and provides actionable comments and suggestions.
5. **Self-Correction & Refinement**: If the review score is below 9/10, the agent automatically executes a single refinement pass (`IMPROVEMENT_PROMPT`) to resolve identified weaknesses.
6. **Persistence Step (`file_saver` & `memory_tool`)**: Generates formatted Markdown files under `outputs/generated_posts/` (study plans) and `outputs/generated_scripts/` (quizzes & notes), and persists session state to `outputs/saved_results/memory.json`.
7. **Structured Output Assembly**: Packages all outputs, metadata, review scores, file paths, and tool call logs into a deterministic Python dictionary return object.

---

## 3. Core Tool Specifications (7 Registered Tools)

All tools are implemented in [`app/tools.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/app/tools.py) and registered with `@log_tool_call` for automated runtime tracing:

1. **`study_planner`**: Queries Ollama with structured constraints to produce daily study activities, goals, and resource types. Includes automated time cap normalization: if generated activity minutes exceed `daily_minutes`, the tool rescales tasks proportionally to stay within bounds.
2. **`quiz_generator`**: Creates verifiable multiple-choice and short-answer questions tailored to daily topics.
3. **`notes_generator`**: Synthesizes daily bullet-point takeaways and executive summaries.
4. **`content_reviewer`**: Evaluates plan difficulty, coverage, and time compliance, returning a 1-10 quality score with actionable feedback.
5. **`file_saver`**: Persists formatted Markdown and JSON outputs to dedicated output directories (`outputs/generated_posts`, `outputs/generated_scripts`, `outputs/saved_results`).
6. **`progress_saver`**: Updates completed day metrics and quiz scores in memory.
7. **`memory_tool`**: High-level interface managing historical learning sessions, total days planned, and completion statistics in `memory.json`.

---

## 4. Safeguards & Prompt Engineering

To guarantee reliability with local LLMs (`llama3.2:latest`), several defensive engineering techniques were integrated:

- **Strict JSON Enforcement**: Prompts mandate JSON format responses (`"format": "json"` payload in Ollama API calls) and provide standard schema examples to eliminate hallucinated formatting.
- **Hallucination Prevention**: Resource guidelines prohibit invented web URLs, fake books, or non-existent paper citations, appending explicit `"(verify before use)"` markers to official documentation recommendations.
- **Time Cap Normalization**: Normalizes activity lengths mathematically if model outputs over-budget daily study minutes.
- **Graceful Fallback Structures**: Every tool includes try-except JSON parsing safeguards with default structured fallbacks, ensuring application execution never crashes on malformed LLM outputs.

---

## 5. Verification & Test Suite Strategy

The repository contains a multi-stage automated test suite verifying every component from network health to UI components:

| Test Script | Target Verification Scope | Result |
|---|---|---|
| [`app/config.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/app/config.py) | Stage 1: Directory creation, Ollama endpoint health check (`/api/tags`), and sample LLM query. | **PASSED** (100%) |
| [`tests/test_stage2.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/tests/test_stage2.py) | Stage 2: Individual 7-tool execution, tool logging registry, and `memory.json` read/write persistence. | **PASSED** (100%) |
| [`tests/test_stage3.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/tests/test_stage3.py) | Stage 3: Complete 7-step agent loop, validation handling, review step, refinement pass, and return schema. | **PASSED** (100%) |
| [`tests/test_stage4.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/tests/test_stage4.py) | Stage 4: Subprocess execution of `demo.py` CLI with stdin pipe inputs and terminal output assertions. | **PASSED** (100%) |
| [`tests/test_stage5.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/tests/test_stage5.py) | Stage 5: Syntax, page config, and entrypoint verification for Streamlit application (`app/main.py`). | **PASSED** (100%) |
| [`tests/run_tests.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/tests/run_tests.py) | Automated execution of 10 diverse test topics generating standard `tests/test_cases.md` table. | **PASSED** (100%) |

---

## 6. Summary of Key File Locations

- **Main Streamlit Web App**: [`app/main.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/app/main.py)
- **Terminal CLI App**: [`demo.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/demo.py)
- **Agent Workflow Engine**: [`app/agent.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/app/agent.py)
- **Tools Definition & Registry**: [`app/tools.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/app/tools.py)
- **Memory Persistence Layer**: [`app/memory.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/app/memory.py)
- **LLM Config & Ollama Health**: [`app/config.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/app/config.py)
- **Automated Benchmark Suite**: [`tests/run_tests.py`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/tests/run_tests.py)
- **Benchmark Results Table**: [`tests/test_cases.md`](file:///d:/projects/AI%20Study%20Buddy%20Agent/agentic_ai_task_2/tests/test_cases.md)

---

## 7. Conclusion

The **AI Study Buddy Agent** is fully implemented, thoroughly tested, and verified end-to-end. All required stages—from local LLM infrastructure configuration and modular tool implementation to interactive Web UI presentation and automated 10-topic testing—are 100% complete and operational.
