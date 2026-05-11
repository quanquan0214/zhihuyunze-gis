import os
import rasterio
from rasterio.mask import mask
import fiona
import numpy as np

# 常量定义
NDVI_DIR_TEMPLATE = "D:/Google/NDVI/NDVI_{}.tif"
FVC_DIR_TEMPLATE = "D:/Google/FVC/FVC_{}.tif"
SHAPE_FILE = "D:/GeographicData/鄱阳湖/PoYangRegion/poyangRegion.shp"
YEARS = range(2000, 2023)  # 2000到2022年
WATER_VALUE = 0  # 水体填充值
NDVI_RANGE = (0, 1)  # NDVI理论范围



def process_ndvi_to_fvc(year):
    # 1. 读取并填补NDVI
    ndvi_path = NDVI_DIR_TEMPLATE.format(year)
    with rasterio.open(ndvi_path) as src:
        ndvi_data = src.read(1)
        print(f"原始NDVI统计: Min={ndvi_data.min()}, Max={ndvi_data.max()}")

        # 填补空值和水体
        ndvi_data[np.isnan(ndvi_data) | (ndvi_data == src.nodata)] = WATER_VALUE
        ndvi_data = np.clip(ndvi_data, 0, 1)  # 强制限制范围

    # 2. 统一坐标系并裁剪
    with fiona.open(SHAPE_FILE, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
        if shapefile.crs.to_epsg() != 4326:
            shapes = [rasterio.warp.transform_geom(shapefile.crs, "EPSG:4326", geom) for geom in shapes]

    with rasterio.open(ndvi_path) as src:
        clipped_data, clipped_transform = mask(src, shapes, crop=True)
        clipped_data = clipped_data[0]
        print(f"裁剪后NDVI统计: Min={clipped_data.min()}, Max={clipped_data.max()}")

    # 3. 计算FVC（动态排除水体）
    valid_ndvi = clipped_data[clipped_data > WATER_VALUE]
    if len(valid_ndvi) == 0:
        print(f"错误: {year}年无有效植被像元，跳过！")
        return

    ndvi_min = np.percentile(valid_ndvi, 5)
    ndvi_max = np.percentile(valid_ndvi, 95)
    print(f"NDVI极值: Min={ndvi_min:.3f}, Max={ndvi_max:.3f}")

    if (ndvi_max - ndvi_min) < 0.01:
        ndvi_min, ndvi_max = 0.2, 0.8  # 默认植被范围

    fvc_data = (clipped_data - ndvi_min) / (ndvi_max - ndvi_min)
    fvc_data = np.clip(fvc_data, 0, 1)
    fvc_data[clipped_data == WATER_VALUE] = WATER_VALUE

    # 4. 保存并验证
    fvc_path = FVC_DIR_TEMPLATE.format(year)
    with rasterio.open(fvc_path, "w", **src.profile) as dst:
        dst.write(fvc_data, 1)

    if rasterio.open(fvc_path).crs.to_epsg() != 4326:
        print(f"坐标系错误: {fvc_path}")

# 批量处理所有年份
for year in YEARS:
    print(f"正在处理 {year} 年数据...")
    process_ndvi_to_fvc(year)

print("全部处理完成！")