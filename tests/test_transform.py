import unittest
import pandas as pd
import numpy as np
from etl.transform import clean_parcel_id, derive_borough, clean_zip_code, transform_sales

class TestTransform(unittest.TestCase):
    def test_clean_parcel_id(self):
        raw_series = pd.Series(["1001230045.00000000", "2054800111", "  3012340001  ", "nan", None])
        cleaned = clean_parcel_id(raw_series)
        self.assertEqual(cleaned.iloc[0], "1001230045")
        self.assertEqual(cleaned.iloc[1], "2054800111")
        self.assertEqual(cleaned.iloc[2], "3012340001")
        self.assertTrue(pd.isna(cleaned.iloc[3]))
        self.assertTrue(pd.isna(cleaned.iloc[4]))

    def test_derive_borough(self):
        df = pd.DataFrame({
            "parcel_id": ["1000100001", "2000200002", "3000300003", "4000400004", "5000500005", "9999999999"],
            "city": [None, None, None, None, None, "Yonkers"]
        })
        boroughs = derive_borough(df)
        self.assertEqual(boroughs.iloc[0], "Manhattan")
        self.assertEqual(boroughs.iloc[1], "Bronx")
        self.assertEqual(boroughs.iloc[2], "Brooklyn")
        self.assertEqual(boroughs.iloc[3], "Queens")
        self.assertEqual(boroughs.iloc[4], "Staten Island")
        self.assertEqual(boroughs.iloc[5], "Yonkers")

    def test_clean_zip_code(self):
        series = pd.Series(["10001.0", "11201", "7030", "00000", np.nan])
        cleaned = clean_zip_code(series)
        self.assertEqual(cleaned.iloc[0], "10001")
        self.assertEqual(cleaned.iloc[1], "11201")
        self.assertEqual(cleaned.iloc[2], "07030")
        self.assertTrue(pd.isna(cleaned.iloc[3]))
        self.assertTrue(pd.isna(cleaned.iloc[4]))

    def test_transform_sales_metrics(self):
        df = pd.DataFrame({
            "record_id": ["sale-1", "sale-2"],
            "parcel_id": ["1000120001", "2000140002"],
            "city": ["New York", "Bronx"],
            "state": ["ny", "NY"],
            "zip_code": ["10001", "10451"],
            "country": ["us", "US"],
            "latitude": [40.71, 40.82],
            "longitude": [-74.00, -73.92],
            "property_class_raw": ["A1", "B2"],
            "sale_price": [1_000_000.0, 500_000.0],
            "sale_date": ["2023-06-15", "2021-11-20"],
            "building_sqft": [1000.0, 500.0],
            "year_built": [2010.0, 1995.0]
        })
        transformed = transform_sales(df)
        self.assertIn("sale_id", transformed.columns)
        self.assertIn("price_per_sqft", transformed.columns)
        self.assertEqual(transformed["price_per_sqft"].iloc[0], 1000.0)
        self.assertEqual(transformed["sale_year"].iloc[0], 2023)
        self.assertEqual(transformed["sale_quarter"].iloc[0], 2)
        self.assertEqual(transformed["sale_month"].iloc[0], 6)
        self.assertEqual(transformed["borough"].iloc[0], "Manhattan")

if __name__ == "__main__":
    unittest.main()
