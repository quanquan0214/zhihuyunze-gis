import numpy as np
import pandas as pd
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict, List, Optional, Union
import logging
from Climate import ClimateDataService, LUCC_CLASSES


class GWRService:
    def __init__(self, climate_service: ClimateDataService):
        """
        Initialize GWRService with a ClimateDataService instance.

        Args:
            climate_service: Instance of ClimateDataService providing aligned data.
        """
        self.climate_service = climate_service
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()

    def prepare_gwr_data(self, year: int, sample_size: Optional[int] = None,
                         random_state: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare data for GWR analysis: RSEI as dependent variable, temperature, rainfall, and LUCC as independent variables.

        Args:
            year: Year of data to analyze.
            sample_size: Number of sample points (None for all points).
            random_state: Random seed for sampling.

        Returns:
            Tuple of (coords, y, X) where:
                - coords: Array of (x, y) coordinates.
                - y: Array of RSEI values (dependent variable).
                - X: Array of independent variables (temperature, rainfall, LUCC dummy variables).
        """
        # Define variables for GWR
        variables = ['rsei', 'temperature', 'rainfall', 'lucc']

        # Get multi-variable sample points
        try:
            sample_data = self.climate_service.get_multivariate_sample_points(
                year=year,
                variables=variables,
                sample_size=sample_size,
                random_state=random_state
            )
        except Exception as e:
            self.logger.error(f"Failed to get sample points: {str(e)}")
            raise

        # Extract coordinates and values
        coords = np.column_stack((sample_data['x'], sample_data['y']))
        y = sample_data['values']['rsei'].reshape(-1, 1)

        # Prepare independent variables
        temperature = sample_data['values']['temperature'].reshape(-1, 1)
        rainfall = sample_data['values']['rainfall'].reshape(-1, 1)

        # Handle LUCC dummy encoding
        lucc_data = sample_data['values']['lucc']
        if isinstance(lucc_data, np.ndarray) and lucc_data.shape[1] > 1:
            # Already dummy-encoded
            lucc_encoded = lucc_data
        else:
            # Need to re-encode (in case get_lucc_data output is not properly formatted)
            lucc_raw, _ = self.climate_service.get_lucc_data(year)
            lucc_encoded = np.zeros((lucc_raw.shape[0], len(LUCC_CLASSES)))
            for idx, cls in enumerate(LUCC_CLASSES.keys()):
                lucc_encoded[:, idx] = (lucc_raw.flatten() == cls).astype(np.float32)
            # Subset to match sampled points
            if sample_size is not None and sample_size < lucc_raw.shape[0]:
                rng = np.random.default_rng(random_state)
                indices = rng.choice(lucc_raw.shape[0], size=sample_size, replace=False)
                lucc_encoded = lucc_encoded[indices]

        # Standardize continuous variables
        continuous_vars = np.hstack((temperature, rainfall, y))
        continuous_vars_scaled = self.scaler.fit_transform(continuous_vars)
        temperature_scaled = continuous_vars_scaled[:, 0].reshape(-1, 1)
        rainfall_scaled = continuous_vars_scaled[:, 1].reshape(-1, 1)
        y_scaled = continuous_vars_scaled[:, 2].reshape(-1, 1)

        # Combine independent variables
        X = np.hstack((temperature_scaled, rainfall_scaled, lucc_encoded))

        # Create column names for reference
        feature_names = ['temperature', 'rainfall'] + [f'lucc_{cls}' for cls in LUCC_CLASSES.keys()]

        return coords, y_scaled, X, feature_names

    def run_gwr(self, year: int, sample_size: Optional[int] = None,
                random_state: Optional[int] = None,
                kernel: str = 'gaussian') -> Dict[str, Union[np.ndarray, float]]:
        """
        Run GWR analysis for the specified year.

        Args:
            year: Year of data to analyze.
            sample_size: Number of sample points (None for all points).
            random_state: Random seed for sampling.
            kernel: Kernel type for GWR ('gaussian', 'bisquare', etc.).

        Returns:
            Dictionary containing:
                - coefficients: GWR coefficients for each point and variable.
                - std_errors: Standard errors of coefficients.
                - t_values: T-values of coefficients.
                - r_squared: Local R-squared values.
                - bandwidth: Selected bandwidth.
                - feature_names: Names of independent variables.
        """
        try:
            # Prepare data
            coords, y, X, feature_names = self.prepare_gwr_data(year, sample_size, random_state)

            # Select optimal bandwidth
            self.logger.info(f"Selecting bandwidth for year {year}...")
            bw_selector = Sel_BW(coords, y, X, kernel=kernel)
            bw = bw_selector.search()
            self.logger.info(f"Optimal bandwidth: {bw}")

            # Run GWR
            self.logger.info(f"Running GWR for year {year}...")
            gwr_model = GWR(coords, y, X, bw, kernel=kernel)
            gwr_results = gwr_model.fit()

            # Extract results
            results = {
                'coefficients': gwr_results.params,
                'std_errors': gwr_results.std_err,
                't_values': gwr_results.tvalues,
                'r_squared': gwr_results.localR2,
                'bandwidth': bw,
                'feature_names': feature_names
            }

            return results

        except Exception as e:
            self.logger.error(f"GWR analysis failed for year {year}: {str(e)}")
            raise

    def summarize_gwr_results(self, gwr_results: Dict[str, Union[np.ndarray, float]]) -> Dict[str, float]:
        """
        Summarize GWR results (mean and std of coefficients, R-squared, etc.).

        Args:
            gwr_results: Dictionary from run_gwr containing GWR results.

        Returns:
            Dictionary with summary statistics (mean and std of coefficients, mean R-squared).
        """
        summary = {
            'mean_coefficients': np.mean(gwr_results['coefficients'], axis=0),
            'std_coefficients': np.std(gwr_results['coefficients'], axis=0),
            'mean_r_squared': np.mean(gwr_results['r_squared']),
            'std_r_squared': np.std(gwr_results['r_squared']),
            'feature_names': gwr_results['feature_names']
        }
        return summary