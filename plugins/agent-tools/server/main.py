"""Entry point that works from any folder: python server/main.py serve"""
import os
import sys

if sys.version_info < (3, 11):
    sys.exit(f"agent-tools: Python 3.11 or later is required; {sys.executable} is "
             f"{sys.version.split()[0]}.")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_tools.__main__ import main  # noqa: E402

sys.exit(main())
