"""Pytest bootstrap: put the backend dir on sys.path so `import app...` resolves
regardless of where pytest is invoked from."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
