import os
import unittest
import tempfile
import shutil
import pandas as pd
import numpy as np
from rasterio.enums import Resampling
from B import SR_highchange


class TestSR_highchange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for test outputs"""
        cls.test_dir = tempfile.mkdtemp()
        print(f"\nTest outputs will be saved to: {cls.test_dir}")

        # Create dummy data that will be used by all tests
        cls.create_dummy_rasters(cls.test_dir)

    @classmethod
    def tearDownClass(cls):
        """Clean up the test directory"""
        shutil.rmtree(cls.test_dir)
        print("\nTest directory cleaned up")

    @classmethod
    def create_dummy_rasters(cls, work_dir, region='NC', year=2020):
        """Create complete set of dummy raster files for testing"""
        from rasterio import Affine
        import numpy as np

        # Create dummy data arrays
        shape = (100, 100)
        transform = Affine.translation(113.94, 30.08) * Affine.scale(0.0045, 0.0045)

        # Create ALL test rasters that would be needed
        raster_data = {
            'rsei': np.random.uniform(0, 1, shape),
            'lucc': np.random.randint(1, 6, shape),
            'temperature': np.random.uniform(10, 30, shape),
            'rainfall': np.random.uniform(500, 1500, shape),
            'fvc': np.random.uniform(0, 1, shape)
        }

        # Save as GeoTIFFs with proper test paths
        from rasterio import open as rio_open
        for name, data in raster_data.items():
            # Create proper input paths that SRService would expect
            if name == 'temperature':
                input_path = f"{work_dir}/temperture/tpt/tpt_{year}.tif"
                os.makedirs(os.path.dirname(input_path), exist_ok=True)
            elif name == 'rainfall':
                input_path = f"{work_dir}/rainfall/RF/{year}.tif"
                os.makedirs(os.path.dirname(input_path), exist_ok=True)
            elif name == 'rsei':
                input_path = f"{work_dir}/RSEI_full/RSEI_{year}.tif"
                os.makedirs(os.path.dirname(input_path), exist_ok=True)
            elif name == 'lucc':
                input_path = f"{work_dir}/GLC_FCS30/merged/poyang_{year}.tif"
                os.makedirs(os.path.dirname(input_path), exist_ok=True)
            elif name == 'fvc':
                input_path = f"{work_dir}/FVC/FVC_{year}.tif"
                os.makedirs(os.path.dirname(input_path), exist_ok=True)

            with rio_open(
                    input_path,
                    'w',
                    driver='GTiff',
                    height=shape[0],
                    width=shape[1],
                    count=1,
                    dtype=data.dtype,
                    crs='EPSG:4326',
                    transform=transform,
                    nodata=0
            ) as dst:
                dst.write(data, 1)

        # Create dummy city boundary
        import geopandas as gpd
        from shapely.geometry import Polygon
        bounds = Polygon([
            (113.94, 30.08),
            (113.94, 30.08 + 0.0045 * 100),
            (113.94 + 0.0045 * 100, 30.08 + 0.0045 * 100),
            (113.94 + 0.0045 * 100, 30.08)
        ])
        gdf = gpd.GeoDataFrame(geometry=[bounds], crs='EPSG:4326')
        os.makedirs(f"{work_dir}/city", exist_ok=True)
        gdf.to_file(f"{work_dir}/city/{region}.shp")

    def setUp(self):
        """Create fresh output directory for each test"""
        self.output_dir = tempfile.mkdtemp(dir=self.test_dir)

    def test_default_configuration(self):
        """Test with default parameters"""
        print("\nRunning test_default_configuration...")

        # Initialize with test directory paths
        sr = SR_highchange(
            year=2020,
            region='NC',
            base_dir=self.test_dir,
            city_shapes={'NC': f"{self.test_dir}/city/NC.shp"}
        )

        # Run analysis with test-safe parameters
        result = sr.run_full_analysis(
            process_tiff_args={'resampling_method': Resampling.nearest},
            regression_args={'model_types': ['OLS']}  # Just test OLS for speed
        )

        self.assertTrue(result)
        print("Default configuration test passed")

    def test_custom_variables(self):
        """Test with custom variable selection"""
        print("\nRunning test_custom_variables...")

        # Test different variable combinations
        test_cases = [
            ['temp', 'fvc'],  # Only temp and vegetation
            ['lucc', 'rain'],  # Only land use and rainfall
        ]

        for vars in test_cases:
            print(f"\nTesting variable combination: {vars}")

            sr = SR_highchange(
                year=2020,
                region='NC',
                independent_vars=vars,
                base_dir=self.test_dir,
                city_shapes={'NC': f"{self.test_dir}/city/NC.shp"}
            )

            result = sr.run_full_analysis(
                regression_args={'model_types': ['OLS']}  # Just test OLS
            )
            self.assertTrue(result)
            print(f"Successfully tested combination: {vars}")

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\nRunning test_edge_cases...")

        # Test empty variable list (should use defaults)
        print("\nTesting empty variable list (should use defaults)")
        sr = SR_highchange(
            year=2020,
            region='NC',
            independent_vars=None,  # Explicit None to trigger defaults
            base_dir=self.test_dir,
            city_shapes={'NC': f"{self.test_dir}/city/NC.shp"}
        )
        self.assertEqual(len(sr.independent_vars), 4)  # Should use defaults
        result = sr.run_full_analysis(regression_args={'model_types': ['OLS']})
        self.assertTrue(result)

        print("Edge case tests passed")

    def test_output_files(self):
        """Verify output files are created correctly"""
        print("\nRunning test_output_files...")

        # Initialize with simplified analysis
        sr = SR_highchange(
            year=2020,
            region='NC',
            base_dir=self.test_dir,
            city_shapes={'NC': f"{self.test_dir}/city/NC.shp"}
        )

        # Run minimal analysis that should produce outputs
        sr.run_regression_models = lambda X, y, w, **kwargs: {
            'OLS': type('DummyModel', (), {
                'predy': np.random.rand(len(y)),
                'u': np.random.rand(len(y)),
                'summary': "Dummy summary",
                'std_err': 0.1,
                'r2': 0.5
            })
        }
        sr.select_best_model = lambda *args: (None, {'name': 'OLS'})

        # Run just the save_results portion
        df = pd.DataFrame({
            'x': np.random.rand(100),
            'y': np.random.rand(100),
            'rsei': np.random.rand(100),
            'lucc_numeric': np.random.randint(0, 5, 100),
            'temperature': np.random.rand(100),
            'rainfall': np.random.rand(100),
            'fvc': np.random.rand(100)
        })
        sr.save_results(df, {'OLS': None})

        # Check output files
        expected_files = [
            'ols_results.shp',
            'best_model_selection.txt'
        ]

        for file in expected_files:
            file_path = os.path.join(sr.work_dir, file)
            self.assertTrue(os.path.exists(file_path), f"Missing output file: {file}")
            print(f"Found expected output: {file}")

        print("Output file verification passed")
        
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("\nAll tests completed!")