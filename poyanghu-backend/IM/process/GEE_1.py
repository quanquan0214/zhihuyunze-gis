# 将从GEE下载的多波段预报降水量数据（2000年）分解为单波段数据，并保存到指定目录。

import os
import rasterio

# 输入输出路径
input_path = "D:/Google/rainfall/2022_precip.tif"
output_dir = "D:/Google/rainfall/data/"
os.makedirs(output_dir, exist_ok=True)  # 创建输出目录

# 读取多波段影像
with rasterio.open(input_path) as src:
    # 获取所有波段名称（应为 precip_01 到 precip_12）
    band_names = src.descriptions

    # 检查波段名称是否符合预期
    if not all([f"precip_{i:02d}" in band_names for i in range(1, 13)]):
        print("警告：波段名称不符合 precip_01 到 precip_12 的格式")

    # 逐个波段处理
    for band_idx, band_name in enumerate(band_names, start=1):
        # 提取月份数字（从 precip_01 中提取 01）
        month = band_name.split('_')[-1]

        # 构建输出文件名（200001.tif）
        output_filename = f"2022{month}.tif"
        output_path = os.path.join(output_dir, output_filename)

        # 读取当前波段数据
        band_data = src.read(band_idx)

        # 写入单波段文件（保持与原文件相同的元数据）
        with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=src.height,
                width=src.width,
                count=1,
                dtype=band_data.dtype,
                crs=src.crs,
                transform=src.transform
        ) as dst:
            dst.write(band_data, 1)
            dst.set_band_description(1, band_name)  # 可选：保留波段描述

        print(f"已保存：{output_path}")

print("处理完成！")