import rasterio

with rasterio.open("D:/Google/GWR/2000_resampled.tif") as src:
    print("数据类型:", src.dtypes)  # 检查波段数据类型
    print("统计信息:", src.statistics(1))  # 直接读取统计信息



# import numpy as np
# import pandas as pd
# import rasterio
# from sklearn.ensemble import RandomForestRegressor
# from libpysal.weights import DistanceBand
# from scipy.spatial import cKDTree
# import joblib
#
# LUCC_CLASSES = {
#     10: "雨养耕地", 11: "草本植被覆盖", 20: "灌溉耕地",
#     51: "开阔常绿阔叶林", 52: "闭阔常绿阔叶林",
#     61: "开阔落叶阔叶林(0.15 < fc <0.4)", 62: "闭阔落叶阔叶林(fc > 0.4)",
#     71: "开阔常绿针叶林(0.15 < fc < 0.4)", 72: "闭阔常绿针叶林(fc > 0.4)",
#     91: "开阔混交叶片林(阔叶树和针叶树)",
#     120: "灌木林", 121: "常绿灌木林", 130: "草地",
#     150: "稀疏植被(fc < 0.15)", 181: "沼泽", 182: "沼泽地", 183: "水淹平地",
#     190: "不透水表面", 200: "裸地", 210: "水体"
# }
# # 读取重采样后的TIFF数据
# def load_tiff_data(temp_path, rf_path, rsei_path, lucc_path):
#     with rasterio.open(temp_path) as temp:
#         temperature = temp.read(1)
#         transform = temp.transform
#     with rasterio.open(rf_path) as rf:
#         rainfall = rf.read(1)
#     with rasterio.open(rsei_path) as rsei:
#         rsei_data = rsei.read(1)
#     with rasterio.open(lucc_path) as lucc:
#         lucc_data = lucc.read(1)
#
#     # 转换为表格
#     rows, cols = temperature.shape
#     x, y = np.meshgrid(np.arange(cols), np.arange(rows))
#     coords = np.vstack([x.ravel(), y.ravel()]).T
#     data = pd.DataFrame({
#         'x': coords[:, 0], 'y': coords[:, 1],
#         'temperature': temperature.ravel(),
#         'rainfall': rainfall.ravel(),
#         'rsei': rsei_data.ravel(),
#         'lucc': lucc_data.ravel()
#     })
#     data = data.dropna()
#
#     # 处理LUCC（转换为植被覆盖度）
#     lucc_dict = {10: 0.4, 20: 0.8, 30: 0.6, 40: 0.1}  # 农田、森林、草地、城市
#     data['lucc_veg'] = data['lucc'].map(lucc_dict).fillna(0)
#     return data, transform, rows, cols
#
#
# # def load_tiff_data(temp_path, rf_path, rsei_path, lucc_path, return_names=False):
# #     # 读取数据（显式处理nodata）
# #     with rasterio.open(temp_path) as src:
# #         temperature = src.read(1)
# #         transform, crs = src.transform, src.crs
# #         temp_nodata = src.nodata or -9999  # 兼容未定义nodata的情况
# #
# #     # 其他数据读取（略，同原代码）
# #
# #     # 构建DataFrame并清理
# #     data = pd.DataFrame({
# #         'x': coords[:, 0], 'y': coords[:, 1],
# #         'temperature': temperature.ravel(),
# #         'rainfall': rainfall.ravel(),
# #         'rsei': rsei_data.ravel(),
# #         'lucc': lucc_data.ravel()
# #     })
# #     data = data[
# #         ~data[['temperature', 'rainfall', 'rsei', 'lucc']].isin([temp_nodata, rf_nodata, rsei_nodata, 0]).any(axis=1)]
# #
# #     # 简化版植被覆盖度映射（核心类别）
# #     VEG_COVER_SIMPLE = {
# #         **{k: 0.9 for k in [52, 62, 72]},  # 密闭森林
# #         **{k: 0.7 for k in [51, 61, 71, 91]},  # 开阔森林
# #         **{k: 0.5 for k in [10, 11, 20, 121]},  # 耕地/灌木
# #         **{k: 0.3 for k in [120, 130]},  # 草地/稀疏植被
# #         **{k: 0.1 for k in [190, 200]},  # 城市/裸地
# #         210: 0.0  # 水体
# #     }
# #     data['veg_cover'] = data['lucc'].map(VEG_COVER_SIMPLE).fillna(0.3)  # 默认设为中性值
# #
# #     if return_names:
# #         data['lucc_name'] = data['lucc'].map(LUCC_CLASSES)
# #
# #     return data, transform, crs  # 仅返回必要参数
#
# data, transform, rows, cols = load_tiff_data(
#     "D:/Google/GWR/tpt_2000_resampled.tif",
#     "D:/Google/GWR/2000_resampled.tif",
#     "D:/Google/GWR/RSEI_2000_resampled.tif",
#     "D:/Google/GWR/poyang_2000_resampled.tif"
# )
#
# # 构建空间权重矩阵（单位：度）
# coords = data[['x', 'y']].values
# bandwidth = 0.045  # 约500m
# tree = cKDTree(coords)
# weights = [tree.query_ball_point(coord, bandwidth) for coord in coords]
#
#
# # GWRF函数
# def local_rf(i):
#     local_indices = weights[i]
#     if len(local_indices) > 30:
#         local_data = data.iloc[local_indices]
#         X = local_data[['temperature', 'rainfall', 'lucc_veg']]
#         y = local_data['rsei']
#         rf = RandomForestRegressor(n_estimators=100, random_state=42)
#         rf.fit(X, y)
#         return rf.feature_importances_
#     else:
#         return np.array([np.nan, np.nan, np.nan])
#
#
# # 并行计算
# results = joblib.Parallel(n_jobs=-1)(
#     joblib.delayed(local_rf)(i) for i in range(len(data))
# )
#
# # 保存结果为TIFF
# importance = np.array(results).reshape(-1, 3)
# output = np.full((rows * cols, 3), np.nan)
# output[:len(importance)] = importance
# output = output.reshape(rows, cols, 3)
#
# with rasterio.open(
#         "D:/Google/GWR/gwrf_importance_2000.tif", 'w',
#         driver='GTiff', height=rows, width=cols, count=3,
#         dtype=output.dtype, crs='EPSG:4326', transform=transform
# ) as dst:
#     dst.write(output)


