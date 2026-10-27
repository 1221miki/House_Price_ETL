import unittest
import pandas as pd
from etl.validate import validate_properties, validate_sales

class TestValidate(unittest.TestCase):
    def test_validate_properties_rules(self):
        df = pd.DataFrame({
            "record_id": ["p1", "p2", "", None, "p5"],
            "parcel_id": ["10001", "20002", "30003", "40004", None],
            "building_sqft": [1500.0, -10.0, 2000.0, 1000.0, 800.0],
            "lot_sqft": [3000.0, 2000.0, -50.0, 1500.0, 1000.0],
            "year_built": [2015, 1990, 2000, 1500, 2020],  # 1500 is before 1600
            "assessed_value": [500000.0, 300000.0, 400000.0, 200000.0, -5000.0]
        })
        
        valid_df, metrics = validate_properties(df)
        self.assertEqual(len(valid_df), 1)
        self.assertEqual(valid_df.iloc[0]["record_id"], "p1")
        self.assertEqual(metrics["rejected_records"], 4)
        self.assertEqual(metrics["failed_keys"], 2)
        self.assertEqual(metrics["failed_parcels"], 1)
        self.assertEqual(metrics["failed_negative_sqft"], 1)

    def test_validate_sales_rules(self):
        df = pd.DataFrame({
            "sale_id": ["s1", "s2", "s3", None],
            "sale_price": [750000.0, 0.0, -500.0, 1000000.0],  # 0 and -500 invalid
            "sale_date": ["2022-05-10", "2021-01-01", "2020-03-15", "2019-08-20"],
            "sale_year": [2022, 2021, 2020, 2019]
        })
        
        valid_df, metrics = validate_sales(df)
        self.assertEqual(len(valid_df), 1)
        self.assertEqual(valid_df.iloc[0]["sale_id"], "s1")
        self.assertEqual(metrics["rejected_records"], 3)
        self.assertEqual(metrics["failed_nonpositive_price"], 2)
        self.assertEqual(metrics["failed_missing_id"], 1)

if __name__ == "__main__":
    unittest.main()
