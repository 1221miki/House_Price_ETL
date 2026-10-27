import unittest
import pandas as pd
from unittest.mock import MagicMock
from etl.load import bulk_load_dataframe

class TestLoad(unittest.TestCase):
    def test_bulk_load_empty_dataframe(self):
        df = pd.DataFrame()
        mock_conn = MagicMock()
        loaded = bulk_load_dataframe(df, "properties", mock_conn)
        self.assertEqual(loaded, 0)
        mock_conn.cursor.assert_not_called()

    def test_bulk_load_dataframe_staging_execution(self):
        df = pd.DataFrame({
            "record_id": ["p1", "p2"],
            "parcel_id": ["10001", "20002"],
            "city": ["New York", "Brooklyn"]
        })
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        loaded = bulk_load_dataframe(df, "properties", mock_conn, primary_key="record_id", use_staging_dedup=True)
        self.assertEqual(loaded, 2)
        
        calls = [str(call) for call in mock_cursor.execute.call_args_list]
        self.assertTrue(any("CREATE TEMP TABLE temp_properties_stage" in c for c in calls))
        self.assertTrue(any("ON CONFLICT (record_id) DO NOTHING" in c for c in calls))
        self.assertTrue(mock_cursor.copy_expert.called)

if __name__ == "__main__":
    unittest.main()
