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
    base_dir = "D:/Google/GWR"
    city_shapes = {
        "NC": "D:/Google/city/NC.shp",
        "JJ": "D:/Google/city/JJ.shp",
        "YT": "D:/Google/city/YT.shp",
        "JDZ": "D:/Google/city/JDZ.shp",
        "FZ": "D:/Google/city/FZ.shp",
        "SR": "D:/Google/city/SR.shp"
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
        self.rsei_dir = f"D:/Google/RSEI_full/RSEI_{self.year}.tif"
        self.temp_dir = f"D:/Google/temperture/tpt/tpt_{self.year}.tif"
        self.rain_dir = f"D:/Google/rainfall/RF/{self.year}.tif"
        self.lucc_dir = f"D:/Google/GLC_FCS30/merged/poyang_{self.year}.tif"
        self.fvc_dir = f"D:/Google/FVC/FVC_{self.year}.tif"

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

    def create_csv(self):
        """Create CSV file with dynamic validation and detailed logging"""
        try:
            # 初始化
            raster_files = {
                'rsei': self.rsei_out,
                'lucc': self.lucc_out,
                'rainfall': self.rain_out,
                'temperature': self.temp_out,
                'fvc': self.fvc_out
            }

            # 1. 动态获取实际LUCC类别
            with rasterio.open(raster_files['lucc']) as src:
                lucc_data = src.read(1)
                unique_lucc = set(np.unique(lucc_data))
                actual_valid_lucc = unique_lucc & {
                    10, 11, 20, 51, 52, 61, 62, 71, 72, 91,
                    120, 121, 130, 150, 181, 182, 183, 190, 200, 210
                }
                print(f"实际存在的LUCC类别: {sorted(unique_lucc)}")
                print(f"有效LUCC类别: {sorted(actual_valid_lucc)}")

            # 2. 读取数据
            coords = {'x': [], 'y': []}
            data_dict = {name: [] for name in raster_files.keys()}

            with rasterio.open(raster_files['lucc']) as src:
                transform = src.transform
                for row in range(src.height):
                    for col in range(src.width):
                        x, y = rasterio.transform.xy(transform, row, col)
                        coords['x'].append(x)
                        coords['y'].append(y)
                        for name, file in raster_files.items():
                            with rasterio.open(file) as data_src:
                                data_dict[name].append(data_src.read(1)[row, col])

            # 3. 创建DataFrame并记录原始行数
            df = pd.DataFrame(coords)
            for name, data in data_dict.items():
                df[name] = data
            original_count = len(df)
            print(f"原始数据行数: {original_count:,}")

            # 4. 分步过滤（带诊断信息）
            # 4.1 过滤RSEI=0
            rsei_zero_mask = (df['rsei'] == 0)
            print(f"\nRSEI=0的像素数量: {rsei_zero_mask.sum():,} ({rsei_zero_mask.mean():.1%})")
            df = df[~rsei_zero_mask]
            print(f"过滤RSEI=0后行数: {len(df):,} (损失率: {(original_count - len(df)) / original_count:.1%})")

            # 4.2 过滤无效LUCC
            invalid_lucc_mask = ~df['lucc'].isin(actual_valid_lucc)
            print(f"无效LUCC像素数量: {invalid_lucc_mask.sum():,} ({invalid_lucc_mask.mean():.1%})")
            df = df[~invalid_lucc_mask]
            print(f"过滤无效LUCC后行数: {len(df):,} (总保留率: {len(df) / original_count:.1%})")

            # 5. 后续处理（保持不变）
            df['lucc_numeric'] = df['lucc']
            lucc_dummies = pd.get_dummies(df['lucc'].astype('category'), prefix='lucc')
            df = pd.concat([df.drop('lucc', axis=1), lucc_dummies], axis=1)

            cont_vars = ['temperature', 'rainfall', 'fvc']
            scaler = StandardScaler()
            df[cont_vars] = scaler.fit_transform(df[cont_vars])

            df.to_csv(self.csv_out, index=False)
            print(f"最终CSV行数: {len(df):,} (路径: {self.csv_out})")
            return True

        except Exception as e:
            print(f"CSV生成失败: {str(e)}\n{traceback.format_exc()}")
            return False

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
        """保存模型结果到SHP文件（包含标准化残差）"""
        try:
            # 获取系数（适配不同API）
            if hasattr(model, 'params'):  # statsmodels风格
                params = model.params
            elif hasattr(model, 'betas'):  # pysal风格
                params = model.betas.flatten()
            else:
                raise AttributeError("无法识别模型系数属性")

            # 计算标准化残差（残差/残差标准差）
            residuals = model.u.flatten()
            std_residuals = residuals / np.std(residuals) if len(residuals) > 1 else np.zeros_like(residuals)

            # 准备空间数据
            gdf = gpd.GeoDataFrame(
                {
                    'observed': y.flatten(),  # 实际观测值
                    'predicted': model.predy.flatten(),  # 模型预测值
                    'residual': residuals,  # 原始残差（观测值-预测值）
                    'std_resid': std_residuals,  # 标准化残差（本次新增）
                    **{
                        f'coef_{name}': [params[i + 1]] * len(y)  # 各变量的系数
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

            # 3. Load data
            print("Loading data...")
            df = pd.read_csv(self.csv_out)

            # 4. Prepare data
            print("Preparing data...")
            df = self.prepare_data(df)

            # 5. Create spatial weights
            print("Creating spatial weights...")
            w = self.create_spatial_weights(df)

            # 6. Prepare variables
            y = df['rsei'].values.reshape(-1, 1)
            X = df[['lucc_numeric', 'temperature', 'rainfall', 'fvc']].values

            # 7. Run models
            print("Running regression models...")
            models = self.run_regression_models(X, y, w)

            # 8. Save results
            print("Saving results...")
            self.save_results(df, models)

            # 9. Select best model
            print("Selecting best model...")
            best_model, best_stats = self.select_best_model(
                models['OLS'], models['SLM'], models['SEM'])

            print(f"Analysis completed successfully for {self.region} {self.year}")
            return True

        except Exception as e:
            print(f"Analysis failed: {str(e)}")
            return False





service = SRService(year=2010, region="NC")  # 以南昌(NC)2010年为例
if service.process_all_rasters():
    print("栅格数据处理成功")
else:
    print("栅格数据处理失败")
if service.create_csv():
    print(f"CSV生成成功，路径: {service.csv_out}")
    # 读取前5行示例
    df = pd.read_csv(service.csv_out)
    print("\nCSV前5行示例:")
    print(df.head())
else:
    print("CSV生成失败")
