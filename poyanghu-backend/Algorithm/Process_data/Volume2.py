# 本文件要使用全年水体面积最大时期的shp文件，以及通过merge_csv后得到的虚拟水位数据文件。


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

def read_elevation_from_csv(csv_file_path,t):
    try:
        # 读取 CSV 文件
        df = pd.read_csv(csv_file_path)
        elevation = df['ht_water_surf'].mean()
        return elevation
    except Exception as e:
        print(f"读取 CSV 文件时发生错误: {e}")
        return None


shp_file_path = 'D:/Google/H5/Processed/2019_NDWI.shp'
area = calculate_area_in_km2(shp_file_path)
if area is not None:
    print(f"面要素的面积是: {area} 平方千米")

csv_file_path = 'D:/Google/H5/Processed/model/New_20190807.csv'
elevation = read_elevation_from_csv(csv_file_path,2019)
if elevation is not None:
    print(f"2019年8月的 Elevation 值是: {elevation}")

Volume = area * elevation * 1000000
print(f"水储量是: {Volume} 立方米")