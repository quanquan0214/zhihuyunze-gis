import os
import time
import traceback

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

warnings.filterwarnings('ignore')

class SRService:
    # Target resolution and bounds (based on RSEI)
    target_res = (0.0044915764205976155, 0.004491576420597607)
    target_bounds = (113.94231063772011, 26.504792457946483, 118.4788028225237, 30.080087288742178)
    target_shape = (796, 1010)  # height, width

    # Directory configurations
    base_dir = "F:/pylake/totaldata/GWR"
    city_shapes = {
        "NC": "F:/pylake/totaldata/city/NC.shp",
        "JJ": "F:/pylake/totaldata/city/JJ.shp",
        "YT": "F:/pylake/totaldata/city/YT.shp",
        "JDZ": "F:/pylake/totaldata/city/JDZ.shp",
        "FZ": "F:/pylake/totaldata/city/FZ.shp",
        "SR": "F:/pylake/totaldata/city/SR.shp"
    }

    def __init__(self, year, region):
        """Initialize the service with year and region"""
        self.year = year
        self.region = region

        # Create working directory
        self.current_time = time.strftime("%Y-%m-%d", time.localtime())
        self.work_dir = os.path.join(self.base_dir, f"sr_{self.current_time}_{region}_{year}")
        os.makedirs(self.work_dir, exist_ok=True)

        # Initialize file paths
        self._init_file_paths()

    def _init_file_paths(self):
        """Initialize all file paths"""
        # Input files
        self.temp_dir = f"F:/pylake/totaldata/temperture/tpt/tpt_{self.year}.tif"
        self.rain_dir = f"F:/pylake/totaldata/rainfall/RF/{self.year}.tif"
        self.rsei_dir = f"F:/pylake/totaldata/RSEI_full/RSEI_{self.year}.tif"
        self.lucc_dir = f"F:/pylake/totaldata/GLC_FCS30/merged/poyang_{self.year}.tif"
        self.fvc_dir = f"F:/pylake/totaldata/FVC/FVC_{self.year}.tif"

        # Output files
        self.rsei_out = os.path.join(self.work_dir, f"rsei_{self.year}.tif")
        self.lucc_out = os.path.join(self.work_dir, f"lucc_{self.year}.tif")
        self.rain_out = os.path.join(self.work_dir, f"rain_{self.year}.tif")
        self.temp_out = os.path.join(self.work_dir, f"temp_{self.year}.tif")
        self.fvc_out = os.path.join(self.work_dir, f"fvc_{self.year}.tif")
        self.csv_out = os.path.join(self.work_dir, f"result_{self.year}.csv")

        # Get city shapefile
        self.city_shp = self.city_shapes.get(self.region, self.city_shapes["NC"])  # Default to Nanchang

    def process_tiff(self, input_path, output_path, resampling_method=Resampling.bilinear, safe_nodata=0):
        """Process and align a TIFF file using raster-based masking"""
        try:
            # Check if input file exists
            if not os.path.exists(input_path):
                print(f"Input file not found: {input_path}")
                return False

            # Step 1: Create mask from shapefile
            with rasterio.open(input_path) as src:
                # Get the shapefile and transform to raster CRS
                city_boundary = gpd.read_file(self.city_shp)
                city_boundary = city_boundary.to_crs(src.crs)

                # Create mask array
                mask = rasterio.features.rasterize(
                    [(geom, 1) for geom in city_boundary.geometry],
                    out_shape=src.shape,
                    transform=src.transform,
                    fill=0,
                    dtype='uint8'
                )

            # Step 2: Process input raster
            with rasterio.open(input_path) as src:
                # Read and prepare data
                data = src.read(1)
                src_nodata = src.nodata if src.nodata is not None else safe_nodata

                # Handle nodata and NaN
                data = np.where((data == src_nodata) | np.isnan(data), safe_nodata, data)

                # Special handling for RSEI
                if "RSEI" in input_path.lower():
                    data[(data < 0) | (data > 2)] = safe_nodata

                # Resample to target specs
                dst_data = np.full(self.target_shape, safe_nodata, dtype=data.dtype)
                dst_transform = rasterio.transform.from_bounds(
                    *self.target_bounds, self.target_shape[1], self.target_shape[0])

                reproject(
                    source=data,
                    destination=dst_data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=src.crs,
                    resampling=resampling_method,
                    src_nodata=safe_nodata,
                    dst_nodata=safe_nodata
                )

                # Apply mask to resampled data
                # First we need to transform the mask to match the resampled data
                mask_resampled = np.full(self.target_shape, 0, dtype='uint8')
                reproject(
                    source=mask,
                    destination=mask_resampled,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=src.crs,
                    resampling=Resampling.nearest  # Use nearest for categorical mask
                )

                # Apply the mask
                final_data = np.where(mask_resampled == 1, dst_data, safe_nodata)

                # Find bounding box of valid data
                rows, cols = np.where(mask_resampled == 1)
                if len(rows) == 0:
                    raise ValueError("No overlap between raster and shapefile")

                min_row, max_row = np.min(rows), np.max(rows)
                min_col, max_col = np.min(cols), np.max(cols)

                # Crop to valid area
                cropped_data = final_data[min_row:max_row + 1, min_col:max_col + 1]
                cropped_transform = rasterio.windows.transform(
                    rasterio.windows.Window.from_slices(
                        (min_row, max_row + 1), (min_col, max_col + 1)
                    ),
                    dst_transform
                )

                # Prepare output profile
                profile = {
                    'driver': 'GTiff',
                    'height': cropped_data.shape[0],
                    'width': cropped_data.shape[1],
                    'count': 1,
                    'dtype': cropped_data.dtype,
                    'crs': src.crs,
                    'transform': cropped_transform,
                    'nodata': safe_nodata,
                    'compress': 'lzw'
                }

                # Write output
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(cropped_data, 1)

            print(f"Successfully processed: {output_path}")
            return True

        except Exception as e:
            print(f"Error processing {input_path}: {str(e)}")
            return False

    def process_all_rasters(self):
        """Process all raster files for the given year and region"""
        results = [
            self.process_tiff(self.temp_dir, self.temp_out),
            self.process_tiff(self.rain_dir, self.rain_out),
            self.process_tiff(self.rsei_dir, self.rsei_out),
            self.process_tiff(self.lucc_dir, self.lucc_out),
            self.process_tiff(self.fvc_dir, self.fvc_out)
        ]
        return all(results)

    # def create_csv(self):
    #     """Create CSV file from processed raster data with consistent column lengths"""
    #     try:
    #         # Dictionary of raster files and their corresponding column names
    #         raster_files = {
    #             'rsei': self.rsei_out,
    #             'lucc': self.lucc_out,
    #             'rainfall': self.rain_out,
    #             'temperature': self.temp_out,
    #             'fvc': self.fvc_out
    #         }
    #
    #         # Initialize coordinate arrays
    #         coords = {'x': None, 'y': None}
    #         data_dict = {}
    #
    #         # First pass: get coordinates from one file and check all rasters
    #         with rasterio.open(raster_files['lucc']) as src:
    #             height, width = src.shape
    #             rows, cols = np.indices((height, width))
    #             xs, ys = rasterio.transform.xy(src.transform, rows.flatten(), cols.flatten())
    #             coords['x'] = np.array(xs)
    #             coords['y'] = np.array(ys)
    #             expected_length = len(coords['x'])
    #
    #         # Second pass: read all raster data and validate lengths
    #         for name, file in raster_files.items():
    #             with rasterio.open(file) as src:
    #                 data = src.read(1).flatten()
    #                 if len(data) != expected_length:
    #                     print(f"Warning: {name} has length {len(data)} but expected {expected_length}")
    #                     # Truncate or pad to match expected length
    #                     data = data[:expected_length] if len(data) > expected_length else np.pad(
    #                         data, (0, expected_length - len(data)),
    #                         mode='constant', constant_values=src.nodata)
    #                 data_dict[name] = data
    #
    #         # Create DataFrame
    #         df = pd.DataFrame(coords)
    #         for name, data in data_dict.items():
    #             df[name] = data
    #
    #         # Clean data - remove rows where RSEI is 0 or nodata
    #         df = df[df['rsei'] != 0]
    #         df = df.replace([np.inf, -np.inf], np.nan).dropna()
    #
    #         # Convert LUCC to one-hot encoding
    #         df['lucc'] = df['lucc'].astype('category')
    #         lucc_dummies = pd.get_dummies(df['lucc'], prefix='lucc', drop_first=True)
    #         df = pd.concat([df.drop('lucc', axis=1), lucc_dummies], axis=1)
    #
    #         # Standardize continuous variables
    #         cont_vars = ['temperature', 'rainfall', 'fvc']
    #         scaler = StandardScaler()
    #         df[cont_vars] = scaler.fit_transform(df[cont_vars])
    #
    #         # Save CSV
    #         df.to_csv(self.csv_out, index=False)
    #         print(f"CSV file successfully created: {self.csv_out}")
    #         return True
    #
    #     except Exception as e:
    #         print(f"Error creating CSV: {str(e)}")
    #         return False

    def create_csv(self):
        """Create CSV file with all required variables for spatial regression"""
        try:
            # Dictionary of raster files and their corresponding column names
            raster_files = {
                'rsei': self.rsei_out,
                'lucc': self.lucc_out,
                'rainfall': self.rain_out,
                'temperature': self.temp_out,
                'fvc': self.fvc_out
            }

            # Define valid LUCC categories
            valid_lucc_categories = {
                10, 11, 20, 51, 52, 61, 62, 71, 72, 91,
                120, 121, 130, 150, 181, 182, 183, 190, 200, 210
            }

            # Initialize coordinate arrays
            coords = {'x': None, 'y': None}
            data_dict = {}

            # First pass: get coordinates from lucc file
            with rasterio.open(raster_files['lucc']) as src:
                height, width = src.shape
                rows, cols = np.indices((height, width))
                xs, ys = rasterio.transform.xy(src.transform, rows.flatten(), cols.flatten())
                coords['x'] = np.array(xs)
                coords['y'] = np.array(ys)
                expected_length = len(coords['x'])

            # Read all raster data
            for name, file in raster_files.items():
                with rasterio.open(file) as src:
                    data = src.read(1).flatten()
                    if len(data) != expected_length:
                        data = data[:expected_length] if len(data) > expected_length else np.pad(
                            data, (0, expected_length - len(data)),
                            mode='constant', constant_values=src.nodata)
                    data_dict[name] = data

            # Create DataFrame
            df = pd.DataFrame(coords)
            for name, data in data_dict.items():
                df[name] = data

            # Data cleaning
            df = df[df['rsei'] != 0].replace([np.inf, -np.inf], np.nan).dropna()
            df = df[df['lucc'].isin(valid_lucc_categories)]

            # Prepare variables for regression
            df['lucc_numeric'] = df['lucc']  # Keep original values for regression
            lucc_dummies = pd.get_dummies(df['lucc'].astype('category'), prefix='lucc')
            df = pd.concat([df.drop('lucc', axis=1), lucc_dummies], axis=1)

            # Standardize continuous variables
            cont_vars = ['temperature', 'rainfall', 'fvc']
            scaler = StandardScaler()
            df[cont_vars] = scaler.fit_transform(df[cont_vars])

            # Ensure all regression variables exist
            regression_vars = ['lucc_numeric', 'temperature', 'rainfall', 'fvc']
            for var in regression_vars:
                if var not in df.columns:
                    df[var] = 0.0  # Fill missing with default value

            df.to_csv(self.csv_out, index=False)
            print(f"CSV created with {len(df)} rows at: {self.csv_out}")
            return True

        except Exception as e:
            print(f"Error in create_csv: {str(e)}")
            return False
    # def create_csv(self):
    #     """Create CSV file with all required variables for spatial regression with dynamic validation"""
    #     try:
    #         # Dictionary of raster files and their corresponding column names
    #         raster_files = {
    #             'rsei': self.rsei_out,
    #             'lucc': self.lucc_out,
    #             'rainfall': self.rain_out,
    #             'temperature': self.temp_out,
    #             'fvc': self.fvc_out
    #         }
    #
    #         # 1. 动态验证栅格文件一致性
    #         print("\n=== 开始栅格数据验证 ===")
    #         base_shape = None
    #         for name, file in raster_files.items():
    #             with rasterio.open(file) as src:
    #                 if base_shape is None:
    #                     base_shape = src.shape
    #                     print(f"基准尺寸来自 {name}: {base_shape}")
    #                 elif src.shape != base_shape:
    #                     print(f"警告: {name} 尺寸不匹配 ({src.shape} vs {base_shape})")
    #
    #         # 2. 初始化坐标和数据存储
    #         coords = {'x': [], 'y': []}
    #         data_dict = {name: [] for name in raster_files.keys()}
    #         valid_pixel_count = 0
    #
    #         # 3. 逐像素处理（内存友好方式）
    #         with rasterio.open(raster_files['lucc']) as lucc_src:
    #             transform = lucc_src.transform
    #             height, width = lucc_src.shape
    #             total_pixels = height * width
    #             print(f"\n=== 开始处理 {total_pixels:,} 个像素 ===")
    #
    #             # 动态验证LUCC类别
    #             actual_lucc_values = set()
    #             unique_lucc_per_batch = set()
    #
    #             for row in range(height):
    #                 for col in range(width):
    #                     x, y = rasterio.transform.xy(transform, row, col)
    #                     coords['x'].append(x)
    #                     coords['y'].append(y)
    #
    #                     # 收集所有数据
    #                     for name, file in raster_files.items():
    #                         with rasterio.open(file) as src:
    #                             val = src.read(1)[row, col]
    #                             data_dict[name].append(val)
    #
    #                             # 动态记录LUCC值
    #                             if name == 'lucc':
    #                                 actual_lucc_values.add(val)
    #                                 unique_lucc_per_batch.add(val)
    #
    #                     valid_pixel_count += 1
    #
    #                 # 每1000行打印进度
    #                 if row % 1000 == 0:
    #                     print(f"处理进度: {row}/{height} 行 | 有效像素: {valid_pixel_count:,}")
    #                     if unique_lucc_per_batch:
    #                         print(f"当前批次发现的LUCC类别: {unique_lucc_per_batch}")
    #                     unique_lucc_per_batch = set()
    #
    #         # 4. 创建DataFrame
    #         print("\n=== 创建DataFrame ===")
    #         df = pd.DataFrame(coords)
    #         for name, data in data_dict.items():
    #             df[name] = data
    #
    #         # 5. 动态生成有效LUCC类别（基于实际数据）
    #         valid_lucc_categories = {
    #             10, 11, 20, 51, 52, 61, 62, 71, 72, 91,
    #             120, 121, 130, 150, 181, 182, 183, 190, 200, 210
    #         }
    #         actual_valid_lucc = actual_lucc_values & valid_lucc_categories
    #         invalid_lucc = actual_lucc_values - valid_lucc_categories
    #
    #         print(f"实际发现的LUCC类别总数: {len(actual_lucc_values)}")
    #         print(f"有效LUCC类别: {actual_valid_lucc}")
    #         print(f"无效LUCC类别: {invalid_lucc if invalid_lucc else '无'}")
    #
    #         # 6. 数据清洗（保留原始数据副本）
    #         raw_df = df.copy()
    #         print(f"\n原始数据行数: {len(raw_df):,}")
    #
    #         # 动态调整过滤条件
    #         rsei_zero_count = (df['rsei'] == 0).sum()
    #         print(f"RSEI=0的像素数量: {rsei_zero_count:,} ({rsei_zero_count / len(df):.1%})")
    #
    #         df = df.replace([np.inf, -np.inf], np.nan).dropna()
    #         df = df[(df['rsei'] != 0) | (df['rsei'].isna())]
    #         df = df[df['lucc'].isin(actual_valid_lucc) if actual_valid_lucc else df]
    #
    #         print(f"清洗后数据行数: {len(df):,}")
    #         print(f"数据保留率: {len(df) / len(raw_df):.1%}")
    #
    #         # 7. 准备回归变量
    #         print("\n=== 准备回归变量 ===")
    #         df['lucc_numeric'] = df['lucc']
    #
    #         # 动态生成虚拟变量（仅针对实际存在的类别）
    #         existing_lucc = [c for c in actual_valid_lucc if c in df['lucc'].unique()]
    #         if existing_lucc:
    #             lucc_dummies = pd.get_dummies(
    #                 df['lucc'].astype('category').cat.set_categories(existing_lucc),
    #                 prefix='lucc'
    #             )
    #             df = pd.concat([df.drop('lucc', axis=1), lucc_dummies], axis=1)
    #
    #         # 标准化连续变量
    #         cont_vars = ['temperature', 'rainfall', 'fvc']
    #         scaler = StandardScaler()
    #         df[cont_vars] = scaler.fit_transform(df[cont_vars])
    #
    #         # 8. 保存结果
    #         df.to_csv(self.csv_out, index=False)
    #         raw_df.to_csv(self.csv_out.replace('.csv', '_raw.csv'), index=False)
    #
    #         print(f"\n=== 处理完成 ===")
    #         print(f"最终CSV行数: {len(df):,}")
    #         print(f"文件已保存至: {self.csv_out}")
    #         return True
    #
    #     except Exception as e:
    #         print(f"\n!!! 处理失败 !!!")
    #         print(f"错误类型: {type(e).__name__}")
    #         print(f"错误详情: {str(e)}")
    #         print(f"追踪信息:\n{traceback.format_exc()}")
    #         return False

    # def create_csv(self):
    #     """Create CSV file from processed raster data with consistent column lengths"""
    #     try:
    #         # Dictionary of raster files and their corresponding column names
    #         raster_files = {
    #             'rsei': self.rsei_out,
    #             'lucc': self.lucc_out,
    #             'rainfall': self.rain_out,
    #             'temperature': self.temp_out,
    #             'fvc': self.fvc_out
    #             # 'dist': self.dist_out  # Add distance raster if available
    #         }
    #
    #         # Define valid LUCC categories
    #         valid_lucc_categories = {
    #             10, 11, 20, 51, 52, 61, 62, 71, 72, 91,
    #             120, 121, 130, 150, 181, 182, 183, 190, 200, 210
    #         }
    #
    #         # Initialize coordinate arrays
    #         coords = {'x': None, 'y': None}
    #         data_dict = {}
    #
    #         # First pass: get coordinates from one file and check all rasters
    #         with rasterio.open(raster_files['lucc']) as src:
    #             height, width = src.shape
    #             rows, cols = np.indices((height, width))
    #             xs, ys = rasterio.transform.xy(src.transform, rows.flatten(), cols.flatten())
    #             coords['x'] = np.array(xs)
    #             coords['y'] = np.array(ys)
    #             expected_length = len(coords['x'])
    #
    #         # Second pass: read all raster data and validate lengths
    #         for name, file in raster_files.items():
    #             with rasterio.open(file) as src:
    #                 data = src.read(1).flatten()
    #                 if len(data) != expected_length:
    #                     print(f"Warning: {name} has length {len(data)} but expected {expected_length}")
    #                     # Truncate or pad to match expected length
    #                     data = data[:expected_length] if len(data) > expected_length else np.pad(
    #                         data, (0, expected_length - len(data)),
    #                         mode='constant', constant_values=src.nodata)
    #                 data_dict[name] = data
    #
    #         # Create DataFrame
    #         df = pd.DataFrame(coords)
    #         for name, data in data_dict.items():
    #             df[name] = data
    #
    #         # Clean data - remove rows where RSEI is 0 or nodata
    #         df = df[df['rsei'] != 0]
    #         df = df.replace([np.inf, -np.inf], np.nan).dropna()
    #
    #         # Filter LUCC data to only include valid categories
    #         df = df[df['lucc'].isin(valid_lucc_categories)]
    #
    #         # Convert LUCC to one-hot encoding
    #         df['lucc'] = df['lucc'].astype('category')
    #         lucc_dummies = pd.get_dummies(df['lucc'], prefix='lucc')
    #         df = pd.concat([df.drop('lucc', axis=1), lucc_dummies], axis=1)
    #
    #         # Standardize continuous variables
    #         cont_vars = ['temperature', 'rainfall', 'fvc']
    #         scaler = StandardScaler()
    #         df[cont_vars] = scaler.fit_transform(df[cont_vars])
    #
    #         # Save CSV
    #         df.to_csv(self.csv_out, index=False)
    #         print(f"CSV file successfully created: {self.csv_out}")
    #         return True
    #
    #     except Exception as e:
    #         print(f"Error creating CSV: {str(e)}")
    #         return False

    def prepare_data(self, df):
        """Prepare data for spatial regression analysis"""
        try:
            # Identify LUCC columns
            lucc_columns = [col for col in df.columns if col.startswith('lucc_')]
            if not lucc_columns:
                raise ValueError("No LUCC columns found")

            # Create LUCC category
            df['lucc_category'] = df[lucc_columns].idxmax(axis=1)

            # Convert to numeric
            category_mapping = {cat: idx for idx, cat in enumerate(df['lucc_category'].unique())}
            df['lucc_numeric'] = df['lucc_category'].map(category_mapping)

            return df

        except Exception as e:
            print(f"Error preparing data: {str(e)}")
            raise

    # def create_spatial_weights(self, df):
    #     """Create spatial weights matrix"""
    #     try:
    #         coords = list(zip(df['x'], df['y']))
    #         w = weights.KNN.from_array(coords, k=8)
    #         w.transform = 'r'
    #         return w
    #
    #     except Exception as e:
    #         print(f"Error creating spatial weights: {str(e)}")
    #         raise
    def create_spatial_weights(self, df):
        """创建空间权重矩阵（明确只使用x,y坐标）"""
        try:
            # 显式只取x,y列
            coords = df[['x', 'y']].values
            w = weights.KNN.from_array(coords, k=8)
            w.transform = 'r'
            return w
        except Exception as e:
            print(f"空间权重创建失败，坐标数据样例: {df[['x', 'y']].head().to_dict()}")
            raise ValueError(f"无法创建空间权重: {str(e)}")

    # def run_regression_models(self, X, y, w):
    #     """Run spatial regression models"""
    #     try:
    #         name_y = 'rsei'
    #         name_x = ['lucc_numeric', 'temperature', 'rainfall', 'fvc']
    #
    #         models = {
    #             'OLS': spreg.OLS(y, X, name_y=name_y, name_x=name_x),
    #             'SLM': spreg.GM_Lag(y, X, w=w, name_y=name_y, name_x=name_x),
    #             'SEM': spreg.GM_Error(y, X, w=w, name_y=name_y, name_x=name_x)
    #         }
    #
    #         # Save model summaries
    #         for name, model in models.items():
    #             summary_file = os.path.join(self.work_dir, f"{name}_summary.txt")
    #             with open(summary_file, 'w') as f:
    #                 f.write(str(model.summary))
    #             print(f"Model summary saved: {summary_file}")
    #
    #         return models
    #
    #     except Exception as e:
    #         print(f"Error running regression models: {str(e)}")
    #         raise
    def run_regression_models(self, X, y, w, name_y='rsei', name_x=None):
        """运行空间回归模型并保存所有结果（包括SHP文件）"""
        try:
            # 参数处理
            name_x = name_x or ['lucc_numeric', 'temperature', 'rainfall', 'fvc']
            if len(name_x) != X.shape[1]:
                raise ValueError(f"自变量名称数量({len(name_x)})与X列数({X.shape[1]})不匹配")

            # 运行模型
            models = {
                'OLS': spreg.OLS(y, X, name_y=name_y, name_x=name_x),
                'SLM': spreg.GM_Lag(y, X, w=w, name_y=name_y, name_x=name_x),
                'SEM': spreg.GM_Error(y, X, w=w, name_y=name_y, name_x=name_x)
            }

            # 保存所有结果
            for model_name, model in models.items():
                # 1. 保存文本摘要
                summary_path = os.path.join(self.work_dir, f"{model_name}_summary.txt")
                with open(summary_path, 'w') as f:
                    f.write(str(model.summary))

                # 2. 生成并保存SHP文件
                self._save_model_results_to_shp(model_name, model, X, y, name_x)

            return models

        except Exception as e:
            print(f"回归模型运行失败: {str(e)}")
            raise

    def _save_model_results_to_shp(self, model_name, model, X, y, name_x):
        """适配pysal的模型结果保存方法"""
        try:
            # 获取系数（适配pysal和statsmodels的不同API）
            if hasattr(model, 'params'):  # statsmodels风格
                params = model.params
            elif hasattr(model, 'betas'):  # pysal风格
                params = model.betas.flatten()
            else:
                raise AttributeError("无法识别模型系数属性")

            # 准备空间数据
            gdf = gpd.GeoDataFrame(
                {
                    'observed': y.flatten(),
                    'predicted': model.predy.flatten(),
                    'residual': model.u.flatten(),
                    **{
                        f'coef_{name}': [params[i + 1]] * len(y)
                        for i, name in enumerate(name_x)
                    }
                },
                geometry=gpd.points_from_xy(self.df['x'], self.df['y']),
                crs="EPSG:4326"
            )

            # 保存SHP
            shp_path = os.path.join(self.work_dir, f"{model_name}_results.shp")
            gdf.to_file(shp_path)
            print(f"{model_name}结果已保存至: {shp_path}")

        except Exception as e:
            print(f"保存{model_name}结果到SHP失败: {str(e)}")
            raise
    # def run_regression_models(self, X, y, w, name_y='rsei', name_x=None):
    #     """Run spatial regression models with customizable variable names
    #
    #     Args:
    #         X: 自变量数据矩阵
    #         y: 因变量数据向量
    #         w: 空间权重矩阵
    #         name_y: 因变量名称 (默认为'rsei')
    #         name_x: 自变量名称列表 (默认为None，将使用['lucc_numeric', 'temperature', 'rainfall', 'fvc'])
    #
    #     Returns:
    #         dict: 包含三种模型(OLS, SLM, SEM)的字典
    #     """
    #     try:
    #         # 设置默认的自变量名称
    #         if name_x is None:
    #             name_x = ['lucc_numeric', 'temperature', 'rainfall', 'fvc']
    #
    #         # 确保自变量名称数量与X的列数匹配
    #         if len(name_x) != X.shape[1]:
    #             raise ValueError(f"Number of independent variable names ({len(name_x)}) "
    #                              f"does not match number of columns in X ({X.shape[1]})")
    #
    #         models = {
    #             'OLS': spreg.OLS(y, X, name_y=name_y, name_x=name_x),
    #             'SLM': spreg.GM_Lag(y, X, w=w, name_y=name_y, name_x=name_x),
    #             'SEM': spreg.GM_Error(y, X, w=w, name_y=name_y, name_x=name_x)
    #         }
    #
    #         # Save model summaries
    #         for name, model in models.items():
    #             summary_file = os.path.join(self.work_dir, f"{name}_summary.txt")
    #             with open(summary_file, 'w') as f:
    #                 f.write(str(model.summary))
    #             print(f"Model summary saved: {summary_file}")
    #
    #         return models
    #
    #     except Exception as e:
    #         print(f"Error running regression models: {str(e)}")
    #         raise

    def save_results(self, df, models):
        """Save regression results to shapefiles"""
        try:
            # Create results DataFrame
            results_df = df.copy()
            n = len(results_df)

            # Add model results
            for name, model in models.items():
                # Predicted values
                predy = model.predy.flatten() if hasattr(model.predy, 'flatten') else model.predy
                results_df[f'{name}_predicted'] = np.resize(predy, n)

                # Residuals
                residuals = model.u.flatten() if hasattr(model.u, 'flatten') else model.u
                results_df[f'{name}_residuals'] = np.resize(residuals, n)

                # Standardized residuals
                resid_std = np.nanstd(residuals)
                results_df[f'{name}_std_resid'] = residuals / resid_std if resid_std != 0 else np.nan

            # Create geometry
            geometry = [Point(xy) for xy in zip(results_df['x'], results_df['y'])]

            # Save each model's results
            for name in models.keys():
                required_cols = ['x', 'y', 'rsei',
                                 f'{name}_predicted',
                                 f'{name}_residuals',
                                 f'{name}_std_resid']

                gdf = gpd.GeoDataFrame(results_df[required_cols], geometry=geometry)
                output_file = os.path.join(self.work_dir, f"{name.lower()}_results.shp")
                gdf.to_file(output_file, driver='ESRI Shapefile', encoding='utf-8')
                print(f"Results saved: {output_file}")

            return True

        except Exception as e:
            print(f"Error saving results: {str(e)}")
            return False

    def select_best_model(self, ols, slm, sem):
        """Select the best model based on statistical criteria"""
        try:
            # Collect model statistics
            models_stats = {
                'OLS': {'name': 'OLS', 'r2': ols.r2},
                'SLM': {'name': 'SLM', 'r2': slm.pr2 if hasattr(slm, 'pr2') else slm.r2},
                'SEM': {'name': 'SEM', 'r2': sem.pr2 if hasattr(sem, 'pr2') else sem.r2}
            }

            # Select model with highest R2
            best_name = max(models_stats.items(), key=lambda x: x[1]['r2'])[0]
            best_model = {'OLS': ols, 'SLM': slm, 'SEM': sem}[best_name]

            # Save selection
            selection_file = os.path.join(self.work_dir, "best_model_selection.txt")
            with open(selection_file, 'w') as f:
                f.write(f"Best model: {best_name}\n")
                f.write(f"R2: {models_stats[best_name]['r2']:.4f}\n")

            print(f"Best model selected: {best_name}")
            return best_model, models_stats[best_name]

        except Exception as e:
            print(f"Error selecting best model: {str(e)}")
            raise

    def run_full_analysis(self):
        """Run the complete analysis pipeline"""
        try:
            print(f"Starting analysis for {self.region} {self.year}")

            # 1. Process raster data
            print("Processing raster data...")
            if not self.process_all_rasters():
                raise Exception("Raster processing failed")

            # 2. Create CSV
            print("Creating CSV file...")
            if not self.create_csv():
                raise Exception("CSV creation failed")

        #     # 3. Load data
        #     print("Loading data...")
        #     df = pd.read_csv(self.csv_out)
        #
        #     # 4. Prepare data
        #     print("Preparing data...")
        #     df = self.prepare_data(df)
        #
        #     # 5. Create spatial weights
        #     print("Creating spatial weights...")
        #     w = self.create_spatial_weights(df)
        #
        #     # 6. Prepare variables
        #     y = df['rsei'].values.reshape(-1, 1)
        #     X = df[['lucc_numeric', 'temperature', 'rainfall', 'fvc']].values
        #
        #     # 7. Run models
        #     print("Running regression models...")
        #     models = self.run_regression_models(X, y, w)
        #
        #     # 8. Save results
        #     print("Saving results...")
        #     self.save_results(df, models)
        #
        #     # 9. Select best model
        #     print("Selecting best model...")
        #     best_model, best_stats = self.select_best_model(
        #         models['OLS'], models['SLM'], models['SEM'])
        #
        #     print(f"Analysis completed successfully for {self.region} {self.year}")
        #     return True
        #
        except Exception as e:
            print(f"Analysis failed: {str(e)}")
            return False


def test_service():
    """Test the SRService class"""
    try:
        print("=== Testing SRService ===")

        # Initialize with test parameters
        service = SRService(year=2010, region="NC")

        # Run full analysis
        success = service.run_full_analysis()

        if success:
            print("Test completed successfully!")
            return True
        else:
            print("Test completed with errors")
            return False

    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run test
    test_result = test_service()

    if test_result:
        print("\nAll tests passed successfully!")
    else:
        print("\nTests completed with errors")