import numpy as np
import pandas as pd
import rasterio
from cuml.ensemble import RandomForestRegressor
from cuml.neighbors import NearestNeighbors
import cupy as cp
import numba.cuda as cuda
from numba import jit
import time


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
print("Loading data...")
start_time = time.time()
data, transform, rows, cols = load_tiff_data(
    "D:/Google/GWR/tpt_2000_resampled.tif",
    "D:/Google/GWR/2000_resampled.tif",
    "D:/Google/GWR/RSEI_2000_resampled.tif",
    "D:/Google/GWR/poyang_2000_resampled.tif"
)
print(f"Data loaded in {time.time() - start_time:.2f} seconds")

# 将数据转换为GPU数组
coords = cp.asarray(data[['x', 'y']].values.astype(np.float32))
features = cp.asarray(data[['temperature', 'rainfall', 'lucc_veg']].values.astype(np.float32))
target = cp.asarray(data['rsei'].values.astype(np.float32))

# 构建空间权重矩阵（使用GPU加速的最近邻搜索）
print("Building spatial weights matrix...")
start_time = time.time()
bandwidth = 0.045  # 约500m
n_neighbors = 100  # 最大邻居数

# 使用近似最近邻搜索加速
knn = NearestNeighbors(n_neighbors=n_neighbors, radius=bandwidth, algorithm='brute')
knn.fit(coords)
distances, indices = knn.kneighbors(coords)

# 转换为权重矩阵
weights = []
for i in range(len(indices)):
    valid_indices = indices[i][distances[i] <= bandwidth]
    weights.append(valid_indices)
print(f"Spatial weights built in {time.time() - start_time:.2f} seconds")

# 预分配结果数组
importance = cp.full((len(data), 3), cp.nan, dtype=np.float32)


# CUDA核函数处理局部随机森林
@cuda.jit
def process_local_rf(features, target, weights, importance, min_samples):
    i = cuda.grid(1)
    if i < features.shape[0]:
        local_indices = weights[i]
        if len(local_indices) >= min_samples:
            # 提取局部数据
            X_local = features[local_indices]
            y_local = target[local_indices]

            # 训练随机森林（这部分需要在CPU上完成，因为cuML的RF不支持在核函数中调用）
            # 实际实现中需要分批处理，这里只是示意

            # 伪代码：实际实现中需要分批处理
            # rf = RandomForestRegressor(n_estimators=100)
            # rf.fit(X_local, y_local)
            # importance[i] = rf.feature_importances_


# 由于CUDA核函数不能直接调用cuML的RF，我们改为分批处理
print("Running GW-RF on GPU...")
start_time = time.time()
batch_size = 10000  # 根据GPU内存调整
n_samples = len(data)

for start in range(0, n_samples, batch_size):
    end = min(start + batch_size, n_samples)
    batch_weights = weights[start:end]

    # 创建批处理数据
    batch_X = []
    batch_y = []
    batch_indices = []

    for i in range(start, end):
        local_indices = weights[i]
        if len(local_indices) >= 30:  # 最小样本量
            batch_X.append(features[local_indices].get())
            batch_y.append(target[local_indices].get())
            batch_indices.append(i)

    if len(batch_X) > 0:
        # 训练随机森林
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        for idx, (X, y) in zip(batch_indices, zip(batch_X, batch_y)):
            rf.fit(X, y)
            importance[idx] = cp.asarray(rf.feature_importances_)

print(f"GW-RF completed in {time.time() - start_time:.2f} seconds")

# 保存结果（将有效值填充回原始栅格）
print("Saving results...")
output = np.full((rows, cols, 3), np.nan)  # 初始化全为NaN
output[data['y'].values, data['x'].values] = importance.get()  # 填充有效位置

with rasterio.open(
        "D:/Google/GWR/gwrf_importance_2000_gpu.tif", 'w',
        driver='GTiff', height=rows, width=cols, count=3,
        dtype=np.float32, crs='EPSG:4326', transform=transform
) as dst:
    dst.write(output.transpose(2, 0, 1))  # 调整维度为 [band, row, col]

print("Processing complete!")