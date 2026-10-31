import sys
from pathlib import Path

# Run scripts/inspect_data.py
script_path = Path(__file__).resolve().parent / "scripts" / "inspect_data.py"
with open(script_path, "r", encoding="utf-8") as f:
    code = f.read()
exec(code)