import numpy as np
import pandas as pd
import rasterio
from sklearn.ensemble import RandomForestRegressor
from scipy.spatial import cKDTree
import joblib
import time

def load_tiff_data(temp_path, rf_path, rsei_path, lucc_path, max_pixels=10000):
    """读取TIFF数据并统一处理无效值，限制最大像素数"""
    def read_and_filter(path, invalid_values):
        with rasterio.open(path) as src:
            data = src.read(1)
            transform = src.transform
            mask = np.ones_like(data, dtype=bool)
            for val in invalid_values:
                if np.isnan(val):
                    mask &= ~np.isnan(data)
                else:
                    mask &= (data != val)
            return data, mask, transform

    # 定义各文件的无效值
    temp_data, temp_mask, transform = read_and_filter(
        temp_path, [-3.4028234663852886e+38]
    )
    rf_data, rf_mask, _ = read_and_filter(rf_path, [np.nan, -9999.0])  # 添加-9999
    rsei_data, rsei_mask, _ = read_and_filter(rsei_path, [-9999.0])
    lucc_data, lucc_mask, _ = read_and_filter(lucc_path, [0])

    # 合并所有掩膜
    global_mask = temp_mask & rf_mask & rsei_mask & lucc_mask
    rows, cols = global_mask.shape

    # 提取有效像素的坐标和值
    y_coords, x_coords = np.where(global_mask)
    valid_pixels = len(y_coords)
    print(f"Total valid pixels: {valid_pixels}")

    # 限制到max_pixels
    if valid_pixels > max_pixels:
        indices = np.random.choice(valid_pixels, max_pixels, replace=False)
        y_coords = y_coords[indices]
        x_coords = x_coords[indices]
    else:
        max_pixels = valid_pixels

    # 转换为地理坐标
    coords_geo = [rasterio.transform.xy(transform, y, x) for y, x in zip(y_coords, x_coords)]
    coords_geo = np.array(coords_geo)  # [lon, lat]

    data = pd.DataFrame({
        'x': x_coords,
        'y': y_coords,
        'lon': coords_geo[:, 0],
        'lat': coords_geo[:, 1],
        'temperature': temp_data[y_coords, x_coords],
        'rainfall': rf_data[y_coords, x_coords],
        'rsei': rsei_data[y_coords, x_coords],
        'lucc': lucc_data[y_coords, x_coords]
    })

    # 处理LUCC
    lucc_dict = {
        10: 0.4, 11: 0.5, 20: 0.4, 51: 0.7, 52: 0.9, 61: 0.6, 62: 0.8,
        71: 0.6, 72: 0.8, 91: 0.7, 120: 0.6, 121: 0.65, 130: 0.5,
        150: 0.3, 181: 0.5, 182: 0.5, 183: 0.4, 190: 0.1, 200: 0.05, 210: 0.0
    }
    data['lucc_veg'] = data['lucc'].map(lucc_dict).fillna(0.0)
    return data, transform, rows, cols, max_pixels

# 加载数据（测试10,000像素）
start_time = time.time()
data, transform, rows, cols, max_pixels = load_tiff_data(
    "D:/Google/GWR/tpt_2000_resampled.tif",
    "D:/Google/GWR/2000_resampled.tif",
    "D:/Google/GWR/RSEI_2000_resampled.tif",
    "D:/Google/GWR/poyang_2000_resampled.tif",
    max_pixels=10000
)
load_time = time.time() - start_time
print(f"Data loading time: {load_time:.2f} seconds")

# 构建空间权重矩阵（使用地理坐标）
coords = data[['lon', 'lat']].values
bandwidth = 0.045  # 约500m
tree = cKDTree(coords)
start_time = time.time()
weights = [tree.query_ball_point(coord, bandwidth) for coord in coords]
weights_time = time.time() - start_time
print(f"Weights computation time: {weights_time:.2f} seconds")

def local_rf(i):
    """局部随机森林"""
    local_indices = weights[i]
    if len(local_indices) >= 30:
        local_data = data.iloc[local_indices]
        X = local_data[['temperature', 'rainfall', 'lucc_veg']]
        y = local_data['rsei']
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        return rf.feature_importances_
    else:
        return np.array([np.nan, np.nan, np.nan])

# 并行计算（测试10,000像素）
start_time = time.time()
results = joblib.Parallel(n_jobs=-1)(
    joblib.delayed(local_rf)(i) for i in range(len(data))
)
gwr_time = time.time() - start_time
print(f"GWRF computation time for {max_pixels} pixels: {gwr_time:.2f} seconds")
print(f"Average time per pixel: {gwr_time / max_pixels:.6f} seconds")

# 保存结果
importance = np.array(results)
output = np.full((rows, cols, 3), np.nan, dtype=np.float32)
output[data['y'].values, data['x'].values] = importance

with rasterio.open(
    "D:/Google/GWR/yiwan_dataTest.tif", 'w',
    driver='GTiff', height=rows, width=cols, count=3,
    dtype=np.float32, crs='EPSG:4326', transform=transform
) as dst:
    dst.write(output.transpose(2, 0, 1))