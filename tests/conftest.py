# tests/conftest.py
import sys
from pathlib import Path

# project_root = .../israeli-media-monitor
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
