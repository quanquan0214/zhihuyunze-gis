import os
os.environ['PROJ_LIB'] = r'C:\Users\33992\Desktop\pythonproject\pythonProject5\.venv\Lib\site-packages\osgeo\data\proj'
import numpy as np
# from osgeo import gdal
import shapely.geometry
import json
from typing import List, Tuple, Dict, Union
import geopandas as gpd
import rasterio.mask
from osgeo import gdal,osr
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.io import MemoryFile
import warnings


class TPRFService:
    def __init__(self, temp_dir: str = r"F:\pylake\totaldata\temperture\data",
                 rain_dir: str = r"F:\pylake\totaldata\rainfall\data"):
        self.temp_dir = temp_dir
        self.rain_dir = rain_dir
        self.data_cache = {}  # Cache for loaded TIFF data
        self._validate_directories()

    def _validate_directories(self) -> None:
        """Validate input directories."""
        if not os.path.exists(self.temp_dir):
            raise ValueError(f"Temperature directory does not exist: {self.temp_dir}")
        if not os.path.exists(self.rain_dir):
            raise ValueError(f"Rainfall directory does not exist: {self.rain_dir}")

    def _get_file_path(self, yearmonth: str, data_type: str) -> str:
        """Get TIFF file path for given yearmonth and data type."""
        if data_type not in ["temperature", "rainfall"]:
            raise ValueError("Data type must be 'temperature' or 'rainfall'")

        base_dir = self.temp_dir if data_type == "temperature" else self.rain_dir
        file_path = os.path.join(base_dir, f"{yearmonth}.tif")

        if not os.path.exists(file_path):
            warnings.warn(f"File not found: {file_path}")
        return file_path

    def _load_tiff(self, file_path: str) -> Tuple[np.ndarray, tuple, str]:
        """Load TIFF file and return data array, transform, and projection."""
        if file_path not in self.data_cache:
            try:
                ds = gdal.Open(file_path)
                if ds is None:
                    raise FileNotFoundError(f"Cannot open TIFF file: {file_path}")

                band = ds.GetRasterBand(1)
                data = band.ReadAsArray()
                nodata = band.GetNoDataValue()

                if nodata is not None:
                    data = np.ma.masked_equal(data, nodata)
                    data = data.filled(np.nan)

                transform = ds.GetGeoTransform()
                projection = ds.GetProjection()
                self.data_cache[file_path] = (data, transform, projection)
            except Exception as e:
                raise RuntimeError(f"Error loading TIFF file {file_path}: {str(e)}")
            finally:
                ds = None  # Ensure dataset is closed

        return self.data_cache[file_path]

    def read_geojson(self, file_path: str) -> gpd.GeoDataFrame:
        """Read GeoJSON file and return GeoDataFrame."""
        try:
            return gpd.read_file(file_path)
        except Exception as e:
            raise ValueError(f"Error reading GeoJSON file: {e}")

    def _mask_by_geometry(self, data: np.ndarray, transform: tuple,
                          geom: shapely.geometry.base.BaseGeometry) -> np.ndarray:
        """Mask raster data by geometry using rasterio for better accuracy."""
        try:
            # Create in-memory raster
            with MemoryFile() as memfile:
                with memfile.open(
                        driver='GTiff',
                        height=data.shape[0],
                        width=data.shape[1],
                        count=1,
                        dtype=data.dtype,
                        transform=Affine.from_gdal(*transform),
                        crs='EPSG:4326'  # Assuming WGS84, adjust if needed
                ) as dataset:
                    dataset.write(data, 1)

                # Perform the masking
                with memfile.open() as dataset:
                    masked_data, _ = rasterio.mask.mask(
                        dataset,
                        [geom],
                        crop=False,
                        all_touched=True,
                        nodata=np.nan
                    )
                    return masked_data[0][~np.isnan(masked_data[0])]
        except Exception as e:
            raise RuntimeError(f"Error masking data with geometry: {str(e)}")

    def get_geojson_yearly_monthly_stats(self, geojson: Dict, year: int,
                                         data_type: str,
                                         stats: str = "mean") -> List[float]:
        """
        Get monthly statistics for a given geojson, year, and data type.

        Args:
            geojson: GeoJSON dictionary
            year: Year between 2000 and 2022
            data_type: Either 'temperature' or 'rainfall'
            stats: Statistical measure ('mean', 'median', 'min', 'max')

        Returns:
            List of 12 monthly statistics (NaN for missing data)
        """
        if not (2000 <= year <= 2022):
            raise ValueError("Year must be between 2000 and 2022")

        # Extract geometry
        try:
            if geojson["type"] == "FeatureCollection":
                geom = shapely.geometry.shape(geojson["features"][0]["geometry"])
            else:
                geom = shapely.geometry.shape(geojson["geometry"])

            if not geom.is_valid:
                raise ValueError("Invalid geometry in GeoJSON")
        except Exception as e:
            raise ValueError(f"Error parsing GeoJSON geometry: {str(e)}")

        monthly_stats = []
        for month in range(1, 13):
            try:
                yearmonth = f"{year}{month:02d}"
                file_path = self._get_file_path(yearmonth, data_type)
                data, transform, _ = self._load_tiff(file_path)
                masked_data = self._mask_by_geometry(data, transform, geom)

                if masked_data.size == 0:
                    monthly_stats.append(np.nan)
                    continue

                if stats == "mean":
                    monthly_stats.append(float(np.nanmean(masked_data)))
                elif stats == "median":
                    monthly_stats.append(float(np.nanmedian(masked_data)))
                elif stats == "min":
                    monthly_stats.append(float(np.nanmin(masked_data)))
                elif stats == "max":
                    monthly_stats.append(float(np.nanmax(masked_data)))
                else:
                    raise ValueError(f"Unsupported statistic: {stats}")
            except Exception as e:
                warnings.warn(f"Error processing {yearmonth}: {str(e)}")
                monthly_stats.append(np.nan)

        return monthly_stats

    def _get_pixel_value(self, data: np.ndarray, transform: tuple,
                         points: List[Tuple[float, float]]) -> np.ndarray:
        """Extract pixel values for given points."""
        values = []
        for x, y in points:
            px = int((x - transform[0]) / transform[1])
            py = int((y - transform[3]) / transform[5])
            if 0 <= px < data.shape[1] and 0 <= py < data.shape[0]:
                values.append(data[py, px])
            else:
                values.append(np.nan)
        return np.array(values)

    def get_yearly_monthly_avg(self, year: int, data_type: str) -> List[float]:
        """
        Get monthly average for a given year and data type.

        Args:
            year: Year between 2000 and 2022
            data_type: Either 'temperature' or 'rainfall'

        Returns:
            List of 12 monthly averages
        """
        if not (2000 <= year <= 2022):
            raise ValueError("Year must be between 2000 and 2022")
        if data_type not in ["temperature", "rainfall"]:
            raise ValueError("Data type must be 'temperature' or 'rainfall'")

        monthly_avgs = []
        for month in range(1, 13):
            yearmonth = f"{year}{month:02d}"
            file_path = self._get_file_path(yearmonth, data_type)

            try:
                data, _, _ = self._load_tiff(file_path)

                # Handle masked arrays and invalid values
                if isinstance(data, np.ma.MaskedArray):
                    valid_data = data.compressed()  # Get only unmasked values
                else:
                    valid_data = data[~np.isnan(data)]

                if valid_data.size > 0:
                    avg = float(np.mean(valid_data))
                    # Additional check for extreme values
                    if not np.isfinite(avg):
                        raise ValueError(f"Non-finite average value for {yearmonth}")
                    monthly_avgs.append(avg)
                else:
                    monthly_avgs.append(np.nan)

            except (FileNotFoundError, ValueError) as e:
                print(f"Warning: {e}")
                monthly_avgs.append(np.nan)

        return monthly_avgs

    def get_points_yearly_monthly_stats(self, points: List[Tuple[float, float]],
                                        year: int, data_type: str,
                                        stats: str = "mean") -> List[float]:
        """
        Get monthly statistics for a polygon defined by points, year, and data type.

        Args:
            points: List of (x, y) coordinates (≥3 points)
            year: Year between 2000 and 2022
            data_type: Either 'temperature' or 'rainfall'
            stats: Statistical measure ('mean', 'median', 'min', 'max')

        Returns:
            List of 12 monthly statistics
        """
        if len(points) < 3:
            raise ValueError("At least 3 points are required to form a polygon")

        geom = shapely.geometry.Polygon(points)
        #print(geom)
        if not geom.is_valid:
            raise ValueError("Invalid polygon geometry formed by points")

        monthly_stats = []
        for month in range(1, 13):
            yearmonth = f"{year}{month:02d}"
            file_path = self._get_file_path(yearmonth, data_type)
            data, transform, _ = self._load_tiff(file_path)
            masked_data = self._mask_by_geometry(data, transform, geom)

            if masked_data.size == 0:
                monthly_stats.append(np.nan)
            else:
                if stats == "mean":
                    monthly_stats.append(float(np.mean(masked_data)))
                elif stats == "median":
                    monthly_stats.append(float(np.median(masked_data)))
                elif stats == "min":
                    monthly_stats.append(float(np.min(masked_data)))
                elif stats == "max":
                    monthly_stats.append(float(np.max(masked_data)))
                else:
                    raise ValueError("Unsupported statistic type")

        return monthly_stats

    def get_point_yearly_monthly_values(self, point: Tuple[float, float],
                                        year: int, data_type: str) -> List[float]:
        """
        Get monthly values for a given point, year, and data type.

        Args:
            point: Tuple of (x, y) coordinates
            year: Year between 2000 and 2022
            data_type: Either 'temperature' or 'rainfall'

        Returns:
            List of 12 monthly values at the point
        """
        if not (2000 <= year <= 2022):
            raise ValueError("Year must be between 2000 and 2022")
        if data_type not in ["temperature", "rainfall"]:
            raise ValueError("Data type must be 'temperature' or 'rainfall'")
        if not isinstance(point, tuple) or len(point) != 2:
            raise ValueError("Point must be a tuple of (x, y) coordinates")

        monthly_values = []
        for month in range(1, 13):
            yearmonth = f"{year}{month:02d}"
            file_path = self._get_file_path(yearmonth, data_type)
            data, transform, _ = self._load_tiff(file_path)
            value = self._get_pixel_value(data, transform, [point])[0]
            monthly_values.append(float(value) if not np.isnan(value) else np.nan)

        return monthly_values

    def get_code_yearly_monthly_stats(self, code: str, year: int, data_type: str,
                                         stats: str = "mean") -> List[float]:
        if code == "NC":
            file_path = "F:/pylake/totaldata/GLC_FCS30/南昌市_市.geojson"
        elif code == "JJ":
            file_path = "F:/pylake/totaldata/GLC_FCS30/九江市_市.geojson"
        elif code == "FZ":
            file_path = "F:/pylake/totaldata/GLC_FCS30/抚州市_市.geojson"
        elif code == "JDZ":
            file_path = "F:/pylake/totaldata/GLC_FCS30/景德镇市_市.geojson"
        elif code == "SR":
            file_path = "F:/pylake/totaldata/GLC_FCS30/上饶市_市.geojson"
        elif code == "YT":
            file_path = "F:/pylake/totaldata/GLC_FCS30/鹰潭市_市.geojson"
        else:
            raise ValueError("Invalid city code")

        with open(file_path, "r", encoding="utf-8") as f:
            city = json.load(f)

        monthly_stats = self.get_geojson_yearly_monthly_stats(
            city,
            year,
            data_type,
            stats
        )
        return monthly_stats

# if __name__ == "__main__":
#     # Example usage
#     test = TPRFService()
#
#     print(test.get_yearly_monthly_avg(2020, "temperature"))
#     # Test with point data
#     print(test.get_point_yearly_monthly_values((115.99, 29.72), 2010, "temperature"))
#
#     # Test with GeoJSON
#     with open("D:/Google/GLC_FCS30/鹰潭市_市.geojson", "r", encoding="utf-8") as f:
#         yingtan_geojson = json.load(f)
#
#     monthly_stats = test.get_geojson_yearly_monthly_stats(
#         geojson=yingtan_geojson,
#         year=2020,
#         data_type="temperature",
#         stats="mean"
#     )
#     print("Monthly stats for Yingtan City (2020):", monthly_stats)
#
#     print("抚州2020年：",test.get_code_yearly_monthly_stats("FZ",year=2020,data_type="temperature", stats="mean"))
#
#     points = [(115.99, 29.72),(115.99, 29.73),(115.98, 29.73),(115.98, 29.72),(115.99, 29.72)]
#     monthly_stats = test.get_points_yearly_monthly_stats(
#         points=points,
#         year=2010,
#         data_type="temperature",
#         stats="mean"
#     )
#     print("Monthly stats for test Points (2010):", monthly_stats)

