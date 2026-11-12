"""
Main Execution Entry Point for NYC Real Estate ETL Data Pipeline.
Course: Big Data Analytics and Business Intelligence
Delegates directly to pipeline.py orchestrator.
"""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline import main

if __name__ == "__main__":
    main()
