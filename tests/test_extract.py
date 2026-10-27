import unittest
from pathlib import Path
from etl.extract import get_parquet_row_count, extract_parquet_chunks

class TestExtract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parent.parent
        cands = [
            root / "data" / "raw" / "properties-00000-of-00001.parquet",
            root / "Data" / "raw" / "properties-00000-of-00001.parquet",
        ]
        cls.prop_file = None
        for c in cands:
            if c.exists():
                cls.prop_file = str(c)
                break

    def test_get_parquet_row_count(self):
        if not self.prop_file:
            self.skipTest("Properties parquet file not found")
        rows = get_parquet_row_count(self.prop_file)
        self.assertGreater(rows, 3_000_000, f"Expected >3M rows, got {rows}")

    def test_extract_parquet_chunks_batching(self):
        if not self.prop_file:
            self.skipTest("Properties parquet file not found")
        batch_size = 500
        generator = extract_parquet_chunks(self.prop_file, chunk_size=batch_size, max_records=1200)
        chunks = list(generator)
        self.assertEqual(len(chunks), 3)  # 500 + 500 + 200 = 1200
        self.assertEqual(len(chunks[0]), 500)
        self.assertEqual(len(chunks[1]), 500)
        self.assertEqual(len(chunks[2]), 200)
        self.assertIn("parcel_id", chunks[0].columns)

if __name__ == "__main__":
    unittest.main()
