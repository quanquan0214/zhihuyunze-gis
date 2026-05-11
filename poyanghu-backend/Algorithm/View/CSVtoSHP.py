# 将csv转换成point的shp文件
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def CSV_to_Shp(csv_path, output_shp_path, lon_col, lat_col):
    # 读取 CSV 文件
    df = pd.read_csv(csv_path)
    # 创建几何点
    geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
    # 创建 GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
    # 添加 FID 字段，从 1 开始顺序增加
    gdf['FID'] = range(1, len(gdf) + 1)
    # 保存为 Shapefile
    gdf.to_file(output_shp_path)

# 文件集合操作
# csv_folder = 'D:/Google/H5/Processed/OutputCSV/'
# vtk_folder = 'D:/Google/H5/Processed/PointSHP/'
# # 使用正确的列名
# lon_col = 'lon'
# lat_col = 'lat'
# for filename in os.listdir(csv_folder):
#     if filename.endswith('.csv'):
#         csv_path = os.path.join(csv_folder, filename)
#         output_shp_path = os.path.join(vtk_folder, filename.replace('.csv', '_points.shp'))
#         CSV_to_Shp(csv_path, output_shp_path, lon_col, lat_col)
#         print('生成shp文件:', output_shp_path)
#     else:
#         print('跳过非csv文件:', filename)


# 单个文件操作
csv_folder = 'D:/Google/H5/Processed/model/New_A.csv'
shp_folder = 'D:/Google/H5/Processed/model/New_A_points.shp'
# 使用正确的列名
lon_col = 'lon'
lat_col = 'lat'
CSV_to_Shp(csv_folder, shp_folder, lon_col, lat_col)