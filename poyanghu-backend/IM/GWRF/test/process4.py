'''4. Python自定义实现GWRF
Python实现GWRF需要结合rasterio（处理TIFF）、libpysal（空间权重）和scikit-learn（随机森林）。由于数据量适中（80万像元），Python的并行化能力（joblib）非常适合。
实现步骤
1. 数据准备：读取重采样后的TIFF数据，转换为表格形式。
2. 空间权重：使用libpysal生成基于距离的权重矩阵。
3. 局部随机森林：对每个像元运行随机森林，计算变量重要性。
4. 结果保存：将结果保存为TIFF格式。'''

# 综合示例代码

import numpy as np
import pandas as pd
import rasterio
from sklearn.ensemble import RandomForestRegressor
from libpysal.weights import DistanceBand
from scipy.spatial import cKDTree
import joblib


# 读取重采样后的TIFF数据
def load_tiff_data(temp_path, rf_path, rsei_path, lucc_path):
    with rasterio.open(temp_path) as temp:
        temperature = temp.read(1)
        transform = temp.transform
    with rasterio.open(rf_path) as rf:
        rainfall = rf.read(1)
    with rasterio.open(rsei_path) as rsei:
        rsei_data = rsei.read(1)
    with rasterio.open(lucc_path) as lucc:
        lucc_data = lucc.read(1)

    # 转换为表格
    rows, cols = temperature.shape
    x, y = np.meshgrid(np.arange(cols), np.arange(rows))
    coords = np.vstack([x.ravel(), y.ravel()]).T
    data = pd.DataFrame({
        'x': coords[:, 0], 'y': coords[:, 1],
        'temperature': temperature.ravel(),
        'rainfall': rainfall.ravel(),
        'rsei': rsei_data.ravel(),
        'lucc': lucc_data.ravel()
    })
    data = data.dropna()

    # 处理LUCC（植被覆盖度）
    lucc_dict = {
        10: 0.4, 11: 0.5, 20: 0.4, 51: 0.7, 52: 0.9, 61: 0.6, 62: 0.8,
        71: 0.6, 72: 0.8, 91: 0.7, 120: 0.6, 121: 0.65, 130: 0.5,
        150: 0.3, 181: 0.5, 182: 0.5, 183: 0.4, 190: 0.1, 200: 0.05, 210: 0.0
    }
    data['lucc_veg'] = data['lucc'].map(lucc_dict).fillna(0.0)  # 未映射类别设为0
    return data, transform, rows, cols


# 加载数据
data, transform, rows, cols = load_tiff_data(
    "D:/Google/GWR_k/tpt_2000_resampled.tif",
    "D:/Google/GWR_k/2000_resampled.tif",
    "D:/Google/GWR_k/RSEI_2000_resampled.tif",
    "D:/Google/GWR_k/poyang_2000_resampled.tif"
)

# 构建空间权重矩阵
coords = data[['x', 'y']].values
bandwidth = 0.045  # 约500m
tree = cKDTree(coords)
weights = [tree.query_ball_point(coord, bandwidth) for coord in coords]


# GWRF函数
def local_rf(i):
    local_indices = weights[i]
    if len(local_indices) > 30:  # 最小样本量
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

# 保存结果为TIFF
importance = np.array(results).reshape(-1, 3)
output = np.full((rows * cols, 3), np.nan)
output[:len(importance)] = importance
output = output.reshape(rows, cols, 3)

with rasterio.open(
        "D:/Google/GWR/gwrf_importance_2000.tif", 'w',
        driver='GTiff', height=rows, width=cols, count=3,
        dtype=output.dtype, crs='EPSG:4326', transform=transform
) as dst:
    dst.write(output)













