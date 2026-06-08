"""
Entry point RAG Chatbot — chạy Streamlit app nhóm.

Usage:
    streamlit run app.py
"""

from __future__ import annotations

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent / "group_project" / "chatbot" / "app.py"))
