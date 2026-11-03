"""Entry point that works from any folder: python server/main.py serve"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_tools.__main__ import main  # noqa: E402

sys.exit(main())
