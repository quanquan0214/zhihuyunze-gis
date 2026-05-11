import unittest
import requests
import os
import json
import shutil
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import tempfile
from http import HTTPStatus

class TestSRServiceAPI(unittest.TestCase):
    BASE_URL = "http://localhost:7891"
    TEST_YEAR = 2020
    TEST_REGION = "JJ"
    TEST_MODEL = "SLM"

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for shapefile uploads
        self.temp_dir = tempfile.mkdtemp()

        # Create a simple test shapefile
        self.test_shp_path = os.path.join(self.temp_dir, "test_region.shp")
        gdf = gpd.GeoDataFrame(
            {"id": [1], "geometry": [Point(115.86, 28.68)]},
            crs="EPSG:4326"
        )
        gdf.to_file(self.test_shp_path, driver="ESRI Shapefile")

        # Paths for associated shapefile files
        self.test_shx_path = os.path.join(self.temp_dir, "test_region.shx")
        self.test_dbf_path = os.path.join(self.temp_dir, "test_region.dbf")
        self.test_prj_path = os.path.join(self.temp_dir, "test_region.prj")

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_preprocess(self):
        """Test /api/preprocess endpoint"""
        url = f"{self.BASE_URL}/api/preprocess"
        payload = {"year": self.TEST_YEAR, "region": self.TEST_REGION}
        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("csv_path", data)
        self.assertTrue(data["csv_path"].endswith(f"result_{self.TEST_YEAR}.csv"))

    def test_download_shapefile(self):
        """Test /api/download-shapefile endpoint"""
        # First run preprocess and spatial regression to generate shapefile
        requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
        requests.post(f"{self.BASE_URL}/api/spatial-regression",
                      json={"year": self.TEST_YEAR, "region": self.TEST_REGION})

        url = f"{self.BASE_URL}/api/download-shapefile?year={self.TEST_YEAR}&region={self.TEST_REGION}&model={self.TEST_MODEL}"
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.headers["Content-Type"], "application/zip")
        self.assertTrue(response.headers["Content-Disposition"].startswith("attachment; filename="))

    def test_shapefile_fields(self):
        """Test /api/shapefile-fields endpoint"""
        # First run preprocess and spatial regression to generate shapefile
        requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
        requests.post(f"{self.BASE_URL}/api/spatial-regression",
                      json={"year": self.TEST_YEAR, "region": self.TEST_REGION})

        url = f"{self.BASE_URL}/api/shapefile-fields?year={self.TEST_YEAR}&region={self.TEST_REGION}&model={self.TEST_MODEL}"
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("fields", data)
        self.assertGreater(len(data["fields"]), 0)
        expected_fields = [
            "x", "y", "rsei",
            f"{self.TEST_MODEL.lower()}_predicted",
            f"{self.TEST_MODEL.lower()}_residuals",
            f"{self.TEST_MODEL.lower()}_std_resid"
        ]
        self.assertTrue(all(field["name"] in expected_fields for field in data["fields"]))
        self.assertEqual(len(data["fields"]), len(expected_fields))

    def test_spatial_regression(self):
        """Test /api/spatial-regression endpoint"""
        # First run preprocess to generate CSV
        requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})

        url = f"{self.BASE_URL}/api/spatial-regression"
        payload = {"year": self.TEST_YEAR, "region": self.TEST_REGION}
        response = requests.post(url, json=payload)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("best_model", data)
        self.assertIn("name", data["best_model"])
        self.assertIn("r2", data["best_model"])
        self.assertIn("output_files", data)
        self.assertGreater(len(data["output_files"]), 0)

    def test_visualize_results(self):
        """Test /api/results/visualize endpoint"""
        # First run preprocess and spatial regression to generate shapefile
        requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
        requests.post(f"{self.BASE_URL}/api/spatial-regression",
                      json={"year": self.TEST_YEAR, "region": self.TEST_REGION})

        url = f"{self.BASE_URL}/api/results/visualize?year={self.TEST_YEAR}&region={self.TEST_REGION}&model={self.TEST_MODEL}"
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("geojson", data)
        self.assertEqual(data["geojson"]["type"], "FeatureCollection")
        self.assertGreater(len(data["geojson"]["features"]), 0)

    def test_download_csv(self):
        """Test /api/download-csv endpoint"""
        # First run preprocess to generate CSV
        requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})

        url = f"{self.BASE_URL}/api/download-csv?year={self.TEST_YEAR}&region={self.TEST_REGION}"
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertTrue(response.headers["Content-Disposition"].startswith("attachment; filename="))

    def test_read_csv(self):
        """Test /api/read-csv endpoint"""
        # First run preprocess to generate CSV
        requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})

        url = f"{self.BASE_URL}/api/read-csv?year={self.TEST_YEAR}&region={self.TEST_REGION}"
        response = requests.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("data", data)
        self.assertGreater(len(data["data"]), 0)
        self.assertIn("x", data["data"][0])
        self.assertIn("y", data["data"][0])
        self.assertIn("rsei", data["data"][0])

    def test_upload_region(self):
        """Test /api/upload/region endpoint"""
        url = f"{self.BASE_URL}/api/upload/region"
        region_code = "TEST_REGION"
        files = {
            "shp_file": open(self.test_shp_path, "rb"),
            "shx_file": open(self.test_shx_path, "rb") if os.path.exists(self.test_shx_path) else None,
            "dbf_file": open(self.test_dbf_path, "rb") if os.path.exists(self.test_dbf_path) else None
        }
        data = {"region_code": region_code}

        # Filter out None values from files
        files = {k: v for k, v in files.items() if v is not None}
        response = requests.post(url, files=files, data=data)

        for f in files.values():
            f.close()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["region_code"], region_code)


