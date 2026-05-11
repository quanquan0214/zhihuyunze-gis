import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling
from shapely.geometry import Point
from sklearn.preprocessing import StandardScaler
from pysal.lib import weights
from pysal.model import spreg

class FlexibleRasterProcessor:
    def __init__(self, year, region_shp, variables, config):
        self.year = year
        self.config = config

        # Map variable names to file paths
        variable_mapping = {
            "temp": f"D:/Google/temperture/tpt/tpt_{year}.tif",
            "rain": f"D:/Google/rainfall/RF/{year}.tif",
            "lucc": f"D:/Google/GLC_FCS30/merged/poyang_{year}.tif",
            "fvc": f"D:/Google/FVC/FVC_{year}.tif"
        }

        # Set region_shp based on predefined rules
        if region_shp in ["NC", "JJ", "JDZ", "SR", "FZ", "TY"]:
            self.region_shp = f"D:/Google/city/{region_shp}.shp"
        else:
            self.region_shp = region_shp

        # Convert list of variables to a dictionary with file paths
        self.variables = {var: variable_mapping[var] for var in variables if var in variable_mapping}

        self.temp_dir = config.get("temp_dir", "D:/Google/GWR")
        self.target_res = config.get("target_res", (0.00449, 0.00449))
        self.target_bounds = config.get("target_bounds", (113.9, 26.5, 118.5, 30.1))
        self.target_shape = config.get("target_shape", (796, 1010))
        self.safe_nodata = config.get("safe_nodata", 0)

        # Ensure resampling_method is a valid Resampling enum
        resampling_method = config.get("resampling_method", Resampling.bilinear)
        if isinstance(resampling_method, str):
            resampling_method = getattr(Resampling, resampling_method, Resampling.bilinear)
        self.resampling_method = resampling_method

        self.standardize = config.get("standardize", True)
        self.output_dir = os.path.join(self.temp_dir, time.strftime("%Y-%m-%d"))
        os.makedirs(self.output_dir, exist_ok=True)


    def process_variable(self, var_name, input_path):  # 处理单个变量,进行重采样和对齐
        input = os.path.join("D:/Google/GWR/temp/", f"{var_name}")#_{self.year}.tif")
        output = input_path
        # print("输入的",input)
        # print("输出的",output)
        with rasterio.open(input) as src:
            data = src.read(1)
            transform = src.transform
            dst_transform = rasterio.transform.from_bounds(*self.target_bounds, self.target_shape[1], self.target_shape[0])
            dst_data = np.full(self.target_shape, self.safe_nodata, dtype=data.dtype)
            print("数据：",data.shape, "变换：", transform, "目标变换：", dst_transform, "目标形状：", self.target_shape, "无效值：", self.safe_nodata, "重采样方法：", self.resampling_method)
            reproject(data, dst_data,
                      src_transform=transform, src_crs=src.crs,
                      dst_transform=dst_transform, dst_crs=src.crs,
                      resampling = self.resampling_method)

            profile = src.profile.copy()
            profile.update({"height": self.target_shape[0], "width": self.target_shape[1],
                            "transform": dst_transform, "nodata": self.safe_nodata})

        with rasterio.open(output, 'w', **profile) as dst:
            dst.write(dst_data, 1)

        return output

    def crop_to_region(self, tif_path): # 裁剪到指定区域
        output_path = tif_path.replace(".tif", "_crop.tif")
        print(self.region_shp, tif_path, output_path)
        region = gpd.read_file(self.region_shp) if isinstance(self.region_shp, str) else self.region_shp
        with rasterio.open(tif_path) as src:
            out_image, out_transform = mask(src, region.geometry, crop=True, all_touched=True)
            out_meta = src.meta.copy()
            out_meta.update({"height": out_image.shape[1], "width": out_image.shape[2],
                             "transform": out_transform})
            with rasterio.open(output_path, 'w', **out_meta) as dst:
                dst.write(out_image, 1)
        return output_path

    def generate_csv(self, var_paths: dict, output_csv):
        df = pd.DataFrame()
        base_path = list(var_paths.values())[0]
        with rasterio.open(base_path) as src:
            rows, cols = np.indices(src.shape)
            xs, ys = rasterio.transform.xy(src.transform, rows.flatten(), cols.flatten())
            df["x"], df["y"] = xs, ys
        for var, path in var_paths.items():
            with rasterio.open(path) as src:
                data = src.read(1).flatten()
                df[var] = data

        df = df[~df.isna().any(axis=1)]
        if "lucc" in df:
            df['lucc'] = df['lucc'].astype('category')
            lucc_dummies = pd.get_dummies(df['lucc'], prefix='lucc', drop_first=True)
            df = pd.concat([df.drop('lucc', axis=1), lucc_dummies], axis=1)

        if self.standardize:
            cont_vars = [v for v in ["temperature", "rainfall", "fvc"] if v in df.columns]
            df[cont_vars] = StandardScaler().fit_transform(df[cont_vars])

        df.to_csv(output_csv, index=False)
        return output_csv

    def run(self):
        tif_paths = {}
        for var, path in self.variables.items():
            output_path= os.path.join(self.output_dir, f"{var}_{self.year}.tif")
            tif = self.process_variable(path,output_path)
            tif_crop = self.crop_to_region(tif)
            # tif_paths[var] = tif_crop

        csv_path = os.path.join(self.output_dir, f"data_{self.year}.csv")
        self.generate_csv(tif_paths, csv_path)
        return csv_path


