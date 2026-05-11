# 数据重采样，将精度都调整到RSEI的500m
# import rasterio
# from rasterio.warp import reproject, Resampling
# import numpy as np

# # 目标分辨率和范围（基于RSEI）
# target_res = (0.0044915764205976155, 0.004491576420597607)
# target_bounds = (113.94231063772011, 26.504792457946483, 118.4788028225237, 30.080087288742178)
# target_shape = (796, 1010)  # 高度、宽度
#
# # 重采样函数
# def resample_tiff(input_path, output_path, target_res, target_bounds, target_shape, resampling_method=Resampling.bilinear):
#     with rasterio.open(input_path) as src:
#         data = src.read(1)
#         transform = src.transform
#         # 计算目标变换矩阵
#         dst_transform = rasterio.transform.from_bounds(*target_bounds, target_shape[1], target_shape[0])
#         # 创建输出数组
#         dst_data = np.zeros(target_shape, dtype=data.dtype)
#         # 重采样
#         reproject(
#             source=data,
#             destination=dst_data,
#             src_transform=transform,
#             src_crs=src.crs,
#             dst_transform=dst_transform,
#             dst_crs=src.crs,
#             resampling=resampling_method
#         )
#         # 保存结果
#         with rasterio.open(
#             output_path, 'w',
#             driver='GTiff', height=target_shape[0], width=target_shape[1], count=1,
#             dtype=dst_data.dtype, crs=src.crs, transform=dst_transform
#         ) as dst:
#             dst.write(dst_data, 1)
#
#
# # 重采样所有数据
# resample_tiff(
#     "D:/Google/temperture/tpt/tpt_2000.tif",
#     "D:/Google/GWR/tpt_2000_resampled.tif",
#     target_res, target_bounds, target_shape, Resampling.bilinear
# )
# resample_tiff(
#     "D:/Google/rainfall/RF/2000.tif",
#     "D:/Google/GWR/2000_resampled.tif",
#     target_res, target_bounds, target_shape, Resampling.bilinear
# )
# resample_tiff(
#     "D:/Google/RSEI_full/RSEI_2000.tif",
#     "D:/Google/GWR/RSEI_2000_resampled.tif",
#     target_res, target_bounds, target_shape, Resampling.bilinear
# )
# resample_tiff(
#     "D:/Google/GLC_FCS30/merged/poyang_2000.tif",
#     "D:/Google/GWR/poyang_2000_resampled.tif",
#     target_res, target_bounds, target_shape, Resampling.nearest  # 分类数据用最近邻
# )

# def fix_nodata(input_path, output_path, nodata_value=-9999.0, new_nodata=np.nan):
#     with rasterio.open(input_path) as src:
#         data = src.read(1)
#         profile = src.profile
#         # 替换nodata值
#         data_fixed = np.where(data == nodata_value, new_nodata, data)
#         # 保存
#         if np.isnan(new_nodata):
#             # rasterio不支持float32的nodata为nan，建议用0或2等特殊值，或直接保留nan（但部分软件读取有问题）
#             profile.update(nodata=None)
#         else:
#             profile.update(nodata=new_nodata)
#         with rasterio.open(output_path, 'w', **profile) as dst:
#             dst.write(data_fixed, 1)
#
# # 示例：将-9999.0替换为np.nan或0或2
# fix_nodata("D:/Google/GWR/RSEI_2000_resampled.tif", "D:/Google/GWR/RSEI_2000_fixed.tif", nodata_value=-9999.0, new_nodata=0)


import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np

# 目标分辨率和范围（基于RSEI）
target_res = (0.0044915764205976155, 0.004491576420597607)
target_bounds = (113.94231063772011, 26.504792457946483, 118.4788028225237, 30.080087288742178)
target_shape = (796, 1010)  # 高度、宽度

def resample_tiff(input_path, output_path, target_res, target_bounds, target_shape, resampling_method=Resampling.bilinear, safe_nodata=0):
    with rasterio.open(input_path) as src:
        data = src.read(1)
        src_nodata = src.nodata

        # 将原始nodata和nan设为一个安全值（如0），方便后续处理
        if src_nodata is not None:
            mask = (data == src_nodata) | np.isnan(data)
        else:
            mask = np.isnan(data)
        data = np.where(mask, safe_nodata, data)

        transform = src.transform
        dst_transform = rasterio.transform.from_bounds(*target_bounds, target_shape[1], target_shape[0])
        dst_data = np.full(target_shape, safe_nodata, dtype=data.dtype)

        # 重采样
        reproject(
            source=data,
            destination=dst_data,
            src_transform=transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=src.crs,
            resampling=resampling_method,
            src_nodata=safe_nodata,
            dst_nodata=safe_nodata
        )

        # 对重采样结果，如果出现非常小的负值或极大异常值，也设为safe_nodata
        # 你可以自定义更严格的范围，比如RSEI范围[0,1]，温度可以合理限制等
        if "RSEI" in input_path or "rsei" in input_path.lower():
            dst_data[(dst_data < 0) | (dst_data > 2)] = safe_nodata  # 有水体为2的情况
        if "poyang" in input_path.lower():
            # 分类数据，0/1/2/3/4...，通常不处理
            pass
        # 其它变量可自定义范围

        profile = src.profile.copy()
        profile.update({
            'height': target_shape[0],
            'width': target_shape[1],
            'transform': dst_transform,
            'nodata': safe_nodata,
            'driver': 'GTiff'
        })

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(dst_data, 1)

# 重采样所有数据
resample_tiff(
    "D:/Google/temperture/tpt/tpt_2000.tif",
    "D:/Google/GWR/tpt_2000_resampled.tif",
    target_res, target_bounds, target_shape, Resampling.bilinear, safe_nodata=0
)
resample_tiff(
    "D:/Google/rainfall/RF/2000.tif",
    "D:/Google/GWR/2000_resampled.tif",
    target_res, target_bounds, target_shape, Resampling.bilinear, safe_nodata=0
)
resample_tiff(
    "D:/Google/RSEI_full/RSEI_2000.tif",
    "D:/Google/GWR/RSEI_2000_resampled.tif",
    target_res, target_bounds, target_shape, Resampling.bilinear, safe_nodata=0
)
resample_tiff(
    "D:/Google/GLC_FCS30/merged/poyang_2000.tif",
    "D:/Google/GWR/poyang_2000_resampled.tif",
    target_res, target_bounds, target_shape, Resampling.nearest, safe_nodata=0
)