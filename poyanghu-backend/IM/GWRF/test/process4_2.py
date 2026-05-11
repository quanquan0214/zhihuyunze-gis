import numpy as np
import pandas as pd
import rasterio
from sklearn.ensemble import RandomForestRegressor
from scipy.spatial import cKDTree
import joblib

def load_tiff_data(temp_path, rf_path, rsei_path, lucc_path):
    """读取TIFF数据并统一处理无效值"""
    def read_and_filter(path, invalid_values):
        with rasterio.open(path) as src:
            data = src.read(1)
            mask = np.ones_like(data, dtype=bool)
            for val in invalid_values:
                if np.isnan(val):
                    mask &= ~np.isnan(data)
                else:
                    mask &= (data != val)
            return data, mask, src.transform

    # 定义各文件的无效值
    temp_data, temp_mask, transform = read_and_filter(
        temp_path, [-3.4028234663852886e+38]
    )
    rf_data, rf_mask, _ = read_and_filter(rf_path, [np.nan])
    rsei_data, rsei_mask, _ = read_and_filter(rsei_path, [-9999.0])
    lucc_data, lucc_mask, _ = read_and_filter(lucc_path, [0])

    # 合并所有掩膜（仅保留所有文件均有效的像素）
    global_mask = temp_mask & rf_mask & rsei_mask & lucc_mask
    rows, cols = global_mask.shape

    # 提取有效像素的坐标和值
    y_coords, x_coords = np.where(global_mask)
    data = pd.DataFrame({
        'x': x_coords,
        'y': y_coords,
        'temperature': temp_data[global_mask],
        'rainfall': rf_data[global_mask],
        'rsei': rsei_data[global_mask],
        'lucc': lucc_data[global_mask]
    })

    # 处理LUCC（植被覆盖度映射）
    lucc_dict = {
        10: 0.4, 11: 0.5, 20: 0.4, 51: 0.7, 52: 0.9, 61: 0.6, 62: 0.8,
        71: 0.6, 72: 0.8, 91: 0.7, 120: 0.6, 121: 0.65, 130: 0.5,
        150: 0.3, 181: 0.5, 182: 0.5, 183: 0.4, 190: 0.1, 200: 0.05, 210: 0.0
    }
    data['lucc_veg'] = data['lucc'].map(lucc_dict).fillna(0.0)
    return data, transform, rows, cols

# 加载数据（自动过滤无效值）
data, transform, rows, cols = load_tiff_data(
    "D:/Google/GWR/tpt_2000_resampled.tif",
    "D:/Google/GWR/2000_resampled.tif",
    "D:/Google/GWR/RSEI_2000_resampled.tif",
    "D:/Google/GWR/poyang_2000_resampled.tif"
)

# 构建空间权重矩阵（仅基于有效像素）
coords = data[['x', 'y']].values
bandwidth = 0.045  # 约500m
tree = cKDTree(coords)
weights = [tree.query_ball_point(coord, bandwidth) for coord in coords]

def local_rf(i):
    """局部随机森林（自动跳过无效样本）"""
    local_indices = weights[i]
    if len(local_indices) >= 30:  # 最小样本量
        local_data = data.iloc[local_indices]
        X = local_data[['temperature', 'rainfall', 'lucc_veg']]
        y = local_data['rsei']
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        return rf.feature_importances_
    else:
        return np.array([np.nan, np.nan, np.nan])

# 并行计算
results = joblib.Parallel(n_jobs=-1)(
    joblib.delayed(local_rf)(i) for i in range(len(data))
)

# 保存结果（将有效值填充回原始栅格）
importance = np.array(results)
output = np.full((rows, cols, 3), np.nan)  # 初始化全为NaN
output[data['y'].values, data['x'].values] = importance  # 填充有效位置

with rasterio.open(
    "D:/Google/GWR/gwrf_importance_2000.tif", 'w',
    driver='GTiff', height=rows, width=cols, count=3,
    dtype=np.float32, crs='EPSG:4326', transform=transform
) as dst:
    dst.write(output.transpose(2, 0, 1))  # 调整维度为 [band, row, col]