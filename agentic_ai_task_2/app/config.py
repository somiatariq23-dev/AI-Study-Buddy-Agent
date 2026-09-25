"""
Configuration module for AI Study Buddy Agent.
Handles environment settings, file paths, model configurations,
directory creation, and Ollama connection health checks.
"""

import sys
import json
from pathlib import Path
import requests

# Single config variable for the local Ollama model name
MODEL_NAME = "llama3.2:latest"

# Ollama server connection settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
LLM_TIMEOUT = 300  # Generous timeout in seconds for local model load/inference

# Base & Output Directory paths using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
GENERATED_POSTS_DIR = OUTPUTS_DIR / "generated_posts"
GENERATED_SCRIPTS_DIR = OUTPUTS_DIR / "generated_scripts"
SAVED_RESULTS_DIR = OUTPUTS_DIR / "saved_results"
TESTS_DIR = BASE_DIR / "tests"

# File encoding
FILE_ENCODING = "utf-8"


def ensure_directories() -> None:
    """Ensure all required output and project directories exist."""
    GENERATED_POSTS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    SAVED_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TESTS_DIR.mkdir(parents=True, exist_ok=True)


def check_ollama_health() -> bool:
    """
    Check if Ollama service is reachable and if MODEL_NAME is installed.
    Prints helpful plain ASCII instructions if checks fail.
    """
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=10)
        if response.status_code != 200:
            print("[Error] Ollama service returned non-200 status. Please run: ollama serve")
            return False
    except requests.exceptions.RequestException:
        print("[Error] Ollama service is not running. Please run: ollama serve")
        return False

    try:
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        
        # Check exact or prefix match (e.g. gemma3:4b or gemma3:4b-latest)
        model_found = any(MODEL_NAME in m for m in models)
        if not model_found:
            print(f"[Error] Model '{MODEL_NAME}' not found in Ollama.")
            print(f"Installed models: {', '.join(models) if models else 'None'}")
            print(f"Please run: ollama pull {MODEL_NAME}")
            return False
    except Exception as err:
        print(f"[Error] Failed to parse Ollama models response: {err}")
        return False

    return True


def query_llm(prompt: str, json_format: bool = True) -> str:
    """
    Query the local Ollama LLM endpoint with configured timeout and parameters.
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    if json_format:
        payload["format"] = "json"

    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json=payload,
            timeout=LLM_TIMEOUT
        )
        response.raise_for_status()
        res_json = response.json()
        return res_json.get("response", "")
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Ollama request timed out after {LLM_TIMEOUT} seconds.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama connection error: {e}")


if __name__ == "__main__":
    print("--- Stage 1 Health Check ---")
    ensure_directories()
    print("Output directories verified/created.")
    
    if check_ollama_health():
        print(f"[Success] Ollama service is running and model '{MODEL_NAME}' is available.")
        print("Sending test prompt to Ollama...")
        test_prompt = "Respond with JSON: {\"status\": \"ok\", \"message\": \"Ollama test successful\"}"
        try:
            result = query_llm(test_prompt, json_format=True)
            print("Response received from Ollama:")
            print(result)
        except Exception as e:
            print(f"[Error] Test prompt execution failed: {e}")
    else:
        sys.exit(1)
