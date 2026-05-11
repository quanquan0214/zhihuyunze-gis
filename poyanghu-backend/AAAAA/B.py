import os
import time
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from rasterio.mask import mask
from shapely.geometry import Point
from pysal.lib import weights
from pysal.model import spreg
import warnings
from A import SRService


class SR_highchange(SRService):
    """
    Enhanced spatial regression analysis with flexible variable selection.
    Now supports choosing independent variables using element codes.
    """

    def __init__(self, year=None, region=None, independent_vars=None, **kwargs):
        """
        Initialize with configurable independent variables.

        Args:
            year (int): Analysis year (default: current year)
            region (str): Region code (default: 'NC')
            independent_vars (list): List of variable codes from:
                'temp' - temperature
                'rain' - rainfall
                'lucc' - land use
                'fvc' - fractional vegetation cover
                'dist' - distance (placeholder, not used yet)
            **kwargs: Additional configuration parameters
        """
        # Set default year and region
        self.year = year if year is not None else int(time.strftime("%Y"))
        self.region = region if region is not None else "NC"

        # Set default independent variables
        self.independent_vars = independent_vars if independent_vars is not None else ['temp', 'rain', 'lucc', 'fvc']

        # Initialize configuration
        self.config = {
            'base_dir': "D:/Google/GWR",
            'target_res': (0.0044915764205976155, 0.004491576420597607),
            'target_bounds': (113.94231063772011, 26.504792457946483,
                              118.4788028225237, 30.080087288742178),
            'target_shape': (796, 1010),
            'city_shapes': {
                "NC": "D:/Google/city/NC.shp",
                "JJ": "D:/Google/city/JJ.shp",
                "YT": "D:/Google/city/YT.shp",
                "JDZ": "D:/Google/city/JDZ.shp",
                "FZ": "D:/Google/city/FZ.shp",
                "SR": "D:/Google/city/SR.shp"
            },
            'safe_nodata': 0,
            'resampling_method': Resampling.bilinear,
            'k_neighbors': 8,
            'standardize_vars': ['temperature', 'rainfall', 'fvc'],
            'rsei_range': (0, 1)
        }
        self.config.update(kwargs)

        # Initialize parent class
        super().__init__(self.year, self.region)

        # Override class attributes
        self.base_dir = self.config['base_dir']
        self.target_res = self.config['target_res']
        self.target_bounds = self.config['target_bounds']
        self.target_shape = self.config['target_shape']
        self.city_shapes = self.config['city_shapes']

        # Create working directory
        self.current_time = time.strftime("%Y-%m-%d", time.localtime())
        self.work_dir = os.path.join(
            self.base_dir,
            f"sr_{self.current_time}_{self.region}_{self.year}"
        )
        os.makedirs(self.work_dir, exist_ok=True)

        # Initialize file paths
        self._init_file_paths()

    def _get_variable_mapping(self):
        """Return mapping between codes and actual column names"""
        return {
            'temp': 'temperature',
            'rain': 'rainfall',
            'lucc': 'lucc_numeric',
            'fvc': 'fvc',
            'dist': 'distance'  # Placeholder for future implementation
        }

    def prepare_data(self, df):
        """Prepare data with selected independent variables"""
        try:
            # Standard LUCC processing
            lucc_columns = [col for col in df.columns if col.startswith('lucc_')]
            if not lucc_columns:
                raise ValueError("No LUCC columns found")

            df['lucc_category'] = df[lucc_columns].idxmax(axis=1)
            category_mapping = {cat: idx for idx, cat in enumerate(df['lucc_category'].unique())}
            df['lucc_numeric'] = df['lucc_category'].map(category_mapping)

            # Handle distance placeholder
            if 'dist' in self.independent_vars:
                print("Note: 'dist' parameter is currently not processed and will be ignored in calculations")
                if 'distance' not in df.columns:
                    df['distance'] = 0  # Placeholder value

            return df

        except Exception as e:
            print(f"Error preparing data: {str(e)}")
            raise

    def run_regression_models(self, X, y, w, model_types=None, **kwargs):
        """Run models with selected independent variables"""
        model_types = model_types if model_types is not None else ['OLS', 'SLM', 'SEM']
        models = {}

        # Get actual column names for selected variables
        var_mapping = self._get_variable_mapping()
        selected_vars = [var_mapping[code] for code in self.independent_vars if code != 'dist']
        name_x = selected_vars.copy()

        # For LUCC, use the numeric version
        if 'lucc' in self.independent_vars:
            name_x[name_x.index('lucc_numeric')] = 'lucc'

        # Run selected models
        if 'OLS' in model_types:
            models['OLS'] = spreg.OLS(
                y, X,
                name_y='rsei',
                name_x=name_x,
                **kwargs
            )

        if 'SLM' in model_types:
            models['SLM'] = spreg.GM_Lag(
                y, X, w=w,
                name_y='rsei',
                name_x=name_x,
                **kwargs
            )

        if 'SEM' in model_types:
            models['SEM'] = spreg.GM_Error(
                y, X, w=w,
                name_y='rsei',
                name_x=name_x,
                **kwargs
            )

        # Save model summaries
        for name, model in models.items():
            summary_file = os.path.join(self.work_dir, f"{name}_summary.txt")
            with open(summary_file, 'w') as f:
                f.write(str(model.summary))

        return models

    def run_full_analysis(self, **kwargs):
        """Complete analysis pipeline with selected variables"""
        try:
            print(f"Starting analysis for {self.region} {self.year}")
            print(f"Selected independent variables: {self.independent_vars}")

            # Process rasters
            if not self.process_all_rasters(**kwargs.get('process_tiff_args', {})):
                raise Exception("Raster processing failed")

            # Create CSV
            if not self.create_csv(**kwargs.get('create_csv_args', {})):
                raise Exception("CSV creation failed")

            # Load and prepare data
            df = pd.read_csv(self.csv_out)
            df = self.prepare_data(df)

            # Create spatial weights
            w = self.create_spatial_weights(df)

            # Prepare variables
            y = df['rsei'].values.reshape(-1, 1)

            # Select only the requested independent variables
            var_mapping = self._get_variable_mapping()
            selected_cols = [var_mapping[code] for code in self.independent_vars if code != 'dist']
            X = df[selected_cols].values

            # Run regression models
            models = self.run_regression_models(X, y, w, **kwargs.get('regression_args', {}))

            # Save results
            self.save_results(df, models)

            # Select best model
            best_model, best_stats = self.select_best_model(
                models.get('OLS'),
                models.get('SLM'),
                models.get('SEM')
            )

            print(f"Analysis completed successfully")
            return True

        except Exception as e:
            print(f"Analysis failed: {str(e)}")
            return False