if __name__ == "__main__":
    unittest.main()







#
#
#
#
# class TestSRServiceAPI(unittest.TestCase):
#     BASE_URL = "http://localhost:7891"
#     TEST_YEAR = 2020
#     TEST_REGION = "JJ"
#     TEST_MODEL = "OLS"
#
#     def setUp(self):
#         """Set up test environment"""
#         # Create temporary directory for shapefile uploads
#         self.temp_dir = tempfile.mkdtemp()
#
#         # Create a simple test shapefile
#         self.test_shp_path = os.path.join(self.temp_dir, "test_region.shp")
#         gdf = gpd.GeoDataFrame(
#             {"id": [1], "geometry": [Point(113.95, 26.51)]},
#             crs="EPSG:4326"
#         )
#         gdf.to_file(self.test_shp_path, driver="ESRI Shapefile")
#
#         # Paths for associated shapefile files
#         self.test_shx_path = os.path.join(self.temp_dir, "test_region.shx")
#         self.test_dbf_path = os.path.join(self.temp_dir, "test_region.dbf")
#         self.test_prj_path = os.path.join(self.temp_dir, "test_region.prj")
#
#     def tearDown(self):
#         """Clean up test environment"""
#         shutil.rmtree(self.temp_dir, ignore_errors=True)
#
#     def test_preprocess(self):
#         """Test /api/preprocess endpoint"""
#         url = f"{self.BASE_URL}/api/preprocess"
#         payload = {"year": self.TEST_YEAR, "region": self.TEST_REGION}
#         response = requests.post(url, json=payload)
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         data = response.json()
#         self.assertEqual(data["status"], "success")
#         self.assertIn("csv_path", data)
#         self.assertTrue(data["csv_path"].endswith(f"result_{self.TEST_YEAR}.csv"))
#
#     def test_download_shapefile(self):
#         """Test /api/download-shapefile endpoint"""
#         # First run preprocess and spatial regression to generate shapefile
#         requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#         requests.post(f"{self.BASE_URL}/api/spatial-regression",
#                       json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#
#         url = f"{self.BASE_URL}/api/download-shapefile?year={self.TEST_YEAR}&region={self.TEST_REGION}&model={self.TEST_MODEL}"
#         response = requests.get(url)
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         self.assertEqual(response.headers["Content-Type"], "application/zip")
#         self.assertTrue(response.headers["Content-Disposition"].startswith("attachment; filename="))
#
#     def test_shapefile_fields(self):
#         """Test /api/shapefile-fields endpoint"""
#         # First run preprocess and spatial regression to generate shapefile
#         requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#         requests.post(f"{self.BASE_URL}/api/spatial-regression",
#                       json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#
#         url = f"{self.BASE_URL}/api/shapefile-fields?year={self.TEST_YEAR}&region={self.TEST_REGION}&model={self.TEST_MODEL}"
#         response = requests.get(url)
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         data = response.json()
#         self.assertEqual(data["status"], "success")
#         self.assertIn("fields", data)
#         self.assertGreater(len(data["fields"]), 0)
#         expected_fields = ["x", "y", "rsei", f"{self.TEST_MODEL.lower()}_predicted"]
#         self.assertTrue(all(field["name"] in expected_fields for field in data["fields"]))
#
#     def test_spatial_regression(self):
#         """Test /api/spatial-regression endpoint"""
#         # First run preprocess to generate CSV
#         requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#
#         url = f"{self.BASE_URL}/api/spatial-regression"
#         payload = {"year": self.TEST_YEAR, "region": self.TEST_REGION}
#         response = requests.post(url, json=payload)
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         data = response.json()
#         self.assertEqual(data["status"], "success")
#         self.assertIn("best_model", data)
#         self.assertIn("name", data["best_model"])
#         self.assertIn("r2", data["best_model"])
#         self.assertIn("output_files", data)
#         self.assertGreater(len(data["output_files"]), 0)
#
#     def test_visualize_results(self):
#         """Test /api/results/visualize endpoint"""
#         # First run preprocess and spatial regression to generate shapefile
#         requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#         requests.post(f"{self.BASE_URL}/api/spatial-regression",
#                       json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#
#         url = f"{self.BASE_URL}/api/results/visualize?year={self.TEST_YEAR}&region={self.TEST_REGION}&model={self.TEST_MODEL}"
#         response = requests.get(url)
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         data = response.json()
#         self.assertEqual(data["status"], "success")
#         self.assertIn("geojson", data)
#         self.assertEqual(data["geojson"]["type"], "FeatureCollection")
#         self.assertGreater(len(data["geojson"]["features"]), 0)
#
#     def test_download_csv(self):
#         """Test /api/download-csv endpoint"""
#         # First run preprocess to generate CSV
#         requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#
#         url = f"{self.BASE_URL}/api/download-csv?year={self.TEST_YEAR}&region={self.TEST_REGION}"
#         response = requests.get(url)
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         self.assertEqual(response.headers["Content-Type"], "text/csv; charset=utf-8")
#         self.assertTrue(response.headers["Content-Disposition"].startswith("attachment; filename="))
#
#     def test_read_csv(self):
#         """Test /api/read-csv endpoint"""
#         # First run preprocess to generate CSV
#         requests.post(f"{self.BASE_URL}/api/preprocess", json={"year": self.TEST_YEAR, "region": self.TEST_REGION})
#
#         url = f"{self.BASE_URL}/api/read-csv?year={self.TEST_YEAR}&region={self.TEST_REGION}"
#         response = requests.get(url)
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         data = response.json()
#         self.assertEqual(data["status"], "success")
#         self.assertIn("data", data)
#         self.assertGreater(len(data["data"]), 0)
#         self.assertIn("x", data["data"][0])
#         self.assertIn("y", data["data"][0])
#         self.assertIn("rsei", data["data"][0])
#
#     def test_upload_region(self):
#         """Test /api/upload/region endpoint"""
#         url = f"{self.BASE_URL}/api/upload/region"
#         region_code = "TEST_REGION"
#         files = {
#             "shp_file": open(self.test_shp_path, "rb"),
#             "shx_file": open(self.test_shx_path, "rb"),
#             "dbf_file": open(self.test_dbf_path, "rb")
#         }
#         data = {"region_code": region_code}
#
#         response = requests.post(url, files=files, data=data)
#
#         for f in files.values():
#             f.close()
#
#         self.assertEqual(response.status_code, HTTPStatus.OK)
#         data = response.json()
#         self.assertEqual(data["status"], "success")
#         self.assertEqual(data["region_code"], region_code)
#
#
# if __name__ == "__main__":
#     unittest.main()