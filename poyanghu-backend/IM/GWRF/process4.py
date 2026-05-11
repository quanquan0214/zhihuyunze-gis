import os
import numpy as np
import pandas as pd
import rasterio
import geopandas as gpd
from sklearn.preprocessing import StandardScaler

# 将裁剪后的栅格数据转换为CSV格式

# 输入输出路径
input_dir = "D:/Google/GWR"  # 裁剪后的栅格目录
output_csv = "D:/Google/GWR/nanchang_1.csv"  # 输出CSV文件

# 需要处理的栅格文件（变量名应与文件名一致）
raster_files = {
    "RSEI": "nanchang_RSEI_2000_resampled.tif",
    "lucc": "nanchang_poyang_2000_resampled.tif",
    "rainfall": "nanchang_2000_resampled.tif",
    "temperature": "nanchang_tpt_2000_resampled.tif"
}

# 检查文件是否存在
for var, file in raster_files.items():
    if not os.path.exists(os.path.join(input_dir, file)):
        raise FileNotFoundError(f"文件 {file} 不存在！")

# 初始化DataFrame
df = pd.DataFrame()

# 读取第一个栅格文件（用于获取坐标）
with rasterio.open(os.path.join(input_dir, raster_files["lucc"])) as src:
    # 获取栅格坐标
    height, width = src.shape
    rows, cols = np.indices((height, width))
    xs, ys = rasterio.transform.xy(src.transform, rows.flatten(), cols.flatten())

    # 添加坐标到DataFrame
    df["x"] = xs
    df["y"] = ys

# 逐个读取栅格数据并添加到DataFrame
for var, file in raster_files.items():
    with rasterio.open(os.path.join(input_dir, file)) as src:
        data = src.read(1)  # 读取第一波段
        df[var] = data.flatten()  # 展平并添加到DataFrame

# 移除无效值（NoData）
df = df[~df.isna().any(axis=1)]  # 删除任何包含NaN的行
df = df[df["RSEI"] != 0]

# 将lucc转换为分类类型并独热编码
data['lucc'] = data['lucc'].astype('category')
lucc_dummies = pd.get_dummies(data['lucc'], prefix='lucc', drop_first=True)  # 避免多重共线性
data = pd.concat([data.drop('lucc', axis=1), lucc_dummies], axis=1)

# 确保独热编码后的lucc列已转换为0/1
lucc_columns = [col for col in data.columns if col.startswith('lucc_')]
data[lucc_columns] = data[lucc_columns].astype(int)

# # 对连续变量标准化（解决尺度差异）
scaler = StandardScaler()
data[['temperature', 'rainfall']] = scaler.fit_transform(data[['temperature', 'rainfall']])

# 保存为CSV
df.to_csv(output_csv, index=False)
print(f"数据已保存至 {output_csv}")

