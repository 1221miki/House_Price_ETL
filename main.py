"""
Main Execution Entry Point for NYC Real Estate ETL Data Pipeline.
Course: Big Data Analytics and Business Intelligence
Instructor: Derbew Felasman
Institution: Debre Berhan University (DBU)

Group Members & Authors:
  1. Asamnew Agiz             - ID: DBU1601394
  2. Solomon Tadese           - ID: DBU1601626
  3. Dagmawit Eshete          - ID: DBU1601878
  4. Jemal Yimer              - ID: DBU1601836
  5. Selamawit Tadese         - ID: 1601596
  6. Ehitemelak Tekle Haymanot - ID: 1602121

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

