import sys
from pathlib import Path

# Run scripts/transform.py
script_path = Path(__file__).resolve().parent / "scripts" / "transform.py"
with open(script_path, "r", encoding="utf-8") as f:
    code = f.read()
exec(code)

