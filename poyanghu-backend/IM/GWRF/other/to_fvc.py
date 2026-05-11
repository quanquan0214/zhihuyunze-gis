# lucc热编码错误，线性太多，不能使用。

# 测试一下什么占比最大
# 该路行不通，GWR不可用。全面换成SLM模型


import os
import numpy as np
import rasterio
from rasterio.mask import mask
import fiona
from rasterio.warp import transform_geom

# 常量定义
NDVI_DIR_TEMPLATE = "D:/Google/NDVI/NDVI_{}.tif"
FVC_DIR_TEMPLATE = "D:/Google/FVC/FVC_{}.tif"
SHAPE_FILE = "D:/GeographicData/鄱阳湖/PoYangRegion/poyangRegion.shp"
YEARS = range(2000, 2023)  # 2000到2022年
WATER_VALUE = 0  # 水体填充值
NDVI_RANGE = (0, 1)  # NDVI理论范围

def process_ndvi_to_fvc(year):
    # 1. 读取NDVI数据
    ndvi_path = NDVI_DIR_TEMPLATE.format(year)
    try:
        with rasterio.open(ndvi_path) as src:
            ndvi_data = src.read(1)
            profile = src.profile.copy()
            print(f"原始NDVI统计 - 有效值: Min={np.nanmin(ndvi_data):.3f}, Max={np.nanmax(ndvi_data):.3f}")

            # 填补空值为水体（0），并裁剪到[0,1]
            ndvi_data = np.where(np.isnan(ndvi_data) | (ndvi_data == src.nodata), WATER_VALUE, ndvi_data)
            ndvi_data = np.clip(ndvi_data, *NDVI_RANGE)

            # 2. 用矢量边界裁剪（统一坐标系为WGS84）
            with fiona.open(SHAPE_FILE, "r") as shapefile:
                shapes = [feature["geometry"] for feature in shapefile]
                if shapefile.crs.to_epsg() != 4326:
                    shapes = [transform_geom(shapefile.crs, "EPSG:4326", geom) for geom in shapes]

            clipped_data, clipped_transform = mask(src, shapes, crop=True)
            clipped_data = clipped_data[0]  # 取第一个波段
            print(f"裁剪后NDVI统计 - 有效值: Min={np.nanmin(clipped_data):.3f}, Max={np.nanmax(clipped_data):.3f}")

            # 3. 计算FVC（仅统计非水体且非NaN的值）
            valid_ndvi = clipped_data[(clipped_data > WATER_VALUE) & ~np.isnan(clipped_data)]
            if len(valid_ndvi) == 0:
                print(f"错误: {year}年无有效植被像元，跳过！")
                return

            ndvi_min = np.percentile(valid_ndvi, 5)
            ndvi_max = np.percentile(valid_ndvi, 95)
            print(f"NDVI极值（排除NaN和水体）: Min={ndvi_min:.3f}, Max={ndvi_max:.3f}")

            # 如果极值差过小，使用默认范围
            if (ndvi_max - ndvi_min) < 0.01:
                ndvi_min, ndvi_max = 0.2, 0.8
                print(f"警告: 动态范围过小，使用默认值[{ndvi_min}, {ndvi_max}]")

            fvc_data = (clipped_data - ndvi_min) / (ndvi_max - ndvi_min)
            fvc_data = np.clip(fvc_data, 0, 1)
            fvc_data[np.isnan(clipped_data) | (clipped_data == WATER_VALUE)] = WATER_VALUE

            # 4. 保存FVC
            profile.update(
                height=clipped_data.shape[0],
                width=clipped_data.shape[1],
                transform=clipped_transform,
                nodata=WATER_VALUE
            )
            fvc_path = FVC_DIR_TEMPLATE.format(year)
            os.makedirs(os.path.dirname(fvc_path), exist_ok=True)
            with rasterio.open(fvc_path, "w", **profile) as dst:
                dst.write(fvc_data, 1)

            # 5. 验证坐标系
            if rasterio.open(fvc_path).crs.to_epsg() != 4326:
                print(f"坐标系非WGS84的文件: {fvc_path}")

    except Exception as e:
        print(f"处理{year}年时出错: {e}")

# 批量处理
for year in YEARS:
    print(f"\n===== 处理 {year} 年 =====")
    process_ndvi_to_fvc(year)

print("全部处理完成！")
