# 测试：由shp和csv文件计算水储量
# 使用的是一年内水体最大的shp文件和e_transTime后的全年平均文件。

import geopandas as gpd
import pyproj
import pandas as pd

def calculate_area_in_km2(shp_file_path):
    try:
        # 读取 Shapefile 文件
        gdf = gpd.read_file(shp_file_path)
        # 确保只有一个面要素
        if len(gdf) != 1:
            raise ValueError("Shapefile 文件中必须只有一个面要素。")
        # 检查投影信息
        if gdf.crs is None:
            raise ValueError("Shapefile 文件缺少投影信息。")
        # 转换为等面积投影
        equal_area_crs = pyproj.CRS('ESRI:54009')
        gdf = gdf.to_crs(equal_area_crs)
        # 计算面积（单位：平方千米）
        area = gdf.geometry.area[0] / 1e6
        return area
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def R_area_in_km2(shp_file_path):
    try:
        # 读取 Shapefile 文件
        gdf = gpd.read_file(shp_file_path)

        if gdf.crs is None:
            raise ValueError("Shapefile 文件缺少投影信息。")
        # 转换为等面积投影
        equal_area_crs = pyproj.CRS('ESRI:54009')
        gdf = gdf.to_crs(equal_area_crs)
        # 计算面积（单位：平方千米）
        sum = 0
        for i in range(len(gdf)):
            sum = gdf.geometry.area[i]+sum
        area = sum / 1e6
        return area
    except Exception as e:
        print(f"发生错误: {e}")
        return None


def read_elevation_from_csv(csv_file_path,t):
    try:
        # 读取 CSV 文件
        df = pd.read_csv(csv_file_path)
        # 筛选 Time 列为 2019 的行
        filtered_df = df[df['Time'] == t]
        if len(filtered_df) == 0:
            print("未找到2019年的数据。")
            return None
        # 获取 Elevation 值
        elevation = filtered_df['Elevation'].values[0]
        return elevation
    except Exception as e:
        print(f"读取 CSV 文件时发生错误: {e}")
        return None

def calculate_volume(shp_file_path, csv_file_path, t):
    ndwi = shp_file_path + "/NDWI_" + t + ".shp"

    area = calculate_area_in_km2(shp_file_path)
    if area is None:
        return None
    elevation = read_elevation_from_csv(csv_file_path, t)
    if elevation is None:
        return None
    Volume = area * elevation * 1000000
    return Volume

shp_file_path = 'D:/A_PyLake/NDWI/NDWI_201908.shp'
csv_file_path = 'D:/Google/H5/Processed/elevationAverage.csv'

area = R_area_in_km2(shp_file_path)
if area is not None:
    print(f"201908面要素的面积是: {area} 平方千米")

elevation = read_elevation_from_csv(csv_file_path,2019)
if elevation is not None:
    print(f"2019年的 Elevation 值是: {elevation}")

Volume = area * elevation * 1000000
print(f"水储量是: {Volume} 立方米")
