import os
import numpy as np
from osgeo import gdal, ogr, osr


def process_and_clip_raster(input_raster_path, output_raster_path, clip_shapefile_path):
    """
    处理栅格数据，将NaN值替换为1，并使用矢量边界裁剪

    参数:
    input_raster_path (str): 输入栅格影像路径
    output_raster_path (str): 输出栅格影像路径
    clip_shapefile_path (str): 用于裁剪的矢量边界路径
    """
    # 注册所有GDAL驱动
    gdal.AllRegister()

    # 读取输入栅格
    print(f"正在读取栅格数据: {input_raster_path}")
    input_ds = gdal.Open(input_raster_path, gdal.GA_ReadOnly)
    if input_ds is None:
        print(f"错误: 无法打开栅格数据 {input_raster_path}")
        return

    # 获取栅格信息
    geotransform = input_ds.GetGeoTransform()
    projection = input_ds.GetProjection()
    width = input_ds.RasterXSize
    height = input_ds.RasterYSize
    band_count = input_ds.RasterCount

    # 创建输出文件夹(如果不存在)
    output_dir = os.path.dirname(output_raster_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")

    # 临时文件路径
    temp_filled_path = os.path.join(output_dir, "temp_filled.tif")

    # 处理每个波段，将NaN替换为1
    print("正在处理栅格数据，将NaN值替换为1...")
    driver = gdal.GetDriverByName('GTiff')
    temp_ds = driver.Create(temp_filled_path, width, height, band_count, gdal.GDT_Float32)
    temp_ds.SetGeoTransform(geotransform)
    temp_ds.SetProjection(projection)

    for band_idx in range(1, band_count + 1):
        input_band = input_ds.GetRasterBand(band_idx)
        data = input_band.ReadAsArray().astype(np.float32)

        # 替换NaN为1
        nan_mask = np.isnan(data)
        data[nan_mask] = 2.0

        # 写入临时文件
        temp_band = temp_ds.GetRasterBand(band_idx)
        temp_band.WriteArray(data)
        temp_band.SetNoDataValue(-9999)  # 设置NoData值(如果需要)
        temp_band.FlushCache()

    # 关闭数据集
    temp_ds = None
    input_ds = None

    # 使用shp文件裁剪栅格
    print(f"正在使用矢量边界裁剪栅格: {clip_shapefile_path}")

    # 打开矢量数据
    ogr.RegisterAll()
    clip_ds = ogr.Open(clip_shapefile_path)
    if clip_ds is None:
        print(f"错误: 无法打开矢量数据 {clip_shapefile_path}")
        # 清理临时文件
        if os.path.exists(temp_filled_path):
            os.remove(temp_filled_path)
        return

    # 获取矢量图层
    clip_layer = clip_ds.GetLayer()

    # 使用gdal.Warp进行裁剪
    warp_options = gdal.WarpOptions(
        cutlineDSName=clip_shapefile_path,
        cropToCutline=True,
        dstNodata=-9999,  # 设置输出NoData值
        format='GTiff'
    )

    gdal.Warp(output_raster_path, temp_filled_path, options=warp_options)

    # 清理临时文件
    if os.path.exists(temp_filled_path):
        os.remove(temp_filled_path)

    print(f"处理完成，结果已保存至: {output_raster_path}")


if __name__ == "__main__":
    # 设置输入输出路径
    # input_raster = r"D:\Google\RSEI_2000_2022\RSEI_2000.tif"
    # output_raster = r"D:\Google\RSEI_full\F_RSEI_del.tif"
    clip_shapefile = r"D:\Google\ESRI\poyangRegion.shp"

    for year in range(2000, 2023):
        input_raster = r"D:\Google\RSEI_2000_2022\RSEI_{}.tif".format(year)
        output_raster = r"D:\Google\RSEI_full\F_RSEI_{}.tif".format(year)
        process_and_clip_raster(input_raster, output_raster, clip_shapefile)
