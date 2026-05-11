# 插值是没有用的，表面上看起来没有区别
# 使用GEE计算year结果，然后用GEE_1提取数据
# 然后直接符号化
# 读取温度的影像，求温度影像的分辨率，将降水的精度插值成和温度一样的分辨率，便于后续分析计算。

# 去Claude里面问精度更高的那个数据集的精度是多少，使用那个数据集
# 使用GEE计算year结果，然后用GEE_1提取数据
# 读取温度的影像，求温度影像的分辨率，将降水的精度插值成和温度一样的分辨率，便于后续分析计算。





# from osgeo import gdal
# import numpy as np
# from scipy.ndimage import zoom
#
# # 读取低分辨率数据
# input_file = "D:/Google/rainfall/data/200001.tif"
# ds = gdal.Open(input_file)
# if ds is None:
#     raise Exception("Failed to open input file")
# band = ds.GetRasterBand(1)
# low_res = band.ReadAsArray()
#
# # 使用 scipy 进行插值
# zoom_factor = 2  # 2倍放大
# high_res = zoom(low_res, zoom_factor, order=1)  # order=1 for bilinear interpolation
#
# # 获取原始地理变换和投影
# geotransform = list(ds.GetGeoTransform())
# projection = ds.GetProjection()
#
# # 更新地理变换（分辨率减半，保持左上角坐标）
# geotransform[1] /= zoom_factor  # x-resolution (e.g., 1000m to 500m)
# geotransform[5] /= zoom_factor  # y-resolution (e.g., -1000m to -500m)
#
# # 保存结果
# driver = gdal.GetDriverByName("GTiff")
# rows, cols = high_res.shape
# out_ds = driver.Create("D:/Google/rainfall/200001_high_res.tif", cols, rows, 1, gdal.GDT_Float32)
# if out_ds is None:
#     raise Exception("Failed to create output file")
#
# # 设置地理变换和投影
# out_ds.SetGeoTransform(geotransform)
# out_ds.SetProjection(projection)
#
# # 写入数据
# out_band = out_ds.GetRasterBand(1)
# out_band.WriteArray(high_res)
#
# # 清理
# out_band = None
# out_ds = None
# ds = None

from osgeo import gdal
import numpy as np
from scipy.ndimage import zoom

# 读取低分辨率数据
input_file = "D:/Google/rainfall/data/200001.tif"
ds = gdal.Open(input_file)
if ds is None:
    raise Exception("Failed to open input file")
band = ds.GetRasterBand(1)
low_res = band.ReadAsArray()

# 使用 scipy 进行插值
zoom_factor = 10  # 2倍放大
high_res = zoom(low_res, zoom_factor, order=1)  # order=1 for bilinear interpolation

# 获取原始地理变换和投影
geotransform = list(ds.GetGeoTransform())
projection = ds.GetProjection()

# 更新地理变换（分辨率减半，保持左上角坐标）
geotransform[1] /= zoom_factor  # x-resolution (e.g., 1000m to 500m)
geotransform[5] /= zoom_factor  # y-resolution (e.g., -1000m to -500m)

# 保存结果
driver = gdal.GetDriverByName("GTiff")
rows, cols = high_res.shape
out_ds = driver.Create("D:/Google/rainfall/200001_550.tif", cols, rows, 1, gdal.GDT_Float32)
if out_ds is None:
    raise Exception("Failed to create output file")

# 设置地理变换和投影
out_ds.SetGeoTransform(geotransform)
out_ds.SetProjection(projection)

# 写入数据
out_band = out_ds.GetRasterBand(1)
out_band.WriteArray(high_res)

# 清理
out_band = None
out_ds = None
ds = None