class FlexibleSRAnalysis:
    def __init__(self, config):
        self.temp_dir = config.get("temp_dir", "D:/Google/GWR")
        self.index_dir = os.path.join(self.temp_dir, f"sr_{time.strftime('%Y-%m-%d')}")
        os.makedirs(self.index_dir, exist_ok=True)
        self.config = config

    def prepare_data(self, df):
        if any(col.startswith("lucc_") for col in df.columns):
            df['lucc_category'] = df[[c for c in df.columns if c.startswith('lucc_')]].idxmax(axis=1)
            df['lucc_numeric'] = df['lucc_category'].astype('category').cat.codes
        return df

    def check_input(self, df, x_vars, y_var):
        X = df[x_vars].astype(float).values
        y = df[[y_var]].astype(float).values
        return X, y

    def create_weights(self, df):
        coords = list(zip(df['x'], df['y']))
        w = weights.KNN.from_array(coords, k=self.config.get("k_neighbors", 8))
        w.transform = 'r'
        return w

    def run_models(self, X, y, x_names, y_name):
        models = {
            "OLS": spreg.OLS(y, X, name_y=y_name, name_x=x_names),
            "SLM": spreg.GM_Lag(y, X, w=self.create_weights(pd.DataFrame(X)), name_y=y_name, name_x=x_names),
            "SEM": spreg.GM_Error(y, X, w=self.create_weights(pd.DataFrame(X)), name_y=y_name, name_x=x_names)
        }
        return models

    def save_results(self, df, models):
        geometry = [Point(xy) for xy in zip(df['x'], df['y'])]
        for name, model in models.items():
            result_df = df.copy()
            result_df[f'{name}_pred'] = np.resize(model.predy, len(df))
            result_df[f'{name}_resid'] = np.resize(model.u, len(df))
            result_df[f'{name}_std_resid'] = result_df[f'{name}_resid'] / np.nanstd(result_df[f'{name}_resid'])
            gdf = gpd.GeoDataFrame(result_df, geometry=geometry)
            gdf.to_file(os.path.join(self.index_dir, f"{name.lower()}_results.shp"))

    def select_best_model(self, models, df):
        """根据显著变量数、R²等选择最佳模型"""
        def get_significant_vars(model):
            if hasattr(model, 'z_stat'):
                return sum(p < 0.05 for _, p in model.z_stat)
            elif hasattr(model, 't_stat'):
                return sum(p < 0.05 for _, p in model.t_stat)
            return 0

        stats = {}
        for name, model in models.items():
            r2 = getattr(model, 'r2', getattr(model, 'pr2', 0))
            sig_vars = get_significant_vars(model)
            coef = model.betas[-1][0] if hasattr(model, 'betas') else None
            stats[name] = {
                'r2': r2,
                'sig_vars': sig_vars,
                'coef': coef,
                'model': model
            }

        # 评分系统
        max_r2 = max(s['r2'] for s in stats.values())
        max_sig = max(s['sig_vars'] for s in stats.values())
        scores = {
            name: int(abs(s['r2'] - max_r2) < 0.01) * 2 + int(s['sig_vars'] == max_sig) * 2 + (
                1 if s['coef'] is not None else 0)
            for name, s in stats.items()
        }

        best_model = max(scores.items(), key=lambda x: x[1])[0]
        best_info = stats[best_model]

        return best_model, best_info, stats

    def run(self, input_csv, auto_select_best_model=True):
        df = pd.read_csv(input_csv)
        df = self.prepare_data(df)
        y_var = self.config.get("dependent_variable", "RSEI")
        x_vars = self.config.get("independent_variables", ["lucc_numeric", "temperature", "rainfall", "fvc"])
        X, y = self.check_input(df, x_vars, y_var)
        w = self.create_weights(df)
        models = self.run_models(X, y, x_vars, y_var)
        self.save_results(df, models)

        if auto_select_best_model:
            best_name, best_info, stats_all = self.select_best_model(models, df)
            return {
                "best_model": best_name,
                "r2": best_info['r2'],
                "sig_vars": best_info['sig_vars'],
                "coef": best_info['coef'],
                "models": list(models.keys()),
                "all_stats": stats_all
            }
        else:
            return {"models": list(models.keys())}

