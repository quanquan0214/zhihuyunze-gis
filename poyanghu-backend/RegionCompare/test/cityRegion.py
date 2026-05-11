import geopandas as gpd
import os
import pandas as pd

# 城市列表
cities = ['抚州市', '鹰潭市', '上饶市', '南昌市', '九江市', '景德镇市']

# 创建一个空的GeoDataFrame来存储所有城市
merged_gdf = gpd.GeoDataFrame()

for city in cities:
    # 假设每个城市的GeoJSON文件名为"城市名.geojson"
    file_path = f"D:/Google/GLC_FCS30/{city}_市.geojson"
    if os.path.exists(file_path):
        # 读取GeoJSON文件
        gdf = gpd.read_file(file_path)
        # 添加城市名称字段（如果原始数据中没有）
        gdf['city_name'] = city
        # 合并到总数据中
        merged_gdf = gpd.GeoDataFrame(pd.concat([merged_gdf, gdf], ignore_index=True))
    else:
        print(f"警告: 未找到 {file_path}")

# 保存为Shapefile
output_path = "D:/Google/GLC_FCS30/cityRegion.shp"
merged_gdf.to_file(output_path, encoding='utf-8')
print(f"合并完成，已保存为 {output_path}")