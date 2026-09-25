"""
Stage 5 Streamlit UI Integration Test Script.
Verifies syntax, imports, and initialization logic of app/main.py.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def test_stage5_streamlit_imports():
    print("=== STAGE 5: STREAMLIT UI IMPORT & SYNTAX TEST ===", flush=True)
    try:
        import app.main as main_module
        print("[Import Check Passed]: Successfully imported app.main module.", flush=True)
        assert hasattr(main_module, "main"), "app.main must contain main() entrypoint."
        assert hasattr(main_module, "setup_page_config"), "app.main must contain setup_page_config()."
        print("[SUCCESS] Stage 5 Streamlit UI verification passed!", flush=True)
    except Exception as e:
        print(f"[ERROR] Stage 5 import test failed: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    test_stage5_streamlit_imports()
