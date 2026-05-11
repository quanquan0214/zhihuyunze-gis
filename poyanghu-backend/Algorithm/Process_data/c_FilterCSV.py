# 读取一个Shapefile文件（.shp）和一个文件夹中所有CSV文件（.csv），然后分别筛选出每个位于Shapefile范围内的CSV数据，
# 并将筛选出的数据分别写入一个新的CSV文件中，新的CSV文件的命名方式为原文件名加上"_shp"后缀：

# import os
# import geopandas as gpd
# import pandas as pd

# #(因在b中定义了bbox,所以这里不再需要通过gdf.bounds获取经纬度范围。直接整合即可)
#
#
# # 读取Shapefile文件(2019年鄱阳湖水域max)
# sf = gpd.read_file('D:/Google/H5/Processed/2019/2019_max.shp')
# # 检查当前的坐标系
# print(sf.crs)
# # 转换为WGS84坐标系（EPSG:4326）
# gdf = sf.to_crs(epsg=4326)
# # 现在gdf.bounds的值应该是经纬度
# print(gdf.bounds)
#
# # 创建保存筛选结果的文件夹
# output_folder = 'D:/Google/H5/Processed/FilteredCSV/'
# os.makedirs(output_folder, exist_ok=True)
#
# # 遍历CSV文件夹中的所有文件
# csv_folder = 'D:/Google/H5/Processed/CSV/'
# for filename in os.listdir(csv_folder):
#     if filename.endswith('.csv'):
#         csv_path = os.path.join(csv_folder, filename)
#
#         # 读取CSV文件
#         df = pd.read_csv(csv_path)
#
#         # 筛选出Shapefile范围内的数据
#         df = df[(df['lon'] > gdf.bounds['minx'][0]) &
#                 (df['lat'] > gdf.bounds['miny'][0]) &
#                 (df['lon'] < gdf.bounds['maxx'][0]) &
#                 (df['lat'] < gdf.bounds['maxy'][0])]
#
#         # 生成新的CSV文件路径
#         output_filename = os.path.splitext(filename)[0] + '_shp.csv'
#         output_path = os.path.join(output_folder, output_filename)
#
#         # 将筛选出的数据写入新的CSV文件
#         df.to_csv(output_path, index=False)
#



# 如果由于相同时间有多个csv文件，将其合并起来，运行以下代码：

import os
import pandas as pd

# 创建保存整合结果的文件夹
output_folder = 'D:/Google/H5/Processed2025/OutputCSV/'
os.makedirs(output_folder, exist_ok=True)

# 遍历CSV文件夹中的所有文件
csv_folder = 'D:/Google/H5/Processed2025/CSV/'
for filename in os.listdir(csv_folder):
    if filename.endswith('.csv'):
        csv_path = os.path.join(csv_folder, filename)

        # 从文件名中提取时间信息
        year = filename[6:10]
        month = filename[10:12]
        day = filename[12:14]
        date = f"{year}-{month}-{day}"

        # 读取CSV文件
        df = pd.read_csv(csv_path)

        # 生成新的CSV文件路径
        output_filename = f"{date}.csv"
        output_path = os.path.join(output_folder, output_filename)

        # 将数据追加到新的CSV文件中
        df.to_csv(output_path, mode='a', index=False, header=not os.path.exists(output_path))
