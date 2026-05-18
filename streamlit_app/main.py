"""
Streamlit Application Entry Point
==================================
This file mirrors the root app.py for containerized deployments.

Run with:
    streamlit run streamlit_app/main.py
"""

import sys
from pathlib import Path

# Ensure src/ is on the path when running from this directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import and run the main app logic from root app.py
from app import main

if __name__ == "__main__":
    main()
