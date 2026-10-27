import unittest
from pathlib import Path
import pyarrow.parquet as pq

class TestQualityAndSamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent.parent
        cls.sample_dir = cls.root / "data" / "samples"
        cls.prop_sample = cls.sample_dir / "properties_sample.parquet"
        cls.sales_sample = cls.sample_dir / "sale_events_sample.parquet"

    def test_sample_datasets_exist(self):
        if not self.prop_sample.exists():
            self.skipTest("Sample files not generated yet")
        self.assertTrue(self.prop_sample.exists())
        self.assertTrue(self.sales_sample.exists())

    def test_sample_dataset_row_counts(self):
        if not self.prop_sample.exists():
            self.skipTest("Sample files not generated yet")
        pf_prop = pq.ParquetFile(self.prop_sample)
        pf_sales = pq.ParquetFile(self.sales_sample)
        
        self.assertEqual(pf_prop.metadata.num_rows, 25000)
        self.assertGreater(pf_sales.metadata.num_rows, 1000)

    def test_quality_report_exists(self):
        report_path = self.root / "logs" / "data_quality_report.md"
        if not report_path.exists():
            self.skipTest("Quality report not generated yet")
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("Data Quality & Integrity Audit Report", content)
        self.assertIn("7,009,514", content)

if __name__ == "__main__":
    unittest.main()